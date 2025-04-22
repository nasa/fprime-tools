"""
(test) fprime.util.cookiecutter_wrapper - new_deployment():
Test adding a new deployment to a project using cookiecutter.

This test verifies the behavior of creating deployments in non-root directories,
specifically testing the automatic detection and adjustment of include paths.
"""

import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from fprime.fbuild.builder import Build
from fprime.util.cookiecutter_wrapper import new_deployment


class TestNewDeployment(unittest.TestCase):
    """Test the new_deployment function"""

    def setUp(self):
        """Set up a temporary directory structure for testing"""
        # Create a temporary directory to simulate a project
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir) / "project_root"
        self.project_root.mkdir()

        # Create a subdirectory to simulate a Deployments directory
        self.deployments_dir = self.project_root / "Deployments"
        self.deployments_dir.mkdir()

        # Create a CMakeLists.txt file in the project root
        with open(self.project_root / "CMakeLists.txt", "w") as f:
            f.write("# Project CMakeLists.txt\n")

        # Create a settings.ini file in the project root
        with open(self.project_root / "settings.ini", "w") as f:
            f.write("[fprime]\n")
            f.write("project_root = .\n")
            f.write(f"framework_path = {self.project_root}\n")

        # Save the original working directory
        self.original_cwd = os.getcwd()

    def tearDown(self):
        """Clean up temporary directory"""
        # Change back to the original working directory
        os.chdir(self.original_cwd)

        # Remove the temporary directory
        shutil.rmtree(self.temp_dir)

    @patch("fprime.util.cookiecutter_wrapper.cookiecutter")
    @patch("fprime.util.cookiecutter_wrapper.register_with_cmake")
    def test_new_deployment_in_root_dir(self, mock_register, mock_cookiecutter):
        """Test creating a deployment in the project root directory"""
        # Change to the project root directory
        os.chdir(self.project_root)

        # Mock the build object
        mock_build = MagicMock(spec=Build)
        mock_build.get_settings.return_value = self.project_root
        mock_build.cmake_root = self.project_root

        # Mock the parsed arguments
        mock_args = MagicMock()
        mock_args.force = False
        mock_args.overwrite = False

        # Mock the cookiecutter function to return a path
        mock_cookiecutter.return_value = str(self.project_root / "MyDeployment")

        # Call the function
        result = new_deployment(mock_build, mock_args)

        # Verify the result
        self.assertEqual(result, 0)

        # Verify that cookiecutter was called with the correct arguments
        mock_cookiecutter.assert_called_once()
        args, kwargs = mock_cookiecutter.call_args
        self.assertIn("extra_context", kwargs)
        self.assertEqual(kwargs["extra_context"], {})  # No include path prefix

    @patch("fprime.util.cookiecutter_wrapper.cookiecutter")
    @patch("fprime.util.cookiecutter_wrapper.register_with_cmake")
    def test_new_deployment_in_subdir(self, mock_register, mock_cookiecutter):
        """Test creating a deployment in a subdirectory"""
        # Change to the Deployments directory
        os.chdir(self.deployments_dir)

        # Mock the build object
        mock_build = MagicMock(spec=Build)
        mock_build.get_settings.return_value = self.project_root
        mock_build.cmake_root = self.project_root

        # Mock the parsed arguments
        mock_args = MagicMock()
        mock_args.force = False
        mock_args.overwrite = False

        # Mock the cookiecutter function to return a path
        mock_cookiecutter.return_value = str(self.deployments_dir / "MyDeployment")

        # Call the function
        result = new_deployment(mock_build, mock_args)

        # Verify the result
        self.assertEqual(result, 0)

        # Verify that cookiecutter was called with the correct arguments
        mock_cookiecutter.assert_called_once()
        args, kwargs = mock_cookiecutter.call_args
        self.assertIn("extra_context", kwargs)
        self.assertIn("__include_path_prefix", kwargs["extra_context"])
        self.assertEqual(
            kwargs["extra_context"]["__include_path_prefix"], "Deployments/"
        )


if __name__ == "__main__":
    unittest.main()
