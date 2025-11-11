"""
Created on Dec 18, 2014
@author: tcanham, reder
"""

import warnings

warnings.warn(
    "EnumType is defined in fprime_gds.common.models.serialize.enum_type. Change your imports accordingly.",
    DeprecationWarning,
    stacklevel=2,
)

# Import from new location for backward compatibility - may be removed in future versions
try:
    from fprime_gds.common.models.serialize.enum_type import (
        EnumType,
        REPRESENTATION_TYPE_MAP,
    )
except ImportError as e:
    raise ImportError(
        "EnumType has been moved to the fprime-gds package. "
        "Please install fprime-gds and update your imports to use "
        "`from fprime_gds.common.models.serialize.enum_type import EnumType`"
    ) from e
