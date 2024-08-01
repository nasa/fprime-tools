module {{cookiecutter.subtopology_name}}Config {
    # Base ID for your subtopology. All instantiated components will be offsets of this
    constant {{cookiecutter.subtopology_name}}_BASE_ID = << FILL THIS IN >>
    
    # include default Queue and Stack sizes here
    module Defaults {
        constant QUEUE_SIZE = 10
        constant STACK_SIZE = 64 * 1024
    }

    # Priorities for active components should be included in a module like so:
    # module Priorities {
    #     const instanceName = 100
    #     ...
    # }

    # Custom ports in your subtopology can be defined like so:
    # port customPort (
    #     ...
    # )

    # Any other constants can go here as well that configure your subtopology
}