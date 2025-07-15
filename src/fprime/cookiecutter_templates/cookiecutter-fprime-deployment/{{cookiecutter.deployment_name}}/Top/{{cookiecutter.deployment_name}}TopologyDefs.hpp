// ======================================================================
// \title  {{cookiecutter.deployment_name}}TopologyDefs.hpp
// \brief required header file containing the required definitions for the topology autocoder
//
// ======================================================================
#ifndef {{cookiecutter.__deployment_name_upper}}_{{cookiecutter.__deployment_name_upper}}TOPOLOGYDEFS_HPP
#define {{cookiecutter.__deployment_name_upper}}_{{cookiecutter.__deployment_name_upper}}TOPOLOGYDEFS_HPP

{%- if cookiecutter.use_core_subtopologies == "no" %}
#include "Fw/Types/MallocAllocator.hpp"
{%- else %}
//Subtopology PingEntries includes
#include "Svc/Subtopologies/CdhCore/PingEntries.hpp"
#include "Svc/Subtopologies/{{cookiecutter.communication_type}}/PingEntries.hpp"
#include "Svc/Subtopologies/DataProducts/PingEntries.hpp"
#include "Svc/Subtopologies/FileHandling/PingEntries.hpp"

//SubtopologyTopologyDefs includes
#include "Svc/Subtopologies/{{cookiecutter.communication_type}}/SubtopologyTopologyDefs.hpp"
#include "Svc/Subtopologies/DataProducts/SubtopologyTopologyDefs.hpp"
#include "Svc/Subtopologies/FileHandling/SubtopologyTopologyDefs.hpp"
{%- endif %}
#include "{{cookiecutter.__include_path_prefix}}{{cookiecutter.deployment_name}}/Top/FppConstantsAc.hpp"

/**
 * \brief required ping constants
 *
 * The topology autocoder requires a WARN and FATAL constant definition for each component that supports the health-ping
 * interface. These are expressed as enum constants placed in a namespace named for the component instance. These
 * are all placed in the PingEntries namespace.
 *
 * Each constant specifies how many missed pings are allowed before a WARNING_HI/FATAL event is triggered. In the
 * following example, the health component will emit a WARNING_HI event if the component instance cmdDisp does not
 * respond for 3 pings and will FATAL if responses are not received after a total of 5 pings.
 *
 * ```c++
 * namespace PingEntries {
 * namespace cmdDisp {
 *     enum { WARN = 3, FATAL = 5 };
 * }
 * }
 * ```
 */
namespace PingEntries {
{%- if cookiecutter.use_core_subtopologies == "no" %}
    namespace {{cookiecutter.deployment_name}}_tlmSend {enum { WARN = 3, FATAL = 5 };}
    namespace {{cookiecutter.deployment_name}}_cmdDisp {enum { WARN = 3, FATAL = 5 };}
    namespace {{cookiecutter.deployment_name}}_cmdSeq {enum { WARN = 3, FATAL = 5 };}
    namespace {{cookiecutter.deployment_name}}_eventLogger {enum { WARN = 3, FATAL = 5 };}
    namespace {{cookiecutter.deployment_name}}_fileDownlink {enum { WARN = 3, FATAL = 5 };}
    namespace {{cookiecutter.deployment_name}}_fileManager {enum { WARN = 3, FATAL = 5 };}
    namespace {{cookiecutter.deployment_name}}_fileUplink {enum { WARN = 3, FATAL = 5 };}
    namespace {{cookiecutter.deployment_name}}_prmDb {enum { WARN = 3, FATAL = 5 };}
{%- endif %}
    namespace {{cookiecutter.deployment_name}}_rateGroup1 {enum { WARN = 3, FATAL = 5 };}
    namespace {{cookiecutter.deployment_name}}_rateGroup2 {enum { WARN = 3, FATAL = 5 };}
    namespace {{cookiecutter.deployment_name}}_rateGroup3 {enum { WARN = 3, FATAL = 5 };}
}  // namespace PingEntries

// Definitions are placed within a namespace named after the deployment
namespace {{cookiecutter.deployment_name}} {

{%- if cookiecutter.use_core_subtopologies == "no" %}
/**
 * \brief required type definition to carry state
 *
 * The topology autocoder requires an object that carries state with the name `{{cookiecutter.deployment_name}}::TopologyState`. Only the type
 * definition is required by the autocoder and the contents of this object are otherwise opaque to the autocoder. The contents are entirely up
 * to the definition of the project. Here, they are derived from command line inputs.
 */
struct TopologyState {
    {%- if cookiecutter.com_driver_type == "UART" %}
    const CHAR* uartDevice;  //!< UART device path
    U32 baudRate;            //!< UART baud rate
    {%- else %}
    const CHAR* hostname;    //!< Hostname or IP address for socket communication
    U16 port;                //!< Port number for socket communication
    {%- endif %}
};
{%- else %}
/**
 * \brief required type definition to carry state
 *
 * The topology autocoder requires an object that carries state with the name `{{cookiecutter.deployment_name}}::TopologyState`. Only the type
 * definition is required by the autocoder and the contents of this object are otherwise opaque to the autocoder. The
 * contents are entirely up to the definition of the project. This deployment uses subtopologies, so the state contains
 * the subtopology state structures which are derived from command line inputs.
 */
struct TopologyState {
    {%- if cookiecutter.communication_type == "ComFprime" %}
    {{cookiecutter.communication_type}}::SubtopologyState comFprime;  //!< Subtopology state for {{cookiecutter.communication_type}} 
    {%- else %}
    {{cookiecutter.communication_type}}::SubtopologyState comCcsds;  //!< Subtopology state for {{cookiecutter.communication_type}} 
    {%- endif %}
};

namespace PingEntries = ::PingEntries;
{%- endif %}
}  // namespace {{cookiecutter.deployment_name}}
#endif
