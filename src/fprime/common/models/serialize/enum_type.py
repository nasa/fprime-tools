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

    def __init__(self, val="UNDEFINED"):
        """ Construct the enumeration value, called through sub-type constructor

        Args:
            val: (optional) value this instance of enumeration is set to. Default: "UNDEFINED"
        """
        super().__init__(val)


    @classmethod
    def construct_type(cls, name, enum_dict=None):
        """ Construct the custom enum type

        Constructs the custom enumeration type, with the supplied enumeration dictionary.

        Args:
            name: name of the enumeration type
            enum_dict: enumeration: value dictionary defining the enumeration
        """
        enum_dict = enum_dict if enum_dict is not None else {"UNDEFINED": 0}
        if not isinstance(enum_dict, dict):
            raise TypeMismatchException(dict, type(enum_dict))
        for member in enum_dict.keys():
            if not isinstance(member, str):
                raise TypeMismatchException(str, type(member))
            elif not isinstance(enum_dict[member], int):
                raise TypeMismatchException(int, enum_dict[member])
        return DictionaryType.construct_type(cls, name, ENUM_DICT=enum_dict)

    def validate(self, val):
        """Validate the value passed into the enumeration"""
        if val != "UNDEFINED" and val not in self.keys():
            raise EnumMismatchException(self.__class__.__name__, val)

    def keys(self):
        """
        Return all the enum key values.
        """
        return list(self.ENUM_DICT.keys())

    def serialize(self):
        """
        Serialize the enumeration type using an int type
        """
        # for enums, take the string value and convert it to
        # the numeric equivalent
        if self.val is None:
            raise NotInitializedException(type(self))
        return struct.pack(">i", self.ENUM_DICT[self.val])

    def deserialize(self, data, offset):
        """
        Deserialize the enumeration using an int type
        """
        try:
            int_val = struct.unpack_from(">i", data, offset)[0]
        except:
            raise DeserializeException(
                f"Could not deserialize enum value. Needed: {self.getSize()} bytes Found: {len(data[offset:])}"
            )
        for key, val in self.ENUM_DICT.items():
            if int_val == val:
                self.val = key
                break
        # Value not found, invalid enumeration value
        else:
            raise TypeRangeException(int_val)

    def getSize(self):
        """Calculates the size based on the size of an integer used to store it"""
        return struct.calcsize(">i")
