from fprime.fbuild.interaction import is_valid_name

#Check to ensure Component Name is valid

if(is_valid_name("{{ cookiecutter.component_name }}") != "valid"):
        raise ValueError("Unacceptable component name. Do not use spaces or special characters")