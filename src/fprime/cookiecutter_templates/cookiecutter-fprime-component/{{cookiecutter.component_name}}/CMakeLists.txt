####
# F prime CMakeLists.txt:
#
# SOURCE_FILES: combined list of source and autocoding files
# MOD_DEPS: (optional) module dependencies
#
####
set(SOURCE_FILES
    "${CMAKE_CURRENT_LIST_DIR}/{{cookiecutter.component_name}}ComponentAi.xml"
    "${CMAKE_CURRENT_LIST_DIR}/{{cookiecutter.component_name}}ComponentImpl.cpp"
)

# Uncomment and add any modules that this component depends on, else
# they might not be available when cmake tries to build this component.

# set(MOD_DEPS
#     Fw/Logger
# )

register_fprime_module()

set(UT_SOURCE_FILES
  "${CMAKE_CURRENT_LIST_DIR}/test/ut/main.cpp"
  "${CMAKE_CURRENT_LIST_DIR}/test/ut/Tester.cpp"
  "${CMAKE_CURRENT_LIST_DIR}/test/ut/TesterBase.cpp"
  "${CMAKE_CURRENT_LIST_DIR}/test/ut/GTestBase.cpp"
)
register_fprime_ut()