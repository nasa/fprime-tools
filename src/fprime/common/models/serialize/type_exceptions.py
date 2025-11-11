"""
Created on Dec 18, 2014

@author: tcanham

"""

# Exception classes for all types
from fprime.common.error import FprimeException

from fprime_gds.common.models.serialize.type_exceptions import (
    FprimeGdsException,
    AbstractMethodException,
    TypeRangeException,
    StringSizeException,
    TypeMismatchException,
    ArrayLengthException,
    EnumMismatchException,
    MissingMemberException,
    IncorrectMembersException,
    DeserializeException,
    ArgNotFoundException,
    NotInitializedException,
    NotOverriddenException,
    ArgLengthMismatchException,
    CompoundTypeLengthMismatchException,
    InvalidRepresentationTypeException,
    RepresentationTypeRangeException,
)

import warnings

warnings.warn(
    "Ground type system has been migrated to the fprime-gds package, in fprime_gds.common.models.serialize. Change your imports accordingly.",
    DeprecationWarning,
    stacklevel=2,
)
