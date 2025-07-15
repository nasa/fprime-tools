module {{cookiecutter.deployment_name}} {

  # ----------------------------------------------------------------------
  # Defaults
  # ----------------------------------------------------------------------

  module Default {
    constant QUEUE_SIZE = 10
    constant STACK_SIZE = 64 * 1024
  }

{% if cookiecutter.use_core_subtopologies == "yes" %}
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

{% else %}
  # ----------------------------------------------------------------------
  # Active component instances
  # ----------------------------------------------------------------------

  instance cmdDisp: Svc.CommandDispatcher base id 0x01050000 \
    queue size 20 \
    stack size Default.STACK_SIZE \
    priority 101

  instance cmdSeq: Svc.CmdSequencer base id 0x01060000 \
    queue size Default.QUEUE_SIZE \
    stack size Default.STACK_SIZE \
    priority 100

  instance comQueue: Svc.ComQueue base id 0x01070000 \
      queue size 50 \
      stack size Default.STACK_SIZE \
      priority 100 \

  instance fileDownlink: Svc.FileDownlink base id 0x01080000 \
    queue size 30 \
    stack size Default.STACK_SIZE \
    priority 100

  instance fileManager: Svc.FileManager base id 0x01090000 \
    queue size 30 \
    stack size Default.STACK_SIZE \
    priority 100

  instance fileUplink: Svc.FileUplink base id 0x010A0000 \
    queue size 30 \
    stack size Default.STACK_SIZE \
    priority 100

  instance eventLogger: Svc.ActiveLogger base id 0x010B0000 \
    queue size Default.QUEUE_SIZE \
    stack size Default.STACK_SIZE \
    priority 98

  # comment in Svc.TlmChan or Svc.TlmPacketizer
  # depending on which form of telemetry downlink
  # you wish to use

  instance tlmSend: Svc.TlmChan base id 0x010C0000 \
    queue size Default.QUEUE_SIZE \
    stack size Default.STACK_SIZE \
    priority 97

  #instance tlmSend: Svc.TlmPacketizer base id 0x010C0000 \
  #    queue size Default.QUEUE_SIZE \
  #    stack size Default.STACK_SIZE \
  #    priority 97

  instance prmDb: Svc.PrmDb base id 0x010D0000 \
    queue size Default.QUEUE_SIZE \
    stack size Default.STACK_SIZE \
    priority 96

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

  instance $health: Svc.Health base id 0x010E0000 \
    queue size 25

  # ----------------------------------------------------------------------
  # Passive component instances
  # ----------------------------------------------------------------------

  @ Communications driver. May be swapped with other com drivers like UART or TCP
{% if cookiecutter.com_driver_type == "UART" %}
  instance comDriver: Drv.LinuxUartDriver base id 0x010F0000
{% else %}
  instance comDriver: Drv.{{cookiecutter.com_driver_type}} base id 0x010F0000 
{% endif %}

  instance framer: Svc.FprimeFramer base id 0x01100000

  instance fatalAdapter: Svc.AssertFatalAdapter base id 0x01110000

  instance fatalHandler: Svc.FatalHandler base id 0x01120000

  instance bufferManager: Svc.BufferManager base id 0x01130000

  instance chronoTime: Svc.ChronoTime base id 0x01140000

  instance rateGroupDriver: Svc.RateGroupDriver base id 0x01150000

  instance textLogger: Svc.PassiveTextLogger base id 0x01160000

  instance deframer: Svc.FprimeDeframer base id 0x01170000

  instance systemResources: Svc.SystemResources base id 0x01180000

  instance comStub: Svc.ComStub base id 0x01190000

  instance frameAccumulator: Svc.FrameAccumulator base id 0x011A0000

  instance fprimeRouter: Svc.FprimeRouter base id 0x011B0000

  instance version: Svc.Version base id 0x011C0000

  instance linuxTimer: Svc.LinuxTimer base id 0x011D0000

{% endif %}

}
