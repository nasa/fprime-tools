"""
@file time_tag.py
@brief Class used to parse and store time tags sent with serialized data

This Class is used to parse, store, and create human readable strings for the
time tags sent with serialized data in the fprime architecture.

@date Created Dec 16, 2015
@author: dinkel

@date Updated June 18, 2018
@author R. Joseph Paetz (rpaetz@jpl.nasa.gov)

@date Updated July 22, 2019
@author Kevin C Oran (kevin.c.oran@jpl.nasa.gov)

@bug No known bugs
"""

import warnings

warnings.warn(
    "TimeType is defined in fprime_gds.common.models.serialize.time_type. Change your imports accordingly.",
    DeprecationWarning,
    stacklevel=2,
)

# Import from new location for backward compatibility - may be removed in future versions
try:
    from fprime_gds.common.models.serialize.time_type import TimeType
except ImportError as e:
    raise ImportError(
        "TimeType has been moved to the fprime-gds package. "
        "Please install fprime-gds and update your imports to use "
        "`from fprime_gds.common.models.serialize.time_type import TimeType`"
    ) from e
