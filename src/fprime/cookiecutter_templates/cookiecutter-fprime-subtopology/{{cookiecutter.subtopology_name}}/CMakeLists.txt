set(SOURCE_FILES
    "${CMAKE_CURRENT_LIST_DIR}/{{cookiecutter.subtopology_name}}.fpp"
    "${CMAKE_CURRENT_LIST_DIR}/intentionally-empty.cpp"
)

register_fprime_module()

set_target_properties(
    ${FPRIME_CURRENT_MODULE}
    PROPERTIES
    SOURCES "${CMAKE_CURRENT_LIST_DIR}/intentionally-empty.cpp"
)