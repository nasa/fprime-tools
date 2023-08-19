"""
Created on Dec 18, 2014
@author: tcanham, reder
"""
import struct

from .type_base import DictionaryType
from .type_exceptions import (
    DeserializeException,
    EnumMismatchException,
    NotInitializedException,
    TypeMismatchException,
    TypeRangeException,
    InvalidRepresentationTypeException,
    RepresentationTypeRangeException,
)

"""
Key is the F prime integer type as a string; value is the struct library
formatter for that type. Note that the big-Endian formatter '>' ensures
the width of the read or write.
"""
FPRIME_INTEGER_METADATA = {
    "U8":  {"struct_formatter": ">B", "min": 0,                    "max": 255},
    "U16": {"struct_formatter": ">H", "min": 0,                    "max": 65535},
    "U32": {"struct_formatter": ">I", "min": 0,                    "max": 4294967295},
    "U64": {"struct_formatter": ">Q", "min": 0,                    "max": 18446744073709551615},
    "I8":  {"struct_formatter": ">b", "min": -128,                 "max": 127},
    "I16": {"struct_formatter": ">h", "min": -32768,               "max": 32767},
    "I32": {"struct_formatter": ">i", "min": -2147483648,          "max": 2147483647},
    "I64": {"struct_formatter": ">q", "min": -9223372036854775808, "max": 9223372036854775807},
}


class EnumType(DictionaryType):
    """
    Representation of the ENUM type.

    The enumeration takes a dictionary that stores the enumeration members
    and current value as a string. The member values will have to be computed
    containing code based on C enum rules
    """

    @classmethod
    def construct_type(cls, name, enum_dict, rep_type):
        """Construct the custom enum type

        Constructs the custom enumeration type, with the supplied enumeration dictionary.

        Args:
            name: name of the enumeration type
            enum_dict: enumeration: value dictionary defining the enumeration
            rep_type: representation type (standard Fprime integer types)
        """
        if not isinstance(enum_dict, dict):
            raise TypeMismatchException(dict, type(enum_dict))
        for member in enum_dict.keys():
            if not isinstance(member, str):
                raise TypeMismatchException(str, type(member))
            if not isinstance(enum_dict[member], int):
                raise TypeMismatchException(int, enum_dict[member])

        if rep_type not in FPRIME_INTEGER_METADATA.keys():
            raise InvalidRepresentationTypeException(rep_type)

        for member in enum_dict.keys():
            if enum_dict[member] < FPRIME_INTEGER_METADATA[rep_type]["min"] or
               enum_dict[member] > FPRIME_INTEGER_METADATA[rep_type]["max"]:
                raise RepresentationTypeRangeException(
                    member,
                    enum_dict[member],
                    rep_type)

        return DictionaryType.construct_type(cls, name, ENUM_DICT=enum_dict, REP_TYPE=rep_type)

    @classmethod
    def validate(cls, val):
        """Validate the value passed into the enumeration"""
        if not isinstance(val, str):
            raise TypeMismatchException(str, type(val))
        if val not in cls.keys():
            raise EnumMismatchException(cls.__class__.__name__, val)

    @classmethod
    def keys(cls):
        """
        Return all the enum key values.
        """
        return list(cls.ENUM_DICT.keys())

    def serialize(self):
        """
        Serialize the enumeration type using an int type
        """
        # for enums, take the string value and convert it to
        # the numeric equivalent
        if self._val is None or (
            self._val == "UNDEFINED" and "UNDEFINED" not in self.ENUM_DICT
        ):
            raise NotInitializedException(type(self))
        return struct.pack(
            FPRIME_INTEGER_METADATA[self.REP_TYPE]["struct_formatter"],
            self.ENUM_DICT[self._val])

    def deserialize(self, data, offset):
        """
        Deserialize the enumeration using an int type
        """
        try:
            int_val = struct.unpack_from(
                FPRIME_INTEGER_METADATA[self.REP_TYPE]["struct_formatter"],
                data,
                offset)[0]

        except struct.error:
            msg = f"Could not deserialize enum value. Needed: {self.getSize()} bytes Found: {len(data[offset:])}"
            raise DeserializeException(msg)
        for key, val in self.ENUM_DICT.items():
            if int_val == val:
                self._val = key
                break
        # Value not found, invalid enumeration value
        else:
            raise TypeRangeException(int_val)

    def getSize(self):
        """Calculates the size based on the size of an integer used to store it"""
        return struct.calcsize(FPRIME_INTEGER_METADATA[self.REP_TYPE]["struct_formatter"])

    @classmethod
    def getMaxSize(cls):
        """Maximum size of type"""
        return struct.calcsize(FPRIME_INTEGER_METADATA["U64"]
