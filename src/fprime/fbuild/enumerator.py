"""fprime.fbuild.enumerator: build module enumeration strategies

This file contains the necessary enumeration strategies for build system targets. Enumeration is used to determine
what targets are available in the given contextual path (working directory), or at the root of the build cache for
project-wide enumeration. The results of the enumeration are then
passed to the target for execution.

Note: this file was created with the help of generative AI.

"""

from abc import ABC, abstractmethod
from argparse import Action
from pathlib import Path
from typing import List, Optional, Tuple

from .types import MissingBuildCachePath

# Enumerated targets with the build-cache context they belong to; None means the root of the build cache
EnumeratedContext = Tuple[List[str], Optional[Path]]
""" Context for enumeration calls (execute_all, any_supported) """


class DesignateTargetAction(Action):
    """This class, when used as the argparse action will set the target of all DesignatedBuildSystemTarget

    argparse.Action actions can be used to handle custom behavior when parsing commands. This class will use the
    --target flag to specify the build target on all known DesignatedBuildSystemTarget that have registered with this
    class.
    """

    _DESIGNEES = []

    @classmethod
    def register_designee(cls, designee):
        """Register designee to this action"""
        cls._DESIGNEES.append(designee)

    def __call__(self, parser, namespace, values, option_string=None):
        """Required __call__ function triggered by the parse"""

        # For each designee, update the build system target
        for designee in self._DESIGNEES:
            designee.set_build_targets(values)
        # The build target detection looks for true/false flags to be set. Mimic this by setting 'target' to True
        setattr(namespace, "target", True)


class BuildTargetEnumerator(ABC):
    """Abstract base class for target enumeration strategies."""

    @abstractmethod
    def enumerate(self, builder: "Build", context_path: Path) -> EnumeratedContext:
        """Enumerates build targets available in the given context path."""
        raise NotImplementedError()


class BasicBuildTargetEnumerator(BuildTargetEnumerator):
    """A basic enumerator that just returns the context given."""

    def __init__(self, target_suffix: str = ""):
        self.target_suffix = target_suffix

    def enumerate_helper(self, builder: "Build", context_path: Path) -> List[str]:
        """Enumeration helper without error handling"""
        module = builder.cmake.get_cmake_module(context_path, builder.build_dir)
        if module and self.target_suffix:
            return [module + "_" + self.target_suffix]
        elif module:
            return [module]
        return [self.target_suffix]

    def enumerate(self, builder: "Build", context_path: Path) -> EnumeratedContext:
        """Enumerate through conversion to cmake module name directly"""
        return self.enumerate_helper(builder, context_path), context_path


class MultiBuildTargetEnumerator(BuildTargetEnumerator):
    """Enumerates targets from the 'build-targets.fprime-util' file."""

    BUILD_TARGETS_FILE = "build-targets.fprime-util"
    TEST_BUILD_TARGETS_FILE = "tests.fprime-util"

    def __init__(
        self,
        build_file_name: str = BUILD_TARGETS_FILE,
        fail_safe_enumerator: BuildTargetEnumerator = None,
    ):
        """Construct the enumerator with the name of the file"""
        self.build_file_name = build_file_name
        self.fail_safe_enumerator = (
            BasicBuildTargetEnumerator()
            if fail_safe_enumerator is None
            else fail_safe_enumerator
        )

    def enumerate_helper(self, builder: "Build", context_path: Path) -> List[str]:
        """Enumeration helper without error handling"""
        build_cache_path = builder.get_build_cache_path(context_path)
        build_targets_file = build_cache_path / self.build_file_name
        with open(build_targets_file, "r") as file_handle:
            enumerated_targets = [line.strip() for line in file_handle.readlines()]
        return enumerated_targets

    def enumerate(self, builder: "Build", context_path: Path) -> EnumeratedContext:
        """Enumerates build targets, falling back to the context if not found."""
        try:
            return self.enumerate_helper(builder, context_path), context_path
        # should an error occur, delegate to a basic enumeration strategy
        except (MissingBuildCachePath, FileNotFoundError):
            return self.fail_safe_enumerator.enumerate(builder, context_path)


