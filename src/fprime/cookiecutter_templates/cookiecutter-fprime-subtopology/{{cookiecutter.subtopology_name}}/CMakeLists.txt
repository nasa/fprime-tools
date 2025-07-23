add_fprime_subdirectory("${CMAKE_CURRENT_LIST_DIR}/{{cookiecutter.subtopology_name}}Config/")

register_fprime_module(
    AUTOCODER_INPUTS
        "${CMAKE_CURRENT_LIST_DIR}/{{cookiecutter.subtopology_name}}.fpp"
    HEADERS
        "${CMAKE_CURRENT_LIST_DIR}/PingEntries.hpp"
    DEPENDS
        {{cookiecutter.subtopology_name}}Config
    INTERFACE
)