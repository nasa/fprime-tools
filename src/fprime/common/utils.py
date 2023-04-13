""" fprime.common.utils: defines common utility functions to be used across subpackages

@author thomas-bc
"""

def confirm(msg):
    """Asks user for a yes or no input after diplaying the given message"""
    # Loop "forever" intended
    while True:
        confirm_input = input(msg)
        if confirm_input.lower() in ["y", "yes"]:
            return True
        if confirm_input.lower() in ["n", "no"]:
            return False
        print(f"{confirm_input} is invalid.  Please use 'yes' or 'no'")
