""" fprime.fbuild.gcovr: coverage target implementations """
import atexit
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Union

from .target import ExecutableAction, Target, TargetScope, CompositeTarget

TEMPORARY_DIRECTORY = "{{AUTOCODE}}"


def _get_project_path(builder: "Build", module: Union[str, Path]) -> Path:
    """Get the project path from a given module string

    Get the project path for a given module or path. Paths are assumed to be contexts and returned verbatim. Modules are
    converted to a project string and then that is returned.

    Args:
        builder: builder object
        module: module string or project path
    """
    # If this module is path then return it as project path already
    if isinstance(module, Path):
        return module
    # Calculate the project path from the module name
    project_root = builder.get_settings(
        "project_root",
        builder.get_settings("framework_path", builder.build_dir.parent),
    )
    return Path(project_root) / module.replace("_", "/")


def _using_root(builder: "Build", context: Path, scope: TargetScope):
    """Are we using repository root for things"""
    return builder.is_deployment(context) or scope == TargetScope.GLOBAL


def _get_ac_directory(builder: "Build", context: Path, scope: TargetScope) -> Path:
    """Gets a directory for AC files to be placed

    AC files need to migrate out of the build cache and into the build for purposes of HTML coverage.  This selects an
    appropriate location for this temporary directory.

    Args:
        builder: build to use
        context: path context to use
    """
    base_path = (
        _get_project_path(builder, ".")
        if _using_root(builder, context, scope)
        else context
    )
    return (base_path / TEMPORARY_DIRECTORY).absolute()


class GcovClean(ExecutableAction):
    """Target used to scrub gcov files before a coverage run

    The way fprime builds unittests means it is easy to see gcov coverage files leak into the coverage report from other
    runs. This target finds all gcov created files (.gcda) and removes them before the build. This applies to the
    entire build cache as report should be complete and isolated to any given run.
    """

    REMOVAL_EXTENSIONS = [".gcda"]

    def execute(
        self, builder: "Build", context: Path, args: Tuple[Dict[str, str], List[str]]
    ):
        """Execute the clean using os.walk"""
        print(f"[INFO] Scrubbing leftover { ', '.join(self.REMOVAL_EXTENSIONS)} files")
        self._recurse(builder.build_dir)

    @classmethod
    def _recurse(cls, parent_path: Path):
        """Recursive helper"""
        for path in parent_path.iterdir():
            if path.is_file() and path.suffix in cls.REMOVAL_EXTENSIONS:
                path.unlink()
            elif path.is_dir():
                cls._recurse(path)


class GcovrAcHelper(ExecutableAction):
    """Helps with AC file paths and gcovr reports

    Autocoded files are created in the build cache, but not in the same directory as the .gcda and .gcno files. This
    causes the --html-details flag to fail to find these files when generating the detailed HTML w/ source output. This
    action will fix this by coping these files to a known working directory to work within.

    Specifically:
    - Create temporary directory
    - Register an at_exit handler to clean-up the directory
    - For each .gcda file in build cache:
    -   Copy matching .cpp and .hpp file from two parent directories above to temporary directory
    """

    EXTENSION_TRIGGER = [".gcno", ".gcda"]

    def __init__(self, scope: TargetScope):
        """Init function"""
        super().__init__(scope)
        self.collided_files = set()

    def execute(
        self, builder: "Build", context: Path, args: Tuple[Dict[str, str], List[str]]
    ):
        """Execute this action"""
        temp_path = _get_ac_directory(builder, context, self.scope)
        print(f"[INFO] Making temporary directory: {temp_path}")
        temp_path.mkdir(exist_ok=False)
        atexit.register(self.removal, temp_path)
        print(f"[INFO] Copying AC files into temporary directory")
        cache_path = builder.build_dir / builder.get_build_cache_path(context)
        recurse_path = (
            Path(builder.build_dir)
            if _using_root(builder, context, self.scope)
            else cache_path
        )
        # Recurse excluding the autocoders directory which is filled with test codes
        self._recurse(
            recurse_path,
            temp_path,
            [(builder.build_dir / "F-Prime" / "Autocoders").absolute()],
        )
        for item in list(self.collided_files):
            print(f"[WARNING] Removing contested file: {item.name}")
            item.unlink()

    def copy_safe(self, source: Path, destination: Path):
        """Copy one file if it doesn't exist. Checking content if it does.

        Copy if the destination does not exist. If the content differs, add the offending file to a list to clean up
        later such that it cannot explode gcovr. Deferring removal prevents a third copy from winning.

        Args:
            source: source file
            destination: destination file
        """
        if not destination.exists():
            shutil.copy(source, destination)
            return
        with open(source) as file1:
            lines1 = file1.readlines()
        with open(destination) as file2:
            lines2 = file2.readlines()
        # Line number deltas are known to cause problems as gcovr becomes unhappy when the line number becomes
        # inconsistent with the source it is reading.
        if len(lines1) != len(lines2):
            self.collided_files.add(destination)
            return
        for line1, line2 in zip(lines1, lines2):
            # Lines that that match and lines that differ only by the include statement are ok. These are the models
            # that implement multiple physical components.
            if (line1.strip() == line2.strip()) or (
                line1.strip().startswith("#include")
                and line2.strip().startswith("#include")
            ):
                continue
            # Real differences count as collisions
            self.collided_files.add(destination)

    @staticmethod
    def removal(directory: Path):
        """Function to remove temporary directory"""
        print(f"[INFO] Removing temporary directory: {directory}")
        shutil.rmtree(directory)

    def copy_gcda_pair(self, destination: Path, gcda: Path):
        """Copy matching CPP and HPP files given an .gcda"""
        base_name = gcda.name
        for extension in self.EXTENSION_TRIGGER:
            base_name = base_name.replace(extension, "")
        ac_folder = gcda.parent.parent.parent

        # Copy both possible AC files into the destination folder
        for possible in [base_name, base_name.replace(".cpp", ".hpp")]:
            source = ac_folder / possible
            if source.exists():
                self.copy_safe(source, destination / possible)

    def _recurse(self, parent_path: Path, destination: Path, excludes: List[Path]):
        """Recursive helper"""
        for path in parent_path.iterdir():
            if path.absolute() in excludes:
                continue
            elif path.is_file() and path.suffix in self.EXTENSION_TRIGGER:
                self.copy_gcda_pair(destination, path)
            elif path.is_file() and path.name.endswith("Ac.hpp"):
                self.copy_safe(path, destination / path.name)
            elif path.is_dir():
                self._recurse(path, destination, excludes)


