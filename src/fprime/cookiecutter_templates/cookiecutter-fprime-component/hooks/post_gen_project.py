from __future__ import print_function

import datetime
import os
from os.path import join
from fprime.fbuild.settings import IniSettings
from fprime.fbuild.builder import Build
from fprime.fbuild.interaction import make_namespace
from pathlib import Path

try:
    from click.termui import secho
except ImportError:
    warn = print
else:
    def warn(text):
        for line in text.splitlines():
            secho(line, fg="white", bg="red", bold=True)


def replace_contents(filename, what, replacement, count = 1):
    with open(filename) as fh:
        changelog = fh.read()
    with open(filename, 'w') as fh:
        fh.write(changelog.replace(what, replacement, count))

if __name__ == "__main__":
    today = datetime.date.today()
    replace_contents(join('docs', 'sdd.md'), '<TODAY>', today.strftime("%m/%d/%Y"))

cwd = Path(os.getcwd())
deployment = Build.find_nearest_deployment(cwd)
namespace = make_namespace(deployment, cwd)
#Use fprime root to get schema for Component.xml file
try:
    settings = IniSettings.load(Path("../settings.ini"), cwd)
    if (settings.get("framework_path") is not None and settings["framework_path"] != "native"):
        path_to_fprime = settings["framework_path"]
    else:
        path_to_fprime = IniSettings.find_fprime(cwd)
except:
    path_to_fprime = IniSettings.find_fprime(cwd)


with open("{{ cookiecutter.component_name }}ComponentAi.xml", "r") as s:
    lines = s.readlines()
    print(type(path_to_fprime))
    s.close()

#Write schema location and namespace to .xml file
with open("{{ cookiecutter.component_name }}ComponentAi.xml", "w") as s:
    lines.insert(1, '<?xml-model href="' + str(path_to_fprime) + '/Autocoders/Python/schema/default/component_schema.rng" type="application/xml" schematypens="http://relaxng.org/ns/structure/1.0"?>\n')
    lines[2] = lines[2].replace("TEMP_NAMESPACE", namespace)
    print(lines[2])
    print(lines[3])
    s.write("".join(lines))
    s.close()


replace_contents("docs/sdd.md", "TEMP_NAMESPACE", namespace)



print("""
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

    If the project root was not found, you will need to add this component to 
    your build system and then possibly purge and generate your project.

    In addition, if no project root was found, the unit test files were not generated.

""")

