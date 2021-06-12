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

# /{/% if cookiecutter.sphinx_docs == "no" %}
#     shutil.rmtree('docs')
# /{/% endif %}

# /{/%- if cookiecutter.command_line_interface == 'no' %}
#     os.unlink(join('src', '/{/{ cookiecutter.package_name }}', '__main__.py'))
#     os.unlink(join('src', '/{/{ cookiecutter.package_name }}', 'cli.py'))
# /{/% endif %}

    print("""
################################################################################
################################################################################

    You have successfully created the `{{ cookiecutter.port_slug }}` port.

################################################################################

    You've used these cookiecutter parameters:
{% for key, value in cookiecutter.items()|sort %}
        {{ "{0:26}".format(key + ":") }} {{ "{0!r}".format(value).strip("u") }}
{%- endfor %}

################################################################################

    You will still need to run `fprime-util` to generate the templates
    from your autocoder input file.

    This requires your port to be included in a deployment.  This
    can be done by adding a line like this, near the bottom of the
    deployment's CMakeLists.txt file:

        add_fprime_subdirectory("${CMAKE_CURRENT_LIST_DIR}/../{{ cookiecutter.port_path }}/{{ cookiecutter.port_dir_name }}")

    Then you need to (possibly purge) and generate the new cmake config
    in that deployment:

        fprime-util generate

    Now you can edit your {{ cookiecutter.port_slug }}Ai.xml file
    define the port to your liking, and generate the implementation
    boilerplate:

        cd {{ cookiecutter.port_dir_name }}
        fprime-util impl -b {path/to/your/deployment}/build-fprime-automatic-default

    Next, copy the `-template` code contents into your .hpp and .cpp files.
    Try not to overwrite the freshly generated comments at the top!

""")

