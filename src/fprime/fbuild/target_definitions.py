""" fprime.fbuild.target_definitions: targets definitions for fprime-util

Defines all the targets for fprime-util. Each target is a singleton that is registered into the list of all targets and
as such, each target need only be instantiated but need not be assigned to anything.

"""
from .gcovr import GcovrTarget
from .check import CheckTarget
from fprime.fbuild.check import CheckTarget
from .enumerator import (
    BasicBuildTargetEnumerator,
    MultiBuildTargetEnumerator,
    RecursiveMultiBuildTargetEnumerator,
    SpecificBuildTargetEnumerator,
    CliBuildTargetEnumerator,
)
from .target import Target, BuildSystemTarget, TargetScope
from .types import BuildType

#### "build" targets for components, deployments, unittests for both normal and testing builds ####
Target.register_target(
    BuildSystemTarget(
        mnemonic="build",
        desc="Build components, ports, and deployments registered in the current directory",
        scope=TargetScope.LOCAL,
        # This target will enumerate all build targets in the current directory
        build_target_enumerator=MultiBuildTargetEnumerator(),
    )
)
Target.register_target(
    BuildSystemTarget(
        mnemonic="build",
        desc="Build components, ports, and deployments recursively from the current directory",
        scope=TargetScope.LOCAL,
        flags={"recursive"},
        # This target will enumerate all build targets recursively from the current directory
        build_target_enumerator=RecursiveMultiBuildTargetEnumerator(),
    )
)
Target.register_target(
    BuildSystemTarget(
        mnemonic="build",
        desc="Build all components, ports, and deployments registered in the project",
        scope=TargetScope.GLOBAL,
        flags={"all"},
        # The build target for building all is "all"
        build_target_enumerator=SpecificBuildTargetEnumerator(["all"]),
    )
)

#### Build unittests ####
Target.register_target(
    BuildSystemTarget(
        mnemonic="build",
        desc="Build all components, ports, deployments, and unit tests registered in the current directory (unit test build)",
        scope=TargetScope.LOCAL,
        flags={"ut"},
        build_type=BuildType.BUILD_TESTING,
        # This target will enumerate all build targets in the current directory
        build_target_enumerator=MultiBuildTargetEnumerator(
            fail_safe_enumerator=BasicBuildTargetEnumerator("ut_exe")
        ),
    )
)
Target.register_target(
    BuildSystemTarget(
        mnemonic="build",
        desc="Build components, ports, deployments, and unit tests recursively from the current directory (unit test build)",
        scope=TargetScope.LOCAL,
        flags={"ut", "recursive"},
        build_type=BuildType.BUILD_TESTING,
        # This target will enumerate all build targets recursively from the current directory
        build_target_enumerator=RecursiveMultiBuildTargetEnumerator(),
    )
)
Target.register_target(
    BuildSystemTarget(
        mnemonic="build",
        desc="Build all components, ports, deployments, and unit tests registered in the project (unit test build)",
        scope=TargetScope.GLOBAL,
        flags={"all", "ut"},
        build_type=BuildType.BUILD_TESTING,
        # The build target for build all is "all"
        build_target_enumerator=SpecificBuildTargetEnumerator(["all"]),
    )
)


#### Check (build and run unittests) ####
check_multi_build_enumerator = MultiBuildTargetEnumerator(
    fail_safe_enumerator=BasicBuildTargetEnumerator("ut_exe")
)
check_multi_test_enumerator = MultiBuildTargetEnumerator(
    build_file_name=MultiBuildTargetEnumerator.TEST_BUILD_TARGETS_FILE,
    fail_safe_enumerator=BasicBuildTargetEnumerator("ut_exe"),
)

