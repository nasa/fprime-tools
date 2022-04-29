""" Cookie cutter wrapper used to template out components
"""
import os
import glob
import sys
import textwrap
from pathlib import Path
from typing import Dict
import re
from contextlib import contextmanager

from cookiecutter.main import cookiecutter
from cookiecutter.exceptions import OutputDirExistsException
from jinja2 import Environment, FileSystemLoader

from fprime.fbuild.builder import Build
from fprime.fbuild.target import Target
from fprime.fbuild.cmake import CMakeExecutionException


def confirm(msg):
    """Confirms the removal of the file with a yes or no input"""
    # Loop "forever" intended
    while True:
        confirm_input = input(msg)
        if confirm_input.lower() in ["y", "yes"]:
            return True
        if confirm_input.lower() in ["n", "no"]:
            return False
        print(f"{confirm_input} is invalid.  Please use 'yes' or 'no'")


def replace_contents(filename, what, replacement, count=1):
    changelog = Path(filename).read_text()
    with open(filename, "w") as fh:
        new_file = changelog.replace(what, replacement, count)
        fh.write(new_file)
        if new_file != changelog:
            return True
        else:
            return False


def run_impl(deployment: Path, path: Path, platform: str, verbose: bool):
    """Run implementation of files one time"""
    target = Target.get_target("impl", set())
    build = Build(target.build_type, deployment, verbose=verbose)
    build.load(platform)

    hpp_files = glob.glob(f"{path}/*.hpp", recursive=False)
    cpp_files = glob.glob(f"{path}/*.cpp", recursive=False)
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

    if not confirm(
        f"Generate implementations and merge into {hpp_dest} and {cpp_dest}?"
    ):
        return False
    print("Generating implementation files and merging...")
    with suppress_stdout():
        build.execute(target, context=path, make_args={})

    hpp_files_template = glob.glob(f"{path}/*.hpp-template", recursive=False)
    cpp_files_template = glob.glob(f"{path}/*.cpp-template", recursive=False)

    if not hpp_files_template or not cpp_files_template:
        print("[WARNING] Failed to find generated .cpp-template or .hpp-template files")
        return False

    hpp_src = hpp_files_template[0]
    cpp_src = cpp_files_template[0]

    # Copy files without headers
    for src, dest in [(hpp_src, hpp_dest), (cpp_src, cpp_dest)]:
        with open(src, "r") as file_handle:
            lines = file_handle.readlines()
        lines = lines[11:]  # Remove old header
        with open(dest, "a") as file_handle:
            file_handle.write("".join(lines))

    removals = [Path(hpp_src), Path(cpp_src)]
    for removal in removals:
        os.remove(removal)
    return True


def add_to_cmake(list_file: Path, comp_path: Path):
    """Adds new component or port to CMakeLists.txt"""
    print(f"[INFO] Found CMakeLists.txt at '{list_file}'")
    with open(list_file, "r") as f:
        lines = f.readlines()

    addition = (
        'add_fprime_subdirectory("${CMAKE_CURRENT_LIST_DIR}/' + str(comp_path) + '/")\n'
    )
    if addition in lines:
        print("Already added to CMakeLists.txt")
        return True

    if not confirm(f"Add component {comp_path} to {list_file} at end of file?"):
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


def regenerate(build: Build):
    print("Refreshing cache to include new addition...")
    with suppress_stdout():
        try:
            build.cmake.cmake_refresh_cache(build.get_build_cache())
        except CMakeExecutionException:
            build.cmake.cmake_refresh_cache(build.get_build_cache(), True)


def add_unit_tests(deployment, comp_path, platform, verbose):
    # Creates unit tests and moves them into test/ut directory
    os.chdir(str(comp_path))
    if confirm("Would you like to generate unit tests?: "):
        test_path = Path("test", "ut")
        test_path.mkdir(parents=True, exist_ok=True)
        target = Target.get_target("impl", {"ut"})
        build = Build(target.build_type, deployment, verbose=verbose)
        build.load(platform)
        print("Generating unit tests...")
        with suppress_stdout():
            build.execute(target, context=comp_path, make_args={})
        test_files = [
            "Tester.hpp",
            "Tester.cpp",
            "TesterBase.hpp",
            "TesterBase.cpp",
            "GTestBase.hpp",
            "GTestBase.cpp",
            "TestMain.cpp",
        ]
        for file in test_files:
            if os.path.isfile(file):
                new_name = test_path / file
                os.rename(file, str(new_name))

        with open("CMakeLists.txt", "r") as f:
            cmakeFile = f.read()

        with open("CMakeLists.txt", "w") as f:
            cmakeFile = cmakeFile + textwrap.dedent(
                """\n
                set(UT_SOURCE_FILES
                  "${CMAKE_CURRENT_LIST_DIR}/test/ut/TestMain.cpp"
                  "${CMAKE_CURRENT_LIST_DIR}/test/ut/Tester.cpp"
                )

                register_fprime_ut()"""
            )
            f.write(cmakeFile)

        if replace_contents(
            Path("test", "ut", "Tester.hpp"), "ComponentImpl.hpp", ".hpp", -1
        ):
            print("[INFO] Fixed hpp include in Tester.hpp")
        print("[INFO] Unit tests were generated.")


