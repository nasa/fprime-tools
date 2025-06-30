""" fprime.fbuild.target: build target support

Contains the supporting definitions for build targets. These targets are used to run various parts of the build and may
contain build system targets (e.g. CMake target invokers), and miscellaneous targets that perform other actions.

@author lestarch
"""

import functools
import itertools
from abc import ABC, abstractmethod
from argparse import Action
from enum import Enum
from pathlib import Path
from typing import Dict, List, Set, Tuple, Union

from .types import BuildType, NoSuchTargetException, MissingBuildCachePath

TargetContext = Union[str, Path]


class TargetScope(Enum):
    """Scoping for target execution: GLOBAL, LOCAL

    GLOBAL targets trigger top-level (global) build system targets. LOCAL targets trigger per-directory build system
    targets. BOTH represents a target that can operate in both LOCAL and GLOBAL mode one at a time. When registering
    a BOTH targets, the system will create a local target and a global target and register those. These targets differ
    in both scope and flags as the GLOBAL target receives the flag "--all" added to its list.
    """

    GLOBAL = 0x1
    LOCAL = 0x2
    BOTH = GLOBAL | LOCAL


class ExecutableAction(ABC):
    """Executable action not declaring a formal mnemonic, description, etc.

    Some steps in the execution of a composite target need to execute "actions lite" or anonymous targets. Things that
    have an execute method but are only executable through other targets. This class can be derived to create that
    without generating all the normal target metadata.
    """

    def __init__(self, scope: TargetScope):
        """Set scope of this action"""
        self.scope = scope

    def is_supported(self, builder: "Build", context: TargetContext):
        """Is supported by the list of build target names

        Checks if the build target names supplied will support this target. Is overridden by subclasses.

        Args:
            builder: builder to check if this action is supported
            context: contextual path to check

        Return:
            True if supported false otherwise
        """
        # Always supported by targets, unless specifically overridden
        return True

    @abstractmethod
    def execute(
        self,
        builder: "Build",
        context: TargetContext,
        args: Tuple[Dict[str, str], List[str], Dict[str, bool]],
    ):
        """Executes the given target"""

    def option_args(self) -> List[Tuple[str, str]]:
        """List of option arguments handled by this target

        Option flags are switches that are not allowed arguments. The current design defaults the value to False unless
        the switch is supplied. This function is expected to return a list of pairs of switch flag and description help
        text. e.g.
        [
            (--turn-on, "Turns on a switch"),
        ]

        Returns:
            list of tuples containing the paired flag and description
        """
        return []

    def allows_pass_args(self):
        """Target allows pass-through arguments"""
        return False

    def pass_handler(self):
        """Handler of pass-through args"""
        return None

    def __repr__(self):
        """Representation"""
        return f"{self.__class__.__name__}"



class MultiTargetAction(ExecutableAction):
    """ ExecutableAction that applies to a set of targets read from the build system

    This action will read the specified file in the given context path, should it exist, and will replicate the call to
    execute for each build target found.

    """
    BUILD_TARGETS_FILE = "build-targets.fprime-util"

    def __init__(self, action, *args, **kwargs):
        """Constructor setting child targets"""
        super().__init__(*args, **kwargs)
        self.action = action

    def __repr__(self):
        """So we can see what it delegated to"""
        return f"{self.__class__.__name__}[{self.action}]"
    
    def enumerate_from_build_cache(self, build_cache_path: Path):
        """ Enumerate from the build cache path """
        # Enumerate all build targets in the current context
        build_targets_file = build_cache_path / self.BUILD_TARGETS_FILE
        with open(build_targets_file, "r") as file_handle:
            build_targets = file_handle.readlines()
        return [build_target.strip() for build_target in build_targets]
    
    def enumerate(self, builder: "Build", context: TargetContext):
        """ Enumerate the build targets in the current context
        
        Enumerates the build targets in the current context, should the build targets file exist. Otherwise, returns a
        list of just the supplied context.
        """
        try:
            # Intentionally raise an error if the target is global to have it caught by the
            # below except block.
            if self.action.scope == TargetScope.GLOBAL:
                raise ValueError("Global targets cannot be enumerated")
            build_cache_path = builder.get_build_cache_path(context)
            # Enumerate all build targets in the current context
            return self.enumerate_from_build_cache(build_cache_path)
        except (MissingBuildCachePath, FileNotFoundError, ValueError):
            return [context]

    def is_supported(self, builder: "Build", context: TargetContext):
        """ Check if this target is supported in the given context

        This will just delegate to the composed target.
        """
        return self.action.is_supported(builder, context)

    def execute(self, builder: "Build", context: TargetContext, args: Tuple[Dict[str, str], List[str], Dict[str, bool]]):
        """ Execute the composite target with enumerated contexts """
        enumerated = self.enumerate(builder, context)
    
        if not enumerated:
            print("[INFO] No build targets found")
        for context in enumerated:
            print("[INFO] Building:", context)
            self.action.execute(builder, context, args)


