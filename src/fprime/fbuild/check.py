""" fprime.fbuild.check: check target implementation

The 'check' target is designed to call CTest executable(s) to run tests. It is a composite target used to build and run
the test targets.
"""
import sys
import subprocess
from typing import Tuple, Dict, List

from fprime.fbuild.target import (
    TargetContext,
    TargetScope,
    ExecutableAction,
    CompositeTarget,
)

from fprime.fbuild.target import BuildSystemTarget
from .enumerator import BuildTargetEnumerator


class Check(ExecutableAction):
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
        cli_args = [self.EXECUTABLE, "--test-dir", str(builder.build_dir)]
        make_args = args[0]
        if "-j" in make_args or "--jobs" in make_args:
            cli_args.extend(
                ["--parallel", str(make_args.get("--jobs", make_args.get("-j", 1)))]
            )

        if context and context != ["all"]:
            test_regex = f"^({'|'.join(context)})$"
            cli_args.extend(["-R", test_regex])
        if builder.is_verbose():
            cli_args.append("-V")
            joined = "' '".join(cli_args)
            print(f"[INFO] Running CTest: '{joined}'")
        subprocess.call(cli_args)


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
            build_target_enumerator=build_target_enumerators[0],
            *args,
            **kwargs,
        )
