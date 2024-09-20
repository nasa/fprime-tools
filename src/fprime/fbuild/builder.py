"""
Supplies high-level build functions to the greater fprime helper CLI. This maps from user command space to the specific
build system handler underneath.
"""

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
    CMAKE_DEFAULT_BUILD_NAME = "build-fprime-automatic-{platform}{suffix}"

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
        self.cmake = CMakeHandler()
        self.cmake.set_verbose(verbose)

    def invent(self, platform: str = None, build_dir: Path = None, force = False):
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

        Raises:
            InvalidBuildCacheException: a build cache already exists as it should not
        """
        self.__setup_default(platform, build_dir)
        if self.build_dir.exists():
            msg = f"{self.build_dir} already exists."
            if(not force):
                raise InvalidBuildCacheException(msg)

    def load(self, platform: str = None, build_dir: Path = None, skip_validation=False):
        """Load an existing build cache

        Sets this build up from an existing build cache. This can be used after a previous run that has generated a
        build cache in order to prepare for other build steps.

        Args:
            platform:   name of platform to build against. None will use default from settings.ini or without this
                        setting, "native". Defaults to None.
            build_dir:  explicitly sets the build path to allow for user override of default
            skip_validation: (optional) skip cache validation. Default: False, validate away!

        Raises:
            InvalidBuildCacheException: the build cache does not exist as it must
        """
        self.__setup_default(platform, build_dir)
        if not skip_validation and (
            not self.build_dir.exists()
            or not (self.build_dir / "CMakeCache.txt").exists()
        ):
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
        return self.cmake_root / Build.CMAKE_DEFAULT_BUILD_NAME.format(
            platform=self.platform, suffix=self.build_type.get_suffix()
        )

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

    def find_toolchain(self):
        """Locates a toolchain file in know locations

        Finds a toolchain for the given platform.  Searches in known locations for the toolchain, and compares against F
        prime provided toolchains, toolchains in libraries, and toolchains provided by project.

        Returns:
            path to CMake toolchain file or None to use builtin
        """
        assert (
            self.platform != "default"
        ), "Default toolchain should have been decided already"
        toolchain_locations = self.get_settings(
            ["framework_path", "project_root"], [None, self.cmake_root]
        )
        toolchain_locations += self.get_settings("library_locations", [])

        # If toolchain is the native target, this is supplied by CMake and we exit here.
        if self.platform == "native":
            return None
        # Otherwise, find locations of toolchain files using the specified locations from settings.
        toolchains_paths = [
            os.path.join(loc, "cmake", "toolchain", f"{self.platform}.cmake")
            for loc in toolchain_locations
            if loc is not None
        ]
        # Create a deduplicated set of toolchains
        toolchains = list(
            {
                toolchain_path
                for toolchain_path in toolchains_paths
                if os.path.exists(toolchain_path)
            }
        )
        if not toolchains:
            msg = f"Could not find toolchain file for {self.platform} at any of: {' '.join(toolchains_paths)}"
            raise NoSuchToolchainException(msg)
        if len(toolchains) > 1:
            msg = f"Found conflicting toolchain files for {self.platform} at: {' '.join(toolchains)}"
            raise AmbiguousToolchainException(msg)
        return toolchains[0]

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

    def get_build_cache_path(self, context: Path) -> Path:
        """Get the path within the build cache associated with the given context

        Each contextual path has a matching path within the build cache that contains the outputs of the various build
        commands executed in that context. This command will return a path to that context.

        Args:
            context: contextual path to return
        """
        project_relative_path = self.get_relative_path(context)
        for possible in [".", "F-Prime"]:
            possible_path = self.build_dir / possible / project_relative_path
            if possible_path.exists():
                return possible_path
        msg = f"{context} has no associated build cache path"
        raise MissingBuildCachePath(msg)

    def get_relative_path(self, path: Path) -> Path:
        """Gets path relative to project"""
        relative_path, _ = self.cmake.get_include_info(path, self.build_dir)
        return Path(relative_path)

    def execute_build_target(
        self, build_target: str, context: Path, top: bool, make_args: dict
    ):
        """Execute a build target

        Executes a target within the build system. This will execute the target by calling into the make system. Context
        is supplied such that the system can match local targets to the global target list.

        Args:
            build_target: build system target to run as string
            context: context path for local targets
            top: True if it is a top-level (global) target, False if it is a local target
            make_args: args to supply to the build tool (make or ninja)
        """
        self.cmake.execute_known_target(
            build_target,
            self.build_dir,
            context.absolute(),
            cmake_args=self.get_cmake_args(),
            make_args=make_args,
            top_target=top,
            environment=self.settings.get("environment", None),
        )

    def generate(self, user_cmake_args):
        """Generates a build given CMake arguments

        This will run a generate step of the cmake build process. This will take in any argument used/passed to CMake.

        Args:
            user_cmake_args: cmake arguments to pass into the generate step
        """
        cmake_args = {}
        try:

            def split_pair(item):
                """Process an item into a two-tuple always"""
                return tuple([*item.strip().split("=", 1), ""][:2])

            default_options_text = self.get_settings("default_cmake_options", None)
            default_options = default_options_text.split("\n")

            default_cmake_options = {
                option: value
                for (option, value) in [split_pair(item) for item in default_options]
                if option != ""
            }

            cmake_args.update(default_cmake_options)  # default_cmake_options
            cmake_args.update(user_cmake_args)  # User-supplied values from command line
            cmake_args.update(self.get_cmake_args())  # FPRIME_* values (settings.ini)

            # When the new v3 autocoder directory exists, this means we can use the new UT api and preserve the build type
            v3_autocoder_directory = Path(
                cmake_args.get("FPRIME_FRAMEWORK_PATH") / "cmake" / "autocoder"
            )
            if (
                v3_autocoder_directory.exists()
                and self.build_type == BuildType.BUILD_TESTING
            ):
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
            )
        except CMakeException as cexc:
            raise GenerateException(str(cexc), cexc.exit_code) from cexc

    def purge(self):
        """Purge a build cache directory"""
        self.cmake.purge(self.build_dir)

    def purge_install(self):
        """Purge the install directory"""
        assert (
            "install_destination" in self.settings
        ), "install_destination not present in settings"
        self.cmake.purge(self.settings["install_destination"])

    def install_dest_exists(self) -> Path:
        """Check if the install destination exists and returns the path if it does"""
        assert (
            "install_destination" in self.settings
        ), "install_destination not present in settings"
        path = Path(self.settings["install_destination"])
        return path if path.exists() else None

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

    def __setup_default(self, platform: str = None, build_dir: Path = None):
        """Sets up default build

        Sets this build up before determining if it is a pre-generated, or post-generated build.

        build_dir is used to specify an exact build directory to use as part of this step. This allows directories to be
        specified by the caller, but is typically not used.

        Args:
            platform:   name of platform to build against. None will use default from settings.ini or without this
                        setting, "native". Defaults to None.
            build_dir:  explicitly sets the build path to allow for user override of default
        """
        assert self.settings is None, "Already setup it is invalid to re-setup"
        assert self.platform is None, "Already setup it is invalid to re-setup"
        assert self.build_dir is None, "Already setup it is invalid to re-setup"

        self.settings = IniSettings.load(
            self.cmake_root / "settings.ini",
            platform,
            self.build_type == BuildType.BUILD_TESTING,
        )

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
