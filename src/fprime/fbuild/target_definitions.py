"""fprime.fbuild.target_definitions: targets definitions for fprime-util

Defines all the targets for fprime-util. Each target is a singleton that is registered into the list of all targets and
as such, each target need only be instantiated but need not be assigned to anything.

"""

from .gcovr import ExistingCoverageTarget, GcovrTarget
from .check import CheckTarget
from fprime.fbuild.check import CheckTarget
from .enumerator import (
    BasicBuildTargetEnumerator,
    MultiBuildTargetEnumerator,
    ProjectBuildTargetEnumerator,
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

Target.register_target(
    BuildSystemTarget(
        mnemonic="build",
        desc="Build the targets the framework records at the build cache root, from any directory within the project (today the framework records the `all` target, so this matches --all; it may record a narrower project set in future)",
        scope=TargetScope.GLOBAL,
        flags={"project"},
        # The project's targets are listed at the root of the build cache
        build_target_enumerator=ProjectBuildTargetEnumerator(),
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

Target.register_target(
    BuildSystemTarget(
        mnemonic="build",
        desc="Build the targets the framework records at the build cache root, from any directory within the project (unit test build; today this is the `all` target and matches --all --ut)",
        scope=TargetScope.GLOBAL,
        flags={"project", "ut"},
        build_type=BuildType.BUILD_TESTING,
        build_target_enumerator=ProjectBuildTargetEnumerator(),
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

Target.register_target(
    CheckTarget(
        mnemonic="check",
        desc="Build and run the unit tests the framework records at the build cache root, from any directory within the project (unit test build; today this is every test and matches --all)",
        scope=TargetScope.GLOBAL,
        flags={"project"},
        build_type=BuildType.BUILD_TESTING,
        # Both steps enumerate from the root of the build cache: project build targets, then project tests
        build_target_enumerators=[
            ProjectBuildTargetEnumerator(),
            ProjectBuildTargetEnumerator(
                build_file_name=MultiBuildTargetEnumerator.TEST_BUILD_TARGETS_FILE
            ),
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

#### Coverage from existing data (gcovr only, no test run) ####
Target.register_target(
    ExistingCoverageTarget(
        mnemonic="check",
        desc="Calculate coverage for the current directory from existing coverage data (no test run)",
        scope=TargetScope.LOCAL,
        flags={"coverage", "existing"},
        build_type=BuildType.BUILD_TESTING,
    )
)

Target.register_target(
    ExistingCoverageTarget(
        mnemonic="check",
        desc="Calculate coverage recursively from the current directory from existing coverage data (no test run)",
        scope=TargetScope.LOCAL,
        flags={"coverage", "existing", "recursive"},
        build_type=BuildType.BUILD_TESTING,
    )
)

Target.register_target(
    ExistingCoverageTarget(
        mnemonic="check",
        desc="Calculate coverage for the whole project from existing coverage data (no test run)",
        scope=TargetScope.GLOBAL,
        flags={"coverage", "existing", "all"},
        build_type=BuildType.BUILD_TESTING,
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
