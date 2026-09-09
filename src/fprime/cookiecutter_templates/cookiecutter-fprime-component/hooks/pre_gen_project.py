from fprime.util.cookiecutter_wrapper import is_valid_name

# Check if the component name is valid
if is_valid_name("{{ cookiecutter.component_name }}") != "valid":
    raise ValueError(
        "Unacceptable component name. Use only letters, digits, and underscores, and do not start with a digit"
    )
