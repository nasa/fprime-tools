"""
Common implementations for FPP tool wrapping

@author mstarch
"""
from typing import List, Dict
from pathlib import Path
from fprime.fbuild.builder import Build, BuildType, GlobalTarget

FPP_TARGETS = [GlobalTarget("fpp-locs", "Generate/regenerate the fpp-locs file")]
FPP_LOCS_DIR = "fpp-locs"


def fpp_get_locations_file(
    cwd: Path, build_cache: Build, make_args: Dict[str, str]
) -> Path:
    """
    Refreshes the fpp locations file and returns the path to it

    Given a build setup, this will update the FPP locations file to ensure it is accurate and then returns the path of
    the FPP locations file.

    Args:
        cwd: current working directory
        build_cache: build cache of the current directory
        make_args: arguments to pass to the make system
    Returns:
        path to the fpp locations file
    """
    fpp_build_cache_path = build_cache.build_dir / FPP_LOCS_DIR
    locs_cache = Build(
        BuildType.BUILD_FPP_LOCS, build_cache.deployment, build_cache.cmake.verbose
    )
    locs_cache.load(build_cache.platform, build_dir=fpp_build_cache_path)

    locs_cache.execute(FPP_TARGETS[0], context=Path(cwd), make_args=make_args)
    return fpp_build_cache_path / "locs.fpp"


def fpp_dependencies(
    cwd: Path, build_cache: Build, make_args: Dict[str, str]
) -> List[Path]:
    """
    Gets a list of FPP paths that are dependencies of the current module

    TODO: fill in a full description here

    Args:
        cwd: current working directory
        build_cache: build cache used for work
        make_args: make arguments

    Returns:
        List of paths to fpp file dependencies of the given directory
    """
    return []


def fpp_check(cwd: Path, build_cache: Build, make_args: Dict[str, str]) -> List[Path]:
    """TODO:"""
    dependencies = fpp_dependencies(cwd, build_cache, make_args)
    # TODO: run fpp-check here.
