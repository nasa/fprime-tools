#ifndef {{cookiecutter.__subtopology_name_upper}}_DEFS_HPP
#define {{cookiecutter.__subtopology_name_upper}}_DEFS_HPP

namespace {{cookiecutter.subtopology_name}} {
    struct {{cookiecutter.subtopology_name}}State {
        /* include any variables that are needed for 
        configuring/starting/tearing down the topology */
    };
    struct TopologyState {
        {{cookiecutter.subtopology_name}}State {{cookiecutter.subtopology_name}}_state;
    };
}

namespace GlobalDefs {
    namespace PingEntries {
        /* include any ping entries that are needed for the subtopology
        e.g., rate groups need FAIL and WARN ping enums
        For example:

        namespace {{cookiecutter.subtopology_name}}_rateGroup {
            enum {
                WARN = 3,
                FATAL = 5
            };
        }
        */
    }
}

#endif