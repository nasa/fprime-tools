module {{cookiecutter.component_namespace}} {
    @ {{cookiecutter.component_short_description}}
    {{cookiecutter.component_kind}} component {{cookiecutter.component_name}} {
{% if cookiecutter.component_kind == "active" %}
        # One async command/port is required for active components
        # This should be overridden by the developers with a useful command/port
        @ TODO
{%- if cookiecutter.enable_commands == "yes" %}
        async command TODO opcode 0
{% else %}
        async input port TODO: Svc.Sched
{% endif -%}
{% endif -%}
{% if cookiecutter.component_kind == "queued" %}
        # One sync and one async command/port are required for queued components
        # This should be overridden by the developers with useful commands/ports
{%- if cookiecutter.enable_commands == "yes" %}
        @ TODO
        async command TODO_1 opcode 0

        @ TODO
        sync command TODO_2
{% else %}
        async input port TODO_1: Svc.Sched
        sync input port TODO_2: Svc.Sched
{% endif -%}
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
{% if cookiecutter.enable_commands == "yes" %}
        @ Port for sending command registrations
        command reg port cmdRegOut

        @ Port for receiving commands
        command recv port cmdIn

        @ Port for sending command responses
        command resp port cmdResponseOut
{% endif -%}
{% if cookiecutter.enable_events == "yes" %}
        @ Port for sending textual representation of events
        text event port logTextOut

        @ Port for sending events to downlink
        event port logOut
{% endif -%}
{% if cookiecutter.enable_telemetry == "yes" %}
        @ Port for sending telemetry channels to downlink
        telemetry port tlmOut
{% endif -%}
{% if cookiecutter.enable_parameters == "yes" %}
        @ Port to return the value of a parameter
        param get port prmGetOut

        @Port to set the value of a parameter
        param set port prmSetOut
{% endif %}
    }
}