"""
Created on Dec 18, 2014

@author: tcanham

"""
import copy

from .type_base import BaseType, DictionaryType
from .type_exceptions import (
    MissingMemberException,
    NotInitializedException,
    TypeMismatchException,
)

from . import array_type
from fprime.util.string_util import format_string_template


class SerializableType(DictionaryType):
    """
    Representation of the Serializable type (comparable to the ANY type)

    The serializable type is a container for other instances of
    BaseType, including itself.

    @param param: typename = "SomeTypeName" string
    To preserve member order, the member argument is a list of members and their types:
    @param param: mem_list = [ ("member",<ref to BaseType>, format string, description), ... ]
    OR mem_list = [ ("member",<ref to BaseType>, format string), ... ].
    The member descriptions can be None
    """

    @classmethod
    def construct_type(cls, name, member_list=None):
        """Construct a new serializable sub-type

        Constructs a new serializable subtype from the supplied member list and name. Member list may optionally exclude
        description keys, which will be filled with None.

        Args:
            name: name of the new sub-type
            member_list: list of member definitions in form list of tuples (name, type, format string, description)
        """
        if member_list:
            member_list = [list(item) + ([None] * (4 -len(item))) for item in member_list]
            # Check that we are dealing with a list
            if not isinstance(member_list, list):
                raise TypeMismatchException(list, type(member_list))
            # Check the validity of the member list
            for member_name, member_type, format_string, description in member_list:
                # Check each of these members for correct types
                if not isinstance(member_name, str):
                    raise TypeMismatchException(str, type(member_name))
                elif not issubclass(member_type, BaseType):
                    raise TypeMismatchException(BaseType, member_type)
                elif format_string is not None and not isinstance(format_string, str):
                    raise TypeMismatchException(str, type(format_string))
                elif description is not None and not isinstance(description, str):
                    raise TypeMismatchException(str, type(description))
        return DictionaryType.construct_type(cls, name, MEMBER_LIST=member_list)

    @classmethod
    def validate(cls, val):
        """Validate this object including member list and values"""
        if not cls.MEMBER_LIST:
            return
        # Ensure that the supplied value is a dictionary
        if not isinstance(val, dict):
            raise TypeMismatchException(dict, type(val))
        # Now validate each field as defined via the value
        for member_name, member_type, _, _ in cls.MEMBER_LIST:
            member_val = val.get(member_name, None)
            if not member_val:
                raise MissingMemberException(member_name)
            member_type.validate(member_val)

    @property
    def val(self) -> dict:
        """
        The .val property typically returns the python-native type. This the python native type closes to a serializable
        without generating full classes would be a dictionary (anonymous object). This returns such an object.

        :return dictionary of member names to python values of member keys
        """
        return {
            member_name: self._val.get(member_name).val
            for member_name, _, _, _ in self.MEMBER_LIST
        }

    @val.setter
    def val(self, val: dict):
        """
        The .val property typically returns the python-native type. This the python native type closes to a serializable
        without generating full classes would be a dictionary (anonymous object). This takes such an object and sets the
        member val list from it.

        :param val: dictionary containing python types to key names. This
        """
        self.validate(val)
        self._val = {
            member_name: member_type(val.get(member_name))
            for member_name, member_type, _, _, in self.MEMBER_LIST
        }

    @property
    def formatted_val(self) -> dict:
        """
        Format all the members of dict according to the member_format.
        Note 1: All elements will be cast to str
        Note 2: If a member is an array will call array formatted_val
        :return a formatted dict
        """
        result = dict()
        for member_name, _, member_format, _ in self.MEMBER_LIST:
            value_object = self._val[member_name]
            if isinstance(value_object, (array_type.ArrayType, SerializableType)):
                result[member_name] = value_object.formatted_val
            else:
                result[member_name] = format_string_template(
                    member_format, value_object.val
                )
        return result

    def serialize(self):
        """Serializes the members of the serializable"""
        if self.MEMBER_LIST is None:
            raise NotInitializedException(type(self))
        return b"".join(
            [
                self._val.get(member_name).serialize()
                for member_name, _, _, _ in self.MEMBER_LIST
            ]
        )

    def deserialize(self, data, offset):
        """Deserialize the values of each of the members"""
        new_value = {}
        for member_name, member_type, _, _ in self.MEMBER_LIST:
            new_member = member_type()
            new_member.deserialize(data, offset)
            new_value[member_name] = new_member
            offset += new_member.getSize()
        self._val = new_value

    def getSize(self):
        """The size of a struct is the size of all the members"""
        return sum(self._val.get(name).getSize() for name, _, _, _ in self.MEMBER_LIST)

    def to_jsonable(self):
        """
        JSONable type for a serializable
        """
        members = {}
        for member_name, member_value, member_format, member_desc in self.mem_list:
            members[member_name] = {"format": member_format, "description": member_desc}
            members[member_name].update(self._val.get(member_name).to_jsonable())
        return members
