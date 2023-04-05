""" fprime.util.commands: General-purpose command definitions

Defines general-purpose command processing. Those are commands that do not belong in fbuild or fpp.
Current commands include:
    - info: Prints out information about the build
    - hash-to-file: Processes hash-to-file to locate file
    - new: Creates a new component, port, or deployment
    - format: Formats code using clang-format

@author thomas-bc
"""

import argparse
import sys

from pathlib import Path
from typing import List, Dict

from fprime.fbuild.builder import Build, InvalidBuildCacheException
from fprime.fbuild.interaction import new_component, new_port, new_deployment, new_project

from fprime.util.code_formatter import ClangFormatter


def run_info(
    base: Build, parsed: argparse.Namespace, _: Dict[str, str], __: Dict[str, str], ___
):
    """Builds and prints the informational output block

    Handles the info command using the given build as a template to discover other build types. This will load the
    information and prints it to the screen.

    Args:
        base: base build used to find other builds including information
        parsed: parsed command namespace
        _: unused cmake arguments
        __: unused make arguments
        ___: unused pass through arguments
    """
    # Roll up targets for more concise display. Dictionaries are used as their keys become a set and as of Python 3.7
    # the native dictionary maintains ordering. Thus it acts as an "ordered set" for a nice predictable display order
    # derived from the order of target definitions.
    build_infos = {}
    local_generic_targets = {}
    global_generic_targets = {}
    # Loop through available builds and harvest targets
    for build in Build.get_build_list(base, parsed.build_cache):
        build_info = build.get_build_info(Path(parsed.path))
        # Target list
        local_targets = {
            f"'{target}'": "" for target in build_info.get("local_targets", [])
        }
        global_targets = {
            f"'{target}'": "" for target in build_info.get("global_targets", [])
        }
        build_artifacts = (
            build_info.get("auto_location")
            if build_info.get("auto_location") is not None
            else "N/A",
            build_info.get("build_dir", "Unknown"),
        )
        local_generic_targets.update(local_targets)
        global_generic_targets.update(global_targets)
        build_infos[build.build_type] = build_artifacts

    # Print out directory and deployment target sections
    if local_generic_targets.keys() or global_generic_targets.keys():
        print("[INFO] fprime build information:")
        print(
            f"    Available directory targets: {' '.join(local_generic_targets.keys())}"
        )
        print()
        print(
            f"    Available global targets: {' '.join(global_generic_targets.keys())}"
        )
        print(f'{"  ":-<60}')
    # Artifact locations come afterwards
    for (
        build_type,
        (build_artifact_location, global_build_cache),
    ) in build_infos.items():
        print(
            f"    {build_type.get_cmake_build_type()} build cache module directory: {build_artifact_location}"
        )
        print(
            f"    {build_type.get_cmake_build_type()} build cache: {global_build_cache}"
        )
    print()


def run_hash_to_file(
    build: Build, parsed: argparse.Namespace, _: Dict[str, str], __: Dict[str, str], ___
):
    """Processes hash-to-file to locate file

    Args:
        build: build to search for hashes.txt
        parsed: parsed arguments for needed for parsed.hash
        _: unused cmake arguments
        __: unused make arguments
        ___: unused pass through arguments
    """
    lines = build.find_hashed_file(parsed.hash)
    if not lines:
        raise InvalidBuildCacheException(
            f"Hash 0x{parsed.hash:x} not found. Do you need '--ut' for a unittest run?"
        )
    print("[INFO] File(s) associated with hash 0x{:x}".format(parsed.hash))
    for line in lines:
        print("   ", line, end="")


def run_new(
    build: Build, parsed: argparse.Namespace, _: Dict[str, str], __: Dict[str, str], ___
):
    """Processes new command

    Args:
        build: build used to inform new component and new port calls
        parsed: parsed arguments
        _: unused cmake arguments
        __: unused make arguments
        ___: unused pass through arguments
    """
    if parsed.component:
        return new_component(build.deployment, parsed.platform, parsed.verbose, build)
    if parsed.port:
        return new_port(build.deployment, build)
    if parsed.deployment:
        return new_deployment(parsed)
    if parsed.project:
        return new_project(parsed)
    raise NotImplementedError(
        "`fprime-util new` target is missing or not implemented. See usage (--help)."
    )


def run_code_format(
    build: Build,
    parsed: argparse.Namespace,
    _: Dict[str, str],
    __: Dict[str, str],
    ___: List[str],
):
    """Runs code formatting using clang-format

    Args:
        build: used to retrieve .clang-format file
        parsed: parsed input arguments
        __: unused cmake_args
        ___: unused make_args
        ____: unused pass-through arguments
    """
    options = {
        "verbose": not parsed.quiet,
        "backup": not parsed.no_backup,
        "validate_extensions": not parsed.force,
    }
    clang_formatter = ClangFormatter(
        "clang-format",
        build.settings.get("framework_path", Path(".")) / ".clang-format",
        options,
    )
    if not clang_formatter.is_supported():
        print(
            f"[ERROR] Cannot find executable: {clang_formatter.executable}. Unable to run formatting.",
            file=sys.stderr,
        )
        return 1
    # Allow requested file extensions
    for file_ext in parsed.allow_extension:
        clang_formatter.allow_extension(file_ext)
    # Stage all files that are passed through stdin, if requested
    if parsed.stdin:
        for filename in sys.stdin.read().split():
            clang_formatter.stage_file(Path(filename))
    # Stage all files that are passed through --files
    for filename in parsed.files:
        clang_formatter.stage_file(Path(filename))
    return clang_formatter.execute(build, parsed.path, ({}, parsed.pass_through))