def add_port_to_cmake(list_file: Path, comp_path: Path):
    """Adds new port to CMakeLists.txt in port directory"""
    print(f"[INFO] Found CMakeLists.txt at '{list_file}'")
    with open(list_file, "r") as file_handle:
        lines = file_handle.readlines()
    index = 0
    while re.search("set\(\s*SOURCE_FILES", lines[index]) is None:
        index += 1
    index += 1
    while "CMAKE_CURRENT_LIST_DIR" in lines[index]:
        index += 1
    if not confirm(f"Add port {comp_path} to {list_file} ports in CMakeLists.txt?"):
        return False

    addition = '    "${{CMAKE_CURRENT_LIST_DIR}}/{}"\n'.format(comp_path)
    lines.insert(index, addition)
    with open(list_file, "w") as file_handle:
        file_handle.write("".join(lines))
    return True


def find_nearest_cmake_lists(component_dir: Path, deployment: Path, proj_root: Path):
    """Find the nearest CMakeLists.txt file

    The "nearest" file is defined as the closes parent that is not the "project root" that contains a CMakeLists.txt. If
    none is found, the same procedure is run from the deployment directory and includes the project root this time. If
    nothing is found, None is returned.

    In short the following in order of preference:
     - Any Component Parent
     - Any Deployment Parent
     - Project Root
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
            cmake_list_file = test_path / "CMakeLists.txt"
            if cmake_list_file.is_file():
                return cmake_list_file
            test_path = test_path.parent
    return None


def new_component(deployment: Path, platform: str, verbose: bool, build: Build):
    """Uses cookiecutter for making new components"""
    try:
        print("[WARNING] **** fprime-util new is prototype functionality ****")
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
        print()
        final_component_dir = Path(
            cookiecutter(source, extra_context={"component_namespace": deployment.name})
        ).resolve()
        if proj_root is None:
            print(
                f"[INFO] Created component directory without adding to build system nor generating implementation {final_component_dir}"
            )
            return 0
        # Attempt to register to CMakeLists.txt
        proj_root = Path(proj_root)
        cmake_lists_file = find_nearest_cmake_lists(
            final_component_dir, deployment, proj_root
        )
        if cmake_lists_file is None or not add_to_cmake(
            cmake_lists_file, final_component_dir.relative_to(cmake_lists_file.parent)
        ):
            print(
                f"[INFO] Could not register {final_component_dir} with build system. Please add it and generate implementations manually."
            )
            return 0
        regenerate(build)
        # Attempt implementation
        if not run_impl(deployment, final_component_dir, platform, verbose):
            print(
                "[INFO] Could not generate implementations. Please do so manually.".format(
                    final_component_dir
                )
            )
            return 0
        cpp_file = glob.glob(str(Path(deployment.name, final_component_dir, "*.cpp")))[
            0
        ]
        print("[INFO] Created new component and created initial implementations.")
        if replace_contents(cpp_file, "ComponentImpl.hpp", ".hpp", -1):
            print("[INFO] Fixed hpp include in cpp file.")

        add_unit_tests(deployment, final_component_dir, platform, verbose)
        print(
            f'[INFO] Next run `fprime-util build{"" if platform is None else f" {platform}"}` in {final_component_dir}'
        )
        return 0
    except OutputDirExistsException as out_directory_error:
        print(f"{out_directory_error}", file=sys.stderr)
    except CMakeExecutionException as exc:
        print(f"[ERROR] Failed to create component. {exc}", file=sys.stderr)
    except OSError as ose:
        print(f"[ERROR] {ose}")
    return 1


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
        elif not isinstance(word, str):
            raise ValueError("Incorrect usage of is_valid_name")
    return "valid"


def get_valid_input(prompt):
    valid_name = False
    while not valid_name:
        name = input(prompt)
        char = is_valid_name(name)
        if char != "valid":
            print("'" + char + "' is not a valid character")
        else:
            valid_name = True
    return name


def get_port_input(namespace):
    # Gather inputs to use as context for the port template
    defaults = {
        "port_name": "ExamplePort",
        "short_description": "Example usage of port",
        "dir_name": ".",
        "namespace": namespace,
        "arg_list": [],
    }
    args_done = False
    arg_list = []
    port_name = get_valid_input(f'Port Name [{defaults["port_name"]}]: ')
    short_description = input(f'Short Description [{defaults["short_description"]}]: ')
    dir_name = get_valid_input(f'Directory Name [{defaults["dir_name"]}]: ')
    namespace = get_valid_input(f'Port Namespace [{defaults["namespace"]}]: ')
    while not args_done:
        if arg_list == []:
            add_arg = confirm("Would you like to add an argument?: ")
        else:
            add_arg = confirm("Would you like to add another argument?: ")
        if add_arg:
            arg_name = get_valid_input("Argument name: ")
            arg_type = get_valid_input(
                "Argument type (Valid primitive types are: I8, I16, "
                + "I32, U8, U16, U32, F32, F64, NATIVE_INT_TYPE, NATIVE_UNIT_TYPE, and POINTER_CAST. "
                + "You may also use your own user-defined types): "
            )
            arg_description = input("Short description of argument: ")
            arg_list.append((arg_name, arg_type, arg_description))
        else:
            args_done = True
    values = {
        "port_name": port_name,
        "short_description": short_description,
        "dir_name": dir_name,
        "namespace": namespace,
        "arg_list": arg_list,
    }

    # Fill in blank values with defaults
    for key in values:
        if values[key] == "":
            values[key] = defaults[key]
    return values


def new_port(deployment: Path, build: Build):
    """Uses cookiecutter for making new ports"""
    try:
        proj_root = build.get_settings("project_root", None)
        if proj_root is not None:
            proj_root = Path(proj_root)
            proj_root_found = True
        else:
            proj_root_found = False

        PATH = os.path.dirname(os.path.abspath(__file__))
        TEMPLATE_ENVIRONMENT = Environment(
            autoescape=False,
            loader=FileSystemLoader(os.path.join(PATH, "../cookiecutter_templates")),
            trim_blocks=False,
        )
        context = get_port_input(deployment.name)

        if Path(context["dir_name"]).resolve() == deployment.resolve():
            print("[ERROR] cannot create port in deployment directory")
            return 0
        fname = context["port_name"] + "Port" + "Ai.xml"
        if os.path.isfile(Path(context["dir_name"], fname)):
            print(
                "[ERROR] Port",
                context["port_name"],
                "already exists in directory",
                context["dir_name"],
            )
            return 0
        with open(fname, "w") as f:
            xml_file = TEMPLATE_ENVIRONMENT.get_template("port_template.xml").render(
                context
            )
            f.write(xml_file)
        if not os.path.isdir(context["dir_name"]):
            os.mkdir(context["dir_name"])

        os.rename(fname, str(Path(context["dir_name"], fname)))
        path_to_cmakelists = Path(context["dir_name"], "CMakeLists.txt")
        if not os.path.isfile(str(path_to_cmakelists)):
            with open(str(path_to_cmakelists), "w") as f:
                CMake_file = TEMPLATE_ENVIRONMENT.get_template(
                    "CMakeLists_template.txt"
                ).render(context)
                f.write(CMake_file)
        else:
            add_port_to_cmake(str(path_to_cmakelists), fname)

        if proj_root_found is False:
            print(
                "[INFO] No project root found. Created port without adding to build system nor generating implementation."
            )
            return 0
        cmake_lists_file = find_nearest_cmake_lists(
            Path(context["dir_name"]).resolve(), deployment, proj_root
        )
        if cmake_lists_file is None or not add_to_cmake(
            cmake_lists_file,
            (Path(context["dir_name"]).resolve()).relative_to(cmake_lists_file.parent),
        ):
            print(
                f'[INFO] Could not register {Path(context["dir_name"]).resolve()} with build system. Please add it and generate implementations manually.'
            )
            return 0
        regenerate(build)
        print("")
        print(
            "################################################################################"
        )
        print("")
        print(
            "You have successfully created the port "
            + context["port_name"]
            + " located in "
            + context["dir_name"]
        )
        print("")
        print(
            "################################################################################"
        )
        return 0
    except OutputDirExistsException as out_directory_error:
        print(f"{out_directory_error}", file=sys.stderr)
    except CMakeExecutionException as exc:
        print(f"[ERROR] Failed to create port. {exc}", file=sys.stderr)
    except OSError as ose:
        print(f"[ERROR] {ose}")
    return 1
