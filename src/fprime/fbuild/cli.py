""" fprime.fbuild.cli: fbuild command line processing

Command line processing functions for fbuild (fprime build system targets) of "generate", "purge", and build system
target operations.

@author mstarch
"""
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Callable
from fprime.fbuild.builder import Target, BuildType, Build
from fprime.fbuild.interaction import confirm


def get_target(parsed: argparse.Namespace) -> Target:
    """Gets the target given the argparse namespace

    Takes the parsed namespace and processes it to a known matching target.

    Args:
        parsed: argparse namespace to read values from

    Returns:
        target that can support the given supplied namespace
    """
    mnemonic = parsed.command
    flags = {
        flag for flag in Target.get_all_possible_flags() if getattr(parsed, flag, False)
    }
    return Target.get_target(mnemonic, flags)


def run_fbuild_cli(
    build: Build,
    parsed: argparse.Namespace,
    cmake_args: Dict[str, str],
    make_args: Dict[str, str],
):
    """Execution of the fbuild commands

    Args:
        build: build object, pre-loaded, iff not "generate" or "purged"
        parsed: parsed arguments object.
        cmake_args: cmake commands from parsed output
        make_args: arguments to the make system
    """
    if parsed.command == "generate":
        build.invent(parsed.platform, build_dir=parsed.build_cache)
        toolchain = build.find_toolchain()
        print(f"[INFO] Generating build directory at: {build.build_dir}")
        print(f"[INFO] Using toolchain file {toolchain} for platform {parsed.platform}")
        if toolchain is not None:
            cmake_args.update({"CMAKE_TOOLCHAIN_FILE": toolchain})
        build.generate(cmake_args)
    elif parsed.command == "purge":
        # Since purge does not load its "base", we need to overload the platform
        build.platform = parsed.platform
        for purge_build in Build.get_build_list(build, parsed.build_cache):
            print(
                f"[INFO] {parsed.command.title()} build directory at: {purge_build.build_dir}"
            )
            if parsed.force or confirm("Purge this directory (yes/no)?"):
                purge_build.purge()
            install_dir = purge_build.install_dest_exists()
            if (
                purge_build.build_type != BuildType.BUILD_CUSTOM
                and install_dir
                and install_dir.exists()
            ):
                print(
                    f"[INFO] {parsed.command.title()} install directory at: {install_dir}"
                )
                if parsed.force or confirm(
                    f"Purge installation directory at {install_dir} (yes/no)?"
                ):
                    purge_build.purge_install()
    else:
        target = get_target(parsed)
        build.execute(target, context=Path(parsed.path), make_args=make_args)


def add_target_parser(
    target: Target,
    subparsers,
    common: argparse.ArgumentParser,
    existing: Dict[str, Tuple[argparse.ArgumentParser, List[str]]],
) -> str:
    """Add a subparser for a given build target

    For a given build target, construct an argument parser with mnemonic as subcommand and needed flags. Then add it as
    a subparser to the global parent. If it already exists in existing, then just add non-existent flags/

    Args:
        target:     target for building a new subparser
        subparsers: argument parser to add a subparser to
        common:     common subparser to be used as parent carrying common flags
        existing:   dictionary storing the mnemonic to parser and flags tuple

    Returns:
        Name of the command this parser handles

    Notes:
        This functions has side effects of editing existing and the list of subparsers
    """
    if target.mnemonic not in existing:
        parser = subparsers.add_parser(
            target.mnemonic,
            parents=[common],
            add_help=False,
            help=f"{target.desc} in the specified directory",
        )
        # --ut flag also exists at the global parsers, skip adding it
        existing[target.mnemonic] = (parser, ["ut"])
        # Common target-only items
        parser.add_argument(
            "-j",
            "--jobs",
            default=1,
            type=int,
            help="Parallel build job count. Default: %(default)s.",
        )
    parser, flags = existing[target.mnemonic]
    new_flags = [flag for flag in target.flags if flag not in flags]
    for flag in new_flags:
        parser.add_argument(
            f"--{flag}", action="store_true", default=False, help=target.desc
        )
    flags.extend(new_flags)
    return target.mnemonic


def add_special_targets(subparsers, common: argparse.ArgumentParser) -> List[str]:
    """Add in generate and purge commands

    Args:
        subparsers: subparsers used to create new subparsers
        common: common parser

    Returns:
        ["generate", "purge"] list of special targets
    """
    generate_parser = subparsers.add_parser(
        "generate",
        help="Generate a build cache directory. Defaults to generating a release build cache",
        parents=[common],
        add_help=False,
    )
    generate_parser.add_argument(
        "-Dxyz",
        action="append",
        help="Pass -D flags through to CMakes",
        nargs=1,
        default=[],
    )
    purge_parser = subparsers.add_parser(
        "purge",
        help="Purge build cache directories",
        add_help=False,
        parents=[common],
    )
    purge_parser.add_argument(
        "-f",
        "--force",
        default=False,
        action="store_true",
        help="Purges the build directory by force. No confirmation will be requested.",
    )
    return ["generate", "purge"]


def add_fbuild_parsers(
    subparsers, common: argparse.ArgumentParser
) -> Dict[str, Callable]:
    """Add in the build-system targets: generate, purge, and all build endpoints

    Sets up the targets used to generate and run the build system. This includes the purge command for cleaning up. This
    wraps up all targets defined in the targets list in fprime.fbuild.builder

    Args:
        subparsers: subparsers object used to add subparsers to the global CLI
        common: common parser used to add all common arguments

    Returns:
        Dictionary mapping command name to the function used to process the commands execution
    """
    parsers = {}
    run_map = {
        add_target_parser(target, subparsers, common, parsers): run_fbuild_cli
        for target in Target.get_all_targets()
    }
    run_map.update(
        {command: run_fbuild_cli for command in add_special_targets(subparsers, common)}
    )
    return run_map
