module {{cookiecutter.subtopology_name}} {
    # include any instance definitions here. For example:
    # instance framer: Svc.Framer base id {{cookiecutter.subtopology_name}}Config.{{cookiecutter.subtopology_name}}_BASE_ID + << OFFSET >>

    # note that subtopologies are written with phases, which means inline c++ within this fpp file.
    # here is an example:
    # instance myCoolComponent: Components.CoolComponent base id {{cookiecutter.subtopology_name}}Config.{{cookiecutter.subtopology_name}}_BASE_ID + << OFFSET >> \
    #   queue size {{cookiecutter.subtopology_name}}Config.QueueSizes.myCoolComponent \
    #   stack size {{cookiecutter.subtopology_name}}Config.StackSizes.myCoolComponent \
    #   priority {{cookiecutter.subtopology_name}}Config.Priorities.CoolComponent \
    #   {
    #       phase Fpp.ToCpp.Phases.configComponents """
    #       {
    #           # some configuration function calls as necessary
    #       }
    #       """
    #   }

    # ---------------------------------------------------------------------
    # Active Components
    # ----------------------------------------------------------------------
    
    # Add your active components here. For example:
    # instance myComponent: Svc.MyComponent base id {{cookiecutter.subtopology_name}}Config.BASE_ID + 0x0100 \
    #     queue size {{cookiecutter.subtopology_name}}Config.QueueSizes.myComponent \
    #     stack size {{cookiecutter.subtopology_name}}Config.StackSizes.myComponent \
    #     priority {{cookiecutter.subtopology_name}}Config.Priorities.myComponent

    # ----------------------------------------------------------------------
    # Queued Components
    # ----------------------------------------------------------------------
    
    # Add your queued components here. For example:
    # instance myQueuedComponent: Svc.MyQueuedComponent base id {{cookiecutter.subtopology_name}}Config.BASE_ID + 0x0200 \
    #     queue size {{cookiecutter.subtopology_name}}Config.QueueSizes.myQueuedComponent

    # ----------------------------------------------------------------------
    # Passive Components
    # ----------------------------------------------------------------------
    
    # Add your passive components here. For example:
    # instance myPassiveComponent: Svc.MyPassiveComponent base id {{cookiecutter.subtopology_name}}Config.BASE_ID + 0x0300        

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