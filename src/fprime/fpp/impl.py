""" fprime.fpp.impl: Command line targets for `fprime-util impl`

Processing and CLI entry points for `fprime-util impl` command line tool.

@author thomas-bc
"""

import argparse
import os
import tempfile
from pathlib import Path

from typing import TYPE_CHECKING, Callable, Dict, List, Tuple

if TYPE_CHECKING:
    from fprime.fbuild.builder import Build

from fprime.fpp.common import FppUtility
from fprime.util.code_formatter import ClangFormatter
from fprime.constants import UT_FILES_TARGET_PATH, UT_TEMPLATE_FILE_SUFFIX


def _apply_clang_formatting(framework_path, files_dir, generated_file_names):
    """
    Format files if clang-format is available.

    Args:
        framework_path: F Prime framework path
        files_dir: Folder with generated files
        generated_file_names: List of generated file names
    """

    format_file = framework_path / ".clang-format"
    if format_file.is_file():
        clang_formatter = ClangFormatter("clang-format", format_file, {"backup": False})
        if clang_formatter.is_supported():
            for file_name in generated_file_names:
                clang_formatter.stage_file(files_dir / file_name)
            clang_formatter.execute(None, None, ({}, []))
    else:
        print(
            f"[INFO] .clang-format file not found at {format_file.resolve()}. Skipping formatting."
        )


def _move_ut_templates(files_dir, generated_file_names):
    """
    Move generated UT templates into "files_dir/<UT_FILES_TARGET_PATH>".
    The UT_TEMPLATE_FILE_SUFFIX is added into a file name unless it is already present.

    Args:
        files_dir: Folder with generated files
        generated_file_names: List of generated file names
    """
    # Create the UT folder
    ut_path = files_dir / Path(*UT_FILES_TARGET_PATH)
    ut_path.mkdir(parents=True, exist_ok=True)

    # Move the generated files
    for file_name in generated_file_names:
        source_path = files_dir / file_name
        destination_file_name = (
            file_name.with_suffix(UT_TEMPLATE_FILE_SUFFIX + file_name.suffix)
            if UT_TEMPLATE_FILE_SUFFIX not in file_name.suffixes
            else file_name
        )
        destination_path = ut_path / destination_file_name
        source_path.rename(destination_path)


def fpp_generate_implementation(
    build: "Build",
    output_dir: Path,
    context: Path,
    apply_formatting: bool,
    generate_ut: bool,
    generate_test_helpers: bool = False,
) -> int:
    """
    Generate implementation files from FPP templates.

    Args:
        build: Build object
        output_dir: The directory where the generated files will be written
        context: The path to the F´ module to generate files for
        apply_formatting: Whether to format the generated files using clang-format
        generate_ut: Generates UT files if set to True
        generate_test_helpers: Generate of test helper code if set to True
    """

    prefixes = [
        build.get_settings("framework_path", ""),
        *build.get_settings("library_locations", []),
        build.get_settings("project_root", ""),
        build.build_dir / "F-Prime",
        build.build_dir,
    ]

    # Holds the list of generated files to be passed to clang-format
    gen_files = tempfile.NamedTemporaryFile(prefix="fprime-impl-")

    output_dir.mkdir(parents=True, exist_ok=True)

    # Run fpp-to-cpp --template
    FppUtility("fpp-to-cpp", imports_as_sources=False).execute(
        build,
        context,
        args=(
            {},
            [
                "--template",
                *(["--unit-test"] if generate_ut else []),
                *(["--auto-test-helpers"] if not generate_test_helpers else []),
                "--names",
                gen_files.name,
                "--directory",
                str(output_dir),
                "--path-prefixes",
                ",".join(map(str, prefixes)),
            ],
        ),
    )

    framework_path = build.settings.get("framework_path", Path("."))
    # FPP --names outputs a list of file names.
    generated_file_names = [
        Path(line.decode("utf-8").strip()) for line in gen_files.readlines()
    ]

    if apply_formatting:
        _apply_clang_formatting(framework_path, output_dir, generated_file_names)

    if generate_ut:
        _move_ut_templates(output_dir, generated_file_names)

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
        Path(parsed.output_dir),
        Path(parsed.path),
        not parsed.no_format,
        parsed.ut,
        parsed.generate_test_helpers,
    )


def add_fpp_impl_parsers(
    subparsers, common: argparse.ArgumentParser
) -> Tuple[Dict[str, Callable], Dict[str, argparse.ArgumentParser]]:
    """Sets up the fprime-viz command line parsers

    Creates command line parsers for fprime-viz commands and associates these commands to processing
    functions for those fpp commands.

    Args:
        subparsers: subparsers to add to
        common: common parser for all fprime-util commands

    Returns:
        Tuple of dictionary mapping command name to processor, and command to parser
    """
    impl_parser = subparsers.add_parser(
        "impl",
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
    impl_parser.add_argument(
        "--generate-test-helpers",
        action="store_true",
        default=False,
        help="Generate test helper code for hand-coding. Default to False, leveraging the test helpers autocoded by FPP.",
        required=False,
    )
    return {"impl": run_fpp_impl}, {"impl": impl_parser}
