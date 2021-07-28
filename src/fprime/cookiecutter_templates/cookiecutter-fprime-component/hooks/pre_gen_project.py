from fprime.fbuild.interaction import is_valid_name

# Check to ensure Component Name is valid

if is_valid_name("{{ cookiecutter.component_name }}") != "valid":
    raise ValueError(
        "Unacceptable component name. Do not use spaces or special characters"
    )
if (
    "{{cookiecutter.commands}}"  # lgtm [py/comparison-of-constants]
    != "yes"  # lgtm [py/comparison-of-constants]  lgtm [py/constant-conditional-expression]
    and "{{cookiecutter.events}}"  # lgtm [py/comparison-of-constants]
    != "yes"  # lgtm [py/comparison-of-constants]  lgtm [py/constant-conditional-expression]
    and "{{cookiecutter.telemetry}}"  # lgtm [py/comparison-of-constants]
    != "yes"  # lgtm [py/comparison-of-constants]  lgtm [py/constant-conditional-expression]
    and "{{cookiecutter.parameters}}"  # lgtm [py/comparison-of-constants]
    != "yes"  # lgtm [py/comparison-of-constants]  lgtm [py/constant-conditional-expression]
):
    raise ValueError(
        "[ERROR] You must select at least one of the following options to have in your component: commands, events, telemetry, parameters"
    )
