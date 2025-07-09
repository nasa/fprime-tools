from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fprime.fbuild.enumerator import (
    BasicBuildTargetEnumerator,
    CliBuildTargetEnumerator,
    DesignateTargetAction,
    MultiBuildTargetEnumerator,
    RecursiveMultiBuildTargetEnumerator,
    SpecificBuildTargetEnumerator,
)
from fprime.fbuild.types import MissingBuildCachePath

# Path to the test data directory
ENUMERATOR_DATA_PATH = Path(__file__).parent / "enumerator_data"


def test_basic_enumeration():
    """Test basic enumeration with and without a suffix"""
    # Setup mock builder
    builder_mock = MagicMock()
    builder_mock.cmake.get_cmake_module.return_value = "TestModule"

    # Test without suffix
    enumerator = BasicBuildTargetEnumerator()
    context_path = ENUMERATOR_DATA_PATH / "BasicBuildTargetEnumerator"
    assert enumerator.enumerate(builder_mock, context_path) == ["TestModule"]
    builder_mock.cmake.get_cmake_module.assert_called_once_with(
        context_path, builder_mock.build_dir
    )


def test_basic_enumeration_with_suffix():
    """Test basic enumeration with a suffix"""
    # Setup mock builder
    builder_mock = MagicMock()
    builder_mock.cmake.get_cmake_module.return_value = "TestModule"
    # Test with suffix
    enumerator_suffix = BasicBuildTargetEnumerator(target_suffix="test")
    context_path = ENUMERATOR_DATA_PATH / "BasicBuildTargetEnumerator"
    assert enumerator_suffix.enumerate(builder_mock, context_path) == [
        "TestModule_test"
    ]
    builder_mock.cmake.get_cmake_module.assert_called_once_with(
        context_path, builder_mock.build_dir
    )


def test_multi_build_target_enumerator_default():
    """Test MultiBuildTargetEnumerator with default file"""
    data_path = ENUMERATOR_DATA_PATH / "MultiBuildTargetEnumerator"
    builder_mock = MagicMock()
    builder_mock.get_build_cache_path.return_value = data_path

    # Test with default build-targets.fprime-util
    enumerator = MultiBuildTargetEnumerator()
    expected_targets = ["targetA", "targetB", "targetC"]
    assert enumerator.enumerate(builder_mock, data_path) == expected_targets


def test_multi_build_target_enumerator_tests_file():
    """Test MultiBuildTargetEnumerator with tests.fprime-util"""
    data_path = ENUMERATOR_DATA_PATH / "MultiBuildTargetEnumerator"
    builder_mock = MagicMock()
    builder_mock.get_build_cache_path.return_value = data_path

    # Test with tests.fprime-util
    test_enumerator = MultiBuildTargetEnumerator(
        build_file_name=MultiBuildTargetEnumerator.TEST_BUILD_TARGETS_FILE
    )
    expected_test_targets = ["testTargetX", "testTargetY"]
    assert test_enumerator.enumerate(builder_mock, data_path) == expected_test_targets


def test_multi_build_target_enumerator_fallback():
    """Test MultiBuildTargetEnumerator fallback"""
    # Test fallback by pointing to a directory without the file
    fallback_path = ENUMERATOR_DATA_PATH / "BasicBuildTargetEnumerator"
    builder_mock = MagicMock()
    builder_mock.get_build_cache_path.return_value = fallback_path
    fail_safe_mock = MagicMock()
    fail_safe_mock.enumerate.return_value = ["fallback_target"]
    fallback_enumerator = MultiBuildTargetEnumerator(
        fail_safe_enumerator=fail_safe_mock
    )
    assert fallback_enumerator.enumerate(builder_mock, fallback_path) == [
        "fallback_target"
    ]
    fail_safe_mock.enumerate.assert_called_once_with(builder_mock, fallback_path)


def test_multi_build_target_enumerator_fallback_exception():
    """Test MultiBuildTargetEnumerator fallback on exception"""
    context_path = Path("/path/to/context")
    builder_mock = MagicMock()
    builder_mock.get_build_cache_path.side_effect = MissingBuildCachePath(context_path)

    fail_safe_mock = MagicMock()
    fail_safe_mock.enumerate.return_value = ["fallback_target"]
    fallback_enumerator = MultiBuildTargetEnumerator(
        fail_safe_enumerator=fail_safe_mock
    )

    assert fallback_enumerator.enumerate(builder_mock, context_path) == [
        "fallback_target"
    ]
    fail_safe_mock.enumerate.assert_called_once_with(builder_mock, context_path)


