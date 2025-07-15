// ======================================================================
// \title  {{cookiecutter.deployment_name}}Topology.cpp
// \brief cpp file containing the topology instantiation code
//
// ======================================================================
// Provides access to autocoded functions
#include <{{cookiecutter.__include_path_prefix}}{{cookiecutter.deployment_name}}/Top/{{cookiecutter.deployment_name}}TopologyAc.hpp>
// Note: Uncomment when using Svc:TlmPacketizer
//#include <{{cookiecutter.__include_path_prefix}}{{cookiecutter.deployment_name}}/Top/{{cookiecutter.deployment_name}}PacketsAc.hpp>

// Necessary project-specified types
#include <Os/Console.hpp>
{%- if cookiecutter.use_core_subtopologies == "no" %}
#include <Fw/Types/MallocAllocator.hpp>
#include <Svc/FrameAccumulator/FrameDetector/FprimeFrameDetector.hpp>
#include <{{cookiecutter.__include_path_prefix}}{{cookiecutter.deployment_name}}/Top/Ports_ComPacketQueueEnumAc.hpp>
{%- endif %}

// Used for 1Hz synthetic cycling
#include <Os/Mutex.hpp>

// Allows easy reference to objects in FPP/autocoder required namespaces
using namespace {{cookiecutter.deployment_name}};

// Instantiate a system logger that will handle Fw::Logger::log calls
Os::Console logger;


{%- if cookiecutter.use_core_subtopologies == "no" %}
// FprimeFrameDetector is used to configure the FrameAccumulator to detect F Prime frames
Svc::FrameDetectors::FprimeFrameDetector frameDetector;
// Malloc-based allocator for components that need to allocate memory during the initialization phase.
Fw::MallocAllocator mallocator;
Svc::ComQueue::QueueConfigurationTable configurationTable;
{%- endif %}

// The reference topology divides the incoming clock signal (1Hz) into sub-signals: 1Hz, 1/2Hz, and 1/4Hz with 0 offset
{{"Svc::RateGroupDriver::DividerSet rateGroupDivisorsSet{{{1, 0}, {2, 0}, {4, 0}}};"}}

// Rate groups may supply a context token to each of the attached children whose purpose is set by the project. The
// reference topology sets each token to zero as these contexts are unused in this project.
U32 rateGroup1Context[Svc::ActiveRateGroup::CONNECTION_COUNT_MAX] = {};
U32 rateGroup2Context[Svc::ActiveRateGroup::CONNECTION_COUNT_MAX] = {};
U32 rateGroup3Context[Svc::ActiveRateGroup::CONNECTION_COUNT_MAX] = {};

{%- if cookiecutter.use_core_subtopologies == "no" %}
// A number of constants are needed for construction of the topology. These are specified here.
enum TopologyConstants {
    CMD_SEQ_BUFFER_SIZE = 5 * 1024,
    FILE_DOWNLINK_TIMEOUT = 1000,
    FILE_DOWNLINK_COOLDOWN = 1000,
    FILE_DOWNLINK_CYCLE_TIME = 1000,
    FILE_DOWNLINK_FILE_QUEUE_DEPTH = 10,
    HEALTH_WATCHDOG_CODE = 0x123,
    COMM_PRIORITY = 100,
    // bufferManager constants
    FRAMER_BUFFER_SIZE = FW_MAX(FW_COM_BUFFER_MAX_SIZE, FW_FILE_BUFFER_MAX_SIZE) + Svc::FprimeProtocol::FrameHeader::SERIALIZED_SIZE + Svc::FprimeProtocol::FrameTrailer::SERIALIZED_SIZE,
    FRAMER_BUFFER_COUNT = 30,
    DEFRAMER_BUFFER_SIZE = FW_MAX(FW_COM_BUFFER_MAX_SIZE, FW_FILE_BUFFER_MAX_SIZE),
    DEFRAMER_BUFFER_COUNT = 30,
    COM_DRIVER_BUFFER_SIZE = 3000,
    COM_DRIVER_BUFFER_COUNT = 30,
    BUFFER_MANAGER_ID = 200
};