class RecursiveMultiBuildTargetEnumerator(BuildTargetEnumerator):
    """Recursively enumerates targets."""

    SUBDIRECTORIES_FILE = "sub-directories.fprime-util"

    def __init__(self, directory_enumerator: "MultiBuildTargetEnumerator" = None):
        """Construct the enumerator with the name of the file"""
        self.directory_enumerator = (
            directory_enumerator
            if directory_enumerator is not None
            else MultiBuildTargetEnumerator()
        )

    def enumerate_helper(self, builder: "Build", context_path: Path) -> List[str]:
        """Enumeration helper without error handling"""
        enumerated_targets = []
        try:
            # Get local targets
            try:
                enumerated_targets.extend(
                    self.directory_enumerator.enumerate_helper(builder, context_path)
                )
            except FileNotFoundError:
                pass  # No local targets, continue to recursion

            # Recurse through subdirectories
            build_cache_path = builder.get_build_cache_path(context_path)
            sub_directories_file = build_cache_path / self.SUBDIRECTORIES_FILE
            with open(sub_directories_file, "r") as file_handle:
                for sub_dir in file_handle.readlines():
                    # Each line is a new path relative to the current context
                    # We need to construct the full path for the recursive call
                    full_sub_dir_path = (build_cache_path / sub_dir.strip()).resolve()
                    enumerated_targets.extend(
                        self.enumerate_helper(builder, full_sub_dir_path)
                    )
        # Any error should return the result of the last update to enumerate_targets hance passing
        except (MissingBuildCachePath, FileNotFoundError):
            pass
        return enumerated_targets

    def enumerate(self, builder: "Build", context_path: Path) -> EnumeratedContext:
        """Recursively enumerates build targets."""
        enumerated_targets = self.enumerate_helper(builder, context_path)
        enumerated_targets = (
            enumerated_targets
            if enumerated_targets
            else self.directory_enumerator.enumerate(builder, context_path)[0]
        )
        return enumerated_targets, context_path


class ProjectBuildTargetEnumerator(BuildTargetEnumerator):
    """Enumerates the project-level targets regardless of the contextual path

    The build system records the project's own targets and tests in the metadata files at the root of the build cache
    (written by ``fprime_setup_included_code`` in the project's top-level CMakeLists.txt). This enumerator reads those
    root files so that a project build may be requested from any directory within the project. Contract: the framework
    defines what "the project" is by what it records there. With the current F Prime framework the root records
    ``all``/``.*`` and ``--project`` is equivalent to ``--all``; the companion F Prime change (nasa/fprime#4436,
    EXCLUDE_FROM_ALL for framework and library modules) narrows ``all`` to the project and its dependencies without any
    change here. When the root metadata is missing or empty (older build caches), the fallback targets are used.
    """

    def __init__(
        self,
        build_file_name: str = MultiBuildTargetEnumerator.BUILD_TARGETS_FILE,
        fallback_targets: List[str] = None,
    ):
        """Set up the enumerator with the root metadata file to read and the targets used when it is missing or empty"""
        self.build_file_name = build_file_name
        self.fallback_targets = (
            ["all"] if fallback_targets is None else fallback_targets
        )

    def enumerate(self, builder: "Build", context_path: Path) -> EnumeratedContext:
        """Enumerate the targets listed at the root of the build cache; context is the root (None)"""
        targets_file = Path(builder.build_dir) / self.build_file_name
        try:
            with open(targets_file, "r") as file_handle:
                enumerated_targets = [
                    line.strip() for line in file_handle.readlines() if line.strip()
                ]
        except FileNotFoundError:
            enumerated_targets = []
        if not enumerated_targets:
            enumerated_targets = list(self.fallback_targets)
        return enumerated_targets, None


class SpecificBuildTargetEnumerator(BuildTargetEnumerator):
    """Enumerates a specific singular build target"""

    def __init__(self, build_targets: List[str] = None):
        """Construct the enumerator with the name of the build target"""
        self.build_targets = build_targets if build_targets is not None else []

    def set_build_targets(self, build_targets: List[str]):
        """Set the build targets"""
        self.build_targets = build_targets

    def enumerate(self, builder: "Build", context_path: Path) -> EnumeratedContext:
        """Enumerates exactly a build target"""
        return self.build_targets, builder.cmake_root


class EverythingBuildTargetEnumerator(SpecificBuildTargetEnumerator):
    """Enumerates everything the build system defines: "all" plus the F Prime "universe" target when it exists

    F Prime (FPRIME_EXCLUDE_LIBRARIES_FROM_ALL) excludes unused framework and library modules from "all" and gathers
    every registered module in a "universe" target whose name is recorded in the CMake cache variable
    FPRIME_UNIVERSE_TARGET. Older framework versions have no such variable and "all" already builds everything.
    """

    UNIVERSE_CACHE_VARIABLE = "FPRIME_UNIVERSE_TARGET"

    def __init__(self):
        super().__init__(["all"])

    def enumerate(self, builder: "Build", context_path: Path) -> EnumeratedContext:
        """Enumerate "all" and, when the cache defines it, the universe target"""
        build_targets = list(self.build_targets)
        (universe,) = builder.cmake._read_values_from_cache(
            [self.UNIVERSE_CACHE_VARIABLE], builder.build_dir
        )
        if universe:
            build_targets.append(universe)
        return build_targets, builder.cmake_root


class CliBuildTargetEnumerator(SpecificBuildTargetEnumerator):
    """Allows users to specify a build target on the command line"""

    def __init__(self):
        super().__init__(build_targets=None)
        DesignateTargetAction.register_designee(self)
