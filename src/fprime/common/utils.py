""" fprime.common.utils: defines common utility functions to be used across sub packages

@author thomas-bc
"""

from pathlib import Path


def confirm(msg):
    """Ask user for a yes or no input after displaying the given message"""
    # Loop "forever" intended
    while True:
        confirm_input = input(msg)
        if confirm_input.lower() in ["y", "yes"]:
            return True
        if confirm_input.lower() in ["n", "no"]:
            return False
        print(f"{confirm_input} is invalid.  Please use 'yes' or 'no'")


def replace_contents(filename, what, replacement, count=1):
    """Replace the first instance of what with replacement in filename"""
    changelog = Path(filename).read_text()
    with open(filename, "w") as fh:
        new_file = changelog.replace(what, replacement, count)
        fh.write(new_file)
        return new_file != changelog
