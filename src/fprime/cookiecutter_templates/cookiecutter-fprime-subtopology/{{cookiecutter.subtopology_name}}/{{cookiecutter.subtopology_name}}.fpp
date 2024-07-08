module {{cookiecutter.subtopology_name}} {
    # include any instance definitions here. For example:
    # instance framer: Svc.Framer base id {{cookiecutter.subtopology_name}}Config.{{cookiecutter.subtopology_name}}_BASE_ID + << OFFSET >>

    # note that subtopologies are written with phases, which means inline c++ within this fpp file.
    # here is an example:
    # instance myCoolComponent: Components.CoolComponent base id {{cookiecutter.subtopology_name}}Config.{{cookiecutter.subtopology_name}}_BASE_ID + << OFFSET >> \
    #   queue size {{cookiecutter.subtopology_name}}Config.Defaults.QUEUE_SIZE \
    #   stack size {{cookiecutter.subtopology_name}}Config.Defaults.STACK_SIZE \
    #   priority {{cookiecutter.subtopology_name}}Config.Priorities.CoolComponent \
    #   {
    #       phase Fpp.ToCpp.Phases.configComponents """
    #       {
    #           # some configuration function calls as necessary
    #       }
    #       """
    #   }

    @ {{cookiecutter.subtopology_desc}}
    topology {{cookiecutter.subtopology_name}} {

        # include any instance declarations here
        # and wiring connections as well. For example:

        # instance framer
        # connections Framer {
        #     ...    
        # }

    } # end topology
} # end {{cookiecutter.subtopology_name}}