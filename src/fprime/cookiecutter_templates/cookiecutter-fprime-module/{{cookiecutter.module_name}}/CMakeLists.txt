####
# FPrime CMakeLists.txt:
#
# SOURCE_FILES: combined list of source and autocoding files
# MOD_DEPS: (optional) module dependencies
# UT_SOURCE_FILES: list of source files for unit tests
#
# More information in the F´ CMake API documentation:
# https://nasa.github.io/fprime/UsersGuide/api/cmake/API.html
#
####

set(SOURCE_FILES
  "${CMAKE_CURRENT_LIST_DIR}/{{cookiecutter.module_name}}.fpp"
)

# Uncomment and add any modules that this module depends on, else
# they might not be available when cmake tries to build this module.

# set(MOD_DEPS
#   MyOtherModule
# )

register_fprime_module()
