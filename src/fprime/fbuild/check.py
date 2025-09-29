"""fprime.fbuild.check: check target implementation

The 'check' target is designed to call CTest executable(s) to run tests. It is a composite target used to build and run
the test targets.
"""

import shutil
import subprocess
import sys
from typing import Tuple, Dict, List

from fprime.fbuild.types import NoTargetFoundException
from fprime.fbuild.target import (
    TargetContext,
    TargetScope,
    EnumeratedAction,
    CompositeTarget,
)

from fprime.fbuild.target import BuildSystemTarget
from .enumerator import BuildTargetEnumerator


class Check(EnumeratedAction):
    """Target invoking CTest executable to run tests"""

    EXECUTABLE = "ctest"

    def __init__(
        self, scope: TargetScope, build_target_enumerator: BuildTargetEnumerator = None
    ):
        """Initialize this action with the test enumerator"""
        super().__init__(scope=scope, build_target_enumerator=build_target_enumerator)

    def any_supported(self, builder: "Build", context: TargetContext):
        """Check if this target is supported in the given context

        This will determine if two conditions are met:
        1. CTest is available
        2. There are test targets to run
        """
        if not bool(shutil.which(self.EXECUTABLE)):
            print("[ERROR] CTest not found", file=sys.stderr)
            return False
        return len(context) > 0

    def execute_all(
        self,
        builder: "Build",
        context: TargetContext,
        args: Tuple[Dict[str, str], List[str], Dict[str, bool]],
    ):
        """Execute this target"""

        if not context:
            # This only happens if the provided path does not contain tests
            # and neither '--all' nor '--recursive' were provided
            raise NoTargetFoundException(
                "No tests were found in the given context. Did you mean to "
                "use `fprime-util check --recursive` or `--all` ?"
            )

        cli_args = [
            self.EXECUTABLE,
            "--test-dir",
            str(builder.build_dir),
            "--no-tests=error",
        ]
        make_args = args[0]

        # Jobs flag
        if "-j" in make_args or "--jobs" in make_args:
            cli_args.extend(
                ["--parallel", str(make_args.get("--jobs", make_args.get("-j", 1)))]
            )
        # Check for conditions that result in verbose output
        # 1. Explicitly verbose
        # 2. Context is not "all" (or .*)
        if builder.is_verbose() or (
            context and context != ["all"] and ".*" not in context
        ):
            cli_args.append("-V")

        # When not "all" append a regex to filter tests. .* works as a regex
        if context and context != ["all"]:
            test_regex = f"^({'|'.join(context)})$"
            cli_args.extend(["-R", test_regex])
        # Extend with "pass through" arguments
        cli_args.extend(args[1])
        # When verbose print the commands run
        if builder.is_verbose():
            joined = "' '".join(cli_args)
            print(f"[INFO] Running CTest: '{joined}'")

        # Check ensures errors result in this process erroring
        subprocess.run(cli_args, check=True)


class CheckTarget(CompositeTarget):
    """Target designed to build and run the tests"""

    def __init__(
        self,
        scope: TargetScope,
        build_target_enumerators: List[BuildTargetEnumerator],
        *args,
        **kwargs,
    ):
        """Constructor setting child targets"""
        build_target = BuildSystemTarget(
            scope=scope,
            build_target_enumerator=build_target_enumerators[0],
            *args,
            **kwargs,
        )
        check_action = Check(
            scope=scope, build_target_enumerator=build_target_enumerators[1]
        )
        super().__init__(
            composite_targets=[build_target, check_action],
            scope=scope,
            *args,
            **kwargs,
        )
