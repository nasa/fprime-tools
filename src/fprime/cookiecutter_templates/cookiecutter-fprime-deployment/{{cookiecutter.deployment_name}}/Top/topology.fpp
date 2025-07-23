module {{cookiecutter.deployment_name}} {

  # ----------------------------------------------------------------------
  # Symbolic constants for port numbers
  # ----------------------------------------------------------------------

  enum Ports_RateGroups {
    rateGroup1
    rateGroup2
    rateGroup3
  }

  topology {{cookiecutter.deployment_name}} {

  # ----------------------------------------------------------------------
  # Subtopology imports
  # ----------------------------------------------------------------------
    import CdhCore.Subtopology
    import {{cookiecutter.communication_type}}.Subtopology
    import DataProducts.Subtopology
    import FileHandling.Subtopology
    
  # ----------------------------------------------------------------------
  # Instances used in the topology
  # ----------------------------------------------------------------------
    instance chronoTime
    instance rateGroup1
    instance rateGroup2
    instance rateGroup3
    instance rateGroupDriver
    instance systemResources
    instance linuxTimer

  # ----------------------------------------------------------------------
  # Pattern graph specifiers
  # ----------------------------------------------------------------------

    command connections instance CdhCore.cmdDisp
    event connections instance CdhCore.events
    telemetry connections instance CdhCore.tlmSend
    text event connections instance CdhCore.textLogger
    health connections instance CdhCore.$health
    param connections instance FileHandling.prmDb
    time connections instance chronoTime

  # ----------------------------------------------------------------------
  # Telemetry packets (only used when TlmPacketizer is used)
  # ----------------------------------------------------------------------

    include "{{cookiecutter.deployment_name}}Packets.fppi"

  # ----------------------------------------------------------------------
  # Direct graph specifiers
  # ----------------------------------------------------------------------

    connections {{cookiecutter.communication_type}}_CdhCore {
      # Core events and telemetry to communication queue
      CdhCore.events.PktSend -> {{cookiecutter.communication_type}}.comQueue.comPacketQueueIn[{{cookiecutter.communication_type}}.Ports_ComPacketQueue.EVENTS]
      CdhCore.tlmSend.PktSend -> {{cookiecutter.communication_type}}.comQueue.comPacketQueueIn[{{cookiecutter.communication_type}}.Ports_ComPacketQueue.TELEMETRY]

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

    connections RateGroups {
      # LinuxTimer to drive rate group
      linuxTimer.CycleOut -> rateGroupDriver.CycleIn

      # Rate group 1
      rateGroupDriver.CycleOut[Ports_RateGroups.rateGroup1] -> rateGroup1.CycleIn
      rateGroup1.RateGroupMemberOut[0] -> CdhCore.tlmSend.Run
      rateGroup1.RateGroupMemberOut[1] -> FileHandling.fileDownlink.Run
      rateGroup1.RateGroupMemberOut[2] -> systemResources.run
      rateGroup1.RateGroupMemberOut[3] -> {{cookiecutter.communication_type}}.comQueue.run

      # Rate group 2
      rateGroupDriver.CycleOut[Ports_RateGroups.rateGroup2] -> rateGroup2.CycleIn
      rateGroup2.RateGroupMemberOut[0] -> {{cookiecutter.communication_type}}.cmdSeq.schedIn

      # Rate group 3
      rateGroupDriver.CycleOut[Ports_RateGroups.rateGroup3] -> rateGroup3.CycleIn
      rateGroup3.RateGroupMemberOut[0] -> CdhCore.$health.Run
      rateGroup3.RateGroupMemberOut[1] -> {{cookiecutter.communication_type}}.commsBufferManager.schedIn
      rateGroup3.RateGroupMemberOut[2] -> DataProducts.dpBufferManager.schedIn
      rateGroup3.RateGroupMemberOut[3] -> DataProducts.dpWriter.schedIn
      rateGroup3.RateGroupMemberOut[4] -> DataProducts.dpMgr.schedIn
    }

    connections {{cookiecutter.deployment_name}} {
      # Add connections here to user-defined components
    }

  }

}
