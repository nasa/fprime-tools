module {{cookiecutter.deployment_name}} {

  # ----------------------------------------------------------------------
  # Symbolic constants for port numbers
  # ----------------------------------------------------------------------

    enum Ports_RateGroups {
      rateGroup1
      rateGroup2
      rateGroup3
    }

    enum Ports_StaticMemory {
      downlink
      uplink
    }

  topology {{cookiecutter.deployment_name}} {

    # ----------------------------------------------------------------------
    # Instances used in the topology
    # ----------------------------------------------------------------------

    instance $health
    instance blockDrv
    instance tlmSend
    instance cmdDisp
    instance cmdSeq
    instance comDriver
    instance comQueue
    instance comStub
    instance downlink
    instance eventLogger
    instance fatalAdapter
    instance fatalHandler
    instance fileDownlink
    instance fileManager
    instance fileUplink
    instance fileUplinkBufferManager
    instance linuxTime
    instance prmDb
    instance rateGroup1
    instance rateGroup2
    instance rateGroup3
    instance rateGroupDriver
    instance staticMemory
    instance textLogger
    instance uplink
    instance systemResources

    # ----------------------------------------------------------------------
    # Pattern graph specifiers
    # ----------------------------------------------------------------------

    command connections instance cmdDisp

    event connections instance eventLogger

    param connections instance prmDb

    telemetry connections instance tlmSend

    text event connections instance textLogger

    time connections instance linuxTime

    health connections instance $health

    # ----------------------------------------------------------------------
    # Direct graph specifiers
    # ----------------------------------------------------------------------

    connections Downlink {

      tlmSend.PktSend -> comQueue.comQueueIn[0]
      eventLogger.PktSend -> comQueue.comQueueIn[1]
      fileDownlink.bufferSendOut -> comQueue.buffQueueIn[0]

      # should these staticMemory be comBufferManager instead?
      downlink.framedAllocate -> staticMemory.bufferAllocate[Ports_StaticMemory.downlink]
      downlink.framedOut -> comStub.comDataIn
      downlink.bufferDeallocate -> fileDownlink.bufferReturn

      comDriver.deallocate -> staticMemory.bufferDeallocate[Ports_StaticMemory.downlink]

      comQueue.comQueueSend -> downlink.comIn
      comQueue.buffQueueSend -> downlink.bufferIn

      comStub.comStatus -> comQueue.comStatusIn

      # ComStub <--> ComDriver connections
      comStub.drvDataOut -> comDriver.send
      comDriver.ready -> comStub.drvConnected
      
    }

    connections FaultProtection {
      eventLogger.FatalAnnounce -> fatalHandler.FatalReceive
    }

    connections RateGroups {
      # Block driver
      blockDrv.CycleOut -> rateGroupDriver.CycleIn

      # Rate group 1
      rateGroupDriver.CycleOut[Ports_RateGroups.rateGroup1] -> rateGroup1.CycleIn
      rateGroup1.RateGroupMemberOut[0] -> tlmSend.Run
      rateGroup1.RateGroupMemberOut[1] -> fileDownlink.Run
      rateGroup1.RateGroupMemberOut[2] -> systemResources.run

      # Rate group 2
      rateGroupDriver.CycleOut[Ports_RateGroups.rateGroup2] -> rateGroup2.CycleIn
      rateGroup2.RateGroupMemberOut[0] -> cmdSeq.schedIn

      # Rate group 3
      rateGroupDriver.CycleOut[Ports_RateGroups.rateGroup3] -> rateGroup3.CycleIn
      rateGroup3.RateGroupMemberOut[0] -> $health.Run
      rateGroup3.RateGroupMemberOut[1] -> blockDrv.Sched
      rateGroup3.RateGroupMemberOut[2] -> fileUplinkBufferManager.schedIn
    }

    connections Sequencer {
      cmdSeq.comCmdOut -> cmdDisp.seqCmdBuff
      cmdDisp.seqCmdStatus -> cmdSeq.cmdResponseIn
    }

    connections Uplink {

      comDriver.allocate -> staticMemory.bufferAllocate[Ports_StaticMemory.uplink]
      comDriver.$recv -> comStub.drvDataIn

      # I don't understand what this port connection does
      comStub.comDataOut -> uplink.framedIn

      uplink.framedDeallocate -> staticMemory.bufferDeallocate[Ports_StaticMemory.uplink]

      uplink.comOut -> cmdDisp.seqCmdBuff
      cmdDisp.seqCmdStatus -> uplink.cmdResponseIn

      uplink.bufferAllocate -> fileUplinkBufferManager.bufferGetCallee
      uplink.bufferOut -> fileUplink.bufferSendIn
      uplink.bufferDeallocate -> fileUplinkBufferManager.bufferSendIn
      fileUplink.bufferSendOut -> fileUplinkBufferManager.bufferSendIn
    }

    connections {{cookiecutter.deployment_name}} {
      # Add here connections to user-defined components
    }

  }

}
