from __future__ import print_function

import datetime
import os
# import shutil
# import subprocess
# import sys
from os.path import join

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

{% if cookiecutter.component_multiplatform_support == "no" %}
    # {{cookiecutter.component_slug}}/
    mp_str = '{{cookiecutter.component_slug}}Component{}Impl.cpp'
    rm_list = ['Arduino', 'AVR', 'CygWin', 'Linux', 'Darwin', 'RPi', 'VxWorks']
    for i in rm_list:
        os.unlink(mp_str.format(i))
{% endif %}

# /{/% if cookiecutter.sphinx_docs == "no" %}
#     shutil.rmtree('docs')
# /{/% endif %}

# /{/%- if cookiecutter.command_line_interface == 'no' %}
#     os.unlink(join('src', '/{/{ cookiecutter.package_name }}', '__main__.py'))
#     os.unlink(join('src', '/{/{ cookiecutter.package_name }}', 'cli.py'))
# /{/% endif %}
print("****************************************************************")
print(os.getcwd() + "\n")
with open("../CMakeLists.txt", "r") as f:
    lines = f.readlines()
    index = 0
    while "add_fprime_subdirectory" not in lines[index]:
        index += 1
    while "add_fprime_subdirectory" in lines[index]:
        index += 1

addition = 'add_fprime_subdirectory("${CMAKE_CURRENT_LIST_DIR}/{{cookiecutter.component_slug}}/")\n'
lines.insert(index, addition)
with open("../CMakeLists.txt", "w") as f:
    f.write("".join(lines))

os.system("fprime-util purge")
print("DONE!!!")
os.system("fprime-util generate")
print("DONE2!!!")
os.system("cd {{cookiecutter.component_slug}}")
os.system("fprime-util impl --ut")
os.rename("Tester.hpp", "test/ut/Tester.hpp")
os.rename("Tester.cpp", "test/ut/Tester.cpp")
os.rename("TesterBase.hpp", "test/ut/TesterBase.hpp")
os.rename("TesterBase.cpp", "test/ut/TesterBase.cpp")
os.rename("GTestBase.hpp", "test/ut/GTestBase.hpp")
os.rename("GTestBase.cpp", "test/ut/GTestBase.cpp")
os.rename("TestMain.cpp", "test/ut/TestMain.cpp")


print("""
################################################################################
################################################################################

    You have successfully created the `{{ cookiecutter.component_slug }}` component.

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

        add_fprime_subdirectory("${CMAKE_CURRENT_LIST_DIR}/../{{ cookiecutter.component_path }}/{{ cookiecutter.component_slug }}")

    Then you need to (possibly purge) and generate the new cmake config
    in that deployment:

        fprime-util generate

    Now you can edit your {{ cookiecutter.component_slug }}Ai.xml file
    define the component to your liking, and generate the implementation
    boilerplate:

        cd {{ cookiecutter.component_slug }}
        fprime-util impl -b {path/to/your/deployment}/build-fprime-automatic-default

    Next, copy the `-template` code contents into your .hpp and .cpp files.
    Try not to overwrite the freshly generated comments at the top!

""")

