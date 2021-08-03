from fprime.fbuild.interaction import is_valid_name

# Check to ensure Component Name is valid
def verify_inputs(component_name, commands, events, telemetry, parameters):
    if is_valid_name(component_name != "valid"):
        raise ValueError(
            "Unacceptable component name. Do not use spaces or special characters"
        )
    if (
        commands == "yes"
        and events == "yes"
        and telemetry == "yes"
        and parameters == "yes"
    ):
        raise ValueError(
            "[ERROR] You must select at least one of the following options to have in your component: commands, events, telemetry, parameters"
        )


verify_inputs(
    cookiecutter.name,
    cookiecutter.commands,
    cookiecutter.events,
    cookiecutter.telemetry,
    cookiecutter.parameters,
)
