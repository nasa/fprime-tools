####
# F prime CMakeLists.txt:
#
# SOURCE_FILES: combined list of source and autocoding files
# MOD_DEPS: (optional) module dependencies
#
####
set(SOURCE_FILES
    "${CMAKE_CURRENT_LIST_DIR}/{{cookiecutter.component_slug}}ComponentAi.xml"
    "${CMAKE_CURRENT_LIST_DIR}/{{cookiecutter.component_slug}}ComponentImpl.cpp"
)
{% if cookiecutter.component_multiplatform_support == "yes" %}
# Determine the platform specific source files to append:
string(TOLOWER "${CMAKE_SYSTEM_NAME}" CMAKE_SYSTEM_NAME_LOWER)

# Arduino additions
if(${CMAKE_SYSTEM_NAME_LOWER} STREQUAL "arduino")
    list(APPEND SOURCE_FILES "${CMAKE_CURRENT_LIST_DIR}/{{cookiecutter.component_slug}}ComponentArduinoImpl.cpp")
# AVR platform additions
elseif(${CMAKE_SYSTEM_NAME_LOWER} STREQUAL "avr")
    list(APPEND SOURCE_FILES "${CMAKE_CURRENT_LIST_DIR}/{{cookiecutter.component_slug}}ComponentAVRImpl.cpp")
# CygWin platform additions
elseif(${CMAKE_SYSTEM_NAME_LOWER} STREQUAL "cygwin")
    list(APPEND SOURCE_FILES "${CMAKE_CURRENT_LIST_DIR}/{{cookiecutter.component_slug}}ComponentCygWinImpl.cpp")
# Darwin platform additions
elseif(${CMAKE_SYSTEM_NAME_LOWER} STREQUAL "darwin")
    list(APPEND SOURCE_FILES "${CMAKE_CURRENT_LIST_DIR}/{{cookiecutter.component_slug}}ComponentDarwinImpl.cpp")
# Raspberry Pi platform additions
elseif(${CMAKE_SYSTEM_NAME_LOWER} STREQUAL "arm-linux-gnueabihf")
    list(APPEND SOURCE_FILES "${CMAKE_CURRENT_LIST_DIR}/{{cookiecutter.component_slug}}ComponentRPiImpl.cpp")
# VxWorks platform additions
elseif(${CMAKE_SYSTEM_NAME_LOWER} STREQUAL "vxworks")
    list(APPEND SOURCE_FILES "${CMAKE_CURRENT_LIST_DIR}/{{cookiecutter.component_slug}}ComponentVxWorksImpl.cpp")
# Otherwise, assume Linux-compatible build
else()
    list(APPEND SOURCE_FILES "${CMAKE_CURRENT_LIST_DIR}/{{cookiecutter.component_slug}}ComponentLinuxImpl.cpp")
endif()
{%- else %}
# # Determine the platform specific source files to append:
# string(TOLOWER "${CMAKE_SYSTEM_NAME}" CMAKE_SYSTEM_NAME_LOWER)

# # CygWin platform additions
# if(${CMAKE_SYSTEM_NAME_LOWER} STREQUAL "cygwin")
#     list(APPEND SOURCE_FILES "${CMAKE_CURRENT_LIST_DIR}/{{cookiecutter.component_slug}}ComponentCygWinImpl.cpp")
# # Darwin platform additions
# elseif(${CMAKE_SYSTEM_NAME_LOWER} STREQUAL "darwin")
#     list(APPEND SOURCE_FILES "${CMAKE_CURRENT_LIST_DIR}/{{cookiecutter.component_slug}}ComponentDarwinImpl.cpp")
# # VxWorks platform additions
# elseif(${CMAKE_SYSTEM_NAME_LOWER} STREQUAL "vxworks")
#     list(APPEND SOURCE_FILES "${CMAKE_CURRENT_LIST_DIR}/{{cookiecutter.component_slug}}ComponentVxWorksImpl.cpp")
# # Otherwise, assume Linux-compatible build
# else()
#     list(APPEND SOURCE_FILES "${CMAKE_CURRENT_LIST_DIR}/{{cookiecutter.component_slug}}ComponentLinuxImpl.cpp")
# endif()
{% endif %}

# Uncomment and add any modules that this component depends on, else
# they might not be available when cmake tries to build this component.

# set(MOD_DEPS
#     Fw/Logger
# )

register_fprime_module()

{% if cookiecutter.component_multiplatform_support == "yes" %}
# Add Arduino dependency
if(${CMAKE_SYSTEM_NAME_LOWER} STREQUAL "arduino")
    get_module_name(${CMAKE_CURRENT_LIST_DIR})
    add_arduino_dependency("${MODULE_NAME}")
endif()

# Add AVR dependency
if(${CMAKE_SYSTEM_NAME_LOWER} STREQUAL "avr")
    get_module_name(${CMAKE_CURRENT_LIST_DIR})
    add_avr_dependency("${MODULE_NAME}")
endif()
{% endif %}

set(UT_SOURCE_FILES
  "${CMAKE_CURRENT_LIST_DIR}/test/ut/main.cpp"
  "${CMAKE_CURRENT_LIST_DIR}/test/ut/Tester.cpp"
  "${CMAKE_CURRENT_LIST_DIR}/test/ut/TesterBase.cpp"
  "${CMAKE_CURRENT_LIST_DIR}/test/ut/GTestBase.cpp"
)
register_fprime_ut()