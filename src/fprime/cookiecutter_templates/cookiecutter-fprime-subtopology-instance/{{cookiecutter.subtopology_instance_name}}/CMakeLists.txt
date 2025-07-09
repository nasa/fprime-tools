register_fprime_module(
    AUTOCODER_INPUTS
        "${CMAKE_CURRENT_LIST_DIR}/{{cookiecutter.subtopology_instance_name}}.fpp"
    HEADERS
    {%- if cookiecutter.subtopology_template != "None" %}
        "{{cookiecutter._framework_path_str}}/Svc/Subtopologies/{{cookiecutter.subtopology_template}}/PingEntries.hpp"
        {%- if cookiecutter.subtopology_template in [] %}
        "{{cookiecutter._framework_path_str}}/Svc/Subtopologies/{{cookiecutter.subtopology_template}}/SubtopologyTopologyDefs.hpp"
        {%- endif %}
    {%- else %}
        # UPDATE NEEDED: Add headers for custom subtopology
        # Example:
        # "${CMAKE_CURRENT_LIST_DIR}/../path/to/your/subtopology/PingEntries.hpp"
        # "${CMAKE_CURRENT_LIST_DIR}/../path/to/your/subtopology/YourSubtopologyTopologyDefs.hpp"
    {%- endif %}
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
