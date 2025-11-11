"""
Created on Dec 18, 2014

@author: tcanham

"""

import warnings

warnings.warn(
    "SerializableType is defined in fprime_gds.common.models.serialize.serializable_type. Change your imports accordingly.",
    DeprecationWarning,
    stacklevel=2,
)

# Import from new location for backward compatibility - may be removed in future versions
try:
    from fprime_gds.common.models.serialize.serializable_type import SerializableType
except ImportError as e:
    raise ImportError(
        "SerializableType has been moved to the fprime-gds package. "
        "Please install fprime-gds and update your imports to use "
        "`from fprime_gds.common.models.serialize.serializable_type import SerializableType`"
    ) from e
