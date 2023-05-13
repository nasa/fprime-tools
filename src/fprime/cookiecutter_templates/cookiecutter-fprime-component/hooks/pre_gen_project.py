from fprime.util.cookiecutter_wrapper import is_valid_name


# Check to ensure Component Name is valid
def verify_inputs(component_name, commands, events, telemetry, parameters):
    if is_valid_name(component_name) != "valid":
        raise ValueError(
            "Unacceptable component name. Do not use spaces or special characters"
        )
    if commands == "no" and events == "no" and telemetry == "no" and parameters == "no":
        raise ValueError(
            "[ERROR] You must select at least one of the following options to have in your component: commands, events, telemetry, parameters"
        )


verify_inputs(
    "{{ cookiecutter.component_name }}",
    "{{ cookiecutter.enable_commands }}",
    "{{ cookiecutter.enable_events }}",
    "{{ cookiecutter.enable_telemetry }}",
    "{{ cookiecutter.enable_parameters }}",
)
