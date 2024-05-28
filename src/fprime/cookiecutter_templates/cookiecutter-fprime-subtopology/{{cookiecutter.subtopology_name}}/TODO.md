# {{cookiecutter.subtopology_name}} - F' Subtopology

The starter files for the subtopology have been generated. To fully integrate it into your project, you need to do the following steps:

1. Add the `{{cookiecutter.subtopology_name}}/` folder to its parent directory's `CMakeLists` file:

```cmake
add_fprime_subdirectory("${CMAKE_CURRENT_LIST_DIR}/{{cookiecutter.subtopology_name}}/")
set(MOD_DEPS ${FPRIME_CURRENT_MODULE}/{{cookiecutter.subtopology_name}})
```

2. Add (and configure) `TopologyConfig.hpp` in `fprime/config`, or wherever your F' config folder resides. This file should include the following:

```cpp
#ifndef TOPOLOGYCONFIG_HPP
#define TOPOLOGYCONFIG_HPP

#include <<DeploymentName>/Top/<DeploymentName>TopologyAc.hpp> // name of deployment using subtopology
using namespace <DeploymentNamespace>; // namespace of deployment using subtopology

#endif
```