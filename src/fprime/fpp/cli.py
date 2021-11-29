""" fprime.fpp.cli: FPP command line targets

Processing and command line functions for FPP tools wrappers in fprime-util.

@mstarch
"""
import argparse
from pathlib import Path
from typing import Dict, Callable
from fprime.fbuild.builder import Build, BuildType, InvalidBuildCacheException
from fprime.fpp.common import fpp_get_locations_file


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
    return {"fpp-locs": run_fpp_locs}
