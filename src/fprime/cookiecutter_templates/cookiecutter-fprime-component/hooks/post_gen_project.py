from __future__ import print_function

import datetime
import os
# import shutil
# import subprocess
# import sys
from os.path import join
from fprime.fbuild.settings import IniSettings
from fprime.fbuild.builder import Build
from pathlib import Path

try:
    from click.termui import secho
except ImportError:
    warn = print
else:
    def warn(text):
        for line in text.splitlines():
            secho(line, fg="white", bg="red", bold=True)


def replace_contents(filename, what, replacement):
    with open(filename) as fh:
        changelog = fh.read()
    with open(filename, 'w') as fh:
        fh.write(changelog.replace(what, replacement))

if __name__ == "__main__":
    today = datetime.date.today()
    # replace_contents('CHANGELOG.rst', '<TODAY>', today.strftime("%Y-%m-%d"))
    replace_contents(join('docs', 'sdd.md'), '<TODAY>', today.strftime("%m/%d/%Y"))

# /{/% if cookiecutter.sphinx_docs == "no" %}
#     shutil.rmtree('docs')
# /{/% endif %}

# /{/%- if cookiecutter.command_line_interface == 'no' %}
#     os.unlink(join('src', '/{/{ cookiecutter.package_name }}', '__main__.py'))
#     os.unlink(join('src', '/{/{ cookiecutter.package_name }}', 'cli.py'))
# /{/% endif %}
print("****************************************************************")
print(os.getcwd() + "\n")

os.chdir("..")
print("****************************************************************")
print(os.getcwd() + "\n")

cwd = Path(os.getcwd())

#Use fprime root to get schema for Component.xml file
try:
    settings = IniSettings.load(Path("settings.ini"), cwd)
    if (settings.get("framework_path") is not None and settings["framework_path"] != "native"):
        path_to_fprime = settings["framework_path"]
    else:
        path_to_fprime = IniSettings.find_fprime(cwd)
except:
    path_to_fprime = IniSettings.find_fprime(cwd)


with open("{{ cookiecutter.component_name }}/{{ cookiecutter.component_name }}ComponentAi.xml", "r") as s:
    lines = s.readlines()
    print(type(path_to_fprime))
    s.close()

with open("{{ cookiecutter.component_name }}/{{ cookiecutter.component_name }}ComponentAi.xml", "w") as s:
    lines.insert(1, '<?xml-model href="' + str(path_to_fprime) + '/Autocoders/Python/schema/default/component_schema.rng" type="application/xml" schematypens="http://relaxng.org/ns/structure/1.0"?>')
    s.write("".join(lines))
    s.close()

'''
os.system("fprime-util purge")
print("DONE!!!")
os.system("fprime-util generate")
print("DONE2!!!")
os.chdir("{{cookiecutter.component_name}}")
os.system("fprime-util impl --ut")
os.rename("Tester.hpp", "test/ut/Tester.hpp")
os.rename("Tester.cpp", "test/ut/Tester.cpp")
os.rename("TesterBase.hpp", "test/ut/TesterBase.hpp")
os.rename("TesterBase.cpp", "test/ut/TesterBase.cpp")
os.rename("GTestBase.hpp", "test/ut/GTestBase.hpp")
os.rename("GTestBase.cpp", "test/ut/GTestBase.cpp")
os.rename("TestMain.cpp", "test/ut/TestMain.cpp")
'''




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

    You will still need to run `fprime-util` to generate the templates
    from your autocoder input file.

    This requires your component to be included in a deployment.  This
    can be done by adding a line like this, near the bottom of the
    deployment's CMakeLists.txt file:

        add_fprime_subdirectory("${CMAKE_CURRENT_LIST_DIR}/{{ cookiecutter.component_name }}")

    Then you need to (possibly purge) and generate the new cmake config
    in that deployment:

        fprime-util generate

    Now you can edit your {{ cookiecutter.component_name }}Ai.xml file
    define the component to your liking, and generate the implementation
    boilerplate:

        cd {{ cookiecutter.component_name }}
        fprime-util impl -b {path/to/your/deployment}/build-fprime-automatic-default

    Next, copy the `-template` code contents into your .hpp and .cpp files.
    Try not to overwrite the freshly generated comments at the top!

""")

