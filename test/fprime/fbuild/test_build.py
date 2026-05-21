"""
(test) fprime.build:

Tests the current F prime build module. Ensures that the selected singleton defines the minimum set of functions and
that they function as expected.

@author mstarch
"""

import os
import pathlib
from unittest.mock import patch

import fprime.fbuild.builder
import fprime.fbuild.cmake
import fprime.fbuild.types
import pytest


def get_cmake_builder():
    """Gets a CMake builder for these tests

    Returns:
        CMakeBuilder for testing
    """
    return fprime.fbuild.cmake.CMakeHandler()


def get_data_dir():
    """
    Gets directory containing test-data specific to the builder being tested. This will enable new implementers, should
    there be any, to implement their own build-directory structure.

    :return:
    """
    if type(get_cmake_builder()) is fprime.fbuild.cmake.CMakeHandler:
        return os.path.join(os.path.dirname(__file__), "cmake-data")
    msg = f"Test data directory not setup for {type(get_cmake_builder())} builder class"
    raise Exception(msg)


def test_hash_finder():
    """
    Tests that the hash finder works given a known builds.
    """
    local = pathlib.Path(os.path.dirname(__file__))
    dep_dir = local / "cmake-data" / "testbuild"
    builder = fprime.fbuild.builder.Build(
        fprime.fbuild.builder.BuildType.BUILD_NORMAL, dep_dir
    )
    builder.load(
        local, build_dir=dep_dir / "build-fprime-automatic-native", skip_validation=True
    )

    assert builder.find_hashed_file(0xDEADBEEF) == ["Abc: 0xdeadbeef\n"]
    assert builder.find_hashed_file(0xC0DEC0DE) == ["HJK: 0xc0dec0de\n"]


def test_needed_functions():
    """
    Test the needed functions for the given builder. This will ensure that the public interface to the builder is
    implemented as expected.
    """
    needed_funcs = [
        "get_include_info",
        "execute_known_target",
        "get_include_locations",
        "get_fprime_configuration",
    ]
    for func in needed_funcs:
        assert hasattr(get_cmake_builder(), func)


def test_get_fprime_configuration():
    """
    Tests the given fprime configuration fetcher. Required for other portion of the system.
    """
    configs = fprime.fbuild.cmake.CMakeHandler.CMAKE_LOCATION_FIELDS
    test_data = {
        "grand-unified": (
            "/home/user11/fprime/Ref/..",
            None,
            "/home/user11/fprime/Ref/..",
        ),
        "subdir": (
            "/home/user11/Proj",
            "/home/user11/Proj/lib1;/home/user11/Proj/lib2",
            "/home/user11/Proj/fprime",
        ),
        "external": ("/home/user11/Proj", "/opt/lib1;/opt/lib2", "/opt/fprime"),
    }
    for key in test_data:
        build_dir = os.path.join(get_data_dir(), key)
        # Test all path, truth pairs
        values = get_cmake_builder().get_fprime_configuration(configs, build_dir)
        assert values == test_data[key]


def test_get_include_locations():
    """
    Test all the include locations. This will ensure that values are properly read from a cache listing. This will
    support various other portions of the system, so debug here first.
    """
    test_data = {
        "grand-unified": ["/home/user11/fprime"],
        "subdir": [
            "/home/user11/Proj",
            "/home/user11/Proj/lib1",
            "/home/user11/Proj/lib2",
            "/home/user11/Proj/fprime",
        ],
        "external": ["/home/user11/Proj", "/opt/lib1", "/opt/lib2", "/opt/fprime"],
    }
    for key in test_data:
        build_dir = os.path.join(get_data_dir(), key)
        paths = list(get_cmake_builder().get_include_locations(build_dir))
        assert paths == test_data[key]


def test_get_include_info():
    """
    Tests that the include root function gets the expected value based on the path and build-directory setups.
    """
    # Test data setup, format build_dir to tuples of path, expected result. Note: None means expect Orphan exception
    test_data = {
        "grand-unified": [
            (
                "/home/user11/fprime/Svc/SomeComp1",
                ("Svc/SomeComp1", "/home/user11/fprime"),
            ),
            (
                "/home/user11/fprime/Ref/SomeComp2",
                ("Ref/SomeComp2", "/home/user11/fprime"),
            ),
            (
                "/home/user11/fprime/Ref/SomeComp2/../SomeComp1",
                ("Ref/SomeComp1", "/home/user11/fprime"),
            ),
            ("/home/user11/external-sw/NachoDeploy/SomeComp3", None),
        ],
        "subdir": [
            (
                "/home/user11/Proj/fprime/Svc/SomeComp1",
                ("Svc/SomeComp1", "/home/user11/Proj/fprime"),
            ),
            # An insidious case where the path contains a common prefix as another possible location without being an
            # exact directory.  Notice /home/user11/Proj/fprime-something/Comps/SomeComp1 contains a non-exact common
            # prefix with the directory /home/user11/Proj/fprime. i.e. /home/user11/Proj/fprime is a prefix but
            # /home/user11/Proj/fprime/ is not.
            (
                "/home/user11/Proj/fprime-something/Comps/SomeComp1",
                ("fprime-something/Comps/SomeComp1", "/home/user11/Proj"),
            ),
            ("/home/user11/Proj/Ref/SomeComp2", ("Ref/SomeComp2", "/home/user11/Proj")),
            (
                "/home/user11/Proj/Ref/SomeComp2/../../fprime/Svc/SomeComp1",
                ("Svc/SomeComp1", "/home/user11/Proj/fprime"),
            ),
            ("/home/user11/external-sw/NachoDeploy/SomeComp3", None),
        ],
        "external": [
            ("/opt/fprime/Svc/SomeComp1", ("Svc/SomeComp1", "/opt/fprime")),
            ("/home/user11/Proj/Ref/SomeComp2", ("Ref/SomeComp2", "/home/user11/Proj")),
            ("/opt/something/else/external-sw/NachoDeploy/SomeComp3", None),
        ],
    }
    # Run through all the above data look for matching answers
    for key in test_data:
        build_dir = os.path.join(get_data_dir(), key)
        # Test all path, truth pairs
        for path, truth in test_data.get(key):
            if truth is None:
                with pytest.raises(fprime.fbuild.cmake.CMakeOrphanException):
                    value = get_cmake_builder().get_include_info(path, build_dir)
            else:
                value = get_cmake_builder().get_include_info(path, build_dir)
                assert value == truth


