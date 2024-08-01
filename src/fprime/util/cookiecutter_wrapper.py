""" Cookie cutter wrapper used to template out components
"""

import glob
import os
import shutil
import sys

from typing import TYPE_CHECKING
from contextlib import contextmanager
from pathlib import Path

from cookiecutter.exceptions import OutputDirExistsException
from cookiecutter.main import cookiecutter

from fprime.common.utils import confirm
from fprime.fbuild.builder import Build
from fprime.fbuild.cmake import CMakeExecutionException
from fprime.fpp.impl import fpp_generate_implementation

if TYPE_CHECKING:
    import argparse


def run_impl(build: Build, source_path: Path):
    """Run implementation of files in source_path"""
    if not confirm("Generate implementation files?"):
        return False
    print("Refreshing cache and generating implementation files...")

    with suppress_stdout():
        fpp_generate_implementation(build, source_path, source_path, True, False)

    # Path(source_path).
    file_list = glob.glob(f"{source_path}/*.template.*pp", recursive=False)
    for filename in file_list:
        new_filename = filename.replace(".template", "")
        os.rename(filename, new_filename)

    return True


@contextmanager
def suppress_stdout():
    with open(os.devnull, "w") as devnull:
        old_stdout = sys.stdout
        sys.stdout = devnull
        try:
            yield
        finally:
            sys.stdout = old_stdout


def find_nearest_cmake_file(component_dir: Path, cmake_root: Path, proj_root: Path):
    """Find the nearest CMake file, i.e. CMakeLists.txt or project.cmake

    The "nearest" file is defined as the closest parent that is not the project root CMakeLists.txt.
    If none is found, the same procedure is run from the deployment directory and includes the project
    root this time. If nothing is found, None is returned.

    In short the following in order of preference:
     - Any Component Parent
     - Any Deployment Parent
     - project.cmake
     - None

    Args:
        component_dir: directory of new component
        deployment: deployment directory
        proj_root: project root directory

    Returns:
        path to CMakeLists.txt or None
    """
    test_path = component_dir.parent
    # First iterate from where we are, then from the deployment to find the nearest CMakeList.txt nearby
    for test_path, end_path in [(test_path, proj_root), (cmake_root, proj_root.parent)]:
        while proj_root is not None and test_path != proj_root.parent:
            project_file = test_path / "project.cmake"
            if project_file.is_file():
                return project_file
            cmake_list_file = test_path / "CMakeLists.txt"
            if cmake_list_file.is_file():
                return cmake_list_file
            test_path = test_path.parent
    return None


def new_component(build: Build, parsed_args: "argparse.Namespace"):
    """Uses cookiecutter for making new components"""
    try:
        proj_root = build.get_settings("project_root", None)

        # Checks if component_cookiecutter is set in settings.ini file, else uses local component_cookiecutter template as default
        if (
            build.get_settings("component_cookiecutter", None) is not None
            and build.get_settings("component_cookiecutter", None) != "default"
        ):
            source = build.get_settings("component_cookiecutter", None)
            print(f"[INFO] Cookiecutter source: {source}")
        else:
            source = (
                os.path.dirname(__file__)
                + "/../cookiecutter_templates/cookiecutter-fprime-component"
            )
            print("[INFO] Cookiecutter source: using builtin")

        # Use current working directory name as default namespace, unless at project root
        extra_context = {}
        if not proj_root.samefile(Path.cwd()):
            extra_context["component_namespace"] = Path.cwd().name

        gen_path = Path(cookiecutter(source, extra_context=extra_context)).resolve()

        if proj_root is None:
            print(
                f"[INFO] Created component directory without adding to build system nor generating implementation {gen_path}"
            )
            return 0
        # Attempt to register to CMakeLists.txt or project.cmake
        register_with_cmake(
            gen_path,
            Path(proj_root).resolve(),
            build.cmake_root,
        )
        # Attempt implementation
        if not run_impl(build, gen_path):
            print(
                f"[INFO] Did not generate implementations for {gen_path}. Please do so manually."
            )
            return 0

        print("[INFO] Created new component and generated initial implementations.")
        return 0
    except OutputDirExistsException as out_directory_error:
        print(f"{out_directory_error}", file=sys.stderr)
    except CMakeExecutionException as exc:
        print(f"[ERROR] Failed to create component. {exc}", file=sys.stderr)
    except FileNotFoundError as e:
        print(
            f"{e}. Permission denied to write to the directory.",
            file=sys.stderr,
        )
        return 1
    except OSError as ose:
        print(f"[ERROR] {ose}")
    return 1


