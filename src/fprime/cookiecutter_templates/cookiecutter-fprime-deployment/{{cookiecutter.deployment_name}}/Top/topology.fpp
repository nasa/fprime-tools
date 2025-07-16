module {{cookiecutter.deployment_name}} {

  # ----------------------------------------------------------------------
  # Symbolic constants for port numbers
  # ----------------------------------------------------------------------

  enum Ports_RateGroups {
    rateGroup1
    rateGroup2
    rateGroup3
  }
{%- if cookiecutter.use_core_subtopologies == "no" %}
  enum Ports_ComPacketQueue {
    EVENTS,
    TELEMETRY
  }
  enum Ports_ComBufferQueue {
    FILE_DOWNLINK
  }
{%- endif %}

  topology {{cookiecutter.deployment_name}} {
{%- if cookiecutter.use_core_subtopologies == "yes" %}

  # ----------------------------------------------------------------------
  # Subtopology imports
  # ----------------------------------------------------------------------
    import CdhCore.Subtopology
    import {{cookiecutter.communication_type}}.Subtopology
    import DataProducts.Subtopology
    import FileHandling.Subtopology
{%- if cookiecutter.enable_logging == "yes" %}
    import EventLoggerTee.Subtopology
    import TlmLoggerTee.Subtopology
{%- endif %}
{%- endif %}
    
  # ----------------------------------------------------------------------
  # Instances used in the topology
  # ----------------------------------------------------------------------
{%- if cookiecutter.use_core_subtopologies == "yes" %}

    instance chronoTime
    instance rateGroup1
    instance rateGroup2
    instance rateGroup3
    instance rateGroupDriver
    instance systemResources
    instance linuxTimer

{%- else %}
    instance $health
    instance tlmSend
    instance cmdDisp
    instance cmdSeq
    instance comDriver
    instance comQueue
    instance comStub
    instance fprimeRouter
    instance deframer
    instance frameAccumulator
    instance eventLogger
    instance fatalAdapter
    instance fatalHandler
    instance fileDownlink
    instance fileManager
    instance fileUplink
    instance bufferManager
    instance framer
    instance chronoTime
    instance prmDb
    instance rateGroup1
    instance rateGroup2
    instance rateGroup3
    instance rateGroupDriver
    instance textLogger
    instance systemResources
    instance version
    instance linuxTimer
{%- endif %}

  # ----------------------------------------------------------------------
  # Pattern graph specifiers
  # ----------------------------------------------------------------------
{%- if cookiecutter.use_core_subtopologies == "yes" %}

    command connections instance CdhCore.cmdDisp
    event connections instance CdhCore.events
    telemetry connections instance CdhCore.tlmSend
    text event connections instance CdhCore.textLogger
    health connections instance CdhCore.$health
    param connections instance FileHandling.prmDb
    time connections instance chronoTime

{%- else %}
    command connections instance cmdDisp
    event connections instance eventLogger
    param connections instance prmDb
    telemetry connections instance tlmSend
    text event connections instance textLogger
    time connections instance chronoTime
    health connections instance $health
{%- endif %}

  # ----------------------------------------------------------------------
  # Telemetry packets
  # ----------------------------------------------------------------------

    include "{{cookiecutter.deployment_name}}Packets.fppi"

  # ----------------------------------------------------------------------
  # Direct graph specifiers
  # ----------------------------------------------------------------------
{%- if cookiecutter.use_core_subtopologies == "yes" %}

    connections {{cookiecutter.communication_type}}_CdhCore {
{%- if cookiecutter.enable_logging == "yes" %}
      # Core events and telemetry to logging subtopologies, then to communication queue
      CdhCore.events.PktSend -> EventLoggerTee.comSplitter.comIn
      EventLoggerTee.comSplitter.comOut -> {{cookiecutter.communication_type}}.comQueue.comPacketQueueIn[{{cookiecutter.communication_type}}.Ports_ComPacketQueue.EVENTS]
      
      CdhCore.tlmSend.PktSend -> TlmLoggerTee.comSplitter.comIn
      TlmLoggerTee.comSplitter.comOut -> {{cookiecutter.communication_type}}.comQueue.comPacketQueueIn[{{cookiecutter.communication_type}}.Ports_ComPacketQueue.TELEMETRY]
{%- else %}
      # Core events and telemetry to communication queue
      CdhCore.events.PktSend -> {{cookiecutter.communication_type}}.comQueue.comPacketQueueIn[{{cookiecutter.communication_type}}.Ports_ComPacketQueue.EVENTS]
      CdhCore.tlmSend.PktSend -> {{cookiecutter.communication_type}}.comQueue.comPacketQueueIn[{{cookiecutter.communication_type}}.Ports_ComPacketQueue.TELEMETRY]
{%- endif %}

      # Router to Command Dispatcher
      {{cookiecutter.communication_type}}.fprimeRouter.commandOut -> CdhCore.cmdDisp.seqCmdBuff
      CdhCore.cmdDisp.seqCmdStatus -> {{cookiecutter.communication_type}}.fprimeRouter.cmdResponseIn
      
      # Command Sequencer
      {{cookiecutter.communication_type}}.cmdSeq.comCmdOut -> CdhCore.cmdDisp.seqCmdBuff
      CdhCore.cmdDisp.seqCmdStatus -> {{cookiecutter.communication_type}}.cmdSeq.cmdResponseIn
    }

    connections {{cookiecutter.communication_type}}_FileHandling {
      # File Downlink to Communication Queue
      FileHandling.fileDownlink.bufferSendOut -> {{cookiecutter.communication_type}}.comQueue.bufferQueueIn[FileHandling.Ports_ComBufferQueue.FILE_DOWNLINK]
      {{cookiecutter.communication_type}}.comQueue.bufferReturnOut[FileHandling.Ports_ComBufferQueue.FILE_DOWNLINK] -> FileHandling.fileDownlink.bufferReturn

      # Router to File Uplink
      {{cookiecutter.communication_type}}.fprimeRouter.fileOut -> FileHandling.fileUplink.bufferSendIn
      FileHandling.fileUplink.bufferSendOut -> {{cookiecutter.communication_type}}.fprimeRouter.fileBufferReturnIn
    }

    connections FileHandling_DataProducts {
      # Data Products to File Downlink
      DataProducts.dpCat.fileOut -> FileHandling.fileDownlink.SendFile
      FileHandling.fileDownlink.FileComplete -> DataProducts.dpCat.fileDone
    }

{%- else %}
    # Legacy connections
    connections Downlink {
      # Inputs to ComQueue (events, telemetry, file)
      eventLogger.PktSend         -> comQueue.comPacketQueueIn[Ports_ComPacketQueue.EVENTS]
      tlmSend.PktSend             -> comQueue.comPacketQueueIn[Ports_ComPacketQueue.TELEMETRY]
      fileDownlink.bufferSendOut  -> comQueue.bufferQueueIn[Ports_ComBufferQueue.FILE_DOWNLINK]
      comQueue.bufferReturnOut[Ports_ComBufferQueue.FILE_DOWNLINK] -> fileDownlink.bufferReturn

      # ComQueue <-> Framer
      comQueue.dataOut   -> framer.dataIn
      framer.dataReturnOut -> comQueue.dataReturnIn
      framer.comStatusOut  -> comQueue.comStatusIn

      # Buffer Management for Framer
      framer.bufferAllocate   -> bufferManager.bufferGetCallee
      framer.bufferDeallocate -> bufferManager.bufferSendIn

      # Framer <-> ComStub
      framer.dataOut        -> comStub.dataIn
      comStub.dataReturnOut -> framer.dataReturnIn
      comStub.comStatusOut  -> framer.comStatusIn

      # ComStub <-> ComDriver
      comStub.drvSendOut      -> comDriver.$send
      comDriver.sendReturnOut -> comStub.drvSendReturnIn
      comDriver.ready         -> comStub.drvConnected
    }

    connections FaultProtection {
      eventLogger.FatalAnnounce -> fatalHandler.FatalReceive
    }

    connections Sequencer {
      cmdSeq.comCmdOut -> cmdDisp.seqCmdBuff
      cmdDisp.seqCmdStatus -> cmdSeq.cmdResponseIn
    }

    connections Uplink {
      # ComDriver buffer allocations
      comDriver.allocate      -> bufferManager.bufferGetCallee
      comDriver.deallocate    -> bufferManager.bufferSendIn
      # ComDriver <-> ComStub
      comDriver.$recv             -> comStub.drvReceiveIn
      comStub.drvReceiveReturnOut -> comDriver.recvReturnIn
      # ComStub <-> FrameAccumulator
      comStub.dataOut                -> frameAccumulator.dataIn
      frameAccumulator.dataReturnOut -> comStub.dataReturnIn
      # FrameAccumulator buffer allocations
      frameAccumulator.bufferDeallocate -> bufferManager.bufferSendIn
      frameAccumulator.bufferAllocate   -> bufferManager.bufferGetCallee
      # FrameAccumulator <-> Deframer
      frameAccumulator.dataOut  -> deframer.dataIn
      deframer.dataReturnOut    -> frameAccumulator.dataReturnIn
      # Deframer <-> Router
      deframer.dataOut           -> fprimeRouter.dataIn
      fprimeRouter.dataReturnOut -> deframer.dataReturnIn
      # Router buffer allocations
      fprimeRouter.bufferAllocate   -> bufferManager.bufferGetCallee
      fprimeRouter.bufferDeallocate -> bufferManager.bufferSendIn
      # Router <-> CmdDispatcher/FileUplink
      fprimeRouter.commandOut  -> cmdDisp.seqCmdBuff
      cmdDisp.seqCmdStatus     -> fprimeRouter.cmdResponseIn
      fprimeRouter.fileOut     -> fileUplink.bufferSendIn
      fileUplink.bufferSendOut -> fprimeRouter.fileBufferReturnIn
    }
{%- endif %}

    connections RateGroups {
      # LinuxTimer to drive rate group
      linuxTimer.CycleOut -> rateGroupDriver.CycleIn

      # Rate group 1
      rateGroupDriver.CycleOut[Ports_RateGroups.rateGroup1] -> rateGroup1.CycleIn
{%- if cookiecutter.use_core_subtopologies == "yes" %}
      rateGroup1.RateGroupMemberOut[0] -> CdhCore.tlmSend.Run
      rateGroup1.RateGroupMemberOut[1] -> FileHandling.fileDownlink.Run
      rateGroup1.RateGroupMemberOut[2] -> systemResources.run
      rateGroup1.RateGroupMemberOut[3] -> {{cookiecutter.communication_type}}.comQueue.run
{%- else %}
      rateGroup1.RateGroupMemberOut[0] -> tlmSend.Run
      rateGroup1.RateGroupMemberOut[1] -> fileDownlink.Run
      rateGroup1.RateGroupMemberOut[2] -> systemResources.run
      rateGroup1.RateGroupMemberOut[3] -> comQueue.run
{%- endif %}

      # Rate group 2
      rateGroupDriver.CycleOut[Ports_RateGroups.rateGroup2] -> rateGroup2.CycleIn
{%- if cookiecutter.use_core_subtopologies == "yes" %}
      rateGroup2.RateGroupMemberOut[0] -> {{cookiecutter.communication_type}}.cmdSeq.schedIn
{%- else %}
      rateGroup2.RateGroupMemberOut[0] -> cmdSeq.schedIn
{%- endif %}

      # Rate group 3
      rateGroupDriver.CycleOut[Ports_RateGroups.rateGroup3] -> rateGroup3.CycleIn
{%- if cookiecutter.use_core_subtopologies == "yes" %}
      rateGroup3.RateGroupMemberOut[0] -> CdhCore.$health.Run
{%- if cookiecutter.communication_type == "ComCcsds" %}
      rateGroup3.RateGroupMemberOut[1] -> {{cookiecutter.communication_type}}.commsBufferManager.schedIn
      rateGroup3.RateGroupMemberOut[2] -> DataProducts.dpBufferManager.schedIn
      rateGroup3.RateGroupMemberOut[3] -> DataProducts.dpWriter.schedIn
      rateGroup3.RateGroupMemberOut[4] -> DataProducts.dpMgr.schedIn
{%- else %}
      rateGroup3.RateGroupMemberOut[1] -> DataProducts.dpBufferManager.schedIn
      rateGroup3.RateGroupMemberOut[2] -> DataProducts.dpWriter.schedIn
      rateGroup3.RateGroupMemberOut[3] -> DataProducts.dpMgr.schedIn
{%- endif %}
{%- else %}
      rateGroup3.RateGroupMemberOut[0] -> $health.Run
      rateGroup3.RateGroupMemberOut[1] -> bufferManager.schedIn
{%- endif %}
    }

    connections {{cookiecutter.deployment_name}} {
      # Add connections here to user-defined components
    }

  }

}