class RecursiveMultiTargetAction(MultiTargetAction):
    """ MultiTargetAction that recursively applies directories """
    SUBDIRECTORIES_FILE = "sub-directories.fprime-util"

    def enumerate(self, builder: "Build", context: TargetContext):
        """ Enumerate the build targets in the current context

        Enumerates the build targets in the current context recursively using the build targets file.
        """
        try:
            # Intentionally raise an error if the target is global to have it caught by the
            # below except block.
            if self.action.scope == TargetScope.GLOBAL:
                raise ValueError("Global targets cannot be enumerated")
            build_cache_path = builder.get_build_cache_path(context)
            try:
                local_enumerated = super().enumerate_from_build_cache(build_cache_path)
            # When local enumeration fails, provide nothing as a stand-in
            except FileNotFoundError:
                local_enumerated = []

            # Enumerate all sub-directories targets in the current context
            sub_directories_targets_file = build_cache_path / self.SUBDIRECTORIES_FILE
            with open(sub_directories_targets_file, "r") as file_handle:
                sub_directories = file_handle.readlines()
            # Sub-directories are relative to the current context
            for sub_directory in sub_directories:
                sub_directory_enumerated = self.enumerate(builder, Path(sub_directory.strip()))
                local_enumerated.extend(sub_directory_enumerated)
        except (MissingBuildCachePath, FileNotFoundError, ValueError) as exc:
            pass
        return local_enumerated

class Target(ExecutableAction):
    """Generic build target base class

    A target can be specified by the user using a mnemonic and flags. The mnemonic is the command typed in by the user,
    and the flags allow the user to remember fewer mnemonics by changing the build target using a modifier. Each build
    target is available in certain build types.

    Targets can be global, using the GlobalTarget base class. Global targets don't use contextual information to modify
    the target, but apply to the whole deployment. Note: global targets are also engaged at the deployment level should
    that be the context.

    Targets may also be local. These targets use context information to figure out what to build. This allows for one
    target to represent a class of targets. i.e. build can be used as a local target to build any given sub directory.
    """

    ALL_TARGETS = []

    def __init__(
        self,
        mnemonic: str,
        desc: str,
        scope: TargetScope,
        build_type: BuildType = None,
        flags: set = None,
    ):
        """Constructs a build target and registers it as one of the global targets

        As part of the construction of a Target it is registered as part of the targets available to be run by
        fprime-util. Targets defined as both global and local are wrapped in delegating targets (one for each scope) and
        those delegates are registered. This is for brevity in definition of these targets. The flag "--all" is added to
        global targets to distinguish them

        Args:
            mnemonic:    mnemonic used to engage build targets. Is not unique, but mnemonic + flags must be.
            desc:        help description of this build target
            build_types: supported build types for target. Defaults to [BuildType.BUILD_NORMAL, BuildType.BUILD_TESTING]
            flags:       flags used to uniquely identify build targets who share logical mnemonics. Defaults to None.
            cmake:       cmake target override to handle oddly named cmake targets
        """
        super().__init__(scope)
        self.mnemonic = mnemonic
        self.desc = desc
        self.build_type = (
            build_type if build_type is not None else BuildType.BUILD_NORMAL
        )
        self.flags = flags if flags is not None else set()

    @classmethod
    def register_target(cls, target: "Target"):
        """Registers the target"""
        cls.ALL_TARGETS.append(target)

    def __repr__(self):
        """Representation"""
        return f"{self.__class__.__name__}({str(self)})"

    def __str__(self):
        """Makes this target into a string"""
        return self.config_string(self.mnemonic, self.flags)

    @staticmethod
    def config_string(mnemonic, flags):
        """Converts a mnemonic and set of flags to string

        Args:
            mnemonic: mnemonic of the target
            flags: set of flags to pair with mnemonic
        Returns:
            string of format "mnemonic --flag1 --flag2 ..."
        """
        flag_string = " ".join([f"--{flag}" for flag in flags])
        flag_string = f" {flag_string}" if flag_string else ""
        return f"{mnemonic}{flag_string}"

    @classmethod
    def get_all_possible_flags(cls) -> Set[str]:
        """Gets list of all targets' flags used

        Returns:
            List of targets supported by the system
        """
        return functools.reduce(
            lambda agg, item: agg.union(item.flags), cls.get_all_targets(), set()
        )

    @classmethod
    def get_all_targets(cls) -> List["Target"]:
        """Gets list of all targets registered

        Returns:
            List of targets supported by the system
        """
        return cls.ALL_TARGETS

    @classmethod
    def get_target(cls, mnemonic: str, flags: Set[str]) -> "Target":
        """Gets the actual build target given the parsed namespace

        Using the global list of build targets and the flags supplied to the namespace, attempt to determine which build
        targets can be used. If more than one are found, then generate exception.

        Args:
            mnemonic: mnemonic of command to look for
            flags:    flags to narrow down target

        Returns:
            single matching target
        """
        matching = [
            target
            for target in cls.get_all_targets()
            if target.mnemonic == mnemonic and flags == target.flags
        ]
        if not matching:
            msg = f"Could not find target '{cls.config_string(mnemonic, flags)}'"
            raise NoSuchTargetException(msg)
        assert len(matching) == 1, "Conflicting targets specified in code"
        return matching[0]