class Gcovr(ExecutableAction):
    """Target invoking `gcovr` utility to calculate coverage

    `gcovr` is a utility used to calculate coverage recursively. It is a wrapper around the gcov executable and patches
    several problems with the utility. This target runs `gcovr` and places the output in a newly created coverage
    directory. arguments are supplied into the `gcovr` execution, however; the default execution is always supplied the
    --txt coverage/summary.txt --txt stdout flags.
    """

    EXECUTABLE = "gcovr"

    def is_supported(self, builder: "Build", context: Path):
        """Is supported by the list of build target names

        Checks if the build target names supplied will support this target. Is overridden by subclasses.

        Args:
            builder: builder to check if this action is supported
            context: contextual path to check

        Return:
            True if supported false otherwise
        """
        return bool(shutil.which(self.EXECUTABLE))

    def execute(
        self, builder: "Build", context: Path, args: Tuple[Dict[str, str], List[str]]
    ):
        """Executes the gcovr target"""
        if not shutil.which(self.EXECUTABLE):
            print(
                f"[ERROR] Cannot find executable: {self.EXECUTABLE}. Unable to run coverage report.",
                file=sys.stderr,
            )
            return
        ac_temporary_path = _get_ac_directory(builder, context, self.scope)
        coverage_output_dir = context / f"coverage"
        coverage_output_dir.mkdir(exist_ok=True)
        project_root = builder.get_settings(
            "project_root",
            builder.get_settings("framework_path", builder.build_dir.parent.parent),
        )
        filter_path = (
            Path(project_root).absolute()
            if _using_root(builder, context, self.scope)
            else _get_project_path(builder, context)
        )
        build_offset = (
            ""
            if _using_root(builder, context, self.scope)
            else builder.get_build_cache_path(context)
        )

        # gcovr is an unhappy beast (but it is *much* better than the raw gcov executable
        # In order to deal with gcovr, we need to do the following things:
        #   1. Setup the project root (deals with relative file paths within project). This is set to our project_root.
        #   2. Next setup the search path for object files. This is set to the build cache or build module directory.
        #   3. Specify two filters: project_path (module directory) and autocode temp directory
        #   4. Exclude the build cache, and autocoders
        #   5. Then supply default output options
        #   6. Then supply pass through arguments
        cli_args = [
            "gcovr",
            "-r",
            str(project_root),
            builder.build_dir / build_offset,  # For efficiency in searching on modules
            "--filter",
            f"{filter_path}/*",
            "--filter",
            f"{ac_temporary_path}",
            "--exclude",
            str(builder.build_dir),
            "--exclude",
            str(
                builder.get_settings("framework_path", builder.build_dir.parent.parent)
                / "Autocoders"
            ),
            "--print-summary",
            "--txt",
            f"{coverage_output_dir}/summary.txt",
            f"--html-details",
            f"{coverage_output_dir}/coverage{'-all' if self.scope == TargetScope.GLOBAL else ''}.html",
        ]
        cli_args.extend(args[1])

        if builder.cmake.verbose:
            print(f"[INFO] Running '{' '.join(cli_args)}'")
        # gcovr must run in the ac_temporary_path or html details cannot find the Ac files
        subprocess.call(cli_args, cwd=str(ac_temporary_path))

    def allows_pass_args(self):
        """Gcovr allows pass-through arguments"""
        return True

    def pass_handler(self):
        """Pass handler"""
        return self.EXECUTABLE


class GcovrTarget(CompositeTarget):
    """Target specific to gcovr

    The gcovr target is a composite target that builds upon an existing check target to perform gcovr work. In addition
    it must support extra arguments as we pass these to the gcovr executable.
    """

    def __init__(self, check_target: Target, scope: TargetScope, *args, **kwargs):
        """Construct the gcovr target around an existing check target"""
        assert (
            check_target.scope == scope or check_target.scope == TargetScope.BOTH
        ), "Cannot create composite target from incompatible target"
        super().__init__(
            [GcovClean(scope), check_target, GcovrAcHelper(scope), Gcovr(scope)],
            scope=scope,
            *args,
            **kwargs,
        )
