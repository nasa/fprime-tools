""" fprime.util.cli: general CLI handling

Sets up parsers and processors for general CLI targets under fprime-util that do not fit elsewhere. Includes parsers
such as: hast-to-file, info, and others.

@author mstarch
"""
import argparse
import sys

from pathlib import Path
from typing import Dict, Callable
from fprime.fbuild.builder import Build, BuildType, InvalidBuildCacheException
from fprime.fbuild.interaction import new_component, new_port


def print_info(
    base: Build, parsed: argparse.Namespace, _: Dict[str, str], __: Dict[str, str]
):
    """Builds and prints the informational output block

    Handles the info command using the given build as a template to discover other build types. This will load the
    information and prints it to the screen.

    Args:
        base: base build used to find other builds including information
        parsed: parsed command namespace
        _: unused cmake arguments
        __: unused make arguments
    """
    build_types = BuildType.get_public_types()

    # Roll up targets for more concise display
    build_infos = {}
    local_generic_targets = set()
    global_generic_targets = set()
    # Loop through available builds and harvest targets
    for build_type in build_types:
        build = Build(base.build_type, base.deployment, verbose=parsed.verbose)
        try:
            build.load(parsed.platform)
        except InvalidBuildCacheException:
            print(
                f"[WARNING] No results for build type '{build_type.get_cmake_build_type()}', missing build cache."
            )
            continue
        build_info = build.get_build_info(Path(parsed.path))
        # Target list
        local_targets = {
            "'{}'".format(target) for target in build_info.get("local_targets", [])
        }
        global_targets = {
            "'{}'".format(target) for target in build_info.get("global_targets", [])
        }
        build_artifacts = (
            build_info.get("auto_location")
            if build_info.get("auto_location") is not None
            else "N/A"
        )
        local_generic_targets = local_generic_targets.union(local_targets)
        global_generic_targets = global_generic_targets.union(global_targets)
        build_infos[build_type] = build_artifacts

    # Print out directory and deployment target sections
    print(f"[INFO] Fprime build information:")
    print(f"    Available directory targets: {' '.join(local_generic_targets)}")
    print()
    print(f"    Available deployment targets: {' '.join(global_generic_targets)}")

    # Artifact locations come afterwards
    print("  ----------------------------------------------------------")
    for build_type, build_artifact_location in build_infos.items():
        print(
            f"    {build_type.get_cmake_build_type()} build cache: {build_artifact_location}"
        )
    print()


def hash_to_file(
    build: Build, parsed: argparse.Namespace, _: Dict[str, str], __: Dict[str, str]
):
    """Processes hash-to-file to locate file

    Args:
        build: build to search for hashes.txt
        parsed: parsed arguments for needed for parsed.hash
        _: unused cmake arguments
        __: unused make arguments
    """
    lines = build.find_hashed_file(parsed.hash)
    if not lines:
        raise InvalidBuildCacheException(
            "No hashes.txt found. Do you need '--ut' for a unittest run?"
        )
    print("[INFO] File(s) associated with hash 0x{:x}".format(parsed.hash))
    for line in lines:
        print("   ", line, end="")


def template(
    build: Build, parsed: argparse.Namespace, _: Dict[str, str], __: Dict[str, str]
):
    """Processes new command

    Args:
        build: build used to inform new component and new port calls
        parsed: parsed arguments
        _: unused cmake arguments
        __: unused make arguments
    """
    if parsed.component and not parsed.port:
        return new_component(build.deployment, parsed.platform, parsed.verbose, build)
    elif parsed.port and not parsed.component:
        return new_port(build.deployment, build)
    print("[ERROR] Use --component or --port, not both.", file=sys.stderr)


def add_special_parsers(
    subparsers, common: argparse.ArgumentParser
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
        help="Converts F prime build hash to filename.",
        parents=[common],
        add_help=False,
    )
    hash_parser.add_argument(
        "hash",
        type=lambda x: int(x, 0),
        help="F prime assert hash to associate with a file.",
    )

    # Add a search for hash function
    subparsers.add_parser(
        "info",
        help="Gets fprime-util contextual information.",
        parents=[common],
        add_help=False,
    )

    # New functionality
    new_parser = subparsers.add_parser(
        "new", help="Generate a new component", parents=[common], add_help=False
    )
    new_parser.add_argument(
        "--component",
        default=False,
        action="store_true",
        help="Tells the new command to generate a component",
    )
    new_parser.add_argument(
        "--port",
        default=False,
        action="store_true",
        help="Tells the new command to generate a port",
    )
    return {"hash-to-file": hash_to_file, "info": print_info, "new": template}
