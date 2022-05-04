""" fprime.fpp.cli: FPP command line targets

Processing and command line functions for FPP tools wrappers in fprime-util.

@mstarch
"""
import argparse
from typing import Dict, List, Tuple, Callable
from fprime.fpp.common import FppUtility


def run_fpp_check(
    build: "Build",
    parsed: argparse.Namespace,
    _: Dict[str, str],
    __: Dict[str, str],
    ___: List[str],
):
    """Run fpp check application

    Handles the fpp-check endpoint by running the utility fpp-check.

    Args:
        build: build directory output
        parsed: parsed input arguments
        _: unused cmake_args
        __: unused make_args
        ___: unused pass-through arguments
    """
    FppUtility("fpp-check").execute(
        build,
        parsed.path,
        args=({}, ["-u", parsed.unconnected] if parsed.unconnected else []),
    )


def add_fpp_parsers(
    subparsers, common: argparse.ArgumentParser
) -> Tuple[Dict[str, Callable], Dict[str, argparse.ArgumentParser]]:
    """Sets up the fpp command line parsers

    Creates command line parsers for fpp commands and associates these commands to processing functions for those fpp
    commands.

    Args:
        subparsers: subparsers to add to
        common: common parser for all fprime-util commands

    Returns:
        Tuple of dictionary mapping command name to processor, and command to parser
    """
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
        "fpp-check": run_fpp_check,
    }, {"fpp-check": check_parser}
