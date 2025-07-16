#####
# '{{cookiecutter.deployment_name}}' Deployment:
#
# This registers the '{{cookiecutter.deployment_name}}' deployment to the build system. 
# Custom components that have not been added at the project-level should be added to 
# the list below.
#
#####

###
# Topology and Components
###
{%- if cookiecutter.use_core_subtopologies == "yes" and cookiecutter.enable_logging == "yes" %}
# ComLoggerTee subtopology instances for logging (must come first)
add_fprime_subdirectory("${CMAKE_CURRENT_LIST_DIR}/Top/EventLoggerTee/")
add_fprime_subdirectory("${CMAKE_CURRENT_LIST_DIR}/Top/TlmLoggerTee/")
{%- endif %}

add_fprime_subdirectory("${CMAKE_CURRENT_LIST_DIR}/Top/")

# Add custom components to this specific deployment here
# add_fprime_subdirectory("${CMAKE_CURRENT_LIST_DIR}/MyComponent/")

register_fprime_deployment(
    SOURCES
        "${CMAKE_CURRENT_LIST_DIR}/Main.cpp"
    DEPENDS
        ${FPRIME_CURRENT_MODULE}_Top
)
