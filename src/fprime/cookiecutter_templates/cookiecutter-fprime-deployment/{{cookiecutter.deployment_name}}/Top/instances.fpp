module {{cookiecutter.deployment_name}} {

  # ----------------------------------------------------------------------
  # Defaults
  # ----------------------------------------------------------------------

  module Default {
    constant QUEUE_SIZE = 10
    constant STACK_SIZE = 64 * 1024
  }

  # ----------------------------------------------------------------------
  # Active component instances
  # ----------------------------------------------------------------------

  instance rateGroup1: Svc.ActiveRateGroup base id 0x01010000 \
    queue size Default.QUEUE_SIZE \
    stack size Default.STACK_SIZE \
    priority 120

  instance rateGroup2: Svc.ActiveRateGroup base id 0x01020000 \
    queue size Default.QUEUE_SIZE \
    stack size Default.STACK_SIZE \
    priority 119

  instance rateGroup3: Svc.ActiveRateGroup base id 0x01030000 \
    queue size Default.QUEUE_SIZE \
    stack size Default.STACK_SIZE \
    priority 118

  # ----------------------------------------------------------------------
  # Queued component instances
  # ----------------------------------------------------------------------


  # ----------------------------------------------------------------------
  # Passive component instances
  # ----------------------------------------------------------------------

  instance chronoTime: Svc.ChronoTime base id 0x01040000

  instance rateGroupDriver: Svc.RateGroupDriver base id 0x01050000

  instance systemResources: Svc.SystemResources base id 0x01060000

  instance linuxTimer: Svc.LinuxTimer base id 0x01070000
{%- if cookiecutter.com_driver_type == "TcpClient" %}
  instance comDriver: Drv.TcpClient base id 0x01080000 \
  {
      phase Fpp.ToCpp.Phases.configComponents """
      if (state.hostname != nullptr && state.port != 0) {
          {{cookiecutter.deployment_name}}::comDriver.configure(state.hostname, state.port);
      }
      """

      phase Fpp.ToCpp.Phases.startTasks """
      // Initialize socket client communication if and only if there is a valid specification
      if (state.hostname != nullptr && state.port != 0) {
          Os::TaskString name("ReceiveTask");
          {{cookiecutter.deployment_name}}::comDriver.start(name, 100, Default.STACK_SIZE);
      }
      """

      phase Fpp.ToCpp.Phases.stopTasks """
      {{cookiecutter.deployment_name}}::comDriver.stop();
      """

      phase Fpp.ToCpp.Phases.freeThreads """
      (void){{cookiecutter.deployment_name}}::comDriver.join();
      """
  }
{%- elif cookiecutter.com_driver_type == "TcpServer" %}
  instance comDriver: Drv.TcpServer base id 0x01080000 \
  {
      phase Fpp.ToCpp.Phases.configComponents """
      if (state.port != 0) {
          {{cookiecutter.deployment_name}}::comDriver.configure(state.port);
      }
      """

      phase Fpp.ToCpp.Phases.startTasks """
      // Initialize socket server communication if and only if there is a valid specification
      if (state.port != 0) {
          Os::TaskString name("ReceiveTask");
          {{cookiecutter.deployment_name}}::comDriver.start(name, 100, Default.STACK_SIZE);
      }
      """

      phase Fpp.ToCpp.Phases.stopTasks """
      {{cookiecutter.deployment_name}}::comDriver.stop();
      """

      phase Fpp.ToCpp.Phases.freeThreads """
      (void){{cookiecutter.deployment_name}}::comDriver.join();
      """
  }
{%- elif cookiecutter.com_driver_type == "UART" %}
  instance comDriver: Drv.LinuxUartDriver base id 0x01080000 \
  {
      phase Fpp.ToCpp.Phases.configComponents """
      if (state.uartDevice != nullptr && state.baudRate != 0) {
          {{cookiecutter.deployment_name}}::comDriver.configure(state.uartDevice, static_cast<Drv::LinuxUartDriver::UartBaudRate>(state.baudRate));
      }
      """

      phase Fpp.ToCpp.Phases.startTasks """
      // Initialize UART communication if and only if there is a valid specification
      if (state.uartDevice != nullptr && state.baudRate != 0) {
          Os::TaskString name("ReceiveTask");
          {{cookiecutter.deployment_name}}::comDriver.start(name, 100, Default.STACK_SIZE);
      }
      """

      phase Fpp.ToCpp.Phases.stopTasks """
      {{cookiecutter.deployment_name}}::comDriver.stop();
      """

      phase Fpp.ToCpp.Phases.freeThreads """
      (void){{cookiecutter.deployment_name}}::comDriver.join();
      """
  }
{%- endif %}

}
