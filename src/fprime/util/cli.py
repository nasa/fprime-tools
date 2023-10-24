""" fprime.util.cli: CLI handling

Defines main entrypoint for fprime-util and sets up parsers for general CLI targets.

@author mstarch
"""
import argparse
import os
import re
import sys
from pathlib import Path
from typing import Callable, Dict

from fprime.fbuild.builder import GenerateException, UnableToDetectProjectException
from fprime.fbuild.cli import add_fbuild_parsers
from fprime.fbuild.target import Target
from fprime.fpp.cli import add_fpp_parsers
from fprime.util.build_helper import load_build
from fprime.util.commands import run_code_format, run_hash_to_file, run_info, run_new
from fprime.util.help_text import HelpText
from fprime.fpp.visualize import add_fpp_viz_parsers


def utility_entry(args):
    """Entrypoint for fprime-util, main interface to F' utility"""
    parsed, cmake_args, make_args, parser, runners = parse_args(args)

    try:
        build = (
            None
            if skip_build_loading(parsed)
            else load_build(parsed, skip_build_cache_validation(parsed))
        )

        # runners is a Dict[str, Callable] of {command_name: handler_functions} pairs
        return runners[parsed.command](
            build, parsed, cmake_args, make_args, getattr(parsed, "pass_through", [])
        )

    except GenerateException as genex:
        print(
            f"[ERROR] {genex}. Partial build cache remains. Run purge to clean-up.",
            file=sys.stderr,
        )
    except UnableToDetectProjectException:
        print(f"[ERROR] Could not detect project directory for: {parsed.path}")
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
    return 1


def skip_build_loading(parsed):
    """Determines if the build load step should be skipped. Commands that do not require a build object
    should manually be added here by the developer.
    """
    if parsed.command == "new" and parsed.new_project:
        return True
    return False


def skip_build_cache_validation(parsed):
    """Determines if the build cache validation step should be skipped. Commands that do not require a
    build **cache** should manually be added here by the developer.
    """
    if parsed.command in [
        "purge",
        "info",
        "format",
    ]:
        return True
    if parsed.command == "new" and parsed.new_deployment:
        return True
    return False


