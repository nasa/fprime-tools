from fprime.util.cookiecutter_wrapper import is_valid_name

name = "{{ cookiecutter.subtopology_name }}"

if is_valid_name(name) != "valid":
    raise ValueError(
        f"Unacceptable subtopology name: {name}. Do not use spaces or special characters"
    )
