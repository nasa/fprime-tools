"""Test CMake interaction

This file contains a set of tests for validating CMake interaction on the back-end of fprime-util. These tests poke at
the CMakeHandler component.
"""

import json
import os
import shutil
import sys
import tempfile


from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch, call

import pytest
from fprime.fbuild.cmake import (
    CMakeHandler,
    CMakeExecutionException,
    CMakeInconsistentCacheException,
)


@contextmanager
def temporary_symbolic_link_context(link_name: str):
    """Context manager to create a symbolic link to 'echoer.py' in a temporary directory and add the to sys.path.

    This context manager is designed to facilitate testing of command-line utilities. Specifically, it:
    1. Creates a temporary directory.
    2. Generates a symbolic link inside the temporary directory that points to a file named 'echoer.py' located next to
       this script.
    3. Adds the temporary directory to `sys.path`, ensuring the symbolic link can be imported or executed during testing

    The purpose of this setup is to intercept calls to command-line utility sub commands during testing and echo back
    the context and environment. This allows developers to verify that the correct commands are run by the
    code-under-test, (sub commands within `fprime-util`. By leveraging the `echoer.py` script, testers can capture and
    validate the execution flow without running actual commands, ensuring consistent and isolated test environments.

    On cleanup, the symbolic link, the temporary directory, and its addition to `sys.path` are all reverted.

    Args:
        link_name (str): The name of the symbolic link to create.

    Yields:
        list: list that will contain the results harvested from files **after** the context manager is done

    Raises:
        OSError: If the symbolic link creation fails.
    """
    script_dir = Path(__file__).resolve().parent
    target_path = script_dir / "echoer.py"
    temp_dir = Path(tempfile.mkdtemp())
    link_path = temp_dir / link_name
    results = []
    try:
        # Create the symbolic link
        link_path.symlink_to(target_path)

        # Add the temporary directory to sys.path
        sys.path.insert(0, str(temp_dir))
        os.environ["PATH"] = f'{temp_dir}:{os.environ["PATH"]}'

        # Yield the symbolic link path to the caller
        yield results

        faux_files = list(link_path.parent.glob(f"faux-{link_path.name}-*.json"))
        faux_files.sort()
        for faux_file in faux_files:
            print("Reading Invocation File:", faux_file)
            with faux_file.open("r") as file:
                results.append(json.load(file))

    finally:
        # Remove the symbolic link if it exists
        if link_path.is_symlink():
            link_path.unlink()

        # Remove the temporary directory
        if temp_dir.is_dir():
            shutil.rmtree(temp_dir)

        sys.path.remove(str(temp_dir))
        new_list = os.environ["PATH"].split(":")
        new_list.remove(str(temp_dir))
        os.environ["PATH"] = ":".join(new_list)


def assert_valid_outputs(
    outputs, program="cmake", arguments=None, directory=None, environment=None
):
    """Assert that the outputs of a program invocation are valid.

    This function validates a list of program outputs, ensuring that the program has been invoked correctly
    with expected directories, environment variables, and arguments. The validation occurs as follows:

    1. Checks that there is at least one invocation of the program.
    2. Ensures that required keys ("environment", "cwd", "arguments") exist in each output.
    3. Verifies the working directory (`cwd`) if a `directory` argument is provided.
    4. Confirms the program's environment contains the expected keys and values.
    5. Validates that the program name and arguments match the supplied `arguments` list.

    Args:
        outputs (list): A list of outputs of the echo invocation, where each output is a dictionary containing:
            - "environment" (dict): The environment variables used for the program invocation.
            - "cwd" (str): The working directory where the program was run.
            - "arguments" (list): The arguments passed to the program.
        program (str): The name of the program being validated (default is "cmake").
        arguments (list, optional): Expected list of arguments to the program, excluding the program name.
        directory (str, optional): Expected working directory where the program should be executed.
        environment (dict, optional): A dictionary of environment variables expected in the program's environment.

    Raises:
        AssertionError: If any of the outputs fail validation.
    """
    assert outputs, f"Expected at least one invocation of {program}"

    # Validate output from CLI override
    for key in ["environment", "cwd", "arguments"]:
        for index, output in enumerate(outputs):
            assert (
                key in output
            ), f"{key} not written in the {index} invocation of {program}"

    for output in outputs:
        # If directory is supplied, standardize and check it
        if directory is not None:
            directory = str(Path(directory).resolve())
            assert (
                output["cwd"] == directory
            ), f"{program} not run in the correct directory"

        # If environment is supplied, check for the presence of each key and value
        if environment is not None:
            for key, value in environment.items():
                assert (
                    key in output["environment"]
                ), f"Environment does not contain {key}"
                assert (
                    output["environment"][key] == environment[key]
                ), f"Environment {key} value incorrect"

    # Check program argument and if supplied, the other arguments
    assert Path(output["arguments"][0]).name == program
    if arguments is not None:
        # Strip program off arguments and compare remainder
        output["arguments"] = output["arguments"][1:]
        assert (
            output["arguments"] == arguments
        ), f"Arguments supplied to {program} are incorrect"


