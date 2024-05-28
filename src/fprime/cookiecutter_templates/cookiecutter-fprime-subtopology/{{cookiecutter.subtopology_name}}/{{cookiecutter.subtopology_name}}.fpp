module {{cookiecutter.subtopology_name}} {
    module Defaults {
        constant QUEUE_SIZE = 10
        constant STACK_SIZE = 64 * 1024
    }

    # include any instance definitions here. For example:
    # instance framer: Svc.Framer base id 0x4100

    topology {{cookiecutter.subtopology_name}} {

        # include any instance declarations here
        # and wiring connections as well. For example:

        # instance framer
        # connections Framer {
        #     ...    
        # }

    } # end topology
} # end {{cookiecutter.subtopology_name}}