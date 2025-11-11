"""
Created on Dec 18, 2014

@author: tcanham

"""

import warnings

warnings.warn(
    "Ground type system has been migrated to the fprime-gds package, in fprime_gds.common.models.serialize. Change your imports accordingly.",
    DeprecationWarning,
    stacklevel=2,
)

# Exception classes for all types
from fprime.common.error import FprimeException

try:
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
except ImportError as e:
    raise ImportError(
        "Type exceptions have been moved to the fprime-gds package. "
        "Please install fprime-gds and update your imports to use "
        "`from fprime_gds.common.models.serialize.type_exceptions import TypeMismatchException, ...`"
    ) from e
