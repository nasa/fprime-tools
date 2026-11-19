"""
Supplies high-level build functions to the greater fprime helper CLI. This maps from user command space to the specific
build system handler underneath.
"""

import copy
import glob
import os
import re
from pathlib import Path
from typing import Iterable, List, Union

# Forces targets into existence
import fprime.fbuild.target_definitions  # lgtm[py/unused-import]
from fprime.common.error import FprimeException
from fprime.fbuild.cmake import CMakeException, CMakeHandler
from fprime.fbuild.settings import IniSettings
from fprime.fbuild.target import Target, TargetScope
from fprime.fbuild.types import (
    AmbiguousToolchainException,
    BuildType,
    InvalidBuildCacheException,
    MissingBuildCachePath,
    NoSuchToolchainException,
    UnableToDetectProjectException,
)


class Build:
    """Represents a build configuration

    Builds in F´ consist of a build type (normal, testing), a cmake project directory, a set of settings, and a target
    platform. These are tracked as part of this Build class. This helps setup a build cache directory, load default
    settings, and track what type of build is being run.

    BuildType represents the type of build as explained in that enum type.
    Projects are an individual build of fprime, and should define the CMakeLists.txt file as a child of this
    directory. A default settings.ini file may be found here.
    Platforms represent the target hardware to build from. This is translated to the CMake toolchain file.

    After creation, a user must use invent to handle new builds (e.g. during the generation step), or load to load a
    previously generated build.

    Examples:
        To use in generation run the following code.

        build = Build(BuildType.BUILD_NORMAL, path/to/project)
        build.invent("raspberrypi")

        To use at any step after generation:

        build = Build(BuildType.BUILD_NORMAL, path/to/project)
        build.load()
    """

    VALID_CMAKE_LIST = re.compile(r"^\s*project\(.*\)", re.MULTILINE)
    CMAKE_DEFAULT_BUILD_NAME = (
        "build-fprime-automatic-{platform}{preset_suffix}{suffix}"
    )

    def __init__(self, build_type: BuildType, project: Path, verbose: bool = False):
        """Constructs a build object from its constituent parts

        Args:
            build_type: member of the enum BuildType specifying fprime build type
            project: path to cmake project that this build represents
        """
        self.build_type = build_type
        self.cmake_root = project
        self.settings = None
        self.platform = None
        self.build_dir = None
        self._build_cache_locations = None
        self._source_locations = None
        self.cmake = CMakeHandler()
        self.cmake.set_verbose(verbose)

    def is_verbose(self) -> bool:
        """Returns the verbose setting of the build"""
        return self.cmake.verbose

    def invent(
        self,
        platform: str = None,
        build_dir: Path = None,
        force=False,
        preset: str = None,
    ):
        """Invents a build path from a given platform

        Sets this build up as a new build that would be used as as part of a generate step. This directory must not
        already exist. If platform is None, a default will be chosen from the settings.ini file. If the settings.ini
        file does not exist, or does not specify a default_toolchain, then "native" will be used. Settings are loaded in
        this step for further uses of this build.

        build_dir is used to specify an exact build directory to use as part of this step. This allows directories to be
        specified by the caller, but is typically not used.

        Args:
            platform:   name of platform to build against. None will use default from settings.ini or without this
                        setting, "native". Defaults to None.
            build_dir:  explicitly sets the build path to allow for user override of default
            preset:     CMake preset name from CLI. Overrides settings.ini preset when provided.

        Raises:
            InvalidBuildCacheException: a build cache already exists as it should not
        """
        self.__setup_default(platform, build_dir, preset=preset)
        if self.build_dir.exists():
            msg = f"{self.build_dir} already exists."
            if not force:
                raise InvalidBuildCacheException(msg)

    # Mapping from CMake cache variable names to settings.ini keys for settings that
    # should be loaded back from the CMake cache after generation.
    CACHE_SETTING_MAP = [
        ("FPRIME_FRAMEWORK_PATH", "framework_path"),
        ("FPRIME_LIBRARY_LOCATIONS", "library_locations"),
        ("FPRIME_PROJECT_ROOT", "project_root"),
        ("FPRIME_SETTINGS_FILE", "settings_file"),
        ("FPRIME_ENVIRONMENT_FILE", "environment_file"),
        ("FPRIME_CONFIG_DIR", "config_directory"),
        ("FPRIME_INSTALL_DEST", "install_destination"),
        ("PROJECT_SOURCE_DIR", "project_source_dir"),
    ]

    def load(self, platform: str = None, build_dir: Path = None, skip_validation=False):
        """Load an existing build cache

        Sets this build up from an existing build cache. This can be used after a previous run that has generated a
        build cache in order to prepare for other build steps. Settings are loaded from the CMake cache as the
        authoritative source, with consistency checks against settings.ini values.

        Args:
            platform:   name of platform to build against. None will use default from settings.ini or without this
                        setting, "native". Defaults to None.
            build_dir:  explicitly sets the build path to allow for user override of default
            skip_validation: (optional) skip cache validation. Default: False, validate away!

        Raises:
            InvalidBuildCacheException: the build cache does not exist as it must
        """
        self.__setup_default(platform, build_dir)
        self._build_cache_locations = self._load_build_cache_locations()

        if skip_validation:
            if self.build_dir is not None and (
                (self.build_dir / "CMakeCache.txt").exists()
            ):
                try:
                    self._load_settings_from_cache()
                except (InvalidBuildCacheException, CMakeException):
                    pass  # Best-effort: cache may be missing or stale
            self._setup_source_locations()
            return
        # Validate this is a build cache by finding either of two known files
        # One is from F´, other from CMake, for redundancy
        if self.build_dir is not None and (
            (self.build_dir / ".fprime-build-dir").exists()
            or (self.build_dir / "CMakeCache.txt").exists()
        ):
            if (self.build_dir / "CMakeCache.txt").exists():
                self._load_settings_from_cache()
            self._setup_source_locations()
            return

        # Message for hard-supplied --build-cache message
        if build_dir is not None:
            gen_args = f" --build-cache {build_dir}"
        else:
            gen_args = " --ut" if self.build_type == BuildType.BUILD_TESTING else ""
            gen_args += (
                " " + platform
                if platform is not None
                and platform != "native"
                and platform != "default"
                else ""
            )
            active_preset = self.settings.get("preset", "") if self.settings else ""
            if active_preset:
                gen_args += f" --preset {active_preset}"
        msg = f"'{self.build_dir}' is not a valid build cache. Generate this build cache with 'fprime-util generate{gen_args} ...'"
        raise InvalidBuildCacheException(
            msg,
            self.build_dir,
        )

    def get_settings(
        self,
        setting: Union[None, str, Iterable[Union[None, str]]],
        default: Union[None, str, Iterable[Union[None, str]]],
    ) -> Union[str, Iterable[str]]:
        """Fetches settings in the settings file

        Reads settings loaded from the settings file and returns them to the caller. If a single string is submitted,
        then a single string is returned. If a list of strings is submitted a list is returned. default provides default
        values to supply in the case that a setting is unavailable.

        Args:
            setting: a string or set of string settings to return
            default: a string or set of string settings to return if no setting is found

        Returns:
            a single string setting or a list of string settings to match request with defaults subbed ins
        """
        if isinstance(setting, str):
            return self.settings.get(setting, default)
        return [self.get_settings(req, back) for req, back in zip(setting, default)]

    def find_hashed_file(self, hash_value: int) -> List[str]:
        """Retrieves the file associated with a hash

        In order to reduce space and memory footprint, filenames are associated with hashes automatically as part of the
        build. This function will retrieve the file name given a has integer.

        Args:
            hash_value: hash number to lookup

        Returns:
            stored file path(s) associated with hash
        """
        hashes_file = self.build_dir / "hashes.txt"
        if not hashes_file.exists():
            msg = f"Failed to find {hashes_file}, was the build generated?"
            raise InvalidBuildCacheException(
                msg,
                self.build_dir,
            )
        with open(hashes_file) as file_handle:
            lines = filter(
                lambda line: hash_value == int(line.split(" ")[-1], 0),
                file_handle.readlines(),
            )
        return list(lines)

    def get_build_cache(self) -> Path:
        """Generates build cache path for this build

        Generates the build path for this build. This will expect a valid build path to exist unless validate is
        specified as false. A valid build cache has been created from the generate step, and thus when using this call
        as part of the generate step, validate should be set to false.

        Returns:
            Path to a build cache directory

        """
        preset = self.settings.get("preset", "")
        preset_suffix = f"-{preset}" if preset else ""
        return self.cmake_root / Build.CMAKE_DEFAULT_BUILD_NAME.format(
            platform=self.platform,
            preset_suffix=preset_suffix,
            suffix=self.build_type.get_suffix(),
        )

    @staticmethod
    def _setting_to_str(value) -> str:
        """Format a setting value as a human-readable string."""
        if isinstance(value, list):
            return ", ".join(str(p) for p in value)
        return str(value)

    def _load_settings_from_cache(self):
        """Load settings from the CMake cache, using it as the authoritative source.

        Reads FPRIME_* variables from the CMake cache and overrides the corresponding
        settings values. If a setting differs between the loaded settings and the cache,
        a hard error is raised instructing the user to regenerate. The cache value is
        always used as the source of truth.
        """
        cache = self.cmake.get_fprime_configuration(
            [cache_var for cache_var, _ in Build.CACHE_SETTING_MAP],
            str(self.build_dir),
        )

        for (cache_var, setting_key), cache_value in zip(
            Build.CACHE_SETTING_MAP, cache
        ):
            if cache_value is None:
                continue

            # Convert cache string to appropriate type matching settings.ini types
            if setting_key == "library_locations":
                converted = (
                    [Path(p) for p in cache_value.split(";") if p]
                    if cache_value
                    else []
                )
            else:
                converted = Path(cache_value)

            # Check consistency with loaded settings
            ini_value = self.settings.get(setting_key)
            if ini_value is not None and ini_value != converted:
                raise InvalidBuildCacheException(
                    f"settings.ini '{setting_key}' value "
                    f"'{Build._setting_to_str(ini_value)}' "
                    f"differs from CMake cache '{cache_var}' value "
                    f"'{Build._setting_to_str(converted)}'. Please regenerate "
                    f"using 'fprime-util generate -f'.",
                    self.build_dir,
                )

            self.settings[setting_key] = converted

        # Reload environment from the (potentially updated) environment file
        env_file = self.settings.get("environment_file")
        if env_file is not None:
            self.settings["environment"] = IniSettings.load_environment(env_file)

    def get_build_info(self, context: Path) -> dict:
        """Constructs an informational packet about this build

        Constructs a packet that allows for users to get meta-build information. This includes: location of build, file
        and other constructs, available make targets, and other items.

        Args:
            context: contextual path to list various information about the build

        Returns:
            Build information dictionary
        """
        temp_targets = Target.get_all_targets()
        # Remove targets that are not supported given the builder and context
        temp_targets = [
            target for target in temp_targets if target.is_supported(self, context)
        ]
        # Now filter for local scope
        local_targets = [
            target
            for target in temp_targets
            if target.scope in [TargetScope.LOCAL, TargetScope.BOTH]
        ]
        global_targets = [
            target
            for target in Target.get_all_targets()
            if target.scope == TargetScope.GLOBAL
        ]
        try:
            auto_location = self.get_build_cache_path(context)
        except MissingBuildCachePath:
            auto_location = None
        return {
            "local_targets": local_targets,
            "global_targets": global_targets,
            "auto_location": auto_location,
            "build_dir": self.build_dir,
        }

    def is_project_root(self, context: Path) -> bool:
        """Check if given path represents a project root

        Args:
            context: contextual path to list various information about the build

        Returns:
            True if the context is a project, false otherwise
        """
        try:
            self.cmake.cmake_validate_source_dir(context)
            return True
        except CMakeException:
            return False

    def _find_cmake_file(
        self, cmake_type: str, name: str
    ) -> "tuple[List[str], List[str]]":
        """Locate cmake files using priority-ordered glob search.

        Search priority (highest to lowest):
            1. Project direct — PROJECT_SOURCE_DIR/cmake/<type>/<name>.cmake
            2. Backwards compat: legacy project root — FPRIME_PROJECT_ROOT/cmake/<type>/<name>.cmake
               (only when FPRIME_PROJECT_ROOT differs from PROJECT_SOURCE_DIR)
            3. Project libraries (lib/) — PROJECT_SOURCE_DIR/lib/*/cmake/<type>/<name>.cmake
            4. Project subdirectories — PROJECT_SOURCE_DIR/*/cmake/<type>/<name>.cmake
            5. Backwards compat: explicit library locations — each FPRIME_LIBRARY_LOCATIONS entry
               (only when defined and non-empty)
            6. Framework fallback — FPRIME_FRAMEWORK_PATH/cmake/<type>/<name>.cmake

        Each pattern is globbed individually and results appended in order to
        preserve priority.  Duplicates are removed preserving first-occurrence
        order.

        Args:
            cmake_type: subdirectory under cmake/ (e.g. "toolchain", "platform")
            name: file stem without .cmake extension

        Returns:
            Tuple of (matched files, searched patterns). Matched files are absolute
            path strings ordered by priority. Searched patterns are the raw glob
            patterns that were attempted.
        """
        project_source_dir = Path(
            self.settings.get("project_source_dir") or self.cmake_root
        )
        project_root = self.get_settings("project_root", None)
        framework_path = self.get_settings("framework_path", None)
        library_locations = self.get_settings("library_locations", [])

        filename = f"{name}.cmake"

        def _cmake_path(*parts):
            return str(Path(*parts) / "cmake" / cmake_type / filename)

        # Pre-compute conditions for backwards-compat patterns
        _project_root_differs = (
            project_root is not None
            and str(project_root) != ""
            and Path(project_root).resolve() != project_source_dir.resolve()
        )

        # Build ordered search patterns — highest priority first
        glob_patterns: List[str] = []

        # 1. Project direct
        glob_patterns += [_cmake_path(project_source_dir)]

        # 2. Backwards compat: legacy project root. Slated for removal.
        glob_patterns += [_cmake_path(project_root)] if _project_root_differs else []

        # 3. Project libraries (lib/) — single level wildcard
        glob_patterns += [_cmake_path(project_source_dir / "lib" / "*")]

        # 4. Project subdirectories — single level wildcard
        glob_patterns += [_cmake_path(project_source_dir / "*")]

        # 5. Backwards compat: explicit library locations. Slated for removal.
        glob_patterns += [
            _cmake_path(loc)
            for loc in library_locations
            if loc is not None and str(loc) != ""
        ]

        # 6. Framework fallback
        glob_patterns += [_cmake_path(framework_path)] if framework_path else []

        # Glob each pattern individually and collect matches
        matches = [
            str(Path(m).resolve())
            for pattern in glob_patterns
            for m in glob.glob(pattern)
        ]
        # De-duplicating by making an ordered dictionary and converting back to a list
        return list(dict.fromkeys(matches)), glob_patterns

    def find_toolchain(self):
        """Locates a toolchain file in known locations.

        Finds a toolchain for the given platform using the priority-ordered glob
        search defined by _find_cmake_file.

        Returns:
            path to CMake toolchain file or None to use builtin
        """
        assert (
            self.platform != "default"
        ), "Default toolchain should have been decided already"

        # Native toolchain is supplied by CMake directly
        if self.platform == "native":
            return None

        results, searched_patterns = self._find_cmake_file("toolchain", self.platform)

        if not results:
            searched_toolchain_paths = "\n" + "\n".join(
                path.removesuffix(f"{self.platform}.cmake")
                for path in searched_patterns
            )
            msg = f"Could not find any toolchain file called {self.platform}.cmake after attempting to search for the file at the following locations: {searched_toolchain_paths}"
            raise NoSuchToolchainException(msg)
        if len(results) > 1:
            conflicting_toolchain_paths = "\n\n" + "\n".join(results)
            msg = f"Found conflicting toolchain files for the toolchain file called {self.platform} in the following locations: {conflicting_toolchain_paths}"
            raise AmbiguousToolchainException(msg)
        return results[0]

    def get_cmake_args(self) -> dict:
        """Generates CMake arguments from project settings (settings.ini file)

        Returns:
            A dictionary of cmake settings
        """
        needed = [
            ("FPRIME_FRAMEWORK_PATH", "framework_path"),
            ("FPRIME_LIBRARY_LOCATIONS", "library_locations"),
            ("FPRIME_PROJECT_ROOT", "project_root"),
            ("FPRIME_SETTINGS_FILE", "settings_file"),
            ("FPRIME_ENVIRONMENT_FILE", "environment_file"),
            ("FPRIME_CONFIG_DIR", "config_directory"),
            ("FPRIME_INSTALL_DEST", "install_destination"),
        ]

        cmake_args = {
            cache: self.get_settings(setting, None)
            for cache, setting in needed
            if self.get_settings(setting, None) is not None
        }

        if "FPRIME_LIBRARY_LOCATIONS" in cmake_args:
            cmake_args["FPRIME_LIBRARY_LOCATIONS"] = ";".join(
                [str(location) for location in cmake_args["FPRIME_LIBRARY_LOCATIONS"]]
            )
        return cmake_args

    def get_module_name(self, path: Path):
        """Gets name of module from path"""
        return self.cmake.get_cmake_module(path, self.build_dir)

    def _load_build_cache_locations(self) -> List[Path]:
        """Parse the binary locations file once and return the result.

        Reads from `fprime-binary-locations.fprime-util` at the root of the build cache. Each
        line in the file is a path (relative or absolute). Relative paths are resolved with
        respect to the build cache directory (the location of the file). Blank lines and lines
        starting with '#' are ignored.

        If the file does not exist, falls back to the build cache root and build cache/F-Prime.
        If the file exists but contains no valid (existing) paths, raises
        InvalidBuildCacheException indicating a corrupt build cache. Also raises if any
        resolved path falls outside the build cache directory (security check).

        Returns:
            List of resolved Path objects to iterate when searching the build cache.

        Raises:
            InvalidBuildCacheException: if the locations file exists but yields no valid paths,
                or if any path resolves outside the build cache directory
        """
        locations_file = self.build_dir / "fprime-binary-locations.fprime-util"
        if not locations_file.exists():
            # build_dir must precede F-Prime: first match wins in get_build_cache_path
            return [self.build_dir.resolve(), (self.build_dir / "F-Prime").resolve()]

        build_dir_resolved = self.build_dir.resolve()
        locations = []
        with open(locations_file, "r") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                path = Path(line)
                path = (
                    path.resolve()
                    if path.is_absolute()
                    else (self.build_dir / path).resolve()
                )
                if not path.is_relative_to(build_dir_resolved):
                    msg = f"'{path}' in '{locations_file}' resolves outside the build cache '{build_dir_resolved}'. This may indicate a malicious build cache."
                    raise InvalidBuildCacheException(msg, str(self.build_dir))
                locations.append(path)
        locations = [loc for loc in locations if loc.exists()]
        if not locations:
            msg = f"'{locations_file}' exists but contains no valid locations. Regenerate the build cache with 'fprime-util generate -f'."
            raise InvalidBuildCacheException(msg, str(self.build_dir))
        return locations

    def get_build_cache_locations(self) -> List[Path]:
        """Return the cached list of build cache locations.

        Returns:
            List of resolved Path objects to iterate when searching the build cache.
        """
        return self._build_cache_locations

    def _load_source_locations(self) -> List[Path]:
        """Parse the source locations file once and return the result.

        Reads from `fprime-source-locations.fprime-util` at the root of the build cache.
        Each line in the file is a source directory path (absolute). Blank lines and
        lines starting with '#' are ignored.

        If the file does not exist, falls back to assembling source locations from
        the traditional settings: framework_path, library_locations, and project_root.

        Returns:
            List of resolved Path objects representing source tree roots.

        Raises:
            InvalidBuildCacheException: if the locations file exists but yields no
                valid paths
        """
        locations_file = self.build_dir / "fprime-source-locations.fprime-util"
        if not locations_file.exists():
            return self._assemble_source_locations_from_settings()

        locations = []
        with open(locations_file, "r") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                path = Path(line)
                if not path.is_absolute():
                    path = (self.build_dir / path).resolve()
                else:
                    path = path.resolve()
                locations.append(path)
        locations = [loc for loc in locations if loc.exists()]
        if not locations:
            msg = f"'{locations_file}' exists but contains no valid source locations. Regenerate the build cache with 'fprime-util generate -f'."
            raise InvalidBuildCacheException(msg, str(self.build_dir))
        return locations

    def _assemble_source_locations_from_settings(self) -> List[Path]:
        """Fallback: assemble source locations from settings.

        Uses framework_path, library_locations, and project_root to build the
        list of source tree roots. This preserves backwards compatibility when
        the fprime-source-locations.fprime-util file is not present.

        Returns:
            List of resolved Path objects representing source tree roots.
        """
        locations = []
        framework_path = self.get_settings("framework_path", None)
        if framework_path is not None:
            locations.append(Path(framework_path).resolve())
        for lib in self.get_settings("library_locations", []):
            locations.append(Path(lib).resolve())
        project_root = self.get_settings("project_root", None)
        if project_root is not None:
            locations.append(Path(project_root).resolve())
        return locations

    def _setup_source_locations(self):
        """Load source locations and propagate to CMakeHandler.

        Must be called after _load_settings_from_cache() so the fallback
        assembly uses fully-resolved settings.
        """
        self._source_locations = self._load_source_locations()
        self.cmake.source_locations = self._source_locations

    def get_source_locations(self) -> List[Path]:
        """Return the cached list of source tree locations.

        Returns:
            List of resolved Path objects representing source tree roots.
        """
        return self._source_locations

    def get_build_cache_path(self, context: Path) -> Path:
        """Get the path within the build cache associated with the given context

        Each contextual path has a matching path within the build cache that contains the outputs of the various build
        commands executed in that context. This command will return a path to that context.

        Args:
            context: contextual path to return
        """
        if not isinstance(context, Path):
            raise ValueError("Context must be a Path")
        project_relative_path = self.get_relative_path(context)
        for possible in self.get_build_cache_locations():
            possible_path = possible / project_relative_path
            if possible_path.exists():
                return possible_path
        component_name = os.path.basename(context)
        msg = f"The call to add_fprime_subdirectory could not be found for {component_name}\nPlease check the CMakeLists.txt files in the parent directories of {context}"
        raise MissingBuildCachePath(msg)

    def get_relative_path(self, path: Path) -> Path:
        """Gets path relative to project"""
        relative_path, _ = self.cmake.get_include_info(path, self.build_dir)
        return Path(relative_path)

    def execute_build_target(
        self, build_target: Union[str, List[str]], context: Path, make_args: dict
    ):
        """Execute a build target, or several build targets in one build system invocation

        Executes a target within the build system. This will execute the target by calling into the make system. Context
        is supplied such that the system can match local targets to the global target list.

        Args:
            build_target: build system target to run as string, or list of such targets
            context: context path for local targets
            make_args: args to supply to the build tool (make or ninja)
        """
        make_args = copy.deepcopy(make_args)
        self.cmake.execute_known_target(
            build_target,
            self.build_dir,
            context.absolute(),
            cmake_args=self.get_cmake_args(),
            make_args=make_args,
            top_target=True,
            environment=self.settings.get("environment", None),
        )

    def generate(self, user_cmake_args, preset=None):
        """Generates a build given CMake arguments

        This will run a generate step of the cmake build process. This will take in any argument used/passed to CMake.

        Args:
            user_cmake_args: cmake arguments to pass into the generate step
            preset: CMake preset name to pass via --preset. None means no preset.
        """
        cmake_args = {}
        try:

            def split_pair(item):
                """Process an item into a two-tuple always"""
                return tuple([*item.strip().split("=", 1), ""][:2])

            default_options_text = self.get_settings("default_cmake_options", "")
            if default_options_text:
                default_options = default_options_text.split("\n")
                default_cmake_options = {
                    option: value
                    for (option, value) in [
                        split_pair(item) for item in default_options
                    ]
                    if option != ""
                }
                cmake_args.update(default_cmake_options)
            cmake_args.update(user_cmake_args)  # User-supplied values from command line
            cmake_args.update(self.get_cmake_args())  # FPRIME_* values (settings.ini)

            # When the v3 autocoder directory exists (or framework path is unset
            # and we assume v3 compliance), use the new UT API and preserve the
            # build type.
            fw_cmake_arg = cmake_args.get("FPRIME_FRAMEWORK_PATH")
            v3_assumed = (
                fw_cmake_arg is None
                or (Path(fw_cmake_arg) / "cmake" / "autocoder").exists()
            )
            if v3_assumed and self.build_type == BuildType.BUILD_TESTING:
                cmake_args["BUILD_TESTING"] = "ON"
                cmake_args["CMAKE_BUILD_TYPE"] = user_cmake_args.get(
                    "CMAKE_BUILD_TYPE", "Debug"
                )
            elif self.build_type == BuildType.BUILD_TESTING:
                cmake_args["CMAKE_BUILD_TYPE"] = "Testing"

            self.cmake.generate_build(
                self.cmake_root,
                self.build_dir,
                cmake_args,
                environment=self.settings.get("environment", None),
                preset=preset,
            )
        except CMakeException as cexc:
            raise GenerateException(str(cexc), cexc.exit_code) from cexc

    def purge(self):
        """Purge a build cache directory"""
        self.cmake.purge(self.build_dir)

    def purge_install(self):
        """Purge the install directory"""
        install_dest = self.settings.get("install_destination")
        if install_dest is None:
            return
        self.cmake.purge(install_dest)

    def install_dest_exists(self) -> Path:
        """Check if the install destination exists and returns the path if it does"""
        install_dest = self.settings.get("install_destination")
        if install_dest is None:
            return None
        path = Path(install_dest)
        return path if path.exists() else None

    def refresh(self):
        """Refresh this build (i.e. the cmake build cache)

        Some build systems (e.g. CMake) require the build to be refreshed (i.e. refresh the build cache). When this
        happens it is imperative that the appropriate environment is set. For this reason, refresh is exposed as a
        helper in this layer rather than the previous pattern of calling builder.cmake.cmake_refresh_cache directly.
        """
        self.cmake.cmake_refresh_cache(
            self.build_dir, environment=self.settings.get("environment", None)
        )

    @staticmethod
    def find_nearest_parent_project(path: Path) -> Path:
        """Recurse up the directory stack looking for a valid CMake project.

        Recurse up the directory tree from the given path, looking for a project definition directory. This means it
        defines a CMakeLists.txt with a project call. This finds where the automatic build directories are allowed to
        exist.

        Notes:
            Historically, the root of the CMake project was an F' deployment. In F' > v3.2.0, this is more often an
            F' project root.

        Returns;
            Path to the nearest project directory searching up the directory tree

        Raises;
            UnableToDetectProjectException: was unable to detect a project directory
        """
        full_path = path.resolve()
        list_file = full_path / "CMakeLists.txt"
        if not full_path.parents:
            raise UnableToDetectProjectException()
        if list_file.exists():
            with open(list_file, encoding="utf8") as file_handle:
                text = file_handle.read()
            if Build.VALID_CMAKE_LIST.search(text):
                return full_path
        return Build.find_nearest_parent_project(full_path.parent)

    @staticmethod
    def get_build_list(base, build_cache=None, ignore_invalid=False):
        """Returns a list of builds that the tool will process

        Will return a list of builds the tool will process. This will be a build for each public build type unless the
        cache has been overridden.  If overridden, this will be one build pointed at that cache.

        Args:
            base: base build identified from command line. Used to get: deployment, platform,
            build_cache: (optional) path to specified build cache.
            ignore_invalid: (optional) ignore invalid build caches and add as long as they exist

        Returns:
            List of builds for public build types, or list of one for a custom build at build cache
        """
        build_types = (
            [BuildType.BUILD_CUSTOM]
            if build_cache is not None
            else BuildType.get_public_types()
        )
        builds = []
        for build_type in build_types:
            build = Build(build_type, base.cmake_root, verbose=base.cmake.verbose)
            try:
                build.load(
                    base.platform, build_dir=build_cache, skip_validation=ignore_invalid
                )
                builds.append(build)
            except InvalidBuildCacheException as error:
                # Warnings only issued when not using an explicit build cache
                if build_cache is None:
                    print(
                        f"[WARNING] Build cache '{error.cache}' invalid or not found. Skipping."
                    )
                    continue
                raise
        return builds

    def __setup_default(
        self, platform: str = None, build_dir: Path = None, preset: str = None
    ):
        """Sets up default build

        Sets this build up before determining if it is a pre-generated, or post-generated build.

        build_dir is used to specify an exact build directory to use as part of this step. This allows directories to be
        specified by the caller, but is typically not used.

        Args:
            platform:   name of platform to build against. None will use default from settings.ini or without this
                        setting, "native". Defaults to None.
            build_dir:  explicitly sets the build path to allow for user override of default
            preset:     CMake preset name from CLI. Overrides settings.ini preset when provided.
        """
        assert self.settings is None, "Already setup it is invalid to re-setup"
        assert self.platform is None, "Already setup it is invalid to re-setup"
        assert self.build_dir is None, "Already setup it is invalid to re-setup"

        self.settings = IniSettings.load(
            self.cmake_root / "settings.ini",
            platform,
            self.build_type == BuildType.BUILD_TESTING,
        )

        # CLI --preset overrides settings.ini preset
        if preset is not None:
            self.settings["preset"] = preset

        if platform is not None and platform != "default":
            self.platform = platform
        elif self.build_type == BuildType.BUILD_TESTING:
            self.platform = self.settings.get("default_ut_toolchain", "native")
        else:
            self.platform = self.settings.get("default_toolchain", "native")
        self.build_dir = build_dir if build_dir is not None else self.get_build_cache()


class GenerateException(FprimeException):
    """An exception indicating generate has failed and the user may need to respond"""

    def __init__(self, message, exit_code=1):
        super().__init__(message)
        self.exit_code = exit_code
