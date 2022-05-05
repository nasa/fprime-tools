""" Generic representation of autocoded array types

Created on May 29, 2020
@author: jishii
"""
import copy

from .type_base import DictionaryType
from .type_exceptions import (
    ArrayLengthException,
    NotInitializedException,
    TypeMismatchException,
)

from . import serializable_type
from fprime.util.string_util import format_string_template


class ArrayType(DictionaryType):
    """Generic fixed-size array type representation.

    Represents a custom named type of a fixed number of like members, each of which are other types in the system.
    """

    @classmethod
    def construct_type(cls, name, member_type, length, format):
        """Constructs a sub-array type

        Constructs a new sub-type of array to represent an array of the given name, member type, length, and format
        string.

        Args:
            name: name of the array subtype
            member_type: type of the members of the array subtype
            length: length of the array subtype
            format: format string for members of the array subtype
        """
        return DictionaryType.construct_type(
            cls, name, MEMBER_TYPE=member_type, LENGTH=length, FORMAT=format
        )

    @classmethod
    def validate(cls, val):
        """Validates the values of the array"""
        if len(val) != cls.LENGTH:
            raise ArrayLengthException(cls.MEMBER_TYPE, cls.LENGTH, len(val))
        for i in range(cls.LENGTH):
            cls.MEMBER_TYPE.validate(val[i])

    @property
    def val(self) -> list:
        """
        The .val property typically returns the python-native type. This the python native type closes to a serializable
        without generating full classes would be a dictionary (anonymous object). This returns such an object.

        :return dictionary of member names to python values of member keys
        """
        return [item.val for item in self.__val]

    @property
    def formatted_val(self) -> list:
        """
        Format all the elements of array according to the arr_format.
        Note 1: All elements will be cast to str
        Note 2: If a member is a serializable will call serializable formatted_val
        :return a formatted array
        """
        result = []
        for item in self.__val:
            if isinstance(item, (serializable_type.SerializableType, ArrayType)):
                result.append(item.formatted_val)
            else:
                result.append(format_string_template(self.FORMAT, item.val))
        return result

    @val.setter
    def val(self, val: list):
        """
        The .val property typically returns the python-native type. This the python native type closes to a serializable
        without generating full classes would be a dictionary (anonymous object). This takes such an object and sets the
        member val list from it.

        :param val: dictionary containing python types to key names. This
        """
        self.validate(val)
        items = [self.MEMBER_TYPE(item) for item in val]
        self.__val = items

    def to_jsonable(self):
        """
        JSONable type
        """
        members = {
            "name": self.__class__.__name__,
            "type": self.__class__.__name__,
            "size": self.LENGTH,
            "format": self.FORMAT,
            "values": None
            if self.__val is None
            else [member.to_jsonable() for member in self.__val],
        }
        return members

    def serialize(self):
        """Serialize the array by serializing the elements one by one"""
        if self.val is None:
            raise NotInitializedException(type(self))
        return b"".join([item.serialize() for item in self.__val])

    def deserialize(self, data, offset):
        """Deserialize the members of the array"""
        values = []
        for i in range(self.LENGTH):
            item = self.MEMBER_TYPE()
            item.deserialize(data, offset + i * item.getSize())
            values.append(item.val)
        self.val = values

    def getSize(self):
        """Return the size of the array"""
        return sum([item.getSize() for item in self.__val])
