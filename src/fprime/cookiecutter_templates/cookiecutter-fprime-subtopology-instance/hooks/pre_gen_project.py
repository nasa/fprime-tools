from pathlib import Path
from fprime.util.cookiecutter_wrapper import is_valid_name

"""
Pre-generation hook that validates inputs before creating the subtopology instance:
1. Validates subtopology instance name format and constraints
2. Validates the template path exists and is accessible
3. Validates that all required files are present in the template
"""

name = "{{ cookiecutter.subtopology_instance_name }}"
subtopology_template_path = "{{ cookiecutter.subtopology_template_path }}"

if is_valid_name(name) != "valid":
    raise ValueError(
        f"Unacceptable subtopology instance name: {name}. Do not use spaces or special characters"
    )

if not subtopology_template_path:
    raise ValueError("Subtopology template path cannot be empty")

# Handle both absolute and relative paths
current_dir = Path.cwd()
template_path = Path(subtopology_template_path)
if not template_path.is_absolute():
    # Need to go up one level since we're already in the target directory
    parent_dir = current_dir.parent
    template_path = (parent_dir / template_path).resolve()
else:
    template_path = template_path.resolve()

if not template_path.exists():
    raise ValueError(f"Subtopology template path does not exist: {template_path}")

if not template_path.is_dir():
    raise ValueError(f"Subtopology template path is not a directory: {template_path}")

required_files = ["subtopology-template.fppi", "PingEntries.hpp"]

for required_file in required_files:
    file_path = template_path / required_file
    if not file_path.exists():
        raise ValueError(
            f"Required file '{required_file}' not found in subtopology template path: {template_path}"
        )

print(f"[INFO] Subtopology template path validated: {template_path}")
print(f"[INFO] Found required files: {', '.join(required_files)}")
