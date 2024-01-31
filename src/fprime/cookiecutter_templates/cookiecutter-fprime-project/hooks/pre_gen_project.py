from fprime.util.cookiecutter_wrapper import is_valid_name

name = "{{ cookiecutter.project_name }}"

if is_valid_name(name) != "valid":
    raise ValueError(
        f"Unacceptable project name: {name}. Do not use spaces or special characters"
    )
