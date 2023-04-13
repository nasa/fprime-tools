module {{cookiecutter.component_namespace}} {
    @ {{cookiecutter.component_short_description}}
    {{cookiecutter.component_kind}} component {{cookiecutter.component_name}} {


# add commented-out examples


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
{% endif %}
{% if cookiecutter.events == "yes" %}
        @ Port for sending textual representation of events
        text event port logTextOut

        @ Port for sending events to downlink
        event port logOut
{% endif %}
{% if cookiecutter.telemetry == "yes" %}
        @ Port for sending telemetry channels to downlink
        telemetry port tlmOut
{% endif %}
{% if cookiecutter.parameters == "yes" %}
        @ Port to return the value of a parameter
        param get port prmGetOut

        @Port to set the value of a parameter
        param set port prmSetOut
{% endif %}
    }
}