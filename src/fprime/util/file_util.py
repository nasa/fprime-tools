"""fprime.util.file_util: Utility functions for general file operations

@author SiboVG
"""

from pathlib import Path

from fprime.fbuild.builder import Build


def get_directory_path_relative_to_root(build: Build) -> str:
    """
    Get the directory path of the current directory (from which F` tools is executed)
    relative to the root of the F` project.

    If the current directory is the project root, it returns an empty string.
    If the current directory is a subdirectory of the project root, it returns the relative path.
    If the current directory is not within the project root, it returns None.

    Args:
        build (Build): The build object containing project settings.
    Returns:
        str: The relative path from the project root to the current directory,
            an empty string if the current directory is the project root,
            or None if not within the project root.
    """
    proj_root = build.get_settings("project_root", None)
    if proj_root is None:
        print("[WARNING] No project root found. Cannot determine relative path.")
        return None

    proj_root = Path(proj_root).resolve()
    cwd = Path.cwd()

    if proj_root == cwd:
        return ""

    if proj_root not in cwd.parents:
        return None

    return str(cwd.relative_to(proj_root))
