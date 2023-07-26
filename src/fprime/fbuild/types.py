from enum import Enum
from typing import List

from fprime.common.error import FprimeException


class InvalidBuildCacheException(FprimeException):
    """An exception indicating a build cache"""

    def __init__(self, message, build_cache=""):
        super().__init__(message)
        self.cache = build_cache


class UnableToDetectProjectException(FprimeException):
    """An exception indicating a build cache"""


class NoSuchTargetException(FprimeException):
    """Could not find a matching build target"""


class NoSuchToolchainException(FprimeException):
    """Could not find a matching build target"""


class AmbiguousToolchainException(FprimeException):
    """Could not find a matching build target"""


class InvalidBuildTypeException(FprimeException):
    """An exception indicating a build type do not exit"""


class MissingBuildCachePath(FprimeException):
    """An exception indicating that a path in the build cache is missing"""


class BuildType(Enum):
    """
    An enumeration used to represent the various build types used to build fprime. These types can support different
    types of targets underneath. i.e. the unit-test build may build unit test executables.
    """

    """ Normal build normal binaries for a deployment mapping to CMake 'Release'"""  # pylint: disable=W0105
    BUILD_NORMAL = (0,)
    """ Testing build allowing unit testing mapping to CMake 'Testing'"""  # pylint: disable=W0105
    BUILD_TESTING = 1
    """ FPP locations build """
    BUILD_FPP_LOCS = 2
    """ User custom build """
    BUILD_CUSTOM = 3

    def get_suffix(self):
        """Get the suffix of a directory supporting this build"""
        if self == BuildType.BUILD_NORMAL:
            return ""
        if self == BuildType.BUILD_TESTING:
            return "-ut"
        msg = f"{self.name} is not a supported build type"
        raise InvalidBuildTypeException(msg)

    def get_cmake_build_type(self):
        """Get the suffix of a directory supporting this build"""
        if self == BuildType.BUILD_NORMAL:
            return "Release"
        if self == BuildType.BUILD_TESTING:
            return "Testing"
        if self == BuildType.BUILD_FPP_LOCS:
            return "Release"
        if self == BuildType.BUILD_CUSTOM:
            return "Custom"
        msg = f"{self.name} is not a supported build type"
        raise InvalidBuildTypeException(msg)

    @staticmethod
    def get_public_types() -> List["BuildType"]:
        """Returns public build types"""
        return [BuildType.BUILD_NORMAL, BuildType.BUILD_TESTING]
