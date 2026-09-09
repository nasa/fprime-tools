from fprime.util.cookiecutter_wrapper import is_valid_name

name = "{{ cookiecutter.subtopology_name }}"

if is_valid_name(name) != "valid":
    raise ValueError(
        f"Unacceptable subtopology name: {name}. Use only letters, digits, and underscores, and do not start with a digit"
    )