def add_special_parsers(
    subparsers, common: argparse.ArgumentParser, help_text: "HelpText"
) -> Dict[str, Callable]:
    """Adds in CLI parsers for other commands

    Args:
        subparsers: subparsers used to create new CLI subparsers
        common: common parent parser

    Returns:
        Dictionary associating special command name to callable used to process it
    """
    # Add a search for hash function
    hash_parser = subparsers.add_parser(
        "hash-to-file",
        description=help_text.long("hash-to-file"),
        help=help_text.short("hash-to-file"),
        parents=[common],
        add_help=False,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    hash_parser.add_argument(
        "hash",
        type=lambda x: int(x, 0),
        help="Assert hash value to convert to filename",
    )

    # Add a search for hash function
    subparsers.add_parser(
        "info",
        description=help_text.long("info"),
        help=help_text.short("info"),
        parents=[common],
        add_help=False,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # New functionality
    new_parser = subparsers.add_parser(
        "new",
        description=help_text.long("new"),
        help=help_text.short("new"),
        parents=[common],
        add_help=False,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    new_parser.add_argument(
        "--overwrite",
        default=False,
        action="store_true",
        help="Generated files will overwrite existing ones",
    )
    new_parser.add_argument(
        "--prevent-tools-installation",
        default=False,
        action="store_true",
        help="Prevent the installation of the tool suite in the current virtual environment",
    )
    new_exclusive = new_parser.add_argument_group(
        "'new' targets"
    ).add_mutually_exclusive_group()
    new_exclusive.add_argument(
        "--component",
        default=False,
        action="store_true",
        dest="new_component",
        help="Generate a new component",
    )
    new_exclusive.add_argument(
        "--deployment",
        default=False,
        action="store_true",
        dest="new_deployment",
        help="Generate a new deployment",
    )
    new_exclusive.add_argument(
        "--project",
        default=False,
        action="store_true",
        dest="new_project",
        help="Generate a new project",
    )

    # Code formatting with clang-format
    format_parser = subparsers.add_parser(
        "format",
        help=help_text.short("format"),
        description=help_text.long("format"),
        parents=[common],
        add_help=False,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        conflict_handler="resolve",
    ).add_argument_group("format utility arguments")
    format_parser.add_argument(
        "-x", "--no-backup", action="store_true", help="Disable backups"
    )
    format_parser.add_argument(
        "-q", "--quiet", action="store_true", help="Disable clang-format verbose mode"
    )
    format_parser.add_argument(
        "--force",
        action="store_true",
        help="Force all listed files to be passed to clang-format (no file extension check)",
    )
    format_parser.add_argument(
        "--allow-extension",
        action="append",
        default=[],
        help="Add a file extension to the allowed set",
    )
    format_parser.add_argument(
        "-f",
        "--files",
        nargs="*",
        default=[],
        type=Path,
        help="List of files to format",
    )
    format_parser.add_argument(
        "--stdin", action="store_true", help="Read stdin for list of files to format"
    )
    format_parser.add_argument(
        "--pass-through",
        nargs=argparse.REMAINDER,
        default=[],
        help="If specified, --pass-through must be the last argument. Remaining arguments passed to underlying executable",
    )
    return {
        "hash-to-file": run_hash_to_file,
        "info": run_info,
        "new": run_new,
        "format": run_code_format,
    }


def validate(parsed, unknown):
    """
    Validate rules to ensure that the args are properly consistent. This will also generate a set of validated arguments
    to pass to CMake. This allows these values to be created, defaulted, and validated in one place
    :param parsed: args to validate
    :param unknown: unknown arguments
    :return: cmake arguments to pass to CMake
    """
    # regex pattern to detect -D<CMAKE_ARGUMENT>[:<TYPE>]=<VALUE> arguments for CMake
    CMAKE_REG = re.compile(r"-D([a-zA-Z0-9_]+(?::[A-Z]+)?)=(.*)")
    cmake_args = {}
    make_args = {}
    # Check platforms for existing toolchain, unless the default is specified.
    if not hasattr(parsed, "command") or parsed.command is None:
        raise ArgValidationException("'fprime-util' not supplied sub-command argument")
    if parsed.command == "generate":
        d_args = {
            match.group(1): match.group(2)
            for match in [CMAKE_REG.match(arg) for arg in unknown]
            if match is not None
        }
        cmake_args.update(d_args)
        unknown = [arg for arg in unknown if not CMAKE_REG.match(arg)]
    # Build type only for generate, jobs only for non-generate
    elif parsed.command in [target.mnemonic for target in Target.get_all_targets()]:
        parsed.settings = None  # Force to load from cache if possible
        make_args["--jobs"] = 1 if parsed.jobs <= 0 else parsed.jobs
    # Check if any arguments are still unknown
    if unknown:
        runnable = f"{os.path.basename(sys.argv[0])} {parsed.command}"
        msg = f"'{runnable}' supplied invalid arguments: {','.join(unknown)}"
        raise ArgValidationException(msg)
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
        "-r",
        "--root",
        default=None,
        help="Root of CMake project to use. May contain multiple build directories.",
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
        description=HelpText.long("subparsers_description"), dest="command"
    )

    # Add all externally defined cli parser command to running functions
    runners = {}
    parsers = {}

    fbuild_runners, fbuild_parsers = add_fbuild_parsers(
        subparsers, common_parser, HelpText
    )
    fpp_runners, fpp_parsers = add_fpp_parsers(subparsers, common_parser)
    viz_runners, viz_parsers = add_fpp_viz_parsers(subparsers, common_parser)
    parsers.update(fbuild_parsers)
    parsers.update(fpp_parsers)
    parsers.update(viz_parsers)
    runners.update(fbuild_runners)
    runners.update(fpp_runners)
    runners.update(viz_runners)
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


class ArgValidationException(Exception):
    """An exception used for argument validation"""