// Ping entries are autocoded, however; this code is not properly exported. Thus, it is copied here.
Svc::Health::PingEntry pingEntries[] = {
    {PingEntries::{{cookiecutter.deployment_name}}_tlmSend::WARN, PingEntries::{{cookiecutter.deployment_name}}_tlmSend::FATAL, "chanTlm"},
    {PingEntries::{{cookiecutter.deployment_name}}_cmdDisp::WARN, PingEntries::{{cookiecutter.deployment_name}}_cmdDisp::FATAL, "cmdDisp"},
    {PingEntries::{{cookiecutter.deployment_name}}_cmdSeq::WARN, PingEntries::{{cookiecutter.deployment_name}}_cmdSeq::FATAL, "cmdSeq"},
    {PingEntries::{{cookiecutter.deployment_name}}_eventLogger::WARN, PingEntries::{{cookiecutter.deployment_name}}_eventLogger::FATAL, "eventLogger"},
    {PingEntries::{{cookiecutter.deployment_name}}_fileDownlink::WARN, PingEntries::{{cookiecutter.deployment_name}}_fileDownlink::FATAL, "fileDownlink"},
    {PingEntries::{{cookiecutter.deployment_name}}_fileManager::WARN, PingEntries::{{cookiecutter.deployment_name}}_fileManager::FATAL, "fileManager"},
    {PingEntries::{{cookiecutter.deployment_name}}_fileUplink::WARN, PingEntries::{{cookiecutter.deployment_name}}_fileUplink::FATAL, "fileUplink"},
    {PingEntries::{{cookiecutter.deployment_name}}_prmDb::WARN, PingEntries::{{cookiecutter.deployment_name}}_prmDb::FATAL, "prmDb"},
    {PingEntries::{{cookiecutter.deployment_name}}_rateGroup1::WARN, PingEntries::{{cookiecutter.deployment_name}}_rateGroup1::FATAL, "rateGroup1"},
    {PingEntries::{{cookiecutter.deployment_name}}_rateGroup2::WARN, PingEntries::{{cookiecutter.deployment_name}}_rateGroup2::FATAL, "rateGroup2"},
    {PingEntries::{{cookiecutter.deployment_name}}_rateGroup3::WARN, PingEntries::{{cookiecutter.deployment_name}}_rateGroup3::FATAL, "rateGroup3"},
};
{%- endif %}

/**
 * \brief configure/setup components in project-specific way
 *
 * This is a *helper* function which configures/sets up each component requiring project specific input. This includes
 * allocating resources, passing-in arguments, etc. This function may be inlined into the topology setup function if
 * desired, but is extracted here for clarity.
 */
void configureTopology(const TopologyState& state) {
    // Rate group driver needs a divisor list
    rateGroupDriver.configure(rateGroupDivisorsSet);

    // Rate groups require context arrays.
    rateGroup1.configure(rateGroup1Context, FW_NUM_ARRAY_ELEMENTS(rateGroup1Context));
    rateGroup2.configure(rateGroup2Context, FW_NUM_ARRAY_ELEMENTS(rateGroup2Context));
    rateGroup3.configure(rateGroup3Context, FW_NUM_ARRAY_ELEMENTS(rateGroup3Context));

{%- if cookiecutter.use_core_subtopologies == "no" %}
    // Buffer managers need a configured set of buckets and an allocator used to allocate memory for those buckets.
    Svc::BufferManager::BufferBins bufferMgrBins;
    memset(&bufferMgrBins, 0, sizeof(bufferMgrBins));
    bufferMgrBins.bins[0].bufferSize = FRAMER_BUFFER_SIZE;
    bufferMgrBins.bins[0].numBuffers = FRAMER_BUFFER_COUNT;
    bufferMgrBins.bins[1].bufferSize = DEFRAMER_BUFFER_SIZE;
    bufferMgrBins.bins[1].numBuffers = DEFRAMER_BUFFER_COUNT;
    bufferMgrBins.bins[2].bufferSize = COM_DRIVER_BUFFER_SIZE;
    bufferMgrBins.bins[2].numBuffers = COM_DRIVER_BUFFER_COUNT;
    bufferManager.setup(200, 0, mallocator, bufferMgrBins);

    // Frame accumulator needs to be passed a frame detector (default F Prime frame detector)
    frameAccumulator.configure(frameDetector, 1, mallocator, 2048);

    // Command sequencer needs to allocate memory to hold contents of command sequences
    cmdSeq.allocateBuffer(0, mallocator, CMD_SEQ_BUFFER_SIZE);

    // File downlink requires some project-derived properties.
    fileDownlink.configure(FILE_DOWNLINK_TIMEOUT, FILE_DOWNLINK_COOLDOWN, FILE_DOWNLINK_CYCLE_TIME,
                           FILE_DOWNLINK_FILE_QUEUE_DEPTH);

    // Parameter database is configured with a database file name, and that file must be initially read.
    prmDb.configure("PrmDb.dat");
    prmDb.readParamFile();

    // Health is supplied a set of ping entires.
    health.setPingEntries(pingEntries, FW_NUM_ARRAY_ELEMENTS(pingEntries), HEALTH_WATCHDOG_CODE);

    // ComQueue configuration
    // Events (highest-priority)
    configurationTable.entries[Ports_ComPacketQueue::EVENTS].depth = 100;
    configurationTable.entries[Ports_ComPacketQueue::EVENTS].priority = 0;
    // Telemetry
    configurationTable.entries[Ports_ComPacketQueue::TELEMETRY].depth = 500;
    configurationTable.entries[Ports_ComPacketQueue::TELEMETRY].priority = 2;
    // File Downlink (first entry after the ComPacket queues = NUM_CONSTANTS)
    configurationTable.entries[Ports_ComPacketQueue::NUM_CONSTANTS].depth = 100;
    configurationTable.entries[Ports_ComPacketQueue::NUM_CONSTANTS].priority = 1;
    // Allocation identifier is 0 as the MallocAllocator discards it
    comQueue.configure(configurationTable, 0, mallocator);
{%- if (cookiecutter.com_driver_type in ["TcpServer", "TcpClient"]) %}
    if (state.hostname != nullptr && state.port != 0) {
        comDriver.configure(state.hostname, state.port);
    }
{%- endif %}

    // Note: Uncomment when using Svc:TlmPacketizer
    // tlmSend.setPacketList({{cookiecutter.deployment_name}}PacketsPkts, {{cookiecutter.deployment_name}}PacketsIgnore, 1);
{%- endif %}
}

