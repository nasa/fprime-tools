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

    # ----------------------------------------------------------------------
    # Pattern graph specifiers
    # ----------------------------------------------------------------------

    command connections instance cmdDisp

    event connections instance eventLogger

    param connections instance prmDb

    telemetry connections instance tlmSend

    text event connections instance textLogger

    time connections instance chronoTime

    health connections instance $health

    # ----------------------------------------------------------------------
    # Direct graph specifiers
    # ----------------------------------------------------------------------

    connections Downlink {
      # Inputs to ComQueue (events, telemetry, file)
      eventLogger.PktSend         -> comQueue.comPacketQueueIn[0]
      tlmSend.PktSend             -> comQueue.comPacketQueueIn[1]
      fileDownlink.bufferSendOut  -> comQueue.bufferQueueIn[0]
      comQueue.bufferReturnOut[0] -> fileDownlink.bufferReturn

      # ComQueue <-> Framer
      comQueue.queueSend   -> framer.dataIn
      framer.dataReturnOut -> comQueue.bufferReturnIn
      framer.comStatusOut  -> comQueue.comStatusIn

      # Buffer Management for Framer
      framer.bufferAllocate   -> bufferManager.bufferGetCallee
      framer.bufferDeallocate -> bufferManager.bufferSendIn

      # Framer <-> ComStub
      framer.dataOut        -> comStub.comDataIn
      comStub.dataReturnOut -> framer.dataReturnIn
      comStub.comStatusOut  -> framer.comStatusIn

      # ComStub <-> ComDriver
      comStub.drvDataOut      -> comDriver.$send
      comDriver.dataReturnOut -> comStub.dataReturnIn
      comDriver.ready         -> comStub.drvConnected
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
      rateGroup1.RateGroupMemberOut[3] -> comQueue.run

      # Rate group 2
      rateGroupDriver.CycleOut[Ports_RateGroups.rateGroup2] -> rateGroup2.CycleIn
      rateGroup2.RateGroupMemberOut[0] -> cmdSeq.schedIn

      # Rate group 3
      rateGroupDriver.CycleOut[Ports_RateGroups.rateGroup3] -> rateGroup3.CycleIn
      rateGroup3.RateGroupMemberOut[0] -> $health.Run
      rateGroup3.RateGroupMemberOut[1] -> blockDrv.Sched
      rateGroup3.RateGroupMemberOut[2] -> bufferManager.schedIn
    }

    connections Sequencer {
      cmdSeq.comCmdOut -> cmdDisp.seqCmdBuff
      cmdDisp.seqCmdStatus -> cmdSeq.cmdResponseIn
    }

    connections Uplink {

      comDriver.allocate -> bufferManager.bufferGetCallee
      comDriver.$recv -> comStub.drvDataIn
      comStub.comDataOut -> frameAccumulator.dataIn

      frameAccumulator.bufferDeallocate -> bufferManager.bufferSendIn
      frameAccumulator.bufferAllocate -> bufferManager.bufferGetCallee
      frameAccumulator.frameOut -> deframer.framedIn
      deframer.deframedOut -> fprimeRouter.dataIn
      deframer.bufferDeallocate -> bufferManager.bufferSendIn

      fprimeRouter.commandOut -> cmdDisp.seqCmdBuff
      fprimeRouter.fileOut -> fileUplink.bufferSendIn
      fprimeRouter.bufferDeallocate -> bufferManager.bufferSendIn

      cmdDisp.seqCmdStatus -> fprimeRouter.cmdResponseIn
      fileUplink.bufferSendOut -> bufferManager.bufferSendIn
    }

    connections {{cookiecutter.deployment_name}} {
      # Add here connections to user-defined components
    }

  }

}