def new_deployment(build: Build, parsed_args: "argparse.Namespace"):
    """Creates a new deployment using cookiecutter"""
    # Checks if deployment_cookiecutter is set in settings.ini file, else uses local install template as default
    if (
        build.get_settings("deployment_cookiecutter", None) is not None
        and build.get_settings("deployment_cookiecutter", None) != "default"
    ):
        source = build.get_settings("deployment_cookiecutter", None)
        print(f"[INFO] Cookiecutter source: {source}")
    else:
        source = (
            os.path.dirname(__file__)
            + "/../cookiecutter_templates/cookiecutter-fprime-deployment"
        )
        print("[INFO] Cookiecutter: using builtin template for new deployment")
    try:
        gen_path = Path(
            cookiecutter(source, overwrite_if_exists=parsed_args.overwrite)
        ).resolve()
        # Attempt to register to CMakeLists.txt or project.cmake
        register_with_cmake(
            gen_path,
            Path(build.get_settings("project_root", None)).resolve(),
            build.cmake_root,
        )

    except OutputDirExistsException as out_directory_error:
        print(
            f"{out_directory_error}. Use --overwrite to overwrite (will not delete non-generated files).",
            file=sys.stderr,
        )
        return 1
    except FileNotFoundError as e:
        print(
            f"{e}. Permission denied to write to the directory.",
            file=sys.stderr,
        )
        return 1
    print(f"[INFO] New deployment successfully created: {gen_path}")
    return 0


def new_subtopology(build: Build, parsed_args: "argparse.Namespace"):
    """Creates a new subtopology using cookiecutter"""
    # Checks if subtopology_cookiecutter is set in settings.ini file, else uses local install template as default
    if (
        build.get_settings("subtopology_cookiecutter", None) is not None
        and build.get_settings("subtopology_cookiecutter", None) != "default"
    ):
        source = build.get_settings("subtopology_cookiecutter", None)
        print(f"[INFO] Cookiecutter source: {source}")
    else:
        source = (
            os.path.dirname(__file__)
            + "/../cookiecutter_templates/cookiecutter-fprime-subtopology"
        )
        print("[INFO] Cookiecutter: using builtin template for new subtopology")
    try:
        gen_path = Path(
            cookiecutter(source, overwrite_if_exists=parsed_args.overwrite)
        ).resolve()
        # Attempt to register to CMakeLists.txt or project.cmake
        register_with_cmake(
            gen_path,
            Path(build.get_settings("project_root", None)).resolve(),
            build.cmake_root,
        )

    except OutputDirExistsException as out_directory_error:
        print(
            f"{out_directory_error}. Use --overwrite to overwrite (will not delete non-generated files).",
            file=sys.stderr,
        )
        return 1
    except FileNotFoundError as e:
        print(
            f"{e}. Permission denied to write to the directory.",
            file=sys.stderr,
        )
        return 1
    print(f"[INFO] New subtopology successfully created: {gen_path}")
    return 0


