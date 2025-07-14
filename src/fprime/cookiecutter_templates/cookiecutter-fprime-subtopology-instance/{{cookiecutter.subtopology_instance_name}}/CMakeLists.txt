# Clear any variables that might cause conflicts with source files
# Helps with backwards compatibility for old F' build system
#unset(SOURCE_FILES)
#unset(MOD_DEPS)

# Determine the subtopology template path and resolve target names
set(SUBTOPOLOGY_TEMPLATE_PATH "{{cookiecutter.subtopology_template_path}}")
get_filename_component(SUBTOPOLOGY_TEMPLATE_PATH "${SUBTOPOLOGY_TEMPLATE_PATH}" ABSOLUTE)
get_module_name("${SUBTOPOLOGY_TEMPLATE_PATH}")
set(SUBTOPOLOGY_DEPENDS "${MODULE_NAME}")

# Check for config dependency named after the template
get_filename_component(SUBTOPOLOGY_TEMPLATE_NAME "${SUBTOPOLOGY_TEMPLATE_PATH}" NAME)
set(CONFIG_DIR "${SUBTOPOLOGY_TEMPLATE_PATH}/${SUBTOPOLOGY_TEMPLATE_NAME}Config")
if(EXISTS "${CONFIG_DIR}" AND IS_DIRECTORY "${CONFIG_DIR}")
    get_module_name("${CONFIG_DIR}")
    list(APPEND SUBTOPOLOGY_DEPENDS "${MODULE_NAME}")
endif()

message(STATUS "SUBTOPOLOGY_DEPENDS: ${SUBTOPOLOGY_DEPENDS}")

register_fprime_module(
    AUTOCODER_INPUTS
        "${CMAKE_CURRENT_LIST_DIR}/{{cookiecutter.subtopology_instance_name}}.fpp"
    HEADERS
        "${CMAKE_CURRENT_LIST_DIR}/PingEntries.hpp"
    DEPENDS
        ${SUBTOPOLOGY_DEPENDS}
    INTERFACE
)
