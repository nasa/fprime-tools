register_fprime_module(
    AUTOCODER_INPUTS
        "${CMAKE_CURRENT_LIST_DIR}/{{cookiecutter.subtopology_instance_name}}.fpp"
    HEADERS
        "${CMAKE_CURRENT_LIST_DIR}/PingEntries.hpp"
    DEPENDS
    {%- if cookiecutter.subtopology_template != "None" %}
        Svc_Subtopologies_{{cookiecutter.subtopology_template}}_{{cookiecutter.subtopology_template}}Config
    {%- else %}
        # UPDATE NEEDED: Add dependency for custom subtopology
        # Example:
        # Your_Custom_Subtopology_Module
    {%- endif %}
    INTERFACE
)