Target.register_target(
    CheckTarget(
        mnemonic="check",
        desc="Build and run unit tests in the current directory (unit test build)",
        scope=TargetScope.LOCAL,
        build_type=BuildType.BUILD_TESTING,
        # Check uses a standard build enumerator for the build step and a test enumerator for the test step
        build_target_enumerators=[
            check_multi_build_enumerator,
            check_multi_test_enumerator,
        ],
    )
)

Target.register_target(
    CheckTarget(
        mnemonic="check",
        desc="Build and run unit tests recursively from the current directory (unit test build)",
        scope=TargetScope.LOCAL,
        flags={"recursive"},
        build_type=BuildType.BUILD_TESTING,
        # Check uses a standard build enumerator for the build step and a test enumerator for the test step. These are
        # converted into recursive enumerators.
        build_target_enumerators=[
            RecursiveMultiBuildTargetEnumerator(
                directory_enumerator=check_multi_build_enumerator
            ),
            RecursiveMultiBuildTargetEnumerator(
                directory_enumerator=check_multi_test_enumerator
            ),
        ],
    )
)
Target.register_target(
    CheckTarget(
        mnemonic="check",
        desc="Build and run all unit tests registered in the project (unit test build)",
        scope=TargetScope.GLOBAL,
        flags={"all"},
        build_type=BuildType.BUILD_TESTING,
        # Both steps will enumerate with "all"
        build_target_enumerators=[
            SpecificBuildTargetEnumerator(["all"]),
            SpecificBuildTargetEnumerator(["all"]),
        ],
    )
)

#### Gcovr (build, run, and cover unittests) ####
Target.register_target(
    GcovrTarget(
        mnemonic="check",
        desc="Build, run, and calculate coverage for unit tests in the current directory (unit test build)",
        scope=TargetScope.LOCAL,
        flags={"coverage"},
        build_type=BuildType.BUILD_TESTING,
        # Gcovr uses the same enumerations as check: a standard build enumerator for the build step and a test enumerator
        # for the other steps.
        build_target_enumerators=[
            check_multi_build_enumerator,
            check_multi_test_enumerator,
        ],
    )
)

Target.register_target(
    GcovrTarget(
        mnemonic="check",
        desc="Build, run, and calculate coverage for unit tests recursively from the current directory (unit test build)",
        scope=TargetScope.LOCAL,
        flags={"coverage", "recursive"},
        build_type=BuildType.BUILD_TESTING,
        # Check uses a standard build enumerator for the build step and a test enumerator for the test step. These are
        # converted into recursive enumerators.
        build_target_enumerators=[
            RecursiveMultiBuildTargetEnumerator(
                directory_enumerator=check_multi_build_enumerator
            ),
            RecursiveMultiBuildTargetEnumerator(
                directory_enumerator=check_multi_test_enumerator
            ),
        ],
    )
)

Target.register_target(
    GcovrTarget(
        mnemonic="check",
        desc="Build, run, and calculate coverage for all unit tests registered in the project (unit test build)",
        scope=TargetScope.GLOBAL,
        flags={"coverage", "all"},
        build_type=BuildType.BUILD_TESTING,
        # Both steps will enumerate with "all"
        build_target_enumerators=[
            SpecificBuildTargetEnumerator(["all"]),
            SpecificBuildTargetEnumerator(["all"]),
        ],
    )
)

#### Direct build targets ####
Target.register_target(
    BuildSystemTarget(
        mnemonic="build",
        desc="Build a specific CMake target by name",
        scope=TargetScope.GLOBAL,
        flags={"target"},
        # Enumerate a specific designated target set by CLI
        build_target_enumerator=CliBuildTargetEnumerator(),
    )
)

Target.register_target(
    BuildSystemTarget(
        mnemonic="build",
        desc="Build a specific CMake target (unit test build)",
        scope=TargetScope.GLOBAL,
        flags={"ut", "target"},
        build_type=BuildType.BUILD_TESTING,
        # Enumerate a specific designated target set by CLI
        build_target_enumerator=CliBuildTargetEnumerator(),
    )
)
