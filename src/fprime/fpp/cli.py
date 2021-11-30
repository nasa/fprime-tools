""" fprime.fpp.cli: FPP command line targets

Processing and command line functions for FPP tools wrappers in fprime-util.

@mstarch
"""
import argparse
from pathlib import Path
from typing import Dict, Callable
from fprime.fbuild.builder import Build
from fprime.fpp.common import fpp_get_locations_file, fpp_dependencies, run_fpp_util


def run_fpp_locs(
    build: Build,
    parsed: argparse.Namespace,
    _: Dict[str, str],
    make_args: Dict[str, str],
):
    """Runs the fpp_locs command

    Args:
        build: build cache
        parsed: parsed arguments object
        _: cmake args, not used
        make_args: make arguments passed to the fpp-locs target
    """
    print(
        f"fpp Locations File: {fpp_get_locations_file(Path(parsed.path), build, make_args=make_args)}"
    )


def run_fpp_deps(
    build: Build,
    parsed: argparse.Namespace,
    _: Dict[str, str],
    make_args: Dict[str, str],
):
    """Runs the fpp_locs command

    Args:
        build: build cache
        parsed: parsed arguments object
        _: cmake args, not used
        make_args: make arguments passed to the fpp-locs target
    """
    print(
        f"fpp dependencies of {parsed.path}:\n{' '.join(str(item) for item in fpp_dependencies(parsed.path, build, make_args))}"
    )


def run_fpp_check(
    build: Build,
    parsed: argparse.Namespace,
    _: Dict[str, str],
    make_args: Dict[str, str],
):
    """Run fpp check application

    Handles the fpp-check endpoint by running the utility fpp-check.

    Args:
        build: build directory output
        parsed: parsed input arguments
        _: unused cmake_args
        make_args: unused make_args

    Returns:

    """
    run_fpp_util(
        parsed.path,
        build,
        make_args,
        "fpp-check",
        ["-u", parsed.unconnected] if parsed.unconnected else [],
    )


def add_fpp_parsers(subparsers, common: argparse.ArgumentParser) -> Dict[str, Callable]:
    """Sets up the fpp command line parsers

    Creates command line parsers for fpp commands and associates these commands to processing functions for those fpp
    commands.

    Args:
        subparsers: subparsers to add to
        common: common parser for all fprime-util commands

    Returns:
        Dictionary mapping command name to processor of that command
    """
    subparsers.add_parser(
        "fpp-locs",
        help="Regenerates the FPP locations file and prints the location",
        parents=[common],
        add_help=False,
    )
    subparsers.add_parser(
        "fpp-depends",
        help="Regenerates the build cache and prints located fpp dependencies",
        parents=[common],
        add_help=False,
    )
    check_parser = subparsers.add_parser(
        "fpp-check",
        help="Runs fpp-check utility",
        parents=[common],
        add_help=False,
    )
    check_parser.add_argument(
        "-u",
        "--unconnected",
        default=None,
        help="write unconnected ports to file",
    )
    return {
        "fpp-locs": run_fpp_locs,
        "fpp-depends": run_fpp_deps,
        "fpp-check": run_fpp_check,
    }
