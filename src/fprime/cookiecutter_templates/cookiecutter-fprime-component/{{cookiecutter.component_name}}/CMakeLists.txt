####
# FPrime CMakeLists.txt:
#
# SOURCE_FILES: combined list of source and autocoding files
# MOD_DEPS: (optional) module dependencies
# UT_SOURCE_FILES: list of source files for unit tests
#
# More information in the F´ CMake API documentation:
# https://fprime.jpl.nasa.gov/latest/docs/user-manual/build-system/cmake-api/
#
####
register_fprime_library(
    AUTOCODER_INPUTS
        "${CMAKE_CURRENT_LIST_DIR}/{{cookiecutter.component_name}}.fpp"
    SOURCES
        "${CMAKE_CURRENT_LIST_DIR}/{{cookiecutter.component_name}}.cpp"
#
# Uncomment and add any modules that this module depends on, else
# they might not be available when cmake tries to build this module.
#
# Module names are derived from the path from the nearest project/library/framework
# root when not specifically overridden by the developer. i.e. The module defined by
# `Ref/SignalGen/CMakeLists.txt` will be named `Ref_SignalGen`.  `Ref/SignalGen`
# is an acceptable alternative and will be internally converted to `Ref_SignalGen`.
#
#    DEPENDS
#      MyPackage_MyOtherModule
#
)

### Unit Tests ###
# register_fprime_ut(
#     AUTOCODER_INPUTS
#         "${CMAKE_CURRENT_LIST_DIR}/{{cookiecutter.component_name}}.fpp"
#     SOURCES
#         "${CMAKE_CURRENT_LIST_DIR}/test/ut/{{cookiecutter.component_name}}TestMain.cpp"
#         "${CMAKE_CURRENT_LIST_DIR}/test/ut/{{cookiecutter.component_name}}Tester.cpp"
#     DEPENDS
#         STest # For rules-based testing
#     UT_AUTO_HELPERS
# )
