####
# F Prime CMakeLists.txt:
#
# SOURCES: list of source files (to be compiled)
# AUTOCODER_INPUTS: list of files to be passed to the autocoders
# DEPENDS: list of libraries that this module depends on
#
# More information in the F´ CMake API documentation:
# https://fprime.jpl.nasa.gov/latest/docs/reference/api/cmake/API/
#
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
