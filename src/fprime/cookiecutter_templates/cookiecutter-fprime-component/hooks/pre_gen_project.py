from fprime.fbuild.interaction import is_valid_name
import textwrap

# Check to ensure Component Name is valid

if is_valid_name("{{ cookiecutter.component_name }}") != "valid":
    raise ValueError(
        "Unacceptable component name. Do not use spaces or special characters"
    )
if (
    "{{cookiecutter.commands}}" != "yes"
    and "{{cookiecutter.events}}" != "yes"
    and "{{cookiecutter.telemetry}}" != "yes"
    and "{{cookiecutter.parameters}}" != "yes"
):
    raise ValueError(
        "[ERROR] You must select at least one of the following options to have in your component: commands, events, telemetry, parameters"
    )
