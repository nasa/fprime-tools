""" fprime.fpp.cli: FPP command line targets

Processing and command line functions for FPP tools wrappers in fprime-util.

@mstarch
"""

import argparse
from typing import Callable, Dict, List, Tuple

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


def run_fpp_to_xml(
    build: "Build",
    parsed: argparse.Namespace,
    _: Dict[str, str],
    __: Dict[str, str],
    ___: List[str],
):
    """Run the fpp-to-xml utility

    Args:
        build: build directory output
        parsed: parsed input arguments
        _: unused cmake_args
        __: unused make_args
        ___: unused pass-through arguments
    """
    FppUtility("fpp-to-xml").execute(
        build,
        parsed.path,
        args=({}, ["--directory", parsed.directory] if parsed.directory else []),
    )


def run_fpp_to_dict(
    build: "Build",
    parsed: argparse.Namespace,
    _: Dict[str, str],
    __: Dict[str, str],
    ___: List[str],
):
    """Run the fpp-to-xml utility

    Args:
        build: build directory output
        parsed: parsed input arguments
        _: unused cmake_args
        __: unused make_args
        ___: unused pass-through arguments
    """
    FppUtility("fpp-to-dict", imports_as_sources=False).execute(
        build,
        parsed.path,
        args=(
            {},
            [
                *(["--directory", parsed.directory] if parsed.directory else []),
                *(["--size", parsed.size] if parsed.size else []),
            ],
        ),
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
        "fpp-check", help="Run fpp-check utility", parents=[common], add_help=False
    )
    check_parser_group = check_parser.add_argument_group("fpp-check arguments")
    check_parser_group.add_argument(
        "-u", "--unconnected", default=None, help="write unconnected ports to file"
    )

    fpp_to_xml_parser = subparsers.add_parser(
        "fpp-to-xml", help="Run fpp-to-xml utility", parents=[common], add_help=False
    )
    fpp_to_xml_group = fpp_to_xml_parser.add_argument_group("fpp-to-xml arguments")
    fpp_to_xml_group.add_argument("-d", "--directory", help="Output directory")

    fpp_to_dict_parser = subparsers.add_parser(
        "fpp-to-dict", help="Run fpp-to-dict utility", parents=[common], add_help=False
    )
    fpp_to_dict_group = fpp_to_dict_parser.add_argument_group("fpp-to-dict arguments")
    fpp_to_dict_group.add_argument("-d", "--directory", help="Output directory")
    fpp_to_dict_group.add_argument("-s", "--size", help="Default string size")

    return {
        "fpp-check": run_fpp_check,
        "fpp-to-xml": run_fpp_to_xml,
        "fpp-to-dict": run_fpp_to_dict,
    }, {
        "fpp-check": check_parser,
        "fpp-to-xml": fpp_to_xml_parser,
        "fpp-to-dict": fpp_to_dict_parser,
    }
