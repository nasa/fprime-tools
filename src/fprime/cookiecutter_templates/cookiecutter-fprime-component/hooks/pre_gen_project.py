#Check to ensure Component Name is valid

invalid_characters = ["#", "%", "&", "{", "}", "/", "\\", "<", ">", "*", "?",
                        " ", "$", "!", "\'", "\"", ":", "@", "+", "`", "|", "="]

for char in invalid_characters:
    assert(char not in "{{ cookiecutter.component_name }}")
