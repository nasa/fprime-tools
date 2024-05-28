#ifndef {{cookiecutter.__subtopology_name_upper}}_HPP
#define {{cookiecutter.__subtopology_name_upper}}_HPP

#include "{{cookiecutter.subtopology_name}}TopologyDefs.hpp"
// TODO: Read TODO.md for setting up the TopologyConfig.hpp file
#include <TopologyConfig.hpp>


namespace {{cookiecutter.subtopology_name}} {
    void configureTopology(const TopologyState& state);
    void startTopology(const TopologyState& state);
    void teardownTopology(const TopologyState& state);
}

#endif