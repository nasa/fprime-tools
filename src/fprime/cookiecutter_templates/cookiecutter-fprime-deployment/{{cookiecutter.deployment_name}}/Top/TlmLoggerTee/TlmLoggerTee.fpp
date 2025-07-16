{%- if cookiecutter.enable_logging == "yes" %}
module TlmLoggerTee {
    constant BASE_ID = 0x10900000
    
    # Include the ComLoggerTee subtopology template
    include "../../../Svc/Subtopologies/ComLoggerTee/subtopology-template.fppi"
}
{%- endif %} 