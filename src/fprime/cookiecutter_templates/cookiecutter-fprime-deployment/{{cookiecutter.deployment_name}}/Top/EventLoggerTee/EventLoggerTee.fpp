{%- if cookiecutter.enable_logging == "yes" %}
module EventLoggerTee {
    constant BASE_ID = 0x10800000
    
    # Include the ComLoggerTee subtopology template
    include "../../../Svc/Subtopologies/ComLoggerTee/subtopology-template.fppi"
}
{%- endif %} 