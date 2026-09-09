"""
Tests for fprime.util.cookiecutter_wrapper
"""

from pathlib import Path, PureWindowsPath
from unittest.mock import patch

import pytest

from fprime.util.cookiecutter_wrapper import (
    _safe_cmake_relpath,
    add_to_cmake,
    find_nearest_cmake_file,
    is_valid_name,
)


@pytest.fixture
def file_structure(tmp_path):
    """Pytest fixture for a temporary file structure"""
    proj_root = tmp_path
    component_dir = proj_root / "component"
    component_subdir = component_dir / "sub"
    deployment_dir = proj_root / "deployment"

    component_dir.mkdir()
    component_subdir.mkdir()
    deployment_dir.mkdir()

    (proj_root / "project.cmake").touch()
    (proj_root / "CMakeLists.txt").touch()

    return proj_root, component_dir, component_subdir, deployment_dir


def test_find_nearest_cmake_in_component_parent(file_structure):
    """Test finding CMakeLists.txt in a component's parent directory"""
    proj_root, component_dir, component_subdir, deployment_dir = file_structure
    (component_dir / "CMakeLists.txt").touch()

    found_path = find_nearest_cmake_file(component_subdir, deployment_dir, proj_root)
    assert found_path == (component_dir / "CMakeLists.txt")


def test_find_nearest_cmake_project_cmake(file_structure):
    """Test falling back to project.cmake"""
    proj_root, component_dir, component_subdir, deployment_dir = file_structure

    found_path = find_nearest_cmake_file(component_subdir, deployment_dir, proj_root)
    assert found_path == (proj_root / "project.cmake")


def test_find_nearest_cmake_no_file(file_structure):
    """Test returning None when no file is found"""
    proj_root, component_dir, component_subdir, deployment_dir = file_structure
    (proj_root / "project.cmake").unlink()
    (proj_root / "CMakeLists.txt").unlink()

    found_path = find_nearest_cmake_file(component_subdir, deployment_dir, proj_root)
    assert found_path is None


@pytest.mark.parametrize(
    "name",
    ["StarTrackerManager", "MyComponent", "_private", "A", "Gps2"],
)
def test_is_valid_name_accepts_fpp_identifiers(name):
    assert is_valid_name(name) == "valid"


@pytest.mark.parametrize(
    "name",
    [
        'x"); file(WRITE /tmp/pwned)',
        "foo;bar",
        "has space",
        "My-Comp",
        "123Foo",
        ".",
        "..",
        "a/b",
        "a\\b",
        "foo\nbar",
        "",
        "ns::Type",
    ],
)
def test_is_valid_name_rejects_non_identifiers(name):
    assert is_valid_name(name) != "valid"


@pytest.mark.parametrize(
    "name, offending",
    [("My-Comp", "-"), ("123Foo", "1"), ("has space", " "), ("", "")],
)
def test_is_valid_name_returns_offending_character(name, offending):
    assert is_valid_name(name) == offending


def test_is_valid_name_rejects_non_str():
    with pytest.raises(ValueError):
        is_valid_name(None)


@pytest.mark.parametrize(
    "rel",
    [
        "StarTrackerManager",
        "Attitude-Determination-Control/StarTrackerManager",
        "Components/Comm/GPSManager",
        "Flight Software/GNC/Gps",
        ".internal/Comp.v2/Gps",
        "Contrôle/Gps",
        "Sub (old)/Gps",
    ],
)
def test_safe_cmake_relpath_accepts_nested_dirs(rel):
    assert _safe_cmake_relpath(Path(rel)) == Path(rel).as_posix()


@pytest.mark.parametrize(
    "rel",
    [
        Path("..") / "etc",
        Path("foo") / ".." / "bar",
        Path("/tmp/outside"),
        Path('x"); file(WRITE /tmp/pwned)'),
        Path("foo;bar"),
        Path("${ENV{HOME}}/x"),
        Path("foo\\bar"),
        Path("foo\nbar"),
        Path("."),
    ],
)
def test_safe_cmake_relpath_rejects_injection(rel):
    with pytest.raises(ValueError):
        _safe_cmake_relpath(rel)


def test_add_to_cmake_writes_safe_line(tmp_path):
    cmake_file = tmp_path / "CMakeLists.txt"
    cmake_file.write_text("project(Test)\n")
    with patch("fprime.util.cookiecutter_wrapper.confirm", return_value=True):
        assert add_to_cmake(cmake_file, Path("Comm/SwitchManager"), tmp_path)
    content = cmake_file.read_text()
    assert (
        'add_fprime_subdirectory("${CMAKE_CURRENT_LIST_DIR}/Comm/SwitchManager/")\n'
        in content
    )


def test_add_to_cmake_refuses_injection(tmp_path):
    cmake_file = tmp_path / "CMakeLists.txt"
    cmake_file.write_text("project(Test)\n")
    with patch("fprime.util.cookiecutter_wrapper.confirm", return_value=True):
        assert (
            add_to_cmake(cmake_file, Path('x"); file(WRITE /tmp/pwned)'), tmp_path)
            is False
        )
    assert cmake_file.read_text() == "project(Test)\n"


def test_add_to_cmake_detects_existing_line(tmp_path):
    cmake_file = tmp_path / "CMakeLists.txt"
    existing = (
        'add_fprime_subdirectory("${CMAKE_CURRENT_LIST_DIR}/Comm/SwitchManager/")\n'
    )
    cmake_file.write_text("project(Test)\n" + existing)
    with patch("fprime.util.cookiecutter_wrapper.confirm") as confirm:
        assert add_to_cmake(cmake_file, Path("Comm/SwitchManager"), tmp_path)
    confirm.assert_not_called()
    assert cmake_file.read_text() == "project(Test)\n" + existing


def test_add_to_cmake_detects_legacy_windows_line(tmp_path):
    cmake_file = tmp_path / "CMakeLists.txt"
    legacy = (
        'add_fprime_subdirectory("${CMAKE_CURRENT_LIST_DIR}/Comm\\SwitchManager/")\n'
    )
    cmake_file.write_text("project(Test)\n" + legacy)
    # PureWindowsPath renders with backslashes on any host, like str(Path) on Windows
    with patch("fprime.util.cookiecutter_wrapper.confirm") as confirm:
        assert add_to_cmake(cmake_file, PureWindowsPath("Comm/SwitchManager"), tmp_path)
    confirm.assert_not_called()
    assert cmake_file.read_text() == "project(Test)\n" + legacy


def test_register_with_cmake_propagates_non_relative_error(tmp_path):
    from fprime.util.cookiecutter_wrapper import register_with_cmake

    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "CMakeLists.txt").write_text("project(Test)\n")
    proj_root = tmp_path / "proj"
    proj_root.mkdir()
    gen_path = outside / "NewComp"
    with (
        patch(
            "fprime.util.cookiecutter_wrapper.find_nearest_cmake_file",
            return_value=outside / "CMakeLists.txt",
        ),
        pytest.raises(ValueError),
    ):
        register_with_cmake(gen_path, proj_root, outside)
