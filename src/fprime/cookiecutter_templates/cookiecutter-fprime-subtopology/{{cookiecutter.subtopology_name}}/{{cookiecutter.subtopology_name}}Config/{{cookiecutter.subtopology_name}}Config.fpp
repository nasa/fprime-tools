module {{cookiecutter.subtopology_name}}Config {
    # Base ID for the {{cookiecutter.subtopology_name}} Subtopology, all components are offsets from this base ID
    constant BASE_ID = {{cookiecutter.base_id}}
    
    # Queue sizes for active components
    module QueueSizes {
        # Add your component queue sizes here. For example:
        # constant myComponent = 10
    }
    
    # Stack sizes for active components
    module StackSizes {
        # Add your component stack sizes here. For example:
        # constant myComponent = 64 * 1024
    }

    # Priorities for active components
    module Priorities {
        # Add your component priorities here. For example:
        # constant myComponent = 23
    }

    # Additional configuration modules can be added here as needed
    # For example:
    # module BufferSizes {
    #     constant myBuffer = 1024
    # }
}
