module {{cookiecutter.subtopology_instance_name}} {
    constant BASE_ID = {{cookiecutter.base_id}}
    {%- if cookiecutter.subtopology_template == "ComLogTSplit" %}
    include "{{cookiecutter.ComLogTSplit_include_path}}"
    {%- else %}
    include "{{cookiecutter.fallback_include_path}}"
    {%- endif %}
}
