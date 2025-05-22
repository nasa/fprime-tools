####
# F prime CMakeLists.txt:
#
# SOURCE_FILES: combined list of source and autocoding files
# MOD_DEPS: (optional) module dependencies
####

register_fprime_module(
    AUTOCODER_INPUTS
        "${CMAKE_CURRENT_LIST_DIR}/instances.fpp"
        "${CMAKE_CURRENT_LIST_DIR}/topology.fpp"
    SOURCES
        "${CMAKE_CURRENT_LIST_DIR}/{{cookiecutter.deployment_name}}Topology.cpp"
    DEPENDS
{%- if cookiecutter.com_driver_type == "TcpClient" %}
        Drv_TcpClient
{%- elif cookiecutter.com_driver_type == "TcpServer" %}
        Drv_TcpServer
{%- elif cookiecutter.com_driver_type == "UART" %}
        Drv_LinuxUartDriver
{%- endif %}
)
