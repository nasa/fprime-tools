{%- if cookiecutter.use_core_subtopologies == "no" %}
telemetry packets {{cookiecutter.deployment_name}}Packets {

  packet CDH id 1 group 1 {
    {{cookiecutter.deployment_name}}.cmdDisp.CommandsDispatched
    {{cookiecutter.deployment_name}}.rateGroup1.RgMaxTime
    {{cookiecutter.deployment_name}}.rateGroup2.RgMaxTime
    {{cookiecutter.deployment_name}}.rateGroup3.RgMaxTime
    {{cookiecutter.deployment_name}}.cmdSeq.CS_LoadCommands
    {{cookiecutter.deployment_name}}.cmdSeq.CS_CancelCommands
    {{cookiecutter.deployment_name}}.cmdSeq.CS_CommandsExecuted
    {{cookiecutter.deployment_name}}.cmdSeq.CS_SequencesCompleted
    {{cookiecutter.deployment_name}}.fileUplink.FilesReceived
    {{cookiecutter.deployment_name}}.fileUplink.PacketsReceived
    {{cookiecutter.deployment_name}}.bufferManager.TotalBuffs
    {{cookiecutter.deployment_name}}.bufferManager.CurrBuffs
    {{cookiecutter.deployment_name}}.bufferManager.HiBuffs
    {{cookiecutter.deployment_name}}.fileDownlink.FilesSent
    {{cookiecutter.deployment_name}}.fileDownlink.PacketsSent
    {{cookiecutter.deployment_name}}.fileManager.CommandsExecuted
    {{cookiecutter.deployment_name}}.comQueue.comQueueDepth
    {{cookiecutter.deployment_name}}.comQueue.buffQueueDepth
    # Note: Uncomment when using Svc:TlmPacketizer
    # {{cookiecutter.deployment_name}}.tlmSend.SendLevel
  }

  packet CDHErrors id 2 group 1 {
    {{cookiecutter.deployment_name}}.rateGroup1.RgCycleSlips
    {{cookiecutter.deployment_name}}.rateGroup2.RgCycleSlips
    {{cookiecutter.deployment_name}}.rateGroup3.RgCycleSlips
    {{cookiecutter.deployment_name}}.cmdSeq.CS_Errors
    {{cookiecutter.deployment_name}}.fileUplink.Warnings
    {{cookiecutter.deployment_name}}.fileDownlink.Warnings
    {{cookiecutter.deployment_name}}.$health.PingLateWarnings
    {{cookiecutter.deployment_name}}.fileManager.Errors
    {{cookiecutter.deployment_name}}.bufferManager.NoBuffs
    {{cookiecutter.deployment_name}}.bufferManager.EmptyBuffs
    {{cookiecutter.deployment_name}}.fileManager.Errors
  }

  packet SystemRes1 id 4 group 2 {
    {{cookiecutter.deployment_name}}.systemResources.MEMORY_TOTAL
    {{cookiecutter.deployment_name}}.systemResources.MEMORY_USED
    {{cookiecutter.deployment_name}}.systemResources.NON_VOLATILE_TOTAL
    {{cookiecutter.deployment_name}}.systemResources.NON_VOLATILE_FREE
  }

  packet SystemRes3 id 5 group 2 {
    {{cookiecutter.deployment_name}}.systemResources.CPU
    {{cookiecutter.deployment_name}}.systemResources.CPU_00
    {{cookiecutter.deployment_name}}.systemResources.CPU_01
    {{cookiecutter.deployment_name}}.systemResources.CPU_02
    {{cookiecutter.deployment_name}}.systemResources.CPU_03
    {{cookiecutter.deployment_name}}.systemResources.CPU_04
    {{cookiecutter.deployment_name}}.systemResources.CPU_05
    {{cookiecutter.deployment_name}}.systemResources.CPU_06
    {{cookiecutter.deployment_name}}.systemResources.CPU_07
    {{cookiecutter.deployment_name}}.systemResources.CPU_08
    {{cookiecutter.deployment_name}}.systemResources.CPU_09
    {{cookiecutter.deployment_name}}.systemResources.CPU_10
    {{cookiecutter.deployment_name}}.systemResources.CPU_11
    {{cookiecutter.deployment_name}}.systemResources.CPU_12
    {{cookiecutter.deployment_name}}.systemResources.CPU_13
    {{cookiecutter.deployment_name}}.systemResources.CPU_14
    {{cookiecutter.deployment_name}}.systemResources.CPU_15
  }

  packet Version1 id 6 group 2 {
    {{cookiecutter.deployment_name}}.version.FrameworkVersion
    {{cookiecutter.deployment_name}}.version.ProjectVersion
  }

  packet Version_Library1 id 7 group 2 {
    {{cookiecutter.deployment_name}}.version.LibraryVersion01
    {{cookiecutter.deployment_name}}.version.LibraryVersion02
  }

  packet Version_Library2 id 8 group 2 {
    {{cookiecutter.deployment_name}}.version.LibraryVersion03
    {{cookiecutter.deployment_name}}.version.LibraryVersion04
  }

  packet Version_Library3 id 9 group 2 {
    {{cookiecutter.deployment_name}}.version.LibraryVersion05
    {{cookiecutter.deployment_name}}.version.LibraryVersion06
  }

  packet Version_Library4 id 10 group 2 {
    {{cookiecutter.deployment_name}}.version.LibraryVersion07
    {{cookiecutter.deployment_name}}.version.LibraryVersion08
  }

  packet Version_Library5 id 11 group 2 {
    {{cookiecutter.deployment_name}}.version.LibraryVersion09
    {{cookiecutter.deployment_name}}.version.LibraryVersion10
  }

  packet Version_Custom1 id 12 group 2 {
    {{cookiecutter.deployment_name}}.version.CustomVersion01
  }

  packet Version_Custom2 id 13 group 2 {
    {{cookiecutter.deployment_name}}.version.CustomVersion02
  }

  packet Version_Custom3 id 14 group 2 {
    {{cookiecutter.deployment_name}}.version.CustomVersion03
  }

  packet Version_Custom4 id 15 group 2 {
    {{cookiecutter.deployment_name}}.version.CustomVersion04
  }

  packet Version_Custom5 id 16 group 2 {
    {{cookiecutter.deployment_name}}.version.CustomVersion05
  }

  packet Version_Custom6 id 17 group 2 {
    {{cookiecutter.deployment_name}}.version.CustomVersion06
  }

  packet Version_Custom7 id 18 group 2 {
    {{cookiecutter.deployment_name}}.version.CustomVersion07
  }

  packet Version_Custom8 id 19 group 2 {
    {{cookiecutter.deployment_name}}.version.CustomVersion08
  }

  packet Version_Custom9 id 20 group 2 {
    {{cookiecutter.deployment_name}}.version.CustomVersion09
  }

  packet Version_Custom10 id 21 group 2 {
    {{cookiecutter.deployment_name}}.version.CustomVersion10
  }

} omit {
  {{cookiecutter.deployment_name}}.cmdDisp.CommandErrors
{%- if cookiecutter.com_driver_type == "UART" %}
  {{cookiecutter.deployment_name}}.comDriver.BytesRecv
  {{cookiecutter.deployment_name}}.comDriver.BytesSent
{%- endif %}
}

