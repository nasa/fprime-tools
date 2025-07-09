module {{cookiecutter.subtopology_instance_name}} {
    constant BASE_ID = {{cookiecutter.base_id}}
    {%- if cookiecutter.subtopology_template == "None" %}
    # UPDATE NEEDED: Add include path for custom subtopology
    # Example:
    # include "../path/to/your/subtopology/topology.fppi"
    {%- else %}
    include "{{cookiecutter._framework_path_str}}/Svc/Subtopologies/{{cookiecutter.subtopology_template}}/subtopology-template.fppi"
    {%- endif %}
}