def test_recursive_multi_build_target_enumerator():
    """Tests the recursive enumeration of targets"""
    root_path = ENUMERATOR_DATA_PATH / "RecursiveMultiBuildTargetEnumerator"
    builder_mock = MagicMock()

    # For our test setup, the 'build cache' is the directory itself.
    builder_mock.get_build_cache_path.side_effect = lambda path: path

    enumerator = RecursiveMultiBuildTargetEnumerator()
    found_targets = enumerator.enumerate(builder_mock, root_path)

    expected_targets = {
        "root_target1",
        "root_target2",
        "sub1_target1",
        "sub2_target1",
        "sub2_1_target1",
    }
    # Using set for order-independent comparison
    assert set(found_targets) == expected_targets


def test_recursive_multi_build_target_enumerator_custom_file():
    """Tests the recursive enumeration with a custom test file"""
    root_path = ENUMERATOR_DATA_PATH / "RecursiveMultiBuildTargetEnumerator"
    builder_mock = MagicMock()

    # For our test setup, the 'build cache' is the directory itself.
    builder_mock.get_build_cache_path.side_effect = lambda path: path

    # Create a MultiBuildTargetEnumerator that looks for the test file
    test_file_enumerator = MultiBuildTargetEnumerator(
        build_file_name=MultiBuildTargetEnumerator.TEST_BUILD_TARGETS_FILE
    )
    # Create the recursive enumerator with the custom enumerator
    enumerator = RecursiveMultiBuildTargetEnumerator(
        directory_enumerator=test_file_enumerator
    )

    found_targets = enumerator.enumerate(builder_mock, root_path)

    expected_targets = {
        "root_test1",
        "sub2_test1",
        "sub2_test2",
    }
    assert set(found_targets) == expected_targets


def test_recursive_enumerator_fallback_on_file_not_found():
    """Test recursive enumerator falls back when helper returns empty"""
    # Point to a directory that exists but does not contain target/sub-directory files
    path = ENUMERATOR_DATA_PATH / "BasicBuildTargetEnumerator"
    builder_mock = MagicMock()
    builder_mock.get_build_cache_path.return_value = path
    # When the recursive search yields no targets, it falls back to the basic
    # enumerator, which will call get_cmake_module. We mock its return value.
    builder_mock.cmake.get_cmake_module.return_value = "fallback_target"

    enumerator = RecursiveMultiBuildTargetEnumerator()
    # Since enumerate_helper returns [], the fallback enumerator should be called
    assert enumerator.enumerate(builder_mock, path) == ["fallback_target"]
    # Verify that the fallback was indeed triggered
    builder_mock.cmake.get_cmake_module.assert_called_once_with(
        path, builder_mock.build_dir
    )


def test_specific_build_target_enumerator_constructor():
    """Test SpecificBuildTargetEnumerator returns constructor-provided targets"""
    targets = ["specific_target1", "specific_target2"]
    enumerator = SpecificBuildTargetEnumerator(build_targets=targets)
    # The builder and context path are not used by this enumerator
    assert enumerator.enumerate(None, None) == targets


def test_specific_build_target_enumerator_assertion():
    """Test SpecificBuildTargetEnumerator asserts when targets are not set"""
    enumerator = SpecificBuildTargetEnumerator()  # Initialized with None
    with pytest.raises(AssertionError):
        enumerator.enumerate(None, None)


def test_specific_build_target_enumerator_setter():
    """Test SpecificBuildTargetEnumerator's setter overrides constructor targets"""
    initial_targets = ["initial1"]
    override_targets = ["override1", "override2"]

    enumerator = SpecificBuildTargetEnumerator(build_targets=initial_targets)
    assert enumerator.enumerate(None, None) == initial_targets

    enumerator.set_build_targets(override_targets)
    assert enumerator.enumerate(None, None) == override_targets


def test_cli_build_target_enumerator():
    """Test CliBuildTargetEnumerator integrates with DesignateTargetAction"""
    # Reset the designees for a clean test
    DesignateTargetAction._DESIGNEES = []

    # 1. Test Registration and enumeration
    cli_enumerator = CliBuildTargetEnumerator()
    assert cli_enumerator in DesignateTargetAction._DESIGNEES

    # 2. Test Target Setting via Action
    action = DesignateTargetAction(option_strings=["--target"], dest="target")
    parser_mock = MagicMock()
    namespace = MagicMock()
    values = ["cli_target1", "cli_target2"]

    # Simulate argparse calling the action, which should call the real `set_build_targets`
    action(parser_mock, namespace, values)

    # Verify that the namespace is updated as expected
    assert namespace.target is True
    # Verify that a subsequent call to enumerate returns the values set by the action
    assert cli_enumerator.enumerate(None, None) == values
