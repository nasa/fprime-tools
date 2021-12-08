"""
Common implementations for FPP tool wrapping

@author mstarch
"""
import subprocess
import sys
from typing import List, Dict
from pathlib import Path

from fprime.common.error import FprimeException
from fprime.fbuild.builder import Build, BuildType, GlobalTarget
from fprime.fbuild.cmake import CMakeExecutionException

FPP_TARGETS = [GlobalTarget("fpp-locs", "Generate/regenerate the fpp-locs file")]
FPP_LOCS_DIR = "fpp-locs"


def fpp_get_locations_file(
    cwd: Path, build: Build, make_args: Dict[str, str], refresh: bool = True
) -> Path:
    """
    Refreshes the fpp locations file and returns the path to it

    Given a build setup, this will update the FPP locations file to ensure it is accurate and then returns the path of
    the FPP locations file.

    Args:
        cwd: current working directory
        build: build cache of the current directory
        make_args: arguments to pass to the make system
        refresh: force an update to the fpp locs file
    Returns:
        path to the fpp locations file
    """
    fpp_build_cache_path = build.build_dir / FPP_LOCS_DIR
    if refresh:
        locs_cache = Build(
            BuildType.BUILD_FPP_LOCS, build.deployment, build.cmake.verbose
        )
        locs_cache.load(build.platform, build_dir=fpp_build_cache_path)
        print("[INFO] Updating fpp locations file. This may take some time.")
        locs_cache.execute(FPP_TARGETS[0], context=Path(cwd), make_args=make_args)
    return fpp_build_cache_path / "locs.fpp"


def fpp_dependencies(cwd: Path, build: Build, make_args: Dict[str, str]) -> List[Path]:
    """
    Gets a list of FPP paths that are dependencies of the current module

    Mines the dependencies from the memo file within the build cache. This is done because there is no clean way to get
    a list of autocoder sources from within the build system for external use, however; the memo file acts like an
    export of the information we do need. This function extracts that.

    Args:
        cwd: current working directory
        build: build cache used for work
        make_args: make arguments

    Returns:
        List of paths to fpp file dependencies of the given directory
    """
    # Force a refresh of the cache, to ensure the memo file is updated and as a by-product the locs file is updated
    print(
        "[INFO] Updating fpp locations file and build cache. This may take some time."
    )
    try:
        build.cmake.cmake_refresh_cache(build.build_dir)
        build_info = build.get_build_info(cwd)
    except CMakeExecutionException as error:
        print("".join(error.stderr), file=sys.stderr)
        raise

    directory_info = build_info.get("auto_location")
    if not directory_info:
        raise FppCannotException(
            "Could not find build cache folder. Perhaps directory is outside build?"
        )
    deps_file = directory_info / "autocoder" / "fpp.multiple.dep"
    if not deps_file.exists():
        raise FppCannotException(
            "No fpp dependency memo found. Perhaps directory is outside build?"
        )
    with open(deps_file, "r") as file_handle:
        lines = file_handle.readlines()
    if len(lines) < 4:
        raise FppCannotException(
            "No fpp dependency memo malformed. Purge and regenerate?"
        )
    make_paths = lambda line: [
        Path(item) for item in line.strip().split(";") if item.endswith(".fpp")
    ]
    all_paths = make_paths(lines[2]) + make_paths(lines[3])
    return all_paths


def run_fpp_util(
    cwd: Path, build: Build, make_args: Dict[str, str], util: str, util_args: List[str]
):

    dependencies = fpp_dependencies(cwd, build, make_args)
    locs_file = fpp_get_locations_file(
        cwd, build, make_args, False
    )  # Avoid refresh iff after fpp_dependencies

    app_args = [util] + util_args + [str(item) for item in ([locs_file] + dependencies)]
    if build.cmake.verbose:
        print(f"[FPP] '{' '.join(app_args)}'")
    return subprocess.run(app_args, capture_output=False)


class FppCannotException(FprimeException):
    """Cannot run fpp"""