@pytest.fixture
def cmake_handler():
    """Fixture to initialize the CMakeHandler"""
    return CMakeHandler()


def test_run_cmake(cmake_handler):
    """Tests the _run_cmake function of the CMakeHandler.

    This function verifies that the `_run_cmake` method of the `CMakeHandler`
    behaves as expected when provided with a basic set of arguments and a custom
    environment. It ensures that the method produces the correct standard output
    and standard error, and it validates the outputs in the specified directory.

    Steps:
        1. A basic set of arguments and environment variables are defined.
        2. A temporary symlink context is created to capture outputs.
        3. The `_run_cmake` function is executed within a temporary directory.
        4. Outputs are validated using `assert_valid_outputs`.
        5. Assertions are made to ensure correct stdout and stderr outputs.

    Raises:
        AssertionError: If the output does not contain the expected information
            or contains unexpected errors.

    Example:
        The function performs the following:
            - Runs `_run_cmake` with arguments ["a", "b", "c"].
            - Ensures no `[ERROR]` appears in the stderr output.
            - Verifies that stdout and stderr contain expected `[INFO]` messages.

    Assertions:
        - Captured arguments, environment, and working directory are as specified
        - `[INFO] Running echoer program (stdout)` appears in the standard output.
        - `[INFO] Running echoer program (stderr)` appears in the standard error.
        - No `[ERROR]` is present in the stderr output.
    """
    arguments = ["a", "b", "c"]
    environment = {"TEST": "TEST_VALUE"}
    with temporary_symbolic_link_context("cmake") as outputs:
        with tempfile.TemporaryDirectory() as test_directory:
            stdout, stderr = cmake_handler._run_cmake(
                arguments=arguments, workdir=test_directory, environment=environment
            )
    # Read only mode
    arguments = ["-N"] + arguments
    assert_valid_outputs(
        outputs, directory=test_directory, arguments=arguments, environment=environment
    )
    assert (
        "[INFO] Running echoer program (stdout)\n" in stdout
    ), "Correct standard out not produced"
    assert (
        "[INFO] Running echoer program (stderr)\n" in stderr
    ), "Correct standard error not produced"
    assert "[ERROR]" not in "".join(stderr), "Echoer produced error"


def test_run_cmake_editable(cmake_handler):
    """Tests the writeable _run_cmake function of the CMakeHandler

    This function verifies that the `_run_cmake` method of the `CMakeHandler`
    behaves as expected when provided with a basic set of arguments and a custom
    environment. It ensures that the method produces the correct standard output
    and standard error, and it validates the outputs in the specified directory.

    This step differs by ensuring that _run_cmake does not supply -N when it is a
    writeable operation.

    See test_run_cmake for more information

    Assertions:
        - Captured arguments, environment, and working directory are as specified
        - `[INFO] Running echoer program (stdout)` appears in the standard output.
        - `[INFO] Running echoer program (stderr)` appears in the standard error.
        - No `[ERROR]` is present in the stderr output.
    """
    arguments = ["a", "b", "c"]
    environment = {"TEST": "TEST_VALUE"}
    with temporary_symbolic_link_context("cmake") as outputs:
        with tempfile.TemporaryDirectory() as test_directory:
            stdout, stderr = cmake_handler._run_cmake(
                arguments=arguments,
                workdir=test_directory,
                environment=environment,
                write_override=True,
            )
    assert_valid_outputs(
        outputs, directory=test_directory, arguments=arguments, environment=environment
    )
    assert (
        "[INFO] Running echoer program (stdout)\n" in stdout
    ), "Correct standard out not produced"
    assert (
        "[INFO] Running echoer program (stderr)\n" in stderr
    ), "Correct standard error not produced"
    assert "[ERROR]" not in "".join(stderr), "Echoer produced error"


