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

try:
    from fprime_gds.common.models.serialize.type_base import (
        BaseType,
        ValueType,
        DictionaryType,
    )
except ImportError as e:
    raise ImportError(
        "BaseType, ValueType, and DictionaryType have been moved to the fprime-gds package. "
        "Please install fprime-gds and update your imports to use "
        "`from fprime_gds.common.models.serialize.type_base import BaseType, ValueType, DictionaryType`"
    ) from e
