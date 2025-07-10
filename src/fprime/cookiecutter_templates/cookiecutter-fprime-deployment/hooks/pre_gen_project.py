#!/usr/bin/env python3
"""
Pre-generation hook for F Prime deployment cookiecutter template.
Validates user input and ensures proper configuration.
"""

from fprime.util.cookiecutter_wrapper import is_valid_name

# Get cookiecutter variables
name = "{{ cookiecutter.deployment_name }}"
use_subtopologies = "{{ cookiecutter.use_core_subtopologies }}"
communication_type = "{{ cookiecutter.communication_type }}"
com_driver_type = "{{ cookiecutter.com_driver_type }}"

# Validate deployment name
if is_valid_name(name) != "valid":
    raise ValueError(
        f"Unacceptable deployment name: {name}. Do not use spaces or special characters"
    )

# Validate subtopologies choice
if use_subtopologies not in ["yes", "no"]:
    raise ValueError(f"Invalid choice for use_core_subtopologies: {use_subtopologies}")

# Validate communication type choice
if communication_type not in ["ComFprime", "ComCcsds"]:
    raise ValueError(f"Invalid communication type: {communication_type}")

# Validate communication driver type
if com_driver_type not in ["TcpClient", "TcpServer", "UART"]:
    raise ValueError(f"Invalid communication driver type: {com_driver_type}")

print(f"Generating F Prime deployment: {name}")
if use_subtopologies == "yes":
    print(f"  Using core subtopologies with {communication_type} communication")
else:
    print(f"  Using individual components (legacy mode) with {com_driver_type} driver")
