from __future__ import print_function

import datetime
import os
from os.path import join
from fprime.fbuild.settings import IniSettings
from fprime.fbuild.builder import Build
from pathlib import Path
import textwrap

def replace_contents(filename, what, replacement, count=1):
    with open(filename) as fh:
        changelog = fh.read()
    with open(filename, "w") as fh:
        fh.write(changelog.replace(what, replacement, count))

def remove_line(filename, removal):
    with open(filename, "r") as f:
        lines = f.readlines()
        f.close()
    with open(filename, "w") as f:
        for line in lines:
            if line != removal:
                f.write(line)
        f.close()

def update_sdd():
    ports = "## Port Descriptions\n| Name | Description |\n"
    if "{{cookiecutter.component_kind}}" == "active":
        ports = ports + textwrap.dedent('''\
        | PingIn | Used for pinging other components |
        | PingOut | Used to recieve ping signal |\n''')
    elif "{{cookiecutter.component_kind}}" == "active":
        ports = ports + textwrap.dedent(
        "| SchedIn | Used as a schedular for queued components |\n")

    if "{{cookiecutter.commands}}" == "yes":
        replace_contents("docs/sdd.md", "## Commands",
        textwrap.dedent('''\
        ## Commands
        | Name | Description |
        | ExampleCommand | Example of how a command is implemented |
        |---|---|\n'''))
        ports = ports + textwrap.dedent('''\
            | cmdIn | Used to recieve commands |
            | cmdRegOut | Used to register with the command dispatcher |
            | cmdResponseOut | Used to return responses to command dispatcher |\n''')
    else:
        remove_line("docs/sdd.md", "## Commands\n")

    if "{{cookiecutter.parameters}}" == "yes":
        replace_contents("docs/sdd.md", "## Parameters",
        textwrap.dedent('''\
        ## Parameters
        | Name | Description |
        | ExampleParameter | Example of how a parameter is implemented |
        |---|---|\n'''))
        ports = ports + textwrap.dedent('''\
            | PrmGetIn | Used to get parameter value |
            | PrmSetIn | Used to set parameter value |\n''')
    else:
        remove_line("docs/sdd.md", "## Parameters\n")

    if "{{cookiecutter.events}}" == "yes":
        replace_contents("docs/sdd.md", "## Events",
        textwrap.dedent('''\
        ## Events
        | Name | Description |
        | EX_ExampleEvent | Example of how an event is implemented |
        |---|---|\n'''))
        ports = ports + textwrap.dedent('''\
            | eventOut | Used to send events |
            | textEventOut | Used to send text formatted events |\n''')
    else:
        remove_line("docs/sdd.md", "## Events\n")

    if "{{cookiecutter.telemetry}}" == "yes":
        replace_contents("docs/sdd.md", "## Telemetry",
        textwrap.dedent('''\
        ## Telemetry
        | Name | Description |
        | ExampleChannel | Example of how a telemetry channel is implemented |
        |---|---|\n'''))
        ports = ports + textwrap.dedent('''\
            | tlmOut | Used to send telemetry data |\n''')
    else:
        remove_line("docs/sdd.md", "## Telemetry\n")
    replace_contents("docs/sdd.md", "## Port Descriptions", ports)


def main():
    cwd = Path(os.getcwd())
    deployment = Build.find_nearest_deployment(cwd)
    settings = IniSettings.load(Path(deployment, "settings.ini"), cwd)
    if settings.get("project_root") is None:
        proj_root_found = False
    else:
        proj_root_found = True
    today = datetime.date.today()
    replace_contents(join("docs", "sdd.md"), "<TODAY>", today.strftime("%m/%d/%Y"))
    update_sdd()
    remove_line("{{cookiecutter.component_name}}ComponentAi.xml", "\n")

    print(
        """
    ################################################################################
    ################################################################################

        You have successfully created the `{{ cookiecutter.component_name }}` component.

    ################################################################################

        You've used these cookiecutter parameters:
    {% for key, value in cookiecutter.items()|sort %}
            {{ "{0:26}".format(key + ":") }} {{ "{0!r}".format(value).strip("u") }}
    {%- endfor %}

    ################################################################################

        Now you can edit your {{ cookiecutter.component_name }}Ai.xml file
        define the component to your liking

        In addition, a sdd.md file has been created in the docs directory 
        for you to document your component
    """
    )

    if not proj_root_found:
        print(
            """
        No project root was specified in your settings.ini file.
        This means you will need to add this component to your build
        system and then possibly purge and generate your project.

        In addition, the unit test files were not generated.
            
        To fix this issue, ensure you have a settings.ini file that 
        specifies your project_root
            """
        )


if __name__ == "__main__":
    main()
