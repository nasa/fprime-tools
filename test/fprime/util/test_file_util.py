"""
(test) fprime.util.file_util:

Tests the file utility functions for the fprime project.

@author SiboVG
"""

import os
from pathlib import Path
import pytest
from unittest.mock import MagicMock, patch

from fprime.fbuild.builder import Build
from fprime.util.file_util import get_directory_path_relative_to_root


@pytest.fixture
def mock_build():
    """Create a mock Build object for testing"""
    mock = MagicMock(spec=Build)
    return mock


def test_current_dir_is_root(mock_build):
    """Test when current directory is the project root"""
    # Setup
    mock_build.get_settings.return_value = str(Path.cwd())

    # Execute
    result = get_directory_path_relative_to_root(mock_build)

    # Verify
    assert result == ""
    mock_build.get_settings.assert_called_once_with("project_root", None)


@patch("fprime.util.file_util.Path.cwd")
def test_current_dir_is_subdirectory(mock_cwd, mock_build):
    """Test when current directory is a subdirectory of the project root"""
    # Setup
    root_path = Path("/path/to/project")
    current_path = root_path / "subdir1" / "subdir2"

    mock_build.get_settings.return_value = str(root_path)
    mock_cwd.return_value = current_path

    # Execute
    result = get_directory_path_relative_to_root(mock_build)

    # Verify
    assert result.replace(os.sep, "/") == "subdir1/subdir2"


@patch("fprime.util.file_util.Path.cwd")
def test_current_dir_outside_project(mock_cwd, mock_build):
    """Test when current directory is outside the project root"""
    # Setup
    root_path = Path("/path/to/project")
    current_path = Path("/different/path")

    mock_build.get_settings.return_value = str(root_path)
    mock_cwd.return_value = current_path

    # Execute
    result = get_directory_path_relative_to_root(mock_build)

    # Verify
    assert result is None


@patch("fprime.util.file_util.Path.cwd")
def test_with_nested_directories(mock_cwd, mock_build):
    """Test with deeply nested directories"""
    # Setup
    root_path = Path("/path/to/project")
    current_path = root_path / "a" / "b" / "c" / "d"

    mock_build.get_settings.return_value = str(root_path)
    mock_cwd.return_value = current_path

    # Execute
    result = get_directory_path_relative_to_root(mock_build)

    # Verify
    assert result.replace(os.sep, "/") == "a/b/c/d"


def test_with_nonexistent_project_root(mock_build):
    """Test behavior when project_root setting doesn't exist"""
    # Setup
    mock_build.get_settings.return_value = None

    # This should return None
    result = get_directory_path_relative_to_root(mock_build)
    assert result is None


@patch("fprime.util.file_util.Path.cwd")
def test_with_relative_path_in_settings(mock_cwd, mock_build):
    """Test with a relative path in the settings"""
    # Setup
    root_path = Path("project")  # Relative path
    abs_root_path = Path("/path/to/project")  # What it resolves to
    current_path = abs_root_path / "subdir"

    # Mock resolve to return the absolute path
    with patch.object(Path, "resolve", return_value=abs_root_path):
        mock_build.get_settings.return_value = str(root_path)
        mock_cwd.return_value = current_path

        # Execute
        result = get_directory_path_relative_to_root(mock_build)

        # Verify
        assert result == "subdir"
