from fprime.util.cookiecutter_wrapper import is_valid_name

name = "{{ cookiecutter.deployment_name }}"

if is_valid_name(name) != "valid":
    raise ValueError(
        f"Unacceptable deployment name: {name}. Do not use spaces or special characters"
    )