@patch("fprime.fbuild.cmake.CMakeHandler.get_cmake_module")
@patch("fprime.fbuild.cmake.CMakeHandler.validate_cmake_cache")
@patch("fprime.fbuild.cmake.CMakeHandler._run_cmake")
def mock_execute_known_target(
    cmake_handler,
    setup_callback,
    mock_run_cmake,
    mock_validate_cmake_cache,
    mock_get_cmake_module,
    **kwargs,
):
    """Run the nominal execution of execute_known_target

    Mocks out the _run_cmake, validate_cmake_cache, and get_cmake_module calls and then calls execute_known_target on
    the provided cmake_handler. `setup_callback` is called to configure the behavior for _run_cmake and
    validate_cmake_cache. Any additional arguments to the call are provided by kwargs.

    This will return the mocked_cmake_run call and the expected "call" object provided to it. The expected_target is
    calculated to reflect CMake structure and is adjusted if top_target is in **kwargs.  Environment will be checked if
    supplied in **kwargs.

    Args:
        cmake_handler: cmake handler to use
        setup_callback: callback taking arguments "mock_run_cmake", "mock_validate_cmake_cache" allowing more setup
        ...: provided by mocking utilities

    Return:
        tuple of (mock_run_cmake, expected_call)

    """
    build_dir = "/fake/build/dir"
    target = "my_valid_target"
    module = "CMake_Module"
    expected_target = (
        f"{target}" if kwargs.get("top_target", False) else f"{module}_{target}"
    )

    mock_get_cmake_module.return_value = module
    if setup_callback is not None:
        setup_callback(mock_run_cmake, mock_validate_cmake_cache)

    cmake_handler.execute_known_target(
        target, build_dir, None, print_output=False, **kwargs
    )
    expected_environment = kwargs.get("environment", {})
    expected_make_args = [
        f"{key}={value}" for key, value in kwargs.get("make_args", {}).items()
    ]

    # Verify that _run_cmake was called with the correct arguments
    expected_call = call(
        ["--build", build_dir, "--target", expected_target, "--"] + expected_make_args,
        write_override=True,
        environment=expected_environment,
        print_output=False,
    )
    return mock_run_cmake, expected_call


def test_execute_known_valid_target(cmake_handler):
    """Test execute_known_target with a valid target"""
    mock_run_cmake, expected_call = mock_execute_known_target(cmake_handler, None)
    mock_run_cmake.assert_called_once()
    mock_run_cmake.assert_has_calls([expected_call])


@patch("fprime.fbuild.cmake.CMakeHandler.cmake_refresh_cache")
def test_refresh_and_execute_known_target_valid(
    mock_cmake_refresh_cache, cmake_handler
):
    """Test execute_known_target triggering a cache refresh and reattempt"""

    def extra_setup(mock_run_cmake, _):
        """Perform extra setup to the basic mock calls"""
        mock_run_cmake.side_effect = CMakeExecutionException(
            ["No rule to make target"], ["No rule to make target"], False
        )

    with pytest.raises(CMakeExecutionException):
        mock_run_cmake, expected_call = mock_execute_known_target(
            cmake_handler, extra_setup
        )
        mock_cmake_refresh_cache.assert_called_once()
        mock_run_cmake.assert_has_calls([expected_call, expected_call])


