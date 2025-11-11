"""
numerical_types.py:

A file that contains the definitions for all the integer types provided as part of F prime.  F prime supports integers
that map to stdint.h integer sizes, that is, 8-bit, 16-bit, 32-bit, and 64-bit signed and unsigned integers.

@author mstarch
"""

import warnings

warnings.warn(
    "Numerical types are defined in fprime_gds.common.models.serialize.numerical_types. Change your imports accordingly.",
    DeprecationWarning,
    stacklevel=2,
)

# Import from new location for backward compatibility - may be removed in future versions
try:
    from fprime_gds.common.models.serialize.numerical_types import (
        NumericalType,
        IntegerType,
        FloatType,
        I8Type,
        I16Type,
        I32Type,
        I64Type,
        U8Type,
        U16Type,
        U32Type,
        U64Type,
        F32Type,
        F64Type,
    )
except ImportError as e:
    raise ImportError(
        "Numerical types have been moved to the fprime-gds package. "
        "Please install fprime-gds and update your imports to use "
        "`from fprime_gds.common.models.serialize.numerical_types import I8Type, U32Type, ...`"
    ) from e
