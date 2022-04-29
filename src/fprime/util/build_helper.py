"""
fprime.util.build_helper.py

This script is defined to help users run standard make processes using CMake. This will support migrants from the old
make system, as well as enable more efficient practices when developing in the CMake system. The following functions
are supported herein:

 - build: build the current directory/module/deployment
 - impl: make implementation templates
 - testimpl: make testing templates
 - build_ut: build the current UTs
 - check: run modules unit tests

@author mstarch
"""
import argparse
import os
import re
import sys
from pathlib import Path

from fprime.fbuild.types import InvalidBuildCacheException
from fprime.fbuild.target import Target, NoSuchTargetException
from fprime.fbuild.builder import (
    Build,
    BuildType,
    GenerateException,
    UnableToDetectDeploymentException,
)
from .help_text import HelpText
from fprime.fbuild.cli import add_fbuild_parsers, get_target

from fprime.util.cli import add_special_parsers

CMAKE_REG = re.compile(r"-D([a-zA-Z0-9_]+)=(.*)")


class ArgValidationException(Exception):
    """An exception used for argument validation"""


def package_version_check():
    """Checks the version of the packages installed match the expected packages of the fprime aggregate package"""
    try:
        import pkg_resources

        fprime_distribution = pkg_resources.get_distribution("fprime")
        tools_requirements = fprime_distribution.requires()

        for requirement in tools_requirements:
            try:
                result = pkg_resources.working_set.find(requirement)
                if not result:
                    print(f"[WARNING] Expected package {requirement} not found")
            except pkg_resources.VersionConflict as version_exception:
                print(
                    f"[WARNING] Expected package version {version_exception.req} but found {version_exception.dist}"
                )
    except (ImportError, pkg_resources.DistributionNotFound):
        print("[WARNING] 'fprime' package not installed, skipping tools version check")


def validate(parsed, unknown):
    """
    Validate rules to ensure that the args are properly consistent. This will also generate a set of validated arguments
    to pass to CMake. This allows these values to be created, defaulted, and validated in one place
    :param parsed: args to validate
    :param unknown: unknown arguments
    :return: cmake arguments to pass to CMake
    """
    cmake_args = {}
    make_args = {}
    # Check platforms for existing toolchain, unless the default is specified.
    if not hasattr(parsed, "command") or parsed.command is None:
        raise ArgValidationException("'fprime-util' not supplied sub-command argument")
    elif parsed.command == "generate":
        d_args = {
            match.group(1): match.group(2)
            for match in [CMAKE_REG.match(arg) for arg in unknown]
        }
        cmake_args.update(d_args)
        unknown = [arg for arg in unknown if not CMAKE_REG.match(arg)]
    # Build type only for generate, jobs only for non-generate
    elif parsed.command in Target.get_all_targets():
        parsed.settings = None  # Force to load from cache if possible
        make_args.update({"--jobs": (1 if parsed.jobs <= 0 else parsed.jobs)})
    # Check if any arguments are still unknown
    if unknown:
        runnable = f"{os.path.basename(sys.argv[0])} {parsed.command}"
        raise ArgValidationException(
            f"'{runnable}' supplied invalid arguments: {','.join(unknown)}"
        )
    parsed.build_cache = (
        None if parsed.build_cache is None else Path(parsed.build_cache)
    )
    return cmake_args, make_args


def parse_args(args):
    """
    Parse the arguments to the CLI. This will then enable the user to run the above listed commands via the commands.
    :param args: CLI arguments to process
    :return: parsed arguments in a Namespace
    """
    # Common parser specifying common arguments input into the utility
    common_parser = argparse.ArgumentParser(
        description="Common Parser for Common Ingredients."
    )
    common_parser.add_argument(
        "platform",
        nargs="?",
        default="default",
        help="F prime build platform (e.g. Linux, Darwin). Default specified in settings.ini",
    )
    common_parser.add_argument(
        "-d",
        "--deploy",
        dest="deploy",
        default=None,
        help="F prime deployment directory to use. May contain multiple build directories.",
    )
    common_parser.add_argument(
        "-p",
        "--path",
        default=os.getcwd(),
        help="F prime directory to operate on. Default: cwd, %(default)s.",
    )
    common_parser.add_argument(
        "--build-cache",
        dest="build_cache",
        default=None,
        help="Overrides the build cache with a specific directory",
    )
    common_parser.add_argument(
        "-v",
        "--verbose",
        default=False,
        action="store_true",
        help="Turn on verbose output.",
    )
    common_parser.add_argument(
        "--ut", action="store_true", help="Run command against unit testing build type"
    )

    # Main parser for the whole application
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=HelpText.long("global_help"),
    )
    subparsers = parser.add_subparsers(
        description=HelpText.long("subparsers_description"),
        dest="command",
    )

    # Add all externally defined cli parser command to running functions
    runners = {}
    parsers = {}

    fbuild_runners, fbuild_parsers = add_fbuild_parsers(
        subparsers, common_parser, HelpText
    )
    runners.update(fbuild_runners)
    parsers.update(fbuild_parsers)
    # runners.update(add_fpp_parsers(subparsers, common_parser))
    runners.update(add_special_parsers(subparsers, common_parser, HelpText))

    # Parse and prepare to run
    parsed, unknown = parser.parse_known_args(args)
    try:
        cmake_args, make_args = validate(parsed, unknown)
    except ArgValidationException as exc:
        print(f"[ERROR] {exc}", end="\n\n")
        parsers.get(parsed.command, (parser,))[0].print_usage()
        sys.exit(1)
    return parsed, cmake_args, make_args, parser, runners


def utility_entry(args):
    """Main interface to F prime utility"""
    package_version_check()
    parsed, cmake_args, make_args, parser, runners = parse_args(args)

    try:
        cwd = Path(parsed.path)

        try:
            target = get_target(parsed)
            build_type = target.build_type
        except NoSuchTargetException:
            build_type = (
                BuildType.BUILD_TESTING if parsed.ut else BuildType.BUILD_NORMAL
            )

        deployment = (
            Path(parsed.deploy)
            if parsed.deploy is not None
            else Build.find_nearest_deployment(Path.cwd())  # Deployments look in CWD
        )
        build = Build(build_type, deployment, verbose=parsed.verbose)

        # All commands need to load the build cache to setup the basic information for the build with the exception of
        # generate, which is run before the creation of the build cache.
        #
        # Some commands, like purge and info, run on sets of directories an will attempt to load the sets later.
        # However, the base directory must be setup here. Errors in this load are ignored to allow the command to find
        # build caches related to that set.
        if parsed.command not in ["generate"]:
            try:
                build.load(parsed.platform, parsed.build_cache)
            except InvalidBuildCacheException:
                if parsed.command not in ["purge", "info"]:
                    raise
        runners[parsed.command](
            build, parsed, cmake_args, make_args, getattr(parsed, "pass_through", [])
        )
    except GenerateException as genex:
        print(
            f"[ERROR] {genex}. Partial build cache remains. Run purge to clean-up.",
            file=sys.stderr,
        )
        return genex.exit_code
    except UnableToDetectDeploymentException:
        print(f"[ERROR] Could not detect deployment directory for: {parsed.path}")
        return 1
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    return 0