class MultiTargetTarget(MultiTargetAction, Target):
    """Target whose execution is a composition of other targets"""
    def __init__(self, target: Target):
        """ Initialize the multi-target action for all the targets """
        # This calls __init__ based on the MRO, which in this case should be:
        # 1. MultiTargetAction.__init__
        # 2. Target.__init__
        # 3. ExecutableAction.__init__
        #
        # This assumes that MultiTargetAction.__init__ has a `super().__init__(*args, **kwargs)` call that will forward
        # the arguments to `Target.__init__` and that `Target.__init__` calls `super().__init__(scope)` to trigger
        # `ExecutableAction.__init__`.
        super().__init__(
            action=target,
            mnemonic=target.mnemonic,
            desc=target.desc,
            scope=target.scope,
            build_type=target.build_type,
            flags=target.flags
        )

class RecursiveMultiTargetTarget(RecursiveMultiTargetAction, MultiTargetTarget):
    """ Recursive Multi-Target Target """


class CompositeTarget(Target):
    """Target whose execution is a composition of other targets"""

    def __init__(self, targets, *args, **kwargs):
        """Constructor setting child targets"""
        super().__init__(*args, **kwargs)
        self.targets = targets

    def __repr__(self):
        """So we can see what it delegated to"""
        return f"{self.__class__.__name__}[{', '.join([target.__repr__() for target in self.targets])}]"

    def is_supported(self, builder: "Build", context: TargetContext):
        """Is supported by the list of build target names

        Checks if the build target names supplied will support this target. Is overridden by subclasses.

        Args:
            builder: builder to check if this action is supported
            context: contextual path to check

        Return:
            True if supported false otherwise
        """
        # Supported only if all steps supported
        return functools.reduce(
            lambda sum, target: sum and target.is_supported(builder, context),
            self.targets,
            True,
        )

    def option_args(self):
        """Returns the set of option arguments"""
        return list(
            set(
                itertools.chain.from_iterable(
                    [target.option_args() for target in self.targets]
                )
            )
        )

    def allows_pass_args(self):
        """Pass args allowed if any child allows it"""
        return functools.reduce(
            lambda sum, target: sum or target.allows_pass_args(), self.targets, False
        )

    def pass_handler(self):
        """Pass handler as , separated list"""
        handlers = [
            target.pass_handler() for target in self.targets if target.pass_handler()
        ]
        return ",".join(handlers)

    def execute(self, *args, **kwargs):
        """Execute the composite target"""
        for child in self.targets:
            # Composite actions must override scope as a delegator may have acted to change the scope
            old_scope = child.scope
            try:
                child.scope = self.scope
                child.execute(*args, **kwargs)
            finally:
                child.scope = old_scope


