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
)


class EnumType(DictionaryType):
    """
    Representation of the ENUM type.

    The enumeration takes a dictionary that stores the enumeration members
    and current value as a string. The member values will have to be computed
    containing code based on C enum rules
    """

    @classmethod
    def construct_type(cls, name, enum_dict):
        """Construct the custom enum type

        Constructs the custom enumeration type, with the supplied enumeration dictionary.

        Args:
            name: name of the enumeration type
            enum_dict: enumeration: value dictionary defining the enumeration
        """
        if not isinstance(enum_dict, dict):
            raise TypeMismatchException(dict, type(enum_dict))
        for member in enum_dict.keys():
            if not isinstance(member, str):
                raise TypeMismatchException(str, type(member))
            if not isinstance(enum_dict[member], int):
                raise TypeMismatchException(int, enum_dict[member])
        return DictionaryType.construct_type(cls, name, ENUM_DICT=enum_dict)

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
        return struct.pack(">i", self.ENUM_DICT[self._val])

    def deserialize(self, data, offset):
        """
        Deserialize the enumeration using an int type
        """
        try:
            int_val = struct.unpack_from(">i", data, offset)[0]
        except struct.error:
            raise DeserializeException(
                f"Could not deserialize enum value. Needed: {self.getSize()} bytes Found: {len(data[offset:])}"
            )
        for key, val in self.ENUM_DICT.items():
            if int_val == val:
                self._val = key
                break
        # Value not found, invalid enumeration value
        else:
            raise TypeRangeException(int_val)

    def getSize(self):
        """Calculates the size based on the size of an integer used to store it"""
        return struct.calcsize(">i")
