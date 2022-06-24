""" fprime.util.help_text:

Contains the strings and minor constructs used to specify help text in fprime utility. Any new help strings for new
commands should be written here. Implementers should use HelpText.long(key) and HelpText.short(key) to get appropriate
help messages when building argument parsers. In addition, implementers are expected to use the formatter class
RawDescriptionHelpFormatter as these messages are written expecting that new lines will be maintained.

Help text format: like pydoc, the first line is assumed to be a short description (summary) and following lines will be
interpreted as the explanation. Usually a blank line separates the short and long description.

`short description

long paragraph description
`

@author lestarch
"""
import os
import sys


# Attempt to get pkg_resources from "setuptools"
try:
    import pkg_resources

    VERSION = pkg_resources.get_distribution("fprime-tools").version
except ImportError:
    VERSION = "(unknown version)"


EXECUTABLE = os.path.basename(sys.argv[0])
MNEMONIC_HELP_MAP = {
    "global_help": f"""{EXECUTABLE} ({VERSION}): Utility supporting fprime development patterns.

'{EXECUTABLE}' wraps the fprime build system enabling developers to follow standard patterns when developing fprime
applications. Specifically it translates between the developer's context (working directory and supplied flags) to the
build system targets defined for that context. i.e. a developer can change directory into a component directory and run
commands restricted to that component.

Almost all {EXECUTABLE} commands require a valid build cache to run. Thus users should start by running '{EXECUTABLE}
generate' in their desired deployment before running command. Once a build cache has been generated other commands can
be run. The '--ut' flag sets up a testing build cache and enables unit test commands to be run. An explanation of how
{EXECUTABLE} determines the build cache is included below. More information on creating build caches can be found with:
'{EXECUTABLE} generate --help'.

Examples:

  -- Setup and Build Ref On Default Platform  --
  cd Ref
  {EXECUTABLE} generate
  {EXECUTABLE} build

  -- Setup and Build Ref Unit Tests --
  cd Ref
  {EXECUTABLE} generate --ut
  {EXECUTABLE} build --ut
  {EXECUTABLE} check  # Runs UTs '--ut' is implied

  -- Setup Ref Build for RaspberryPI Platform --
  cd Ref
  {EXECUTABLE} generate raspberrypi
  {EXECUTABLE} build

{EXECUTABLE} uses the working directory and supplied flags as context for all the commands it runs. This context is used
to determine two build properties: build cache (created by 'fprime-util generate') to be used and build target to
execute. The build cache is chosen by recurring upward from the current working directory looking for the first build
cache matching the specified platform. If '--ut' is specified, only UT caches will be selected. The platform is read
from the optional positional argument 'platform'. If not specified on the command line, the 'default_toolchain' setting
in the deployment's settings.ini file is read. In not specified there, the default toolchain "native" is used.

If a different deployment is desired, the recursive search behavior can be altered with the '-d/--deployment'. When
'-d/--deployment' is specified, a matching build cache will be selected from within the supplied deployment directory.
'--build-cache' may be supplied to force '{EXECUTABLE}' to use the supplied build cache regardless of other conditions.

Once the build cache has been selected, the build target is chosen. {EXECUTABLE} will run the supplied command for
a chosen directory.  This directory is can be set using the '-p/--path' argument and defaults to the user's current
working directory. This command and directory are translated into the build target to be executed.
e.g. 'cd Ref/SignalGen; {EXECUTABLE} impl' will run the build target 'Ref_SignalGen_impl'. Most users need not care
about the specific build target being run and should think "command run in chosen directory".

There are two other conditions where the described behavior will differ slightly. If the current working directory or
the path specified '-p/--path' points to a deployment, the command supplied will be run against the deployment and will
be run against all components used by that deployment. e.g. 'cd Ref; {EXECUTABLE} build --ut' will build all UTs for
components used by the Ref deployment. Supplying the '--all' flag executes the command on everything defined within the
build system. e.g 'cd Ref; {EXECUTABLE} build --all' builds all components found anywhere in the build system regardless
if they are used by the deployment or merely defined in the build system.

Contextual Examples:

  -- Build SignalGen Component --
  cd Ref/SignalGen
  {EXECUTABLE} build

  -- Build Command Dispatcher UTs for Ref Deployment --
  cd Svc/CmdDispatcher
  {EXECUTABLE} build --ut -d ../../Ref/

  -- Build Command Dispatcher UTs for Ref Deployment (Alternate) --
  cd Ref
  {EXECUTABLE} build --ut -p ../../Svc/CmdDispatcher

  -- Build Everything --
  {EXECUTABLE} build --all

""",
    "subparsers_description": f"""Commands supported by {EXECUTABLE} ({VERSION})

These are the commands that may be run as part of {EXECUTABLE}. These commands wrap various functions of the
development process. One of these commands should be the first argument to an invocation of {EXECUTABLE}. For more
explanation on an individual command, please run '{EXECUTABLE} <command> --help>'.
""",
    "build": f"""{EXECUTABLE} build ({VERSION}): Build fprime components, deployments, and unit tests

'{EXECUTABLE} build' builds in the selected directory ('-p/--path' or current working directory). When the selected
directory contains a component, the component is built. When the current directory contains a deployment, the deployment
is built and installed into the build artifact directory. The build cache used to perform this build is described in
'{EXECUTABLE} --help'. Notably supplying the '--ut' flag switches to building the unit tests for components and all
deployment unit tests for deployments.. Supplying the '--all' flag will switch to building everything defined in the
build system.

'{EXECUTABLE} build' requires a build cache to have been generated
'{EXECUTABLE} build --ut' requires a testing build cache to have been generated

Examples:

  -- Build Ref/SignalGen --
  cd Ref/SignalGen
  {EXECUTABLE} build

  -- Build Reg/SignalGen UTs --
  cd Ref/SignalGen
  {EXECUTABLE} build

""",
    "impl": f"""{EXECUTABLE} impl ({VERSION}): Generate fprime implementation templates.

'{EXECUTABLE} impl' generates the implementation templates for the specified directory ('-p/--path' or current working
directory). Implementation generation is only available for component directories and should not be used on deployments.
Two files will be created <component>.cpp-template and <component>.hpp-template. These contain the fill-in base code for
the component implementation as defined by the component's model. 

When the '--ut' flag is specified the unit test implementation templates are created instead. The user should use the
Tester.cpp, Tester.hpp and TestMain.cpp files as their fill-in templates. Other files created can be safely removed as
they will be regenerated at build time.

Example:

  -- Create Ref/SignalGen Implementation Templates --
  cd Ref/SignalGen
  {EXECUTABLE} impl

  -- Create Ref/SignalGen Unit Test Implementation Templates --
  cd Ref/SignalGen
  {EXECUTABLE} impl --ut

""",
    "check": f"""{EXECUTABLE} check ({VERSION}): Run fprime unit tests with optional leak checking and test coverage.

'{EXECUTABLE} check' handles the running of unit tests. It can be used on components to run the component's unit tests,
deployments to run deployment unit tests, and with the '--all' flag to run all unit tests found in the build system.
'{EXECUTABLE} check' implies the '--ut' flag and specifying it is redundant.  When '{EXECUTABLE} check' is run with the
'--leak' flag, valgrind is used to look for resource leaks.

'{EXECUTABLE} check' can also be supplied the '--coverage' flag. When the '--coverage' flag is supplied, the unit test
is run and 'gcovr' is run on the output to check coverage. The default flags to 'gcovr' are '--print-summary', '--txt',
'--html-details' along with filters to restrict the coverage to the existing component/deployment. Outputs are put in a
subdirectory of the component/deployment titled "coverage".  Additional arguments can be supplied after the
'--pass-through' flag with several caveats: '--pass-through ...' must be the last arguments on the command line, and
all paths supplied to 'gcovr' must be full paths. Users should purge the build cache when switching between
'--coverage --all' and '--coverage' in a deployment cache.

Examples:

  -- Run Ref/SignalGen Unit Tests --
  cd Ref/SignalGen
  {EXECUTABLE} check

  -- Run Ref/SignalGen Unit Tests With Leak Check --
  cd Ref/SignalGen
  {EXECUTABLE} check --leak

  -- Run Ref/SignalGen Unit Tests With Coverage --
  cd Ref/SignalGen
  {EXECUTABLE} check --coverage

  -- Run Ref/SignalGen Unit Tests With Detailed HTML Coverage --
  cd Ref/SignalGen
  {EXECUTABLE} check --coverage
""",
    "generate": f"""{EXECUTABLE} generate ({VERSION}): Generate build caches for the specified deployment

'{EXECUTABLE} generate' is used to setup a build cache to support other commands run by {EXECUTABLE}. Without additional
arguments a build cache will be created for the deployment in the specified directory ('-p/--path', or current working
directory). It will use the default settings specified in the deployment's settings.ini file for the target platform,
fprime libraries, etc. Specifying '-d/--deployment' generates the deployment at the supplied directory overriding the
directory specified with '-p/--path' and the current working directory. '--ut' should be specified to generate testing
build caches for running unit tests.

Basic Examples:
  -- Generate Ref Build Cache With Default Settings --
  cd Ref
  {EXECUTABLE} generate

  -- Generate Ref Testing Build Cache With Default Settings --
  cd Ref
  {EXECUTABLE} generate --ut

The target platform for the build cache can be overridden using an optional positional argument. This will setup the
build to target the supplied platform using a toolchain configuration and platform support files of the same name.
{EXECUTABLE} searches for these named files in appropriate folders in following locations: cmake directory in the
project's root folder, cmake directories in projects included fprime libraries, cmake directory in fprime framework.
These locations are search in the above order with toolchains expected in a 'toolchain' sub folder and platforms in a
'platform' subdirectory.

Toolchain Example:

  -- Generate Ref Build Cache for Raspberrypi --
  cd Ref
  {EXECUTABLE} generate raspberrypi

Other build properties and variables can be specified using flags of the form '-DVARIABLE_NAME=VALUE'. This allows
developers to switch build options for a specific build generated build. This is often combined with the '--build-cache'
flag to put the specifically configured build cache at a specifically named location. All commands (build, check, etc.)
run against that build cache must also specify the same location with the '--build-cache' flag. '-DVARIABLE_NAME=VALUE'
sets a CMake cache variable of name VARIABLE_NAME to the value VALUE. Most of these variables are described in:
fprime/cmake/options.cmake. Warnings from CMake saying VARIABLE_NAME was set but unused likely means the VARIABLE_NAME
was misspelled.

CMake Flag Examples:

  -- Generate Ref Unit Tests Disabling Autocoder UTs --
  cd Ref
  {EXECUTABLE} generate --ut -DFPRIME_ENABLE_AUTOCODER_UTS=OFF

  -- Generate Ref With Baremetal Scheduler Into Specific Cache --
  cd Ref
  {EXECUTABLE} generate --build-cache `pwd`/build-ref-with-baremetal -DFPRIME_USE_BAREMETAL_SCHEDULER=ON

""",
    "purge": f"""{EXECUTABLE} purge ({VERSION}): Removes build caches for specified deployment
    
'{EXECUTABLE} purge' removes build caches for the specified deployment. It also removes the build_artifacts directory
in that deployment as well. Caches are searched in pairs: normal build cache, paired unit testing build cache. The
user will be asked to confirm when a build cache is being removed unless the '--force' flag is specified. The platform
will use the settings specified in 'settings.ini' or as specified with the optional positional argument. The
'--build-cache' flag can be used to remove an exact build cache without looking at other build caches.

'{EXECUTABLE} purge' will not remove build caches that do not look like valid build caches unless the '--force' flag is
supplied. In this case, the build cache will be removed with reckless abandon.
    """,
    "info": f"""Print contextual target and build cache information before exiting

'{EXECUTABLE} info' is used to print contextual information to the user before exiting. It will print the available]
commands within the current context (working directory, '-p/--path', '-d/--deployment', etc.) and then exit. Users may
use the info command as a way to test and understand how {EXECUTABLE} is mapping to the context and targets used. info
may also be used to locate the artifact output folders within the build cache in order to see generated files, compiler
outputs, etc.

'{EXECUTABLE} info' will print information for both normal and unit testing builds when possible. If '--build-cache' is
specified then only the information for that build cache will be printed.
""",
    "hash-to-file": f"""{EXECUTABLE} hash-to-file ({VERSION}): Convert FW_ASSERT file id hash to file path

When a project compiles fprime with 'FW_ASSERT_LEVEL' set to 'FW_FILEID_ASSERT' a hash will be emitted in place of the
file path in order to keep assert messages succinct. '{EXECUTABLE} hash-to-file <hash>' will convert this hash value to
the file path of the file that produced the assert. This must be run against the same build cache that created the
binary that tripped the assert. When specifying a non-default platform, the platform comes before the hash value. This
command cannot detect changes to the underlying file data as hashes are computed only from the file name.

Examples:

  -- Map Ref Hash to File --
  cd Ref
  {EXECUTABLE} hash-to-file 0xABCD1234

  -- Map Ref Hash to File for RaspberryPI Platform --
  cd Ref
  {EXECUTABLE} hash-to-file raspberrypi 0xABCD1234
""",
    "new": f"""{EXECUTABLE} new ({VERSION}):       -- WARNING: prototype code -- Creates a new fprime object

WARNING: prototype code. Not recommended for inexperienced users. '{EXECUTABLE} new' runs a wizard to create new ports
and components in fprime. The code has not been updated to use FPP models. Please check back later.
""",
}


class HelpText:
    """
    There are two styles of help text: short (for argument descriptions) and long for full descriptions. This function
    will take a context key (command name, mnemonic, or other string) to lookup the full help text. The short help text
    is the first line of the full help text. This class provides functions for both.
    """

    @staticmethod
    def short(context_key: str, default: str = ""):
        """Short help text for context

        Returns the short help message (first line of the long help).

        Args:
            context_key: mnemonic or other key to look-up appropriate help text
            default: default string to use as the full help text
        Returns:
            short help description
        """
        lines = MNEMONIC_HELP_MAP.get(context_key, default).splitlines()
        return lines[0] if lines else default

    @staticmethod
    def long(context_key: str, default: str = "", version="(unknown version)"):
        """long help text for context

        Returns the long help message.

        Args:
            context_key: mnemonic or other key to look-up appropriate help text
            default: default string to use as the full help text
        Returns:
            long help description
        """
        return MNEMONIC_HELP_MAP.get(context_key, default)
