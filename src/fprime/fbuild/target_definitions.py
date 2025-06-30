""" fprime.fbuild.target_definitions: targets definitions for fprime-util

Defines all the targets for fprime-util. Each target is a singleton that is registered into the list of all targets and
as such, each target need only be instantiated but need not be assigned to anything.

"""

from .gcovr import GcovrTarget
from .target import Target, BuildSystemTarget, DesignatedBuildSystemTarget, MultiTargetTarget, RecursiveMultiTargetTarget, TargetScope
from .types import BuildType

#### "build" targets for components, deployments, unittests for both normal and testing builds ####
Target.register_target(MultiTargetTarget(BuildSystemTarget(
    "",
    mnemonic="build",
    desc="Build components, ports, and deployments",
    scope=TargetScope.LOCAL,
)))
Target.register_target(RecursiveMultiTargetTarget(BuildSystemTarget(
    "",
    mnemonic="build",
    desc="Build components, ports, and deployments recursively from the current directory",
    scope=TargetScope.LOCAL,
    flags={"recursive"}
)))
Target.register_target(BuildSystemTarget(
    "all",
    mnemonic="build",
    desc="Build components, ports, and deployments",
    scope=TargetScope.GLOBAL,
    flags={"all"},
))
Target.register_target(MultiTargetTarget(BuildSystemTarget(
    "ut_exe",
    mnemonic="build",
    desc="Build unittests",
    scope=TargetScope.LOCAL,
    flags={"ut"},
    build_type=BuildType.BUILD_TESTING,
)))
Target.register_target(RecursiveMultiTargetTarget(BuildSystemTarget(
    "ut_exe",
    mnemonic="build",
    desc="Build components, ports, and deployments recursively from the current directory",
    scope=TargetScope.LOCAL,
    flags={"ut", "recursive"}
)))
Target.register_target(BuildSystemTarget(
    "all",
    mnemonic="build",
    desc="Build all components, ports, UTs, and deployments for unittest build",
    scope=TargetScope.GLOBAL,
    flags={"all", "ut"},
    build_type=BuildType.BUILD_TESTING,
))

Target.register_target(DesignatedBuildSystemTarget(
    "target",
    mnemonic="build",
    desc="Build a specific CMake target by name",
    scope=TargetScope.GLOBAL,
    flags={"target"},
))

Target.register_target(DesignatedBuildSystemTarget(
    "target",
    mnemonic="build",
    desc="Build a specific CMake target by name using the UT build",
    scope=TargetScope.GLOBAL,
    flags={"ut", "target"},
    build_type=BuildType.BUILD_TESTING,
))