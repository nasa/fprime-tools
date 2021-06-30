#Check to ensure Component Name is valid

invalid_characters = ["#", "%", "&", "{", "}", "/", "\\", "<", ">", "*", "?",
                        " ", "$", "!", "\'", "\"", ":", "@", "+", "`", "|", "="]

for char in invalid_characters:
    if (char in "{{ cookiecutter.component_name }}"):
        raise ValueError("Unacceptable component name. Do not use spaces or special characters")