{%- else %}

telemetry packets {{cookiecutter.deployment_name}}Packets {

  packet CDH id 1 group 1 {
    CdhCore.cmdDisp.CommandsDispatched

    FileHandling.fileUplink.FilesReceived
    FileHandling.fileUplink.PacketsReceived
    FileHandling.fileDownlink.FilesSent
    FileHandling.fileDownlink.PacketsSent
    FileHandling.fileManager.CommandsExecuted

    {{cookiecutter.communication_type}}.cmdSeq.CS_LoadCommands
    {{cookiecutter.communication_type}}.cmdSeq.CS_CancelCommands
    {{cookiecutter.communication_type}}.cmdSeq.CS_CommandsExecuted
    {{cookiecutter.communication_type}}.cmdSeq.CS_SequencesCompleted
    {{cookiecutter.communication_type}}.comQueue.comQueueDepth
    {{cookiecutter.communication_type}}.comQueue.buffQueueDepth
    {{cookiecutter.communication_type}}.commsBufferManager.TotalBuffs
    {{cookiecutter.communication_type}}.commsBufferManager.CurrBuffs
    {{cookiecutter.communication_type}}.commsBufferManager.HiBuffs
    #{{cookiecutter.communication_type}}.tlmSend.SendLevel

    {{cookiecutter.deployment_name}}.rateGroup1.RgMaxTime
    {{cookiecutter.deployment_name}}.rateGroup2.RgMaxTime
    {{cookiecutter.deployment_name}}.rateGroup3.RgMaxTime
  }

  packet CDHErrors id 2 group 1 {
    CdhCore.$health.PingLateWarnings

    FileHandling.fileUplink.Warnings
    FileHandling.fileDownlink.Warnings
    FileHandling.fileManager.Errors

    {{cookiecutter.communication_type}}.cmdSeq.CS_Errors
    {{cookiecutter.communication_type}}.commsBufferManager.NoBuffs
    {{cookiecutter.communication_type}}.commsBufferManager.EmptyBuffs

    {{cookiecutter.deployment_name}}.rateGroup1.RgCycleSlips
    {{cookiecutter.deployment_name}}.rateGroup2.RgCycleSlips
    {{cookiecutter.deployment_name}}.rateGroup3.RgCycleSlips
  }

  packet SystemRes1 id 5 group 2 {
    {{cookiecutter.deployment_name}}.systemResources.MEMORY_TOTAL
    {{cookiecutter.deployment_name}}.systemResources.MEMORY_USED
    {{cookiecutter.deployment_name}}.systemResources.NON_VOLATILE_TOTAL
    {{cookiecutter.deployment_name}}.systemResources.NON_VOLATILE_FREE
  }

  packet SystemRes3 id 6 group 2 {
    {{cookiecutter.deployment_name}}.systemResources.CPU
    {{cookiecutter.deployment_name}}.systemResources.CPU_00
    {{cookiecutter.deployment_name}}.systemResources.CPU_01
    {{cookiecutter.deployment_name}}.systemResources.CPU_02
    {{cookiecutter.deployment_name}}.systemResources.CPU_03
    {{cookiecutter.deployment_name}}.systemResources.CPU_04
    {{cookiecutter.deployment_name}}.systemResources.CPU_05
    {{cookiecutter.deployment_name}}.systemResources.CPU_06
    {{cookiecutter.deployment_name}}.systemResources.CPU_07
    {{cookiecutter.deployment_name}}.systemResources.CPU_08
    {{cookiecutter.deployment_name}}.systemResources.CPU_09
    {{cookiecutter.deployment_name}}.systemResources.CPU_10
    {{cookiecutter.deployment_name}}.systemResources.CPU_11
    {{cookiecutter.deployment_name}}.systemResources.CPU_12
    {{cookiecutter.deployment_name}}.systemResources.CPU_13
    {{cookiecutter.deployment_name}}.systemResources.CPU_14
    {{cookiecutter.deployment_name}}.systemResources.CPU_15
  }

  packet DataProducts id 21 group 3 {
    DataProducts.dpCat.CatalogDps
    DataProducts.dpCat.DpsSent

    DataProducts.dpMgr.NumSuccessfulAllocations
    DataProducts.dpMgr.NumFailedAllocations
    DataProducts.dpMgr.NumDataProducts
    DataProducts.dpMgr.NumBytes

    DataProducts.dpWriter.NumBuffersReceived
    DataProducts.dpWriter.NumBytesWritten
    DataProducts.dpWriter.NumSuccessfulWrites
    DataProducts.dpWriter.NumFailedWrites
    DataProducts.dpWriter.NumErrors

    DataProducts.dpBufferManager.TotalBuffs
    DataProducts.dpBufferManager.CurrBuffs
    DataProducts.dpBufferManager.HiBuffs
    DataProducts.dpBufferManager.NoBuffs
    DataProducts.dpBufferManager.EmptyBuffs
  }

  packet Version1 id 22 group 2 {
    CdhCore.version.FrameworkVersion
    CdhCore.version.ProjectVersion
  }

  packet Version_Library1 id 23 group 2 {
    CdhCore.version.LibraryVersion01
    CdhCore.version.LibraryVersion02
  }

  packet Version_Library2 id 24 group 2 {
    CdhCore.version.LibraryVersion03
    CdhCore.version.LibraryVersion04
  }

  packet Version_Library3 id 25 group 2 {
    CdhCore.version.LibraryVersion05
    CdhCore.version.LibraryVersion06
  }

  packet Version_Library4 id 26 group 2 {
    CdhCore.version.LibraryVersion07
    CdhCore.version.LibraryVersion08
  }

  packet Version_Library5 id 27 group 2 {
    CdhCore.version.LibraryVersion09
    CdhCore.version.LibraryVersion10
  }

  packet Version_Custom1 id 28 group 2 {
    CdhCore.version.CustomVersion01
  }

  packet Version_Custom2 id 29 group 2 {
    CdhCore.version.CustomVersion02
  }

  packet Version_Custom3 id 30 group 2 {
    CdhCore.version.CustomVersion03
  }

  packet Version_Custom4 id 31 group 2 {
    CdhCore.version.CustomVersion04
  }

  packet Version_Custom5 id 32 group 2 {
    CdhCore.version.CustomVersion05
  }

  packet Version_Custom6 id 33 group 2 {
    CdhCore.version.CustomVersion06
  }

  packet Version_Custom7 id 34 group 2 {
    CdhCore.version.CustomVersion07
  }

  packet Version_Custom8 id 35 group 2 {
    CdhCore.version.CustomVersion08
  }

  packet Version_Custom9 id 36 group 2 {
    CdhCore.version.CustomVersion09
  }

  packet Version_Custom10 id 37 group 2 {
    CdhCore.version.CustomVersion10
  }

} omit {
  CdhCore.cmdDisp.CommandErrors
}

{%- endif %}
