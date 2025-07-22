# {{cookiecutter.subtopology_name}} - F' Subtopology

The starter files for the subtopology have been generated. To fully integrate it into your project, you need to do the following steps:

## 1. Add to Parent CMakeLists.txt
Add the `{{cookiecutter.subtopology_name}}/` folder to its parent directory's `CMakeLists.txt` file if not already there:

```cmake
add_fprime_subdirectory("${CMAKE_CURRENT_LIST_DIR}/{{cookiecutter.subtopology_name}}/")
```

## 2. Complete Your Subtopology Implementation
Update the following files based on your subtopology's requirements:

### Required Files:
- **`{{cookiecutter.subtopology_name}}.fpp`**: Define your subtopology's instances and connections
- **`{{cookiecutter.subtopology_name}}Config/{{cookiecutter.subtopology_name}}Config.fpp`**: Configure constants, queue sizes, stack sizes, and priorities
- **`PingEntries.hpp`**: Define ping entries for health monitoring of components (if needed)

### Optional Files (add as needed):
- **`{{cookiecutter.subtopology_name}}Config/{{cookiecutter.subtopology_name}}SubtopologyConfig.cpp/.hpp`**: 
  - Add C++ configuration code (e.g., memory allocators, custom initialization)
  - Update `{{cookiecutter.subtopology_name}}Config/CMakeLists.txt` to include:
    ```cmake
    register_fprime_config(
        SOURCES
            "${CMAKE_CURRENT_LIST_DIR}/{{cookiecutter.subtopology_name}}SubtopologyConfig.cpp"
        HEADERS
            "${CMAKE_CURRENT_LIST_DIR}/{{cookiecutter.subtopology_name}}SubtopologyConfig.hpp"
        AUTOCODER_INPUTS
            "${CMAKE_CURRENT_LIST_DIR}/{{cookiecutter.subtopology_name}}Config.fpp"
    )
    ```

- **`{{cookiecutter.subtopology_name}}Config/Additional*.fpp`**: 
  - Add additional FPP configuration files (e.g., ComDriverConfig.fpp for communication subtopologies)
  - Include them in the `{{cookiecutter.subtopology_name}}Config/CMakeLists.txt` AUTOCODER_INPUTS

- **`{{cookiecutter.subtopology_name}}TopologyDefs.hpp`**: 
  - Add topology state structures or additional definitions if needed
  - This file is already created but may need customization

## 3. Implementation Examples
Look at existing core subtopologies for reference:
- **ComFprime & ComCcsds**: Memory allocator configuration with C++ files, Communication driver configuration with additional FPP file
- **CdhCore**: Core command and datahandling functionality, Fault Handler configuration with additional FPP file 
- **FileHandling**: Simple configuration with only FPP files
- **DataProducts**: Data product handling
- **ComLoggerTee**: Instance-based subtopology (special case)

## 4. Common Patterns
- **Queue/Stack/Priority Configuration**: Define in `{{cookiecutter.subtopology_name}}Config.fpp`
- **Memory Management**: Add SubtopologyConfig.cpp/.hpp for custom allocators
- **Topology Connections**: Define connections in the main `.fpp` file
- **Health Monitoring**: Update `PingEntries.hpp` with appropriate ping entries
- **Component Configuration**: Add additional FPP files in config `{{cookiecutter.subtopology_name}}Config` 