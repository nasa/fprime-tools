####
# FPrime CMakeLists.txt:
#
# SOURCE_FILES: combined list of source and autocoding files
# MOD_DEPS: (optional) module dependencies
# UT_SOURCE_FILES: list of source files for unit tests
#
# More information in the F´ CMake API:
# https://nasa.github.io/fprime/UsersGuide/api/cmake/API.html#function-register_fprime_module
#
####

set(SOURCE_FILES
  "${CMAKE_CURRENT_LIST_DIR}/{{cookiecutter.component_name}}.fpp"
  "${CMAKE_CURRENT_LIST_DIR}/{{cookiecutter.component_name}}.cpp"
)

# Uncomment and add any modules that this component depends on, else
# they might not be available when cmake tries to build this component.

# set(MOD_DEPS
#     Add your dependencies here
# )

register_fprime_module()
