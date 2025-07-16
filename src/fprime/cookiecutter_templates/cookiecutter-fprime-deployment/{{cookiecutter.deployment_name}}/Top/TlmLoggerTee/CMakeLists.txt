{%- if cookiecutter.enable_logging == "yes" %}
register_fprime_module(
    AUTOCODER_INPUTS
        "${CMAKE_CURRENT_LIST_DIR}/TlmLoggerTee.fpp"
    HEADERS
        "${CMAKE_CURRENT_LIST_DIR}/PingEntries.hpp"
    DEPENDS
        Svc_Subtopologies_ComLoggerTee
        Svc_Subtopologies_ComLoggerTee_ComLoggerTeeConfig
    INTERFACE
)
{%- endif %} 