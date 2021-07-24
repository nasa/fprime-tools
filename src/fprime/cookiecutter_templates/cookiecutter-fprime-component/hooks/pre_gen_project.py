from fprime.fbuild.interaction import is_valid_name

# Check to ensure Component Name is valid

if is_valid_name("{{ cookiecutter.component_name }}") != "valid":
    raise ValueError(
        "Unacceptable component name. Do not use spaces or special characters"
    )
if "{{ cookiecutter.component_kind }}" == "active" and "{{ cookiecutter.ports }}" == "no":
    raise ValueError(
        "Active components require an async_input port, select yes when asked to include ports"
    )