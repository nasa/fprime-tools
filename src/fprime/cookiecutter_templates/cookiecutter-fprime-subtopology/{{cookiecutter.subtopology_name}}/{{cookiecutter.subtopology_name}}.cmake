list(APPEND MOD_DEPS
    Fw/Logger
    # Add other dependencies as necessary
)

list(APPEND SOURCE_FILES
    "${CMAKE_CURRENT_LIST_DIR}/{{cookiecutter.subtopology_name}}.cpp"
)