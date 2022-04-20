""" fprime.fbuild.gcovr: coverage target implementations """
import shutil
import subprocess
import sys
from pathlib import Path
from .target import ExecutableAction


class GcovClean(ExecutableAction):
    """ Target used to scrub gcov files before a coverage run

    The way fprime builds unittests means it is easy to see gcov coverage files leak into the coverage report from other
    runs. This target finds all gcov created files (.gcno, .gcna) and removes them before the build. This applies to the
    entire build cache as report should be complete and isolated to any given run.
    """
    REMOVAL_EXTENSIONS = [".gcna"]

    def execute(self, builder: "Builder", context: Path, args: dict):
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
    def execute(self, builder: "Builder", context: Path, args: dict):
        """ Executes the gcovr target """
        for executable in ["gcovr"]:
            if not shutil.which(executable):
                print(f"[ERROR] Cannot find executable: {executable}. Unable to run coverage report.", file=sys.stderr)
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
        subprocess.call(cli_args, cwd=str(build_directory))