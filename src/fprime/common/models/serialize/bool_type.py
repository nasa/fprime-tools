"""
Created on Dec 18, 2014
@author: tcanham, reder
"""

import warnings

warnings.warn(
    "BoolType is defined in fprime_gds.common.models.serialize.bool_type. Change your imports accordingly.",
    DeprecationWarning,
    stacklevel=2,
)

# Import from new location for backward compatibility - may be removed in future versions
from fprime_gds.common.models.serialize.bool_type import BoolType
