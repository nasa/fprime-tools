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

#endif