"""
This script is run as a cookiecutter hook after the project is generated.

It does the following:
- Initializes a git repository
- Adds F' as a submodule
- Checks out the requested branch/tag
- Installs the virtual environment if requested

@author thomas-bc
"""
import subprocess
import sys

PRINT_VENV_WARNING = False

# Add F' as a submodule
subprocess.run(["git", "init"])
print("[INFO] Checking out F' submodule at branch/tag: {{cookiecutter.fprime_branch_or_tag}}")
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
res = subprocess.run(
    ["git", "fetch", "origin", "--depth", "1", "{{cookiecutter.fprime_branch_or_tag}}"],
    cwd="./fprime",
    capture_output=True,
)
# Checkout requested branch/tag
res = subprocess.run(
    ["git", "checkout", "-B", "{{cookiecutter.fprime_branch_or_tag}}", "FETCH_HEAD"],
    cwd="./fprime",
    capture_output=True,
)

if res.returncode != 0:
    print(
        "[ERROR] Unable to checkout branch/tag: {{cookiecutter.fprime_branch_or_tag}}. Exiting..."
    )
    sys.exit(1) # sys.exit(1) indicates failure to cookiecutter

# Install venv if requested
if "{{cookiecutter.install_venv}}" == "yes":
    if sys.prefix != sys.base_prefix:
        subprocess.run(
            [
                sys.prefix + "/bin/pip",
                "install",
                "-Ur",
                "fprime/requirements.txt",
            ]
        )
    else:
        # Print warning after the following message so users do not miss it
        PRINT_VENV_WARNING = True

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
        "Install with `pip install -Ur fprime/requirements.txt`"
    )
