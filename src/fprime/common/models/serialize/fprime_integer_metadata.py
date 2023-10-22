"""
Created on Aug 29, 2023
@author: Jack White
"""

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
