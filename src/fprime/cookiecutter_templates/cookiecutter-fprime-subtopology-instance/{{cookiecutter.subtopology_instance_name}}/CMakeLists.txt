# Clear any variables that might cause conflicts with source files
# Helps with backwards compatibility for old F' build system
unset(SOURCE_FILES)
unset(MOD_DEPS)

# Dependencies resolved by post-generation hook
# SUBTOPOLOGY_TEMPLATE_PATH: {{cookiecutter.subtopology_template_path}}
set(SUBTOPOLOGY_DEPENDS "PLACEHOLDER_DEPENDENCIES")

register_fprime_module(
    AUTOCODER_INPUTS
        "${CMAKE_CURRENT_LIST_DIR}/{{cookiecutter.subtopology_instance_name}}.fpp"
    HEADERS
        "${CMAKE_CURRENT_LIST_DIR}/PingEntries.hpp"
    DEPENDS
        ${SUBTOPOLOGY_DEPENDS}
    INTERFACE
)
