from fprime.fbuild.interaction import is_valid_name

# Check to ensure Component Name is valid

if is_valid_name("{{ cookiecutter.component_name }}") != "valid":
    raise ValueError(
        "Unacceptable component name. Do not use spaces or special characters"
    )
if (
    "{{cookiecutter.commands}}" != "yes"  # lgtm [py/comparison-of-constants]
    and "{{cookiecutter.events}}" != "yes"  # lgtm [py/comparison-of-constants]
    and "{{cookiecutter.telemetry}}" != "yes"  # lgtm [py/comparison-of-constants]
    and "{{cookiecutter.parameters}}" != "yes"  # lgtm [py/comparison-of-constants]
):
    raise ValueError(
        "[ERROR] You must select at least one of the following options to have in your component: commands, events, telemetry, parameters"
    )
