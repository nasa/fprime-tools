####
# F prime CMakeLists.txt:
#
# SOURCE_FILES: combined list of source and autocoding files
# MOD_DEPS: (optional) module dependencies
####

set(SOURCE_FILES
  "${CMAKE_CURRENT_LIST_DIR}/instances.fpp"
  # Note: Uncomment when using Svc:TlmPacketizer
  #"${CMAKE_CURRENT_LIST_DIR}/{{cookiecutter.deployment_name}}Packets.xml"
  "${CMAKE_CURRENT_LIST_DIR}/topology.fpp"
  "${CMAKE_CURRENT_LIST_DIR}/{{cookiecutter.deployment_name}}Topology.cpp"
)
set(MOD_DEPS
  Fw/Logger
  Svc/PosixTime
  # Communication Implementations
  Drv/Udp
{%- if cookiecutter.com_driver_type == "TcpClient" %}
  Drv/TcpClient
{%- elif cookiecutter.com_driver_type == "TcpServer" %}
  Drv/TcpServer
{%- elif cookiecutter.com_driver_type == "UART" %}
  Drv/LinuxUartDriver
{%- endif %}
)

register_fprime_module()
