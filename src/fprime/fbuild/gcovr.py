""" fprime.fbuild.gcovr: coverage target implementations """
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

from .target import ExecutableAction, Target, CompositeTarget

class GcovClean(ExecutableAction):
    """ Target used to scrub gcov files before a coverage run

    The way fprime builds unittests means it is easy to see gcov coverage files leak into the coverage report from other
    runs. This target finds all gcov created files (.gcno, .gcna) and removes them before the build. This applies to the
    entire build cache as report should be complete and isolated to any given run.
    """
    REMOVAL_EXTENSIONS = [".gcna"]

    def execute(self, builder: "Builder", context: Path, args: Tuple[Dict[str,str], List[str]]):
        """ Execute the clean using os.walk """
        print(f"[INFO] Scrubbing leftover { ', '.join(self.REMOVAL_EXTENSIONS)} files")
        self._recurse(builder.build_dir)

    @classmethod
    def _recurse(cls, parent_path: Path):
        """ Recursive helper """
        for path in parent_path.iterdir():
            if path.is_file() and path.suffix in cls.REMOVAL_EXTENSIONS:
                path.unlink()
            elif path.is_dir():
                cls._recurse(path)


class Gcovr(ExecutableAction):
    """ Target invoking `gcovr` utility to calculate coverage

    `gcovr` is a utility used to calculate coverage recursively. It is a wrapper around the gcov executable and patches
    several problems with the utility. This target runs `gcovr` and places the output in a newly created coverage
    directory. arguments are supplied into the `gcovr` execution, however; the default execution is always supplied the
    --txt coverage/summary.txt --txt stdout flags.
    """
    EXECUTABLE = "gcovr"

    def is_supported(self, build_target_names: List[str]):
        """ Is supported by the list of build target names

        Checks if the build target names supplied will support this target. Is overridden by subclasses.

        Args:
            build_target_names: names of builds system targets
        Return:
            True if supported false otherwise
        """
        return bool(shutil.which(self.EXECUTABLE))

    def execute(self, builder: "Builder", context: Path, args: Tuple[Dict[str,str], List[str]]):
        """ Executes the gcovr target """
        if not shutil.which(self.EXECUTABLE):
            print(f"[ERROR] Cannot find executable: {self.EXECUTABLE}. Unable to run coverage report.", file=sys.stderr)
            return
        coverage_output_dir = (context / "coverage")
        coverage_output_dir.mkdir(exist_ok=True)
        project_root = builder.get_settings("project_root", builder.get_settings("framework_path", builder.build_dir.parent))
        build_directory = builder.build_dir / builder.get_relative_path(context, to_build_cache=True)
        cli_args = [
            "gcovr",
            "-r",
            str(project_root),
            str(build_directory),
            "--filter",
            str(build_directory),
            "--filter",
            str(context),
            "--print-summary",
            "--txt",
            str(coverage_output_dir / "summary.txt"),
        ]
        subprocess.call(cli_args + args[1], cwd=str(build_directory))

    def allows_pass_args(self):
        """ Gcovr allows pass-through arguments """
        return True

    def pass_handler(self):
        """ Pass handler """
        return self.EXECUTABLE


class GcovrTarget(CompositeTarget):
    """ Target specific to gcovr

    The gcovr target is a composite target that builds upon an existing check target to perfrom gcovr work. In addition
    it must support extra arguments as we pass these to the gcovr executable.
    """
    def __init__(self, clean_target: Target, *args, **kwargs):
        """ Construct the gcovr target around an existing check target """
        super().__init__([GcovClean(), clean_target, Gcovr()], *args, **kwargs)
