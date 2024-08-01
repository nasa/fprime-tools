# {{cookiecutter.subtopology_name}} - F' Subtopology

The starter files for the subtopology have been generated. To fully integrate it into your project, you need to do the following steps:

1. Add the `{{cookiecutter.subtopology_name}}/` folder to its parent directory's `.cmake (or CMakeLists)` file if not already there:

```cmake
add_fprime_subdirectory("${CMAKE_CURRENT_LIST_DIR}/{{cookiecutter.subtopology_name}}/")
```

2. Create a directory in the root of your project called `SubtopologyConfigs`. This will include the config files for your subtopologies. Move `{{cookiecutter.subtopology_name}}Config.fpp` into `SubtopologyConfigs`. Create a CMakeLists.txt file in the folder, and include the config file as a source file:

```cmake
# in SubtopologyConfigs/CMakeLists.txt

set(SOURCE_FILES
    ...
  "${CMAKE_CURRENT_LIST_DIR}/{{cookiecutter.subtopology_name}}Config.fpp"
    ...
)

register_fprime_module()
```

3. Lastly, add `add_fprime_subdirectory("${CMAKE_CURRENT_LIST_DIR}/SubtopologyConfigs/")` to your `project.cmake` folder.

In the future, you only need to add the config file to your source list. The directory setup should be a one-time event.