def test_find_nearest_parent_project():
    """
    This will test the ability for the system to detect valid deployment directories
    """

    test_dir = pathlib.Path(get_data_dir())
    test_data = [
        ("testbuild/subdir1/subdir2/subdir3", "testbuild/subdir1/"),
        ("testbuild/subdir1/subdir2", "testbuild/subdir1/"),
        ("testbuild/", "testbuild/"),
        ("/nonexistent/dirone/someotherpath", None),
    ]
    for path, truth in test_data:
        path = test_dir / path
        if truth is not None:
            truth = test_dir / truth
            value = fprime.fbuild.builder.Build.find_nearest_parent_project(path)
            assert value == truth
        else:
            with pytest.raises(fprime.fbuild.builder.UnableToDetectProjectException):
                fprime.fbuild.builder.Build.find_nearest_parent_project(path)


def _make_build(tmp_path, locations_content=None):
    """Helper to create a Build with a minimal fake build cache directory.

    Bypasses CMake and settings loading to isolate _load_build_cache_locations.
    If locations_content is not None, writes it to fprime-locations.fprime-util
    inside tmp_path.
    """
    if locations_content is not None:
        (tmp_path / "fprime-locations.fprime-util").write_text(locations_content)
    with patch.object(fprime.fbuild.cmake.CMakeHandler, "__init__", lambda self: None):
        build = fprime.fbuild.builder.Build(
            fprime.fbuild.builder.BuildType.BUILD_NORMAL, tmp_path
        )
    build.build_dir = tmp_path
    build._build_cache_locations = build._load_build_cache_locations()
    return build


def test_get_build_cache_locations_no_file(tmp_path):
    """When fprime-locations.fprime-util is absent, fall back to F-Prime/ and build_dir."""
    build = _make_build(tmp_path)
    locations = build.get_build_cache_locations()
    assert locations == [
        (tmp_path / "F-Prime").resolve(),
        tmp_path.resolve(),
    ]


def test_get_build_cache_locations_with_file(tmp_path):
    """When fprime-locations.fprime-util exists, read paths from it."""
    # Create directories that will be listed in the file
    rel_dir = tmp_path / "my-lib"
    rel_dir.mkdir()
    abs_dir = tmp_path / "abs-lib"
    abs_dir.mkdir()

    content = f"# comment line\n my-lib\n\n{abs_dir}\n"
    build = _make_build(tmp_path, locations_content=content)
    locations = build.get_build_cache_locations()
    assert locations == [rel_dir.resolve(), abs_dir.resolve()]


def test_get_build_cache_locations_empty_file(tmp_path):
    """An empty locations file is a corrupt build cache and should raise."""
    with pytest.raises(fprime.fbuild.types.InvalidBuildCacheException):
        _make_build(tmp_path, locations_content="\n")


def test_get_build_cache_locations_no_valid_paths(tmp_path):
    """A file listing only non-existent (but in-cache) relative paths should raise."""
    with pytest.raises(fprime.fbuild.types.InvalidBuildCacheException):
        _make_build(tmp_path, locations_content="does-not-exist\n")


def test_get_build_cache_locations_comments_only(tmp_path):
    """A file with only comments and blank lines should raise."""
    with pytest.raises(fprime.fbuild.types.InvalidBuildCacheException):
        _make_build(tmp_path, locations_content="# just a comment\n\n  \n")


def test_get_build_cache_locations_stripped_spaces(tmp_path):
    """Lines with leading/trailing whitespace should be stripped correctly."""
    d = tmp_path / "spaced-lib"
    d.mkdir()
    build = _make_build(tmp_path, locations_content="  spaced-lib  \n")
    assert build.get_build_cache_locations() == [d.resolve()]


def test_get_build_cache_locations_mixed_valid_invalid(tmp_path):
    """Valid paths are kept; non-existent paths are silently filtered out."""
    valid = tmp_path / "exists"
    valid.mkdir()
    content = "exists\nmissing-dir\n"
    build = _make_build(tmp_path, locations_content=content)
    assert build.get_build_cache_locations() == [valid.resolve()]


def test_get_build_cache_locations_outside_build_dir(tmp_path):
    """A path resolving outside the build cache should raise (security)."""
    with pytest.raises(fprime.fbuild.types.InvalidBuildCacheException, match="outside"):
        _make_build(tmp_path, locations_content="../escape\n")