// Public functions for use in main program are namespaced with deployment name {{cookiecutter.deployment_name}}
namespace {{cookiecutter.deployment_name}} {
void setupTopology(const TopologyState& state) {
    // Autocoded initialization. Function provided by autocoder.
    initComponents(state);
    // Autocoded id setup. Function provided by autocoder.
    setBaseIds();
    // Autocoded connection wiring. Function provided by autocoder.
    connectComponents();
    // Autocoded command registration. Function provided by autocoder.
    regCommands();
    // Autocoded configuration. Function provided by autocoder.
    configComponents(state);
    // Project-specific component configuration. Function provided above. May be inlined, if desired.
    configureTopology(state);
    // Autocoded parameter loading. Function provided by autocoder.
    loadParameters();
    // Autocoded task kick-off (active components). Function provided by autocoder.
    startTasks(state);
{%- if cookiecutter.use_core_subtopologies == "no" %}
{%- if (cookiecutter.com_driver_type in ["TcpServer", "TcpClient"]) %}
    // Initialize socket communication if and only if there is a valid specification
    if (state.hostname != nullptr && state.port != 0) {
        Os::TaskString name("ReceiveTask");
        // Uplink is configured for receive so a socket task is started
        comDriver.start(name, 100, Default::STACK_SIZE);
    }
{%- elif cookiecutter.com_driver_type == "UART" %}
    if (state.uartDevice != nullptr) {
        Os::TaskString name("ReceiveTask");
        // Uplink is configured for receive so a socket task is started
        if (comDriver.open(state.uartDevice, static_cast<Drv::LinuxUartDriver::UartBaudRate>(state.baudRate), 
                           Drv::LinuxUartDriver::NO_FLOW, Drv::LinuxUartDriver::PARITY_NONE, 2048)) {
            comDriver.start(100, Default::STACK_SIZE);
        } else {
            printf("Failed to open UART device %s at baud rate %" PRIu32 "\n", state.uartDevice, state.baudRate);
        }
    }
{%- endif %}
{%- endif %}
}

void startRateGroups(Fw::TimeInterval interval) {
    // This timer drives the fundamental tick rate of the system.
    // Svc::RateGroupDriver will divide this down to the slower rate groups.
    // This call will block until the stopRateGroups() call is made.
    // For this Linux demo, that call is made from a signal handler.
    linuxTimer.startTimer(interval.getSeconds()*1000+interval.getUSeconds()/1000);
}

void stopRateGroups() {
    linuxTimer.quit();
}

void teardownTopology(const TopologyState& state) {
    // Autocoded (active component) task clean-up. Functions provided by topology autocoder.
    stopTasks(state);
    freeThreads(state);
    tearDownComponents(state);
{%- if cookiecutter.use_core_subtopologies == "no" %}
    // Other task clean-up.
{%- if cookiecutter.com_driver_type == "UART" %}
    comDriver.quitReadThread();
    (void)comDriver.join();
{%- else %}
    comDriver.stop();
    (void)comDriver.join();
{%- endif %}
    // Resource deallocation
    cmdSeq.deallocateBuffer(mallocator);
    bufferManager.cleanup();
{%- endif %}
}
};  // namespace {{cookiecutter.deployment_name}}
