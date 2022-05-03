"""
Created on Dec 18, 2014

@author: tcanham

"""

# Exception classes for all types
from fprime.common.error import FprimeException


class TypeException(FprimeException):
    """An exception in our python types"""

    def __init__(self, val):
        super().__init__(val)
        self.except_msg = val

    def getMsg(self):
        """Gets the exception message"""
        return self.except_msg


class AbstractMethodException(TypeException):
    """Not implemented exception under another name"""

    def __init__(self, val):
        super().__init__(f"{str(val)} must be implemented since it is abstract!")


class TypeRangeException(TypeException):
    """Value is out of range"""

    def __init__(self, val):
        super().__init__(f"Value {str(val)} out of range!")


class StringSizeException(TypeException):
    """String size is to large for defined type"""

    def __init__(self, size, max_size):
        super().__init__(f"String size {str(size)} is greater than {str(max_size)}!")


class TypeMismatchException(TypeException):
    """Wrong type found exception"""

    def __init__(self, expected_type, actual_type):
        super().__init__(f"Type {expected_type} expected, type {actual_type} found!")


class ArrayLengthException(TypeException):
    """Array length mismatched"""

    def __init__(self, arr_type, expected_len, actual_len):
        super().__init__(
            f"Array type {arr_type} is of length {expected_len}, actual length {actual_len} found!"
        )


class EnumMismatchException(TypeException):
    """Enum member not defined"""

    def __init__(self, enum, bad_member):
        super().__init__(f"Invalid enum member {bad_member} set in {enum} enum!")


class MissingMemberException(TypeException):
    """Member was not defined on type"""

    def __init__(self, field):
        super().__init__(f"Value does not define required field: {field}")


class DeserializeException(TypeException):
    """Exception during deserialization"""

    pass


class ArgNotFoundException(TypeException):
    """Argument not found exception"""

    def __init__(self, message):
        super().__init__(f"Arg {message} not found!")


class NotInitializedException(TypeException):
    """Did not initialize types"""

    def __init__(self, message):
        super().__init__(f"Instance {message} not initialized!")


class NotOverriddenException(TypeException):
    """Not implemented exception by another name"""

    def __init__(self, message):
        super().__init__(
            f"Required base class method not overwritten in type {message}!"
        )


class ArgLengthMismatchException(TypeException):
    """Mismatch in args lengths vs definition of args"""

    def __init__(self, arg_length_actual, arg_length_given):
        super().__init__(
            "%d args provided, but command expects %d args!"
            % (arg_length_given, arg_length_actual)
        )


class CompoundTypeLengthMismatchException(TypeException):
    """Compound type fields mismatch"""

    def __init__(self, field_length_actual, field_length_given):
        super().__init__(
            "%d fields provided, but compound type expects %d fields!"
            % (field_length_given, field_length_actual)
        )
