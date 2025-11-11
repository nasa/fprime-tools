"""
Created on Dec 18, 2014

@author: reder
Replaced type base class with decorators
"""

import warnings


warnings.warn(
    "TypeBase is defined in fprime_gds.common.models.serialize.type_base. Change your imports accordingly.",
    DeprecationWarning,
    stacklevel=2,
)

from fprime_gds.common.models.serialize.type_base import (
    BaseType,
    ValueType,
    DictionaryType,
)
