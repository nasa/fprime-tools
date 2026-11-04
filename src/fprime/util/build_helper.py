"""
fprime.util.build_helper.py

This script is defined to help users run standard make processes using CMake. This will support migrants from the old
make system, as well as enable more efficient practices when developing in the CMake system. The following functions
are supported herein:

 - build: build the current directory/module/deployment
 - impl: make implementation templates
 - testimpl: make testing templates
 - build_ut: build the current UTs
 - check: run modules unit tests

@author mstarch
"""

import re
from pathlib import Path

from fprime.fbuild.builder import Build, BuildType
from fprime.fbuild.cli import get_target
from fprime.fbuild.target import NoSuchTargetException

from .versioning import VersionException, get_version, FPRIME_PIP_PACKAGES

import importlib.metadata


def package_version_check(package: str, requirement_path: Path):
    """Checks the version of the packages installed match the expected packages of the fprime aggregate package"""
    expected_version = get_version(package, requirement_path).lstrip(
        "v"
    )  # Python version
    try:
        ver = importlib.metadata.version(package)
        if ver != expected_version:
            print(
                f"[WARNING] {package} has unexpected version. Expected: {expected_version} found {ver}"
            )
    except importlib.metadata.PackageNotFoundError:
        print(f"[WARNING] {package} is not installed")


def validate_tools_from_requirements(build: Build):
    """Uses build settings to find requirements file and validate the correct versions installed"""
    # Find prioritized order of requirements.txt, ensuring that each member exists
    possibilities = [
        build.settings.get("project_root", None),
        build.settings.get("framework_path", None),
    ]
    possibilities = [
        Path(possible) / "requirements.txt"
        for possible in possibilities
        if possible is not None
    ]
    possibilities = [possible for possible in possibilities if possible.exists()]
    # Skip tools check, as not requirements.txt found
    if not possibilities:
        print(
            f"[WARNING] Could not find 'requirements.txt' in: {possibilities}. Will not check tool versions."
        )
        return
    # Now check each required tool for fprime
    for tool in FPRIME_PIP_PACKAGES:
        for possible in possibilities:
            try:
                package_version_check(tool, possible)
                break
            except (OSError, VersionException) as exc:
                message = f"[WARNING] {exc}"
        else:
            print(message)


def parse_gitmodules(gitmodules_path: Path):
    """Parse a .gitmodules file and return a list of submodule paths.

    Args:
        gitmodules_path: path to the .gitmodules file

    Returns:
        list of submodule path strings relative to the .gitmodules parent directory
    """
    if not gitmodules_path.is_file():
        return []
    content = gitmodules_path.read_text()
    return [
        match.strip()
        for match in re.findall(r"^\s*path\s*=\s*(.+)", content, re.MULTILINE)
    ]


def validate_submodules(build: Build):
    """Check for uninitialized git submodules.

    Parses .gitmodules in the project root and framework path, and warns about any
    submodule whose directory is empty or missing. Does not attempt to correct the
    problem. Silently skips if no .gitmodules file exists.
    """
    try:
        _check_submodules(build)
    except (OSError, UnicodeDecodeError):
        pass  # Advisory only — never block the build


def _check_submodules(build: Build):
    """Internal implementation of submodule validation."""
    project_root = build.settings.get("project_root", None)
    framework_path = build.settings.get("framework_path", None)

    # Collect unique roots to check for .gitmodules
    roots_to_check = []
    if project_root is not None:
        roots_to_check.append(Path(project_root))
    if framework_path is not None:
        fw = Path(framework_path)
        if fw not in roots_to_check:
            roots_to_check.append(fw)

    # Check submodules declared in .gitmodules
    for root in roots_to_check:
        gitmodules_file = root / ".gitmodules"
        submodule_paths = parse_gitmodules(gitmodules_file)
        for sub_path in submodule_paths:
            full_path = root / sub_path
            if full_path.is_dir():
                if not any(full_path.iterdir()):
                    print(
                        f"[WARNING] Git submodule '{sub_path}' appears uninitialized "
                        f"(directory is empty): {full_path}\n"
                        f"  Run 'git submodule update --init --recursive' to initialize submodules."
                    )
            elif not full_path.exists():
                print(
                    f"[WARNING] Git submodule '{sub_path}' directory does not exist: {full_path}\n"
                    f"  Run 'git submodule update --init --recursive' to initialize submodules."
                )


def load_build(parsed, skip_validation=False):
    """
    Loads Build object and returns it to the caller. Additionally, this will validate the
    installed tool versions (such as fpp and other F' utilities) against the requirements.txt
    """

    try:
        target = get_target(parsed)
        build_type = target.build_type
    except NoSuchTargetException:
        build_type = BuildType.BUILD_TESTING if parsed.ut else BuildType.BUILD_NORMAL

    cmake_root = (
        Path(parsed.root)
        if parsed.root is not None
        else Build.find_nearest_parent_project(Path.cwd())
    )

    build = Build(build_type, cmake_root, verbose=parsed.verbose)

    # All commands need to load the build cache to setup the basic information for the build with the exception of
    # generate, which is run before the creation of the build cache and thus must invent the cache instead. This
    # call will ensure the build is in a ready state before attempting to check tool versions and run the command.
    #
    # Some commands, like purge and info, run on sets of directories and will attempt to load those sets later.
    # However, the base directory must be setup here. Errors in this load are ignored to allow the command to find
    # build caches related to that set.
    if parsed.command == "generate":
        preset = getattr(parsed, "preset", None)
        build.invent(
            parsed.platform,
            build_dir=parsed.build_cache,
            force=parsed.force,
            preset=preset,
        )
    else:
        build.load(
            parsed.platform,
            parsed.build_cache,
            skip_validation=skip_validation,
        )
    validate_tools_from_requirements(build)
    validate_submodules(build)
    return build
