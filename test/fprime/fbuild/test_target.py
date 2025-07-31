"""
Tests for fprime.fbuild.target
"""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from fprime.fbuild.target import (
    Target,
    TargetScope,
    CompositeTarget,
    BuildSystemTarget,
    NoSuchTargetException,
    EnumeratedAction,
)
from fprime.fbuild.enumerator import BuildTargetEnumerator


@pytest.fixture(autouse=True)
def clear_registered_targets():
    """Fixture to clear registered targets before each test"""
    Target._Target__REGISTRY = {}
    yield
    Target._Target__REGISTRY = {}


@pytest.fixture
def mock_builder():
    """Pytest fixture for a mock builder object"""
    builder = MagicMock()
    builder.is_verbose.return_value = False
    return builder


def test_register_and_get_target():
    """Test target registration and retrieval"""
    target = Target("test", "A test target", TargetScope.LOCAL)
    Target.register_target(target)

    found_target = Target.get_target("test", set())
    assert found_target == target

    with pytest.raises(NoSuchTargetException):
        Target.get_target("nonexistent", set())


def test_composite_target_execution(mock_builder):
    """Test that a composite target executes its children"""
    child1 = MagicMock(spec=Target, scope=TargetScope.LOCAL)
    child2 = MagicMock(spec=Target, scope=TargetScope.LOCAL)
    composite = CompositeTarget([child1, child2], "composite", "", TargetScope.LOCAL)

    composite.execute(mock_builder, Path("."), (None, None, None))

    child1.execute.assert_called_once()
    child2.execute.assert_called_once()


def test_build_system_target_execution(mock_builder):
    """Test that BuildSystemTarget calls the build system"""
    target = BuildSystemTarget("build", "", TargetScope.LOCAL)
    target.original_context = Path(".")

    target.execute_one(mock_builder, "target_name", ({}, [], {}))

    mock_builder.execute_build_target.assert_called_once_with(
        "target_name", Path("."), {}
    )


def test_enumerated_action_execution(mock_builder):
    """Test that EnumeratedAction executes its enumerator and then execute_all"""
    mock_enumerator = MagicMock(spec=BuildTargetEnumerator)
    enumerated_results = ["target1", "target2"]
    mock_enumerator.enumerate.return_value = enumerated_results

    class ConcreteEnumeratedAction(EnumeratedAction):
        def execute_all(self, builder, context, args):
            pass  # This will be mocked

        def any_supported(self, builder, context):
            return True

    action = ConcreteEnumeratedAction(TargetScope.LOCAL, mock_enumerator)
    action.execute_all = MagicMock()

    context_path = Path("/path/to/context")
    args = ({}, [], {})
    action.execute(mock_builder, context_path, args)

    mock_enumerator.enumerate.assert_called_once_with(mock_builder, context_path)
    action.execute_all.assert_called_once_with(mock_builder, enumerated_results, args)


def test_enumerated_action_is_supported(mock_builder):
    """Test that EnumeratedAction.is_supported calls the enumerator and any_supported"""
    mock_enumerator = MagicMock(spec=BuildTargetEnumerator)
    enumerated_results = ["target1", "target2"]
    mock_enumerator.enumerate.return_value = enumerated_results

    class ConcreteEnumeratedAction(EnumeratedAction):
        def execute_all(self, builder, context, args):
            pass

        def any_supported(self, builder, context):
            return True  # This will be mocked

    action = ConcreteEnumeratedAction(TargetScope.LOCAL, mock_enumerator)
    action.any_supported = MagicMock(return_value=True)

    context_path = Path("/path/to/context")
    result = action.is_supported(mock_builder, context_path)

    assert result is True
    mock_enumerator.enumerate.assert_called_once_with(mock_builder, context_path)
    action.any_supported.assert_called_once_with(mock_builder, enumerated_results)


@pytest.mark.parametrize(
    "child_supported, expected_composite_supported",
    [
        ([True, True], True),
        ([True, False], False),
        ([False, False], False),
    ],
)
def test_composite_target_is_supported(
    child_supported, expected_composite_supported, mock_builder
):
    """Test CompositeTarget.is_supported logic"""
    child1 = MagicMock(spec=Target)
    child1.is_supported.return_value = child_supported[0]
    child2 = MagicMock(spec=Target)
    child2.is_supported.return_value = child_supported[1]

    composite = CompositeTarget([child1, child2], "composite", "", TargetScope.LOCAL)
    result = composite.is_supported(mock_builder, Path("."))

    assert result == expected_composite_supported


def test_composite_target_option_args():
    """Test CompositeTarget.option_args aggregation and deduplication"""
    child1 = MagicMock(spec=Target)
    child1.option_args.return_value = [("--opt1", "Help 1"), ("--opt2", "Help 2")]
    child2 = MagicMock(spec=Target)
    child2.option_args.return_value = [("--opt2", "Help 2"), ("--opt3", "Help 3")]

    composite = CompositeTarget([child1, child2], "composite", "", TargetScope.LOCAL)
    options = composite.option_args()

    assert len(options) == 3
    assert ("--opt1", "Help 1") in options
    assert ("--opt2", "Help 2") in options
    assert ("--opt3", "Help 3") in options


@pytest.mark.parametrize(
    "child_allows_pass, expected_composite_allows_pass",
    [
        ([True, True], True),
        ([True, False], True),
        ([False, False], False),
    ],
)
def test_composite_target_allows_pass_args(
    child_allows_pass, expected_composite_allows_pass
):
    """Test CompositeTarget.allows_pass_args logic"""
    child1 = MagicMock(spec=Target)
    child1.allows_pass_args.return_value = child_allows_pass[0]
    child2 = MagicMock(spec=Target)
    child2.allows_pass_args.return_value = child_allows_pass[1]

    composite = CompositeTarget([child1, child2], "composite", "", TargetScope.LOCAL)
    assert composite.allows_pass_args() == expected_composite_allows_pass


def test_composite_target_pass_handler():
    """Test CompositeTarget.pass_handler joining"""
    child1 = MagicMock(spec=Target)
    child1.pass_handler.return_value = "handler1"
    child2 = MagicMock(spec=Target)
    child2.pass_handler.return_value = None
    child3 = MagicMock(spec=Target)
    child3.pass_handler.return_value = "handler3"

    composite = CompositeTarget(
        [child1, child2, child3], "composite", "", TargetScope.LOCAL
    )
    assert composite.pass_handler() == "handler1,handler3"