class BuildSystemTarget(Target):
    """Target whose execution invokes a command within the build system"""

    def __init__(self, build_target, *args, **kwargs):
        """Constructor setting child targets"""
        super().__init__(*args, **kwargs)
        self.build_target = build_target

    def execute(
        self,
        builder: "Build",
        context: TargetContext,
        args: Tuple[Dict[str, str], List[str], Dict[str, bool]],
    ):
        """Execute a build target

        Executes a target within the build system. This will execute the target by calling into the build system.
        Context is supplied such that the system can match local targets to the global target list.

        Args:
            builder: builder to execute target with
            context: context path for local targets
            args: make system arguments directly supplied
        """
        # Global targets with build target "" must be mapped to "arg"
        build_target = (
            self.build_target
            if self.build_target != "" or self.scope == TargetScope.LOCAL
            else "all"
        )

        # When the context is a path, and the scope is local then the build target is prepended with the context path
        # (e.g. building "" in Svc/FatalHandler yields "Svc_FatalHandler"). This is historical behavior of fprime-util
        # when operating without the --target flag nor operating by reading multi-target files.
        if isinstance(context, Path) and self.scope == TargetScope.LOCAL:
            prepend_context_path = True
            build_target = self.build_target
            context = context
        # When the context is a path, but the scope is global, then the build target is not prepended with the context
        # path. This is historical behavior of fprime-util when operating without the --target flag nor operating by
        # reading multi-target files and triggering "global" targets.
        elif isinstance(context, Path) and self.scope == TargetScope.GLOBAL:
            prepend_context_path = False
            build_target = self.build_target if self.build_target != "" else "all"
            context = context
        # When context is not a path then the context must contain the build target, and prepending the context path
        # should not be done. Context is set to the current working directory for lack of a better solution.
        #
        # TODO: how do we pass the context in (e.g. if -p was used.  Do we care?)
        elif not isinstance(context, Path):
            prepend_context_path = False
            build_target = context
            context = Path.cwd()
        else:
            assert False, f"Invalid scope supplied to execute: {self.scope}"

        # Execute the build target
        builder.execute_build_target(
            build_target, context, not prepend_context_path, args[0]
        )

    def is_supported(self, builder: "Build", context: TargetContext):
        """Is supported by the list of build target names

        Checks if the build target names supplied will support this target. Is overridden by subclasses.

        Args:
            builder: builder to check if this action is supported
            context: contextual path to check

        Return:
            True if supported false otherwise
        """
        build_target_names = builder.cmake.get_available_targets(
            str(builder.build_dir), context
        )
        return self.build_target in build_target_names


class DesignateTargetAction(Action):
    """This class, when used as the action will set the target of all DesignatedBuildSystemTarget

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
        assert len(values) == 1, "Values object should contain 1 value"

        # Build system targets are determined by appending the suffix (target in python) to a name determined by the
        # context. When specifying a specific build system target, the context must be updated to indicate this change.
        for designee in self._DESIGNEES:
            designee.set_context(values[0])
        # The build target detection looks for true/false flags to be set. Mimic this by setting 'target' to True
        setattr(namespace, "target", True)


class DesignatedBuildSystemTarget(BuildSystemTarget):
    """Invokes a designated target using the --target flag"""

    def __init__(self, _, *args, **kwargs):
        """Constructor setting child targets"""
        self.context = None
        super().__init__(None, *args, **kwargs)
        DesignateTargetAction.register_designee(self)

    def set_context(self, context: TargetContext):
        """Set the context to build"""
        self.context = context

    def execute(
        self,
        builder: "Build",
        context: TargetContext,
        args: Tuple[Dict[str, str], List[str], Dict[str, bool]],
    ):
        """ Execute with overridden context

        This will execute the underlying build system target with the context specified by the --target flag.

        Args:
            builder: builder to execute target with
            context: context path for local targets, will be ignored
            args: make system arguments directly supplied
        """
        self.execute(builder, self.context, args)



class DelegatorTarget(Target):
    """Delegates to another target

    Sometimes a target needs to be created that delegates to another target. As an example, local and global variants of
    a "both" target need to delegate through the original. This target delegates to other targets.
    """

    def __init__(self, delegate: Target, *args, **kwargs):
        """Constructor"""
        super().__init__(*args, **kwargs)
        self.delegate = delegate

    def __repr__(self):
        """So we can see what it delegated to"""
        return f"{self.__class__.__name__}[{self.delegate.__repr__()}]"

    def is_supported(self, builder: "Build", context: TargetContext):
        """Is supported by the list of build target names

        Checks if the build target names supplied will support this target. Is overridden by subclasses.

        Args:
            builder: builder to check if this action is supported
            context: contextual path to check

        Return:
            True if supported false otherwise
        """
        return self.delegate.is_supported(builder, context)

    def set_build_target(self, target):
        """Set the build target"""
        if hasattr(self.delegate, "set_build_target"):
            self.delegate.set_build_target(target)

    def option_args(self):
        """Delegate the arguments"""
        return self.delegate.option_args()

    def allows_pass_args(self):
        """Pass args allowed if any child allows it"""
        return self.delegate.allows_pass_args()

    def pass_handler(self):
        """Pass handler from delegate"""
        return self.delegate.pass_handler()

    def execute(self, *args, **kwargs):
        """Delegate the execution"""
        old_scope = self.delegate.scope
        try:
            # Temporarily overrides effective scope of delegate for this invocation
            self.delegate.scope = self.scope
            return_value = self.delegate.execute(*args, **kwargs)
        finally:
            self.delegate.scope = old_scope
        return return_value
