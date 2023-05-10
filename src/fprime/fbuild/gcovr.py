""" fprime.fbuild.gcovr: coverage target implementations """
import itertools
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Union

from .target import ExecutableAction, Target, TargetScope, CompositeTarget


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
        "project_root", builder.get_settings("framework_path", builder.build_dir.parent)
    )
    return Path(project_root) / module.replace("_", "/")


def _using_root(builder: "Build", context: Path, scope: TargetScope):
    """Are we using repository root for things"""
    return builder.is_deployment(context) or scope == TargetScope.GLOBAL


class GcovClean(ExecutableAction):
    """Target used to scrub gcov files before a coverage run

    The way fprime builds unittests means it is easy to see gcov coverage files leak into the coverage report from other
    runs. This target finds all gcov created files (.gcda) and removes them before the build. This applies to the
    entire build cache as report should be complete and isolated to any given run.
    """

    REMOVAL_EXTENSIONS = [".gcda"]

    def execute(
        self,
        builder: "Build",
        context: Path,
        args: Tuple[Dict[str, str], List[str], Dict[str, bool]],
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
        self,
        builder: "Build",
        context: Path,
        args: Tuple[Dict[str, str], List[str], Dict[str, bool]],
    ):
        """Executes the gcovr target"""
        if not shutil.which(self.EXECUTABLE):
            print(
                f"[ERROR] Cannot find executable: {self.EXECUTABLE}. Unable to run coverage report.",
                file=sys.stderr,
            )
            return
        build_cache_resolved = Path(builder.build_dir).resolve()

        _, pass_through_args, options = args
        include_all = options["--all-sources"]
        include_comp_ac = include_all or options["--comp-ac"]
        include_port_ac = include_all or options["--port-ac"]
        include_type_ac = include_all or options["--type-ac"]
        include_test_ac = include_all or options["--test-ac"]
        include_test = include_all or options["--test-sources"]
        build_cache_exclusion_filter_bases = [
            None if include_comp_ac else ".*ComponentAc.[ch]pp",
            None if include_port_ac else ".*PortAc.[ch]pp",
            None if include_type_ac else ".*SerializableAc.[ch]pp",
            None if include_type_ac else ".*ArrayAc.[ch]pp",
            None if include_type_ac else ".*EnumAc.[ch]pp",
            None if include_test_ac else ".*/GTestBase.[ch]pp",
            None if include_test_ac else ".*/TesterBase.[ch]pp",
            None if include_test_ac else ".*/TesterHelpers.[ch]pp",
        ]
        raw_source_exclusion_filter_bases = [
            None if include_test else ".*/test/ut/.*",
            None if include_test else ".*/GTest/.*",
            None if include_test else "test/ut/.*",
        ]

        build_cache_exclusion_filter_bases = filter(
            lambda item: item is not None, build_cache_exclusion_filter_bases
        )

        raw_source_exclusion_filter_bases = filter(
            lambda item: item is not None, raw_source_exclusion_filter_bases
        )

        exclusion_filter_bases = [
            ["--exclude", f"{build_cache_resolved}/{exclusion}"]
            for exclusion in build_cache_exclusion_filter_bases
        ] + [
            ["--exclude", f"{exclusion}"]
            for exclusion in raw_source_exclusion_filter_bases
        ]

        build_cache_path = (
            builder.build_dir
            if _using_root(builder, context, self.scope)
            else builder.get_build_cache_path(context)
        ).resolve()

        coverage_output_dir = context.resolve() / "coverage"
        coverage_output_dir.mkdir(exist_ok=True)
        project_root = builder.get_settings(
            "project_root",
            builder.get_settings("framework_path", builder.build_dir.parent.parent),
        ).resolve()
        filter_path = (
            Path(project_root).resolve()
            if _using_root(builder, context, self.scope)
            else _get_project_path(builder, context)
        ).resolve()
        framework_path = builder.get_settings("framework_path", builder.build_dir.parent.parent)
        # gcovr is an unhappy beast
        cli_args = (
            [
                "gcovr",
                "-r",
                str(project_root),
                str(build_cache_path),  # For efficiency in searching on modules
            ]
            + list(itertools.chain.from_iterable(exclusion_filter_bases))
            + [
                "--exclude",
                f"{framework_path}/Autocoders",
                "--exclude",
                f"{framework_path}/gtest",
                "--exclude",
                f"{framework_path}/STest",
                "--filter",
                f"{filter_path}",
                "--filter",
                f"{build_cache_path}",
                "--print-summary",
                "--txt",
                f"{coverage_output_dir}/summary.txt",
                "--html-details",
                f"{coverage_output_dir}/coverage{'-all' if self.scope == TargetScope.GLOBAL else ''}.html",
            ]
        )
        cli_args.extend(pass_through_args)

        if builder.cmake.verbose:
            joined_args = "' '".join(cli_args)
            print(f'[INFO] Running "\'{ joined_args }\'"')
        # gcovr must run in the ac_temporary_path or html details cannot find the Ac files
        subprocess.call(cli_args)

    def option_args(self):
        """Option arguments"""
        return [
            ("--all-sources", "[coverage only] Include all sources in coverage"),
            ("--comp-ac", "[coverage only] Include component autocode in coverage"),
            ("--port-ac", "[coverage only] Include port autocode in coverage"),
            ("--type-ac", "[coverage only] Include data type autocode in coverage"),
            ("--test-ac", "[coverage only] Include data test autocode in coverage"),
            ("--test-sources", "[coverage only] Include unit test sources in coverage"),
        ]

    def allows_pass_args(self):
        """Gcovr allows pass-through arguments"""
        return True

    def pass_handler(self):
        """Pass handler"""
        return self.EXECUTABLE


class GcovrTarget(CompositeTarget):
    """Target specific to gcovr

    The gcovr target is a composite target that builds upon an existing check target to perform gcovr work. In addition,
    it must support extra arguments as we pass these to the gcovr executable.
    """

    def __init__(self, check_target: Target, scope: TargetScope, *args, **kwargs):
        """Construct the gcovr target around an existing check target"""
        assert check_target.scope in [
            scope,
            TargetScope.BOTH,
        ], "Cannot create composite target from incompatible target"
        super().__init__(
            [GcovClean(scope), check_target, Gcovr(scope)],
            scope=scope,
            *args,
            **kwargs,
        )
