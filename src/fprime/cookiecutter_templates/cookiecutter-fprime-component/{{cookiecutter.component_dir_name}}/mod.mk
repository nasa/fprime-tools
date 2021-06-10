# This is a template for the mod.mk file that goes in each module
# and each module's subdirectories.
# With a fresh checkout, "make gen_make" should be invoked. It should also be
# run if any of the variables are updated. Any unused variables can
# be deleted from the file.

# There are some standard files that are included for reference


SRC = {{cookiecutter.component_slug}}ComponentAi.xml \
      {{cookiecutter.component_slug}}{{cookiecutter.component_explicit_component_suffix}}{{cookiecutter.component_explicit_common}}{{cookiecutter.component_impl_suffix}}.cpp
{% if cookiecutter.component_multiplatform_support == "yes" %}
SRC_LINUX = {{cookiecutter.component_slug}}{{cookiecutter.component_explicit_component_suffix}}Linux{{cookiecutter.component_impl_suffix}}.cpp

SRC_CYGWIN = {{cookiecutter.component_slug}}{{cookiecutter.component_explicit_component_suffix}}CygWin{{cookiecutter.component_impl_suffix}}.cpp

SRC_DARWIN = {{cookiecutter.component_slug}}{{cookiecutter.component_explicit_component_suffix}}Darwin{{cookiecutter.component_impl_suffix}}.cpp

SRC_RASPIAN = {{cookiecutter.component_slug}}{{cookiecutter.component_explicit_component_suffix}}Linux{{cookiecutter.component_impl_suffix}}.cpp
{% endif %}
HDR = {{cookiecutter.component_slug}}{{cookiecutter.component_explicit_component_suffix}}{{cookiecutter.component_impl_suffix}}.hpp

SUBDIRS =
