"""
Created on Dec 18, 2014

@author: reder
Replaced type base class with decorators
"""
import abc
import struct

from .type_exceptions import AbstractMethodException


class BaseType(abc.ABC):
    """
    An abstract base defining the methods supported by all base classes.
    """

    @abc.abstractmethod
    def serialize(self):
        """
        Serializes the current object type.
        """
        raise AbstractMethodException("serialize")

    @abc.abstractmethod
    def deserialize(self, data, offset):
        """
        AbstractDeserialize interface
        """
        raise AbstractMethodException("deserialize")

    @abc.abstractmethod
    def getSize(self):
        """
        Abstract getSize interface
        """
        raise AbstractMethodException("getSize")

    def __repr__(self):
        """Produces a string representation of a given type"""
        return self.__class__.__name__.replace("Type", "")

    @abc.abstractmethod
    def to_jsonable(self):
        """
        Converts this type to a JSON serializable object
        """
        raise AbstractMethodException("to_jsonable")


class ValueType(BaseType):
    """
    An abstract base type used to represent a single value. This defines the value property, allowing for setting and
    reading from the .val member.
    """

    def __init__(self, val=None):
        """Defines the single value"""
        self.__val = None
        # Run full setter
        if val is not None:
            self.val = val

    @abc.abstractmethod
    def validate(self, val):
        """
        Checks the val for validity with respect to the current type. This will raise TypeMismatchException when the
        validation fails of the val's type fails. It will raise TypeRangeException when val is out of range.

        :param val: value to validate
        :raises TypeMismatchException: value has incorrect type, TypeRangeException: val is out of range
        """

    @property
    def val(self):
        """Getter for .val"""
        return self.__val

    @val.setter
    def val(self, val):
        """Setter for .val calls validate internally"""
        self.validate(val)
        self.__val = val

    def to_jsonable(self):
        """
        Converts this type to a JSON serializable object
        """
        return {"value": self.val, "type": str(self)}


class DictionaryType(ValueType, abc.ABC):
    """Type whose specification is defined in the dictionary

    Certain types in fprime (strings, serializables, enums) are defined in the dictionary. Where all projects have
    access to primitave types (U8, F32, etc) and the definitions of theses types is global, other types complete
    specification comes from the dictionary itself. String set max-lengths per project, serializable fields are defined,
    and enumeration values are enumerated. This class is designed to take a baes framework (StringType, etc) and build
    a dynamic subclass for the given dictionary defined type.
    """

    _CONSTRUCTS = {}

    @classmethod
    def construct_type(this_cls, cls, name, **class_properties):
        """Construct a new dictionary type

        Construct a new dynamic subtype of the given base type. This type will be named with the name parameter, define
        the supplied class properties, and will be a subtype of the class.

        Args:
            name: name of the new sub type
            **class_properties: properties to define on the subtype (e.g. max lenght for strings)
        """
        assert (
            cls != DictionaryType
        ), "Cannot build dictionary type from dictionary type directly"
        construct = this_cls._CONSTRUCTS.get(name, type(name, (cls,), class_properties))
        for attr, value in class_properties.items():
            previous_value = getattr(construct, attr, None)
            assert (
                previous_value == value
            ), f"Class {name} differs by attribute {attr}. {previous_value} vs {value}"
        this_cls._CONSTRUCTS[name] = construct
        return construct


#
#
def showBytes(byteBuffer):
    """
    Routine to show bytes in buffer for testing.
    """
    print("Byte buffer size: %d" % len(byteBuffer))
    for entry in range(0, len(byteBuffer)):
        print(
            "Byte %d: 0x%02X (%c)"
            % (
                entry,
                struct.unpack("B", bytes([byteBuffer[entry]]))[0],
                struct.unpack("B", bytes([byteBuffer[entry]]))[0],
            )
        )
