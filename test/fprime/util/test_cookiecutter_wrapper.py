"""
Tests for fprime.util.cookiecutter_wrapper
"""

import pytest

from fprime.util.cookiecutter_wrapper import find_nearest_cmake_file


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
