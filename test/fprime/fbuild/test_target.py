"""
Tests for fprime.fbuild.target
"""

from pathlib import Path
from unittest.mock import MagicMock, call

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

        def any_supported(self, builder, context_with_path):
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
    enumerated_results = ["target1", "target2"], Path("/path/to/context")
    mock_enumerator.enumerate.return_value = enumerated_results

    class ConcreteEnumeratedAction(EnumeratedAction):
        def execute_all(self, builder, context, args):
            pass

        def any_supported(self, builder, context_with_path):
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


def test_check_coverage_existing_targets_gcovr_only():
    """Test that check --coverage --existing targets run gcovr only (no test execution)"""
    import fprime.fbuild.target_definitions  # noqa: F401 registers targets
    from fprime.fbuild.gcovr import ExistingCoverageTarget, Gcovr

    for flags in [
        {"coverage", "existing"},
        {"coverage", "existing", "recursive"},
        {"coverage", "existing", "all"},
    ]:
        target = Target.get_target("check", flags)
        assert isinstance(target, ExistingCoverageTarget)
        assert len(target.targets) == 1
        assert isinstance(target.targets[0], Gcovr)


def test_build_system_target_execute_all_batches(mock_builder):
    """Test that execute_all refreshes the cache, then hands every target to one build system call"""
    target = BuildSystemTarget("build", "", TargetScope.LOCAL)
    target.original_context = Path(".")
    mock_builder.is_verbose.return_value = False

    target.execute_all(
        mock_builder, (["Mod_a", "Mod_b", "Mod_a", "Sub_c"], Path(".")), ({}, [], {})
    )

    assert mock_builder.execute_build_target.call_args_list == [
        call("refresh_cache", Path("."), {}),
        call(["Mod_a", "Mod_b", "Sub_c"], Path("."), {}),
    ]


def test_build_system_target_execute_all_empty(mock_builder):
    """Test that execute_all with no enumerated targets only refreshes the cache"""
    target = BuildSystemTarget("build", "", TargetScope.LOCAL)
    target.original_context = Path(".")
    mock_builder.is_verbose.return_value = False

    target.execute_all(mock_builder, ([], Path(".")), ({}, [], {}))

    mock_builder.execute_build_target.assert_called_once_with(
        "refresh_cache", Path("."), {}
    )


def test_project_and_all_targets_registered():
    """Test --project targets exist alongside the unchanged --all targets"""
    import fprime.fbuild.target_definitions  # noqa: F401 registers the targets
    from fprime.fbuild.enumerator import (
        EverythingBuildTargetEnumerator,
        ProjectBuildTargetEnumerator,
        SpecificBuildTargetEnumerator,
    )

    all_build = Target.get_target("build", {"all"})
    assert isinstance(
        all_build.build_target_enumerator, EverythingBuildTargetEnumerator
    )
    old_cache_builder = MagicMock()
    old_cache_builder.cmake._read_values_from_cache.return_value = (None,)
    assert all_build.build_target_enumerator.enumerate(old_cache_builder, Path("."))[
        0
    ] == ["all"]
    for flags in ({"project"}, {"project", "ut"}):
        project_build = Target.get_target("build", flags)
        assert isinstance(
            project_build.build_target_enumerator, ProjectBuildTargetEnumerator
        )
    project_check = Target.get_target("check", {"project"})
    build_enumerator, test_enumerator = [
        target.build_target_enumerator for target in project_check.targets
    ]
    assert isinstance(build_enumerator, ProjectBuildTargetEnumerator)
    assert isinstance(test_enumerator, ProjectBuildTargetEnumerator)
    assert build_enumerator.build_file_name == "build-targets.fprime-util"
    assert test_enumerator.build_file_name == "tests.fprime-util"
    all_check = Target.get_target("check", {"all"})
    assert len(all_check.targets) == 2
    build_step, test_step = all_check.targets
    assert isinstance(
        build_step.build_target_enumerator, EverythingBuildTargetEnumerator
    )
    assert isinstance(test_step.build_target_enumerator, SpecificBuildTargetEnumerator)


def test_build_system_target_execute_all_verbose(mock_builder, capsys):
    """Test that the verbose path lists every batched target once"""
    target = BuildSystemTarget("build", "", TargetScope.LOCAL)
    target.original_context = Path(".")
    mock_builder.is_verbose.return_value = True

    target.execute_all(mock_builder, (["Mod_a", "Mod_b"], Path(".")), ({}, [], {}))

    assert "[INFO] Building: Mod_a, Mod_b" in capsys.readouterr().out
