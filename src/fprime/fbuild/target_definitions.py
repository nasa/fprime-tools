""" fprime.fbuild.target_definitions: targets definitions for fprime-util

Defines all the targets for fprime-util. Each target is a singleton that is registered into the list of all targets and
as such, each target need only be instantiated but need not be assigned to anything.

"""
import os
import sys
from .types import BuildType
from .target import TargetScope, BuildSystemTarget
from .gcovr import GcovrTarget


#### "build" targets for components, deployments, unittests for both normal and testing builds ####
BuildSystemTarget("", mnemonic="build", desc="Build components, ports, and deployments", scope=TargetScope.BOTH)
BuildSystemTarget("ut_exe", mnemonic="build", desc="Build unittests", scope=TargetScope.LOCAL, flags={"ut"},
                  build_type=BuildType.BUILD_TESTING)
BuildSystemTarget("all", mnemonic="build", desc="Build components, ports, UTs, and deployments for unittest build",
                  scope=TargetScope.GLOBAL, flags={"all", "ut"}, build_type=BuildType.BUILD_TESTING)


#### Implementation targets ####
BuildSystemTarget("impl", mnemonic="impl", desc="Generate implementation template files", scope=TargetScope.LOCAL)
BuildSystemTarget("testimpl", mnemonic="impl", desc="Generate unit test files", flags={"ut"},
                  build_type=BuildType.BUILD_TESTING, scope=TargetScope.LOCAL)


#### Check targets ####
check = BuildSystemTarget("check", mnemonic="check", desc="Build and run unittests", build_type=BuildType.BUILD_TESTING,
                  scope=TargetScope.BOTH)
BuildSystemTarget("check_leak", mnemonic="check", desc="Build and run unittests with memory leak checking",
                  flags={"leak"}, build_type=BuildType.BUILD_TESTING, scope=TargetScope.BOTH)
GcovrTarget(check, mnemonic="check", desc="Build run and calculate coverage of unittests",
            build_type=BuildType.BUILD_TESTING, scope=TargetScope.BOTH, flags={"coverage"})

