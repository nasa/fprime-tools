"""
Created on Dec 18, 2014

@author: tcanham

"""
import struct

from fprime.constants import DATA_ENCODING

from . import type_base
from .type_exceptions import (
    DeserializeException,
    NotInitializedException,
    StringSizeException,
    TypeMismatchException,
)


class StringType(type_base.DictionaryType):
    """
    String type representation for F prime. This is a type that stores a half-word first for representing the length of
    this given string. Each sub string class defines the sub-type property max length that represents the maximum
    length of any string value stored to it.

    All string types follow this implementation, but have some specific type-based properties: MAX_LENGTH.
    """

    @classmethod
    def construct_type(cls, name, max_length=None):
        """Constructs a new string type with given name and maximum length"""
        return type_base.DictionaryType.construct_type(cls, name, MAX_LENGTH=max_length)

    @classmethod
    def validate(cls, val):
        """Validates that this is a string"""
        if not isinstance(val, str):
            raise TypeMismatchException(str, type(val))
        if cls.MAX_LENGTH is not None and len(val) > cls.MAX_LENGTH:
            raise StringSizeException(len(val), cls.MAX_LENGTH)

    def serialize(self):
        """
        Serializes the string in a binary format
        """
        # If val is never set then it is init exception...
        if self.val is None:
            raise NotInitializedException(type(self))
        # Check string size before serializing
        if self.MAX_LENGTH is not None and len(self.val) > self.MAX_LENGTH:
            raise StringSizeException(len(self.val), self.MAX_LENGTH)
        # Pack the string size first then return the encoded data buffer
        return struct.pack(">H", len(self.val)) + self.val.encode(DATA_ENCODING)

    def deserialize(self, data, offset):
        """
        Deserializes a string from the given data buffer.
        """
        try:
            val_size = struct.unpack_from(">H", data, offset)[0]
            # Deal with not enough data left in the buffer
            if len(data[offset + 2 :]) < val_size:
                raise DeserializeException(
                    f"Not enough data to deserialize string data. Needed: {val_size} Left: {len(data[offset + 2 :])}"
                )
            # Deal with a string that is larger than max string
            if self.MAX_LENGTH is not None and val_size > self.MAX_LENGTH:
                raise StringSizeException(val_size, self.MAX_LENGTH)
            self.val = data[offset + 2 : offset + 2 + val_size].decode(DATA_ENCODING)
        except struct.error:
            raise DeserializeException("Not enough bytes to deserialize string length.")

    def getSize(self):
        """
        Get the size of this object
        """
        return struct.calcsize(">H") + len(self.val)

    @classmethod
    def getMaxSize(cls):
        """ Get maximum size of the type """
        return struct.calcsize(">H") + cls.MAX_LENGTH