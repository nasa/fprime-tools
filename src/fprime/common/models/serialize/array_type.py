"""Generic representation of autocoded array types

Created on May 29, 2020
@author: jishii
"""

import warnings

warnings.warn(
    "ArrayType is defined in fprime_gds.common.models.serialize.array_type. Change your imports accordingly.",
    DeprecationWarning,
    stacklevel=2,
)

# Import from new location for backward compatibility - may be removed in future versions
from fprime_gds.common.models.serialize.array_type import ArrayType
