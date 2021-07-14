from __future__ import print_function

import datetime
import os
from os.path import join
from fprime.fbuild.settings import IniSettings
from fprime.fbuild.builder import Build
from fprime.fbuild.interaction import make_namespace
from pathlib import Path


def replace_contents(filename, what, replacement, count=1):
    with open(filename) as fh:
        changelog = fh.read()
    with open(filename, "w") as fh:
        fh.write(changelog.replace(what, replacement, count))


def main():
    cwd = Path(os.getcwd())
    deployment = Build.find_nearest_deployment(cwd)
    namespace = make_namespace(deployment, cwd)
    settings = IniSettings.load(Path(deployment,"settings.ini"), cwd)
    if settings.get("project_root") is None:
        proj_root_found = False
    else:
        proj_root_found = True

    replace_contents(
        "{{ cookiecutter.component_name }}ComponentAi.xml", "TEMP_NAMESPACE", namespace
    )

    replace_contents("docs/sdd.md", "TEMP_NAMESPACE", namespace)

    today = datetime.date.today()
    replace_contents(join("docs", "sdd.md"), "<TODAY>", today.strftime("%m/%d/%Y"))

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