def new_module(build: Build, parsed_args: "argparse.Namespace"):
    """Creates a new F' project"""

    source = (
        os.path.dirname(__file__)
        + "/../cookiecutter_templates/cookiecutter-fprime-module"
    )
    try:
        gen_path = Path(
            cookiecutter(
                source,
                overwrite_if_exists=parsed_args.overwrite,
                output_dir=parsed_args.path,
            )
        ).resolve()
        # Attempt to register to CMakeLists.txt or project.cmake
        register_with_cmake(
            gen_path,
            Path(build.get_settings("project_root", None)).resolve(),
            build.cmake_root,
        )
    except OutputDirExistsException as out_directory_error:
        print(
            f"{out_directory_error}. Use --overwrite to overwrite (will not delete non-generated files).",
            file=sys.stderr,
        )
        return 1
    except FileNotFoundError as e:
        print(
            f"{e}. Permission denied to write to the directory.",
            file=sys.stderr,
        )
        return 1
    return 0


def new_project(parsed_args: "argparse.Namespace"):
    """Creates a new F' project"""

    print(
        "[DEPRECATED] This command is deprecated and will be removed in a future release."
        " Please use `fprime-bootstrap project` instead."
        " Install fprime-bootstrap with `pip install fprime-bootstrap`,"
        " or refer to https://nasa.github.io/fprime/INSTALL.html"
    )

    # Check if Git is installed and available - needed for cloning F' as submodule
    if not shutil.which("git"):
        print(
            "[ERROR] Git is not installed or in PATH. Please install Git and try again.",
            file=sys.stderr,
        )
        return 1

    source = (
        os.path.dirname(__file__)
        + "/../cookiecutter_templates/cookiecutter-fprime-project"
    )
    try:
        cookiecutter(
            source,
            overwrite_if_exists=parsed_args.overwrite,
            output_dir=parsed_args.path,
            extra_context={"__install_venv": "no" if parsed_args.no_venv else "yes"},
        )
    except OutputDirExistsException as out_directory_error:
        print(
            f"{out_directory_error}. Use --overwrite to overwrite (will not delete non-generated files).",
            file=sys.stderr,
        )
        return 1
    except FileNotFoundError as e:
        print(
            f"{e}. Permission denied to write to the directory.",
            file=sys.stderr,
        )
        return 1
    return 0


def register_with_cmake(gen_path: Path, proj_root: Path, cmake_root: Path):
    cmake_file = find_nearest_cmake_file(gen_path, cmake_root, proj_root)
    if cmake_file is None or not add_to_cmake(
        cmake_file,
        gen_path.relative_to(cmake_file.parent),
        proj_root,
    ):
        print(
            f"[INFO] Could not register {gen_path} with build system. Please add it manually."
        )


def add_to_cmake(list_file: Path, comp_path: Path, project_root: Path = None):
    """Adds comp_path directory to CMakeLists.txt. If project_root is supplied,
    the logged path will be relative to the project root instead of absolute"""
    short_display_path = (
        list_file
        if project_root is None
        else project_root.name / list_file.relative_to(project_root)
    )
    print(f"[INFO] Found CMake file at '{short_display_path}'")
    with open(list_file, "r") as f:
        lines = f.readlines()

    addition = (
        'add_fprime_subdirectory("${CMAKE_CURRENT_LIST_DIR}/' + str(comp_path) + '/")\n'
    )
    if addition in lines:
        print("Already added to CMakeLists.txt")
        return True

    if not confirm(f"Add {comp_path} to {short_display_path} at end of file?"):
        return False

    lines.append(addition)
    with open(list_file, "w") as f:
        f.write("".join(lines))
    return True


def is_valid_name(word: str):
    invalid_characters = [
        "#",
        "%",
        "&",
        "{",
        "}",
        "/",
        "\\",
        "<",
        ">",
        "*",
        "?",
        " ",
        "$",
        "!",
        "'",
        '"',
        ":",
        "@",
        "+",
        "`",
        "|",
        "=",
        "-",
    ]
    for char in invalid_characters:
        if isinstance(word, str) and char in word:
            return char
        if not isinstance(word, str):
            raise ValueError("Incorrect usage of is_valid_name")
    return "valid"
