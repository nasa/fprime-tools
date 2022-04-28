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

from fprime.common.error import FprimeException
from fprime.fbuild.builder import (
    Build,
    BuildType,
    GenerateException,
    NoSuchTargetException,
    Target,
    UnableToDetectDeploymentException,
)
from fprime.fbuild.cli import add_fbuild_parsers, get_target
from fprime.fpp.cli import add_fpp_parsers
from fprime.util.cli import add_special_parsers

CMAKE_REG = re.compile(r"-D([a-zA-Z0-9_]+)=(.*)")


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
    if parsed.command == "generate":
        d_args = {
            match.group(1): match.group(2)
            for match in [CMAKE_REG.match(arg) for arg in unknown]
        }
        cmake_args.update(d_args)
    # Build type only for generate, jobs only for non-generate
    elif parsed.command in Target.get_all_targets():
        parsed.settings = None  # Force to load from cache if possible
        make_args.update({"--jobs": (1 if parsed.jobs <= 0 else parsed.jobs)})
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
    parser = argparse.ArgumentParser(description="F prime helper application.")
    subparsers = parser.add_subparsers(
        description="F prime utility command line. Please run one of the commands. "
        + "For help, run a command with the --help flag.",
        dest="command",
    )

    # Add all externally defined cli parser command to running functions
    runners = {}
    runners.update(add_fbuild_parsers(subparsers, common_parser))
    runners.update(add_fpp_parsers(subparsers, common_parser))
    runners.update(add_special_parsers(subparsers, common_parser))

    # Parse and prepare to run
    parsed, unknown = parser.parse_known_args(args)
    bad = [bad for bad in unknown if not CMAKE_REG.match(bad)]
    if not hasattr(parsed, "command") or parsed.command is None:
        parser.print_help()
        sys.exit(1)
    elif bad:
        print(f'[ERROR] Unknown arguments: {", ".join(bad)}')
        parser.print_help()
        sys.exit(1)
    cmake_args, make_args = validate(parsed, unknown)
    return parsed, cmake_args, make_args, parser, runners


def utility_entry(args):
    """Main interface to F prime utility"""
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

        # When not handling generate/purge we need a valid build cache and should load it
        if parsed.command not in ["generate", "purge"]:
            build.load(parsed.platform, parsed.build_cache)
        runners[parsed.command](build, parsed, cmake_args, make_args)
    except GenerateException as genex:
        print(
            f"[ERROR] {genex}. Partial build cache remains. Run purge to clean-up.",
            file=sys.stderr,
        )
        return genex.exit_code
    except UnableToDetectDeploymentException:
        print(f"[ERROR] Could not detect deployment directory for: {parsed.path}")
        return 1
    except FprimeException as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    return 0
