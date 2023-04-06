"""
This script is run as a cookiecutter hook after the project is generated.
"""

import subprocess

DEFAULT_BRANCH = "devel"

# Add F' as a submodule
subprocess.run(["git", "init"])
subprocess.run(["git", "submodule", "add", "-b", DEFAULT_BRANCH, "https://github.com/nasa/fprime.git"])

# Checkout requested branch/tag
available_tags = subprocess.run(["git", "tag", "-l"], cwd="./fprime", capture_output=True).stdout.decode("utf-8").split()
if ("{{cookiecutter.fprime_branch_or_tag}}" in available_tags):
    res = subprocess.run(["git", "checkout", "tags/{{cookiecutter.fprime_branch_or_tag}}"], cwd="./fprime", capture_output=True)
    print("[INFO] F' submodule checked out to tag: {{cookiecutter.fprime_branch_or_tag}}")
else:
    res = subprocess.run(["git", "checkout", "{{cookiecutter.fprime_branch_or_tag}}"], cwd="./fprime", capture_output=True)
    print("[INFO] F' submodule checked out to branch: {{cookiecutter.fprime_branch_or_tag}}")
if (res.returncode != 0):
    print( "[WARNING] Unable to checkout branch/tag: {{cookiecutter.fprime_branch_or_tag}}")
    print(f"[WARNING] Reverted to default branch: {DEFAULT_BRANCH}")

# Install Venv
if ("{{cookiecutter.install_venv}}" == "yes"):
    subprocess.run(["python",  "-m", "venv", "{{cookiecutter.venv_install_path}}"])
    subprocess.run(["{{cookiecutter.venv_install_path}}/bin/pip", "install", "-r", "fprime/requirements.txt"])


print("""
################################################################

Congratulations! You have successfully created a new F' project.

A git repository has been initialized and F' has been added as a
submodule, you can now create your first commit.

Get started with your F' project:

-- Activate the virtual environment --
Linux/MacOS: source venv/bin/activate
Windows: venv\Scripts\\activate.bat

-- Generate a new component --
fprime-util new --component

-- Generate a new deployment --
fprime-util new --deployment

-- Run the base deployment --
cd <DeploymentName>
fprime-util generate
fprime-util build
fprime-gds

################################################################
""")

if (res.returncode != 0):
    print( "[WARNING] Unable to checkout branch/tag: {{cookiecutter.fprime_branch_or_tag}}")
    print(f"[WARNING] Reverted to default branch: {DEFAULT_BRANCH}")
else:
    print("[INFO] F' submodule checked out to branch/tag: {{cookiecutter.fprime_branch_or_tag}}")
