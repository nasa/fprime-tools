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
from pathlib import Path

from fprime.fbuild.target import NoSuchTargetException
from fprime.fbuild.builder import Build, BuildType
from .versioning import get_version, VersionException
from fprime.fbuild.cli import get_target

# Attempt to get pkg_resources from "setuptools"
try:
    import pkg_resources
except ImportError:
    pkg_resources = None


def package_version_check(package: str, requirement_path: Path):
    """Checks the version of the packages installed match the expected packages of the fprime aggregate package"""
    expected_version = get_version(package, requirement_path).lstrip(
        "v"
    )  # Python version
    try:
        version = pkg_resources.get_distribution(package).version
        if version != expected_version:
            print(
                f"[WARNING] {package} has unexpected version. Expected: {expected_version} found {version}"
            )
    except pkg_resources.DistributionNotFound:
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
    # Pre-roll import errors from pkg_resources
    if pkg_resources is None:
        print("[WARNING] Cannot import 'pkg_resources'. Will not check tool versions.")
        return

    # Now check each required tool for fprime
    tools = ["fprime-fpp", "fprime-tools", "fprime-gds"]
    for tool in tools:
        for possible in possibilities:
            try:
                package_version_check(tool, possible)
                break
            except (OSError, VersionException) as exc:
                message = f"[WARNING] {exc}"
        else:
            print(message)


def load_build(parsed):
    """
    Loads Build object and returns it to the caller. Additionally, this will validate the
    installed tool versions (such as fpp and other F' utilitiles) against the requirements.txt
    """

    try:
        target = get_target(parsed)
        build_type = target.build_type
    except NoSuchTargetException:
        build_type = (
            BuildType.BUILD_TESTING if parsed.ut else BuildType.BUILD_NORMAL
        )

    deployment = (
        Path(parsed.deploy)
        if parsed.deploy is not None
        else Build.find_nearest_deployment(Path.cwd())  # Deployments look in CWD
    )

    build = Build(build_type, deployment, verbose=parsed.verbose)

    # All commands need to load the build cache to setup the basic information for the build with the exception of
    # generate, which is run before the creation of the build cache and thus must invent the cache instead. This
    # call will ensure the build is in a ready state before attempting to check tool versions and run the command.
    #
    # Some commands, like purge and info, run on sets of directories and will attempt to load those sets later.
    # However, the base directory must be setup here. Errors in this load are ignored to allow the command to find
    # build caches related to that set.
    if parsed.command == "generate":
        build.invent(parsed.platform, build_dir=parsed.build_cache)
    else:
        does_not_need_cache_directory = parsed.command in [
            "purge",
            "info",
            "format",
        ]
        build.load(
            parsed.platform,
            parsed.build_cache,
            skip_validation=does_not_need_cache_directory,
        )
    validate_tools_from_requirements(build)
    return build
