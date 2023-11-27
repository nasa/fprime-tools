"""
This script is run as a cookiecutter hook after the project is generated.

It does the following:
- Initializes a git repository
- Adds F' as a submodule
- Checks out the latest release of F'
- Installs the virtual environment if requested

@author thomas-bc
"""
import subprocess
import sys
import requests
from pathlib import Path

response = requests.get("https://api.github.com/repos/nasa/fprime/releases/latest")
latest_tag_name = response.json()["tag_name"]

PRINT_VENV_WARNING = False

# Add F' as a submodule
subprocess.run(["git", "init"])
print(f"[INFO] Checking out F' submodule at latest release: {latest_tag_name}")
subprocess.run(
    [
        "git",
        "submodule",
        "add",
        "--depth",
        "1",
        "https://github.com/nasa/fprime.git",
    ]
)
subprocess.run(
    ["git", "fetch", "origin", "--depth", "1", "tag", latest_tag_name],
    cwd="./fprime",
    capture_output=True,
)

# Checkout requested branch/tag
res = subprocess.run(
    ["git", "checkout", latest_tag_name],
    cwd="./fprime",
    capture_output=True,
)
if res.returncode != 0:
    print(f"[ERROR] Unable to checkout tag: {latest_tag_name}. Exit...")
    sys.exit(1)  # sys.exit(1) indicates failure to cookiecutter

# Checkout submodules (e.g. googletest)
res = subprocess.run(
    ["git", "submodule", "update", "--init", "--recursive"],
    capture_output=True,
)
if res.returncode != 0:
    print("[WARNING] Unable to initialize submodules. Functionality may be limited.")

# Install venv if requested
if "{{cookiecutter.__install_venv}}" == "yes":
    if sys.prefix != sys.base_prefix:
        subprocess.run(
            [
                Path(sys.prefix) / "bin" / "pip",
                "install",
                "-Ur",
                Path("fprime") / "requirements.txt",
            ]
        )
    else:
        # Print warning after the following message so users do not miss it
        PRINT_VENV_WARNING = True
else:
    print(
        "[INFO] requirements.txt has not been installed because you did not request it.",
        "Install with `pip install -Ur fprime/requirements.txt`",
    )

print(
    """
################################################################

Congratulations! You have successfully created a new F' project.

A git repository has been initialized and F' has been added as a
submodule, you can now create your first commit.

Get started with your F' project:

-- Generate a new component --
fprime-util new --component

-- Generate a new deployment --
fprime-util new --deployment

################################################################
"""
)

if PRINT_VENV_WARNING:
    print(
        "[WARNING] requirements.txt has not been installed because you are not running in a virtual environment.",
        "Install with `pip install -Ur fprime/requirements.txt`",
    )
