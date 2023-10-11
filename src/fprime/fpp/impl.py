""" fprime.fpp.impl: Command line targets for `fprime-util impl`

Processing and CLI entry points for `fprime-util impl` command line tool.

@author chammard
"""


import argparse
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from typing import TYPE_CHECKING, Callable, Dict, List, Tuple

if TYPE_CHECKING:
    from fprime.fbuild.builder import Build

from fprime.fpp.common import FppUtility
from fprime.util.code_formatter import ClangFormatter


def fpp_generate_implementation(
    build: "Build",
    output_dir: Path,
    context: Path,
    apply_formatting: bool,
    ut: bool,
) -> int:
    """
    Generate implementation files from FPP templates.

    Args:
        build: Build object
        output_dir: The directory where the generated files will be written
        context: The path to the F´ module to generate files for
        apply_formatting: Whether to format the generated files using clang-format
        ut: Generates UT files if set to True
    """

    prefixes = [
        build.get_settings("framework_path", ""),
        *build.get_settings("library_locations", []),
        build.cmake_root,
        build.build_dir / "F-Prime",
        build.build_dir,
    ]

    # Holds the list of generated files to be passed to clang-format
    gen_files = tempfile.NamedTemporaryFile(prefix="fprime-impl-")

    output_path = Path(output_dir)
    if ut:
        output_path = output_path / "test/ut"
    output_path.mkdir(parents=True, exist_ok=True)

    # Run fpp-to-cpp --template
    FppUtility("fpp-to-cpp", imports_as_sources=False).execute(
        build,
        context,
        args=(
            {},
            [
                "--template",
                *(["--unit-test"] if ut else []),
                "--names",
                gen_files.name,
                "--directory",
                output_path,
                "--path-prefixes",
                ",".join(map(str, prefixes)),
            ],
        ),
    )

    # Format files if clang-format is available
    format_file = build.settings.get("framework_path", Path(".")) / ".clang-format"
    if not format_file.is_file():
        print(
            f"[INFO] .clang-format file not found at {format_file.resolve()}. Skipping formatting."
        )
        return 0

    clang_formatter = ClangFormatter("clang-format", format_file, {"backup": False})
    if apply_formatting and clang_formatter.is_supported():
        for line in gen_files.readlines():
            # FPP --names outputs a list of file names. output_dir is added to get relative path
            filename = Path(line.decode("utf-8").strip())
            clang_formatter.stage_file(output_path / filename)
        clang_formatter.execute(None, None, ({}, []))

    return 0


def run_fpp_impl(
    build: "Build",
    parsed: argparse.Namespace,
    _: Dict[str, str],
    __: Dict[str, str],
    ___: List[str],
):
    """

    Args:
        build: build object
        parsed: parsed input arguments
        _: unused cmake_args
        __: unused make_args
        ___: unused pass-through arguments
    """

    return fpp_generate_implementation(
        build,
        parsed.output_dir,
        parsed.path,
        not parsed.no_format,
        parsed.ut,
    )


def add_fpp_impl_parsers(
    subparsers, common: argparse.ArgumentParser
) -> Tuple[Dict[str, Callable], Dict[str, argparse.ArgumentParser]]:
    """Sets up the fprime-viz command line parsers

    Creates command line parsers for fprime-viz commands and associates these commands to processing functions for those fpp
    commands.

    Args:
        subparsers: subparsers to add to
        common: common parser for all fprime-util commands

    Returns:
        Tuple of dictionary mapping command name to processor, and command to parser
    """
    impl_parser = subparsers.add_parser(
        "fpp_impl",
        help="Generate implementation templates",
        parents=[common],
        add_help=False,
    )
    impl_parser.add_argument(
        "--output-dir",
        help="Directory to generate files in. Default: cwd",
        required=False,
        default=os.getcwd(),
    )
    impl_parser.add_argument(
        "--no-format",
        action="store_true",
        help="Disable formatting (using clang-format) of generated files",
        required=False,
    )
    return {"fpp_impl": run_fpp_impl}, {"fpp_impl": impl_parser}
