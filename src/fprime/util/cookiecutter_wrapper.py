""" Cookie cutter wrapper used to template out components
"""
import glob
import os
import shutil
import sys
from contextlib import contextmanager
from pathlib import Path

from cookiecutter.exceptions import OutputDirExistsException
from cookiecutter.main import cookiecutter

from fprime.common.utils import confirm
from fprime.fbuild.builder import Build
from fprime.fbuild.cmake import CMakeExecutionException
from fprime.fbuild.target import Target
from fprime.util.code_formatter import ClangFormatter


def run_impl(build: Build, source_path: Path):
    """Run implementation of files in source_path"""
    target = Target.get_target("impl", set())

    hpp_files = glob.glob(f"{source_path}/*.hpp", recursive=False)
    cpp_files = glob.glob(f"{source_path}/*.cpp", recursive=False)
    cpp_files.sort(key=len)

    # Check destinations
    if not hpp_files or not cpp_files:
        print(
            "[WARNING] Failed to find .cpp and .hpp destination files for implementation."
        )
        return False

    common = [name for name in cpp_files if "Common" in name] + []
    hpp_dest = hpp_files[0]
    cpp_dest = common[0] if common else cpp_files[0]

    if not confirm("Generate implementation files (yes/no)? "):
        return False
    print(
        "Refreshing cache and generating implementation files (ignore 'Stop' CMake warning)..."
    )
    with suppress_stdout():
        target.execute(build, source_path, ({}, [], {}))

    hpp_files_template = glob.glob(f"{source_path}/*.hpp-template", recursive=False)
    cpp_files_template = glob.glob(f"{source_path}/*.cpp-template", recursive=False)

    if not hpp_files_template or not cpp_files_template:
        print("[WARNING] Failed to find generated .cpp-template or .hpp-template files")
        return False

    hpp_src = hpp_files_template[0]
    cpp_src = cpp_files_template[0]

    # Move (and overwrite) files from *.(c|h)pp-template to *.(c|h)pp
    shutil.move(hpp_src, hpp_dest)
    shutil.move(cpp_src, cpp_dest)

    # Format files if clang-format is available
    format_file = build.settings.get("framework_path", Path(".")) / ".clang-format"
    if not format_file.is_file():
        print(
            f"[WARNING] .clang-format file not found at {format_file.resolve()}. Skipping formatting."
        )
        return True
    clang_formatter = ClangFormatter("clang-format", format_file, {"backup": False})
    if clang_formatter.is_supported():
        clang_formatter.stage_file(Path(hpp_dest))
        clang_formatter.stage_file(Path(cpp_dest))
        clang_formatter.execute(None, None, ({}, []))
    else:
        print("[WARNING] clang-format not found in PATH. Skipping formatting.")

    return True


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

    if not confirm(
        f"Add component {comp_path} to {short_display_path} at end of file (yes/no)? "
    ):
        return False

    lines.append(addition)
    with open(list_file, "w") as f:
        f.write("".join(lines))
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


def find_nearest_cmake_file(component_dir: Path, deployment: Path, proj_root: Path):
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
    for test_path, end_path in [(test_path, proj_root), (deployment, proj_root.parent)]:
        while proj_root is not None and test_path != proj_root.parent:
            project_file = test_path / "project.cmake"
            if project_file.is_file():
                return project_file
            cmake_list_file = test_path / "CMakeLists.txt"
            if cmake_list_file.is_file():
                return cmake_list_file
            test_path = test_path.parent
    return None


def new_component(build: Build):
    """Uses cookiecutter for making new components"""
    try:
        deployment = build.deployment
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

        # Use deployment name as default namespace if a deployment was found
        extra_context = {}
        if not proj_root.samefile(deployment):
            extra_context["component_namespace"] = deployment.name

        final_component_dir = Path(
            cookiecutter(source, extra_context=extra_context)
        ).resolve()

        if proj_root is None:
            print(
                f"[INFO] Created component directory without adding to build system nor generating implementation {final_component_dir}"
            )
            return 0

        # Attempt to register to CMakeLists.txt
        proj_root = Path(proj_root)
        cmake_file = find_nearest_cmake_file(final_component_dir, deployment, proj_root)
        if cmake_file is None or not add_to_cmake(
            cmake_file,
            final_component_dir.relative_to(cmake_file.parent),
            proj_root,
        ):
            print(
                f"[INFO] Could not register {final_component_dir} with build system. Please add it and generate implementations manually."
            )
            return 0
        # Attempt implementation
        if not run_impl(build, final_component_dir):
            print(
                f"[INFO] Did not generate implementations for {final_component_dir}. Please do so manually."
            )
            return 0

        print("[INFO] Created new component and generated initial implementations.")
        return 0
    except OutputDirExistsException as out_directory_error:
        print(f"{out_directory_error}", file=sys.stderr)
    except CMakeExecutionException as exc:
        print(f"[ERROR] Failed to create component. {exc}", file=sys.stderr)
    except OSError as ose:
        print(f"[ERROR] {ose}")
    return 1


def new_deployment(build: Build, parsed_args):
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

        proj_root = build.get_settings("project_root", None)
        # Attempt to register to CMakeLists.txt or project.cmake
        proj_root = Path(proj_root)
        cmake_file = find_nearest_cmake_file(gen_path, build.deployment, proj_root)
        if cmake_file is None or not add_to_cmake(
            cmake_file,
            gen_path.relative_to(cmake_file.parent),
            proj_root,
        ):
            print(
                f"[INFO] Could not register {gen_path} with build system. Please add it manually."
            )
            return 0

    except OutputDirExistsException as out_directory_error:
        print(
            f"{out_directory_error}. Use --overwrite to overwrite (will not delete non-generated files).",
            file=sys.stderr,
        )
        return 1
    print(f"[INFO] New deployment successfully created: {gen_path}")
    return 0


def new_project(parsed_args):
    """Creates a new F' project"""

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
        gen_path = cookiecutter(
            source,
            overwrite_if_exists=parsed_args.overwrite,
            output_dir=parsed_args.path,
        )
    except OutputDirExistsException as out_directory_error:
        print(
            f"{out_directory_error}. Use --overwrite to overwrite (will not delete non-generated files).",
            file=sys.stderr,
        )
        return 1
    print(f"[INFO] New project successfully created: {gen_path}")
    return 0


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
    ]
    for char in invalid_characters:
        if isinstance(word, str) and char in word:
            return char
        if not isinstance(word, str):
            raise ValueError("Incorrect usage of is_valid_name")
    return "valid"
