from fprime.util.cookiecutter_wrapper import is_valid_name

name = "{{ cookiecutter.module_name }}"

if is_valid_name(name) != "valid":
    raise ValueError(
        f"Unacceptable module name: {name}. Use only letters, digits, and underscores, and do not start with a digit"
    )