def test_execute_known_global_target_valid(cmake_handler):
    """Test execute_known_target with a valid target at global scope"""
    mock_run_cmake, expected_call = mock_execute_known_target(
        cmake_handler, None, top_target=True
    )
    mock_run_cmake.assert_called_once()
    mock_run_cmake.assert_has_calls([expected_call])


def test_execute_known_cache_invalid(cmake_handler):
    """Test execute_known_target triggering an invalid cache"""

    def extra_setup(_, mock_validate_cmake_cache):
        """Perform extra setup to the basic mock calls"""
        mock_validate_cmake_cache.side_effect = CMakeInconsistentCacheException(
            "Module", "A", "B"
        )

    with pytest.raises(
        CMakeInconsistentCacheException,
        match="Module to be set to 'A', was actually set to 'B'",
    ):
        mock_run_cmake, expected_call = mock_execute_known_target(
            cmake_handler, extra_setup
        )
        # Verify that _run_cmake was called with the correct arguments
        mock_run_cmake.assert_not_called()


def test_execute_known_valid_targets_with_environment(cmake_handler):
    """Test execute_known_target on valid local and global targets with supplied environment"""
    mock_run_cmake, expected_call = mock_execute_known_target(
        cmake_handler, None, environment={"MY_ENV_VAR": "VALUE1"}
    )
    mock_run_cmake.assert_called_once()
    mock_run_cmake.assert_has_calls([expected_call])
    mock_run_cmake, expected_call = mock_execute_known_target(
        cmake_handler, None, environment={"MY_ENV_VAR": "VALUE1"}, top_target=True
    )
    mock_run_cmake.assert_called_once()
    mock_run_cmake.assert_has_calls([expected_call])


def test_execute_known_valid_targets_with_make_args(cmake_handler):
    """Test execute_known_target on valid local and global targets with supplied make_args

    Make args are supplied as command line arguments after a -- when CMake is called.
    """
    mock_run_cmake, expected_call = mock_execute_known_target(
        cmake_handler, None, make_args={"--make-arg": "VALUE1"}
    )
    mock_run_cmake.assert_called_once()
    mock_run_cmake.assert_has_calls([expected_call])
    mock_run_cmake, expected_call = mock_execute_known_target(
        cmake_handler, None, make_args={"--make-arg": "VALUE1"}, top_target=True
    )
    mock_run_cmake.assert_called_once()
    mock_run_cmake.assert_has_calls([expected_call])


def test_execute_known_valid_targets_with_cmake_args(cmake_handler):
    """Test execute_known_target on valid local and global targets with supplied cmake_args

    CMake args **are not** supplied to the cmake call, but are used only to validate the cache.
    """
    mock_run_cmake, expected_call = mock_execute_known_target(
        cmake_handler, None, make_args={"--make-arg": "VALUE1"}
    )
    mock_run_cmake.assert_called_once()
    mock_run_cmake.assert_has_calls([expected_call])
    mock_run_cmake, expected_call = mock_execute_known_target(
        cmake_handler, None, cmake_args={"--cmake-arg": "VALUE1"}, top_target=True
    )
    mock_run_cmake.assert_called_once()
    mock_run_cmake.assert_has_calls([expected_call])


@patch("fprime.fbuild.cmake.CMakeHandler._is_noop_supported")
@patch("fprime.fbuild.cmake.CMakeHandler.execute_known_target")
def cmake_refresh_cache(
    noop_supported,
    cmake_handler,
    mock_execute_known_target,
    mock_is_noop_supported,
    **kwargs,
):
    """Test the CMake cache refresh calls

    Tests that cmake_refresh_cache properly operates in calling execute_known_target under different circumstances. This
    helper assumes that this code will not do a full refresh.
    """
    mock_is_noop_supported.return_value = noop_supported
    assert not kwargs.get(
        "full", False
    ), "CMake refresh cache helper cannot be used with 'full'"

    cmake_handler.cmake_refresh_cache("/some/build/dir", **kwargs)
    mock_execute_known_target.assert_called_once_with(
        "noop" if noop_supported else "refresh_cache",  # Expected target to use
        "/some/build/dir",  # Build directory
        None,  # Path unused for global target
        top_target=True,  # Global target
        full_cache_rebuild=True,  # Prevents infinite recursion, fallback for if the refresh target fails
        print_output=True,  # User will want to know
        environment=kwargs.get("environment", {}),
    )


