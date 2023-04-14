module {{cookiecutter.component_namespace}} {
    @ {{cookiecutter.component_short_description}}
    {{cookiecutter.component_kind}} component {{cookiecutter.component_name}} {
{% if cookiecutter.component_kind in ["active", "queued"] %}
        @ Default command for {{cookiecutter.component_kind}} components - to be overriden developer
        async command CMD_DEFAULT_AQ opcode 0
{% endif -%}
{% if cookiecutter.component_kind == "queued" %}
        @ Default command for {{cookiecutter.component_kind}} components - to be overriden developer
        sync command CMD_DEFAULT_Q
{% endif %}
        ##############################################################################
        #### Uncomment the following examples to start customizing your component ####
        ##############################################################################

        # @ Example async command
        # async command COMMAND_NAME(param_name: U32)

        # @ Example telemetry counter
        # telemetry ExampleCounter: U64

        # @ Example event
        # event ExampleStateEvent(example_state: Fw.On) severity activity high id 0 format "State set to {}"

        # @ Example port: receiving calls from the rate group
        # sync input port run: Svc.Sched

        # @ Example parameter
        # param PARAMETER_NAME: U32

        ###############################################################################
        # Standard AC Ports: Required for Channels, Events, Commands, and Parameters  #
        ###############################################################################
        @ Port for requesting the current time
        time get port timeCaller
{% if cookiecutter.commands == "yes" %}
        @ Port for sending command registrations
        command reg port cmdRegOut

        @ Port for receiving commands
        command recv port cmdIn

        @ Port for sending command responses
        command resp port cmdResponseOut
{% endif -%}
{% if cookiecutter.events == "yes" %}
        @ Port for sending textual representation of events
        text event port logTextOut

        @ Port for sending events to downlink
        event port logOut
{% endif -%}
{% if cookiecutter.telemetry == "yes" %}
        @ Port for sending telemetry channels to downlink
        telemetry port tlmOut
{% endif -%}
{% if cookiecutter.parameters == "yes" %}
        @ Port to return the value of a parameter
        param get port prmGetOut

        @Port to set the value of a parameter
        param set port prmSetOut
{% endif %}
    }
}