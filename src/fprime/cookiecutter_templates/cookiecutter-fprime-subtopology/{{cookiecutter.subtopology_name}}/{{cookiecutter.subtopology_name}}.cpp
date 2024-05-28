#include <{{cookiecutter.subtopology_name}}/{{cookiecutter.subtopology_name}}.hpp>
// TODO: include the necessary header files for the subtopology
// this may need to be modified with the correct path depending on the parent folder of your subtopology
#include <{{cookiecutter.subtopology_name}}/{{cookiecutter.subtopology_name}}TopologyAc.hpp>

namespace {{cookiecutter.subtopology_name}}
{
    void configureTopology(const TopologyState &state) {
        // TODO: Add configuration code here
    }

    void startTopology(const TopologyState &state) {
        // TODO: Add start code here
    }

    void teardownTopology(const TopologyState &state) {
        // TODO: Add teardown code here
    }
}

// GNJ7BBP73WE9