def test_refresh_cache_noop(cmake_handler):
    """Test the refresh cache handler with older 'noop' target"""
    cmake_refresh_cache(True, cmake_handler)


def test_refresh_cache_refresh(cmake_handler):
    """Test the refresh cache handler with newer 'refresh_cache' target"""
    cmake_refresh_cache(False, cmake_handler)


def test_refresh_cache_noop_with_environment(cmake_handler):
    """Test the refresh cache handler with older 'noop' target"""
    cmake_refresh_cache(True, cmake_handler, environment={"MY_ENV_VAR": "VALUE1"})


@patch("os.makedirs")
@patch("os.path.exists")
@patch("pathlib.Path.touch")
@patch("fprime.fbuild.cmake.CMakeHandler.cmake_validate_source_dir")
@patch("fprime.fbuild.cmake.CMakeHandler._run_cmake")
def generate_build(
    arguments,
    exists,
    cmake_handler,
    mock_run_cmake,
    mock_validate_source_dir,
    mock_touch,
    mock_path_exists,
    mock_makedirs,
    **kwargs,
):
    """Run the generate_build function with mocked dependencies.

    This will run a mocked version of generate_build for the purposes of testing the function. This function supplies
    the standard inputs and asserts the basic calls to the underlying functions (e.g. _run_cmake) through the mocking
    pattern.

    Args:
        arguments: tuple of (dictionary, list of strings) representing the passed-in and output arguments to cmake
        cmake_handler: object under test (from harness)
        ...: mocked out functions
    """
    source_dir = "/fake/source/dir"
    build_dir = "/fake/build/dir"
    kwargs["args"], expected_cmake_args = arguments

    # Mock os.path.exists to return False, simulating that the build_dir does not exist
    mock_path_exists.return_value = exists

    # Call the generate_build function
    cmake_handler.generate_build(source_dir, build_dir, **kwargs)

    # Asset that the touch method was called once
    mock_touch.assert_called_once()

    # Assert that cmake_validate_source_dir was called with the correct source_dir
    mock_validate_source_dir.assert_called_once_with(source_dir)

    # Assert that os.makedirs was called to create the build directory only when it does not exist
    if exists:
        mock_makedirs.assert_not_called()
    else:
        mock_makedirs.assert_called_once_with(build_dir)
    # Assert that _run_cmake was called with the correct arguments
    expected_cmake_args = ["-S", str(Path(source_dir).resolve())] + expected_cmake_args
    mock_run_cmake.assert_called_once_with(
        expected_cmake_args,
        workdir=build_dir,
        print_output=True,
        write_override=True,
        environment=kwargs.get("environment", None),
    )


def test_generate(cmake_handler):
    """Test basic generate build call

    Tests generate_build with no arguments, off-nominal conditions, nor environment. Delegates to the generate_build.
    """
    generate_build(({}, []), False, cmake_handler)


def test_generate_with_args(cmake_handler):
    """Test basic generate build call with supplied cmake arguments

    Tests generate_build with arguments but no off-nominal conditions, nor environment. Delegates to the generate_build.
    """
    generate_build(
        (
            {"CMAKE_BUILD_TYPE": "Debug", "--some-flag": "some-value"},
            ["-DCMAKE_BUILD_TYPE=Debug", "--some-flag=some-value"],
        ),
        False,
        cmake_handler,
    )


def test_generate_environment(cmake_handler):
    """Test basic generate build call with supplied environment

    Tests generate_build with environment but no off-nominal conditions, nor arguments. Delegates to the generate_build.
    """
    generate_build(({}, []), False, cmake_handler, environment={"MY_ENV_VAR": "VALUE1"})


def test_generate_exists(cmake_handler):
    """Test basic generate build call with supplied environment

    Tests generate_build with pre-existing directory.
    """
    generate_build(({}, []), True, cmake_handler)
