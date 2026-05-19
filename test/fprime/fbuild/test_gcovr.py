"""test_gcovr.py — unit tests for fprime.fbuild.gcovr.Gcovr.execute()

Focused on the subprocess return-code handling fix:
  subprocess.call()  →  subprocess.run() + CalledProcessError on non-zero exit

Each test patches subprocess.run so no real gcovr binary is needed.

Exit-code semantics (from gcovr docs):
  0  — report generated successfully
  1  — gcovr internal error (bad args, missing .gcda files, permission denied)
  2  — coverage threshold not met (triggered by --fail-under-line / --fail-under-branch)
"""

import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest

from fprime.fbuild.gcovr import Gcovr
from fprime.fbuild.target import TargetScope


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def gcovr_action():
    """Return a bare Gcovr action (no enumerator needed for execute())."""
    return Gcovr(scope=TargetScope.LOCAL)


@pytest.fixture
def mock_builder():
    """Minimal mock Build object providing the attributes Gcovr.execute() reads."""
    builder = MagicMock()
    builder.build_dir = Path("/fake/build")
    builder.cmake.verbose = False
    builder.is_project_root.return_value = False
    builder.get_settings.return_value = Path("/fake/project")
    builder.settings = {"environment": {}}

    # get_build_cache_path must return a Path
    builder.get_build_cache_path.return_value = Path("/fake/build/cache")
    return builder


@pytest.fixture
def execute_args():
    """Standard (make_args, pass_through, options) tuple for Gcovr.execute()."""
    options = {
        "--all-sources": False,
        "--comp-ac": False,
        "--port-ac": False,
        "--type-ac": False,
        "--test-ac": False,
        "--test-sources": False,
    }
    return ({}, [], options)


# ---------------------------------------------------------------------------
# Helper: run Gcovr.execute() with a mocked subprocess returncode
# ---------------------------------------------------------------------------


def _run_with_returncode(gcovr_action, mock_builder, execute_args, returncode):
    """
    Patch shutil.which (gcovr found), patch the coverage output dir mkdir,
    patch subprocess.run to return the given returncode, then call execute().

    Returns (raised_exception_or_None, mock_run_call_args).
    """
    completed = MagicMock()
    completed.returncode = returncode

    with patch("fprime.fbuild.gcovr.shutil.which", return_value="/usr/bin/gcovr"), \
         patch("fprime.fbuild.gcovr.Path.mkdir"), \
         patch("fprime.fbuild.gcovr.subprocess.run", return_value=completed) as mock_run:
        try:
            gcovr_action.execute(mock_builder, Path("/fake/context"), execute_args)
            return None, mock_run
        except Exception as exc:
            return exc, mock_run


# ---------------------------------------------------------------------------
# Tests: subprocess is called correctly
# ---------------------------------------------------------------------------


def test_subprocess_run_is_called(gcovr_action, mock_builder, execute_args):
    """subprocess.run() must be called exactly once (not subprocess.call)."""
    exc, mock_run = _run_with_returncode(
        gcovr_action, mock_builder, execute_args, returncode=0
    )
    assert exc is None
    mock_run.assert_called_once()


def test_subprocess_run_receives_env(gcovr_action, mock_builder, execute_args):
    """The combined OS + settings environment must be forwarded to subprocess.run()."""
    mock_builder.settings = {"environment": {"MY_VAR": "hello"}}
    exc, mock_run = _run_with_returncode(
        gcovr_action, mock_builder, execute_args, returncode=0
    )
    assert exc is None
    _, kwargs = mock_run.call_args
    assert "env" in kwargs
    assert kwargs["env"].get("MY_VAR") == "hello"


def test_gcovr_invoked_as_first_arg(gcovr_action, mock_builder, execute_args):
    """The first element of the cli_args list must be 'gcovr'."""
    exc, mock_run = _run_with_returncode(
        gcovr_action, mock_builder, execute_args, returncode=0
    )
    assert exc is None
    cli_args = mock_run.call_args[0][0]
    assert cli_args[0] == "gcovr"


# ---------------------------------------------------------------------------
# Tests: success path (exit code 0)
# ---------------------------------------------------------------------------


def test_success_no_exception(gcovr_action, mock_builder, execute_args):
    """Exit code 0: execute() must return without raising."""
    exc, _ = _run_with_returncode(
        gcovr_action, mock_builder, execute_args, returncode=0
    )
    assert exc is None


# ---------------------------------------------------------------------------
# Tests: failure paths (exit codes 1 and 2)
# ---------------------------------------------------------------------------


def test_internal_error_raises_called_process_error(
    gcovr_action, mock_builder, execute_args
):
    """Exit code 1 (internal gcovr error) must raise CalledProcessError."""
    exc, _ = _run_with_returncode(
        gcovr_action, mock_builder, execute_args, returncode=1
    )
    assert isinstance(exc, subprocess.CalledProcessError)


def test_internal_error_carries_exit_code(gcovr_action, mock_builder, execute_args):
    """The raised CalledProcessError must carry returncode 1."""
    exc, _ = _run_with_returncode(
        gcovr_action, mock_builder, execute_args, returncode=1
    )
    assert exc.returncode == 1


def test_threshold_not_met_raises_called_process_error(
    gcovr_action, mock_builder, execute_args
):
    """Exit code 2 (threshold not met) must raise CalledProcessError."""
    exc, _ = _run_with_returncode(
        gcovr_action, mock_builder, execute_args, returncode=2
    )
    assert isinstance(exc, subprocess.CalledProcessError)


def test_threshold_not_met_carries_exit_code(gcovr_action, mock_builder, execute_args):
    """The raised CalledProcessError must carry returncode 2."""
    exc, _ = _run_with_returncode(
        gcovr_action, mock_builder, execute_args, returncode=2
    )
    assert exc.returncode == 2


def test_arbitrary_nonzero_raises_called_process_error(
    gcovr_action, mock_builder, execute_args
):
    """Any non-zero exit code (e.g. 127 = binary not found by shell) must raise."""
    exc, _ = _run_with_returncode(
        gcovr_action, mock_builder, execute_args, returncode=127
    )
    assert isinstance(exc, subprocess.CalledProcessError)


# ---------------------------------------------------------------------------
# Tests: stderr messages
# ---------------------------------------------------------------------------


def test_unexpected_error_prints_generic_message(
    gcovr_action, mock_builder, execute_args, capsys
):
    """Exit code 1 must print a generic [ERROR] message to stderr."""
    _run_with_returncode(gcovr_action, mock_builder, execute_args, returncode=1)
    captured = capsys.readouterr()
    assert "[ERROR]" in captured.err
    assert "1" in captured.err  # exit code must appear in the message


def test_threshold_prints_threshold_message(
    gcovr_action, mock_builder, execute_args, capsys
):
    """Exit code 2 must print the coverage-threshold-specific [ERROR] message."""
    _run_with_returncode(gcovr_action, mock_builder, execute_args, returncode=2)
    captured = capsys.readouterr()
    assert "[ERROR]" in captured.err
    # The message should mention thresholds, not just a raw exit code
    assert "threshold" in captured.err.lower()


def test_internal_error_prints_internal_error_message(
    gcovr_action, mock_builder, execute_args, capsys
):
    """Exit code 1 must print a message that mentions 'internal error' and the code.

    Guards against two bugs:
    - print(str1, str2, file=stderr) joins with a space, not a newline — the two
      string args must be concatenated into one so the message reads correctly.
    - The message must not say 'successfully' for a non-zero exit code.
    """
    _run_with_returncode(gcovr_action, mock_builder, execute_args, returncode=1)
    captured = capsys.readouterr()
    assert "[ERROR]" in captured.err
    assert "internal error" in captured.err.lower()
    assert "successfully" not in captured.err.lower()
    # Both parts of the message must appear in one unbroken stderr line
    assert "Check the output above for details." in captured.err


def test_unexpected_exit_code_does_not_say_successfully(
    gcovr_action, mock_builder, execute_args, capsys
):
    """Exit codes other than 1 and 2 must not use the word 'successfully'.

    Guards against the misleading 'gcovr successfully exited' wording that
    appeared in the else-branch before it was corrected.
    """
    _run_with_returncode(gcovr_action, mock_builder, execute_args, returncode=127)
    captured = capsys.readouterr()
    assert "successfully" not in captured.err.lower()
    assert "[ERROR]" in captured.err


def test_success_prints_no_error(gcovr_action, mock_builder, execute_args, capsys):
    """Exit code 0 must produce no [ERROR] output."""
    _run_with_returncode(gcovr_action, mock_builder, execute_args, returncode=0)
    captured = capsys.readouterr()
    assert "[ERROR]" not in captured.err


# ---------------------------------------------------------------------------
# Tests: pass-through args are forwarded to gcovr
# ---------------------------------------------------------------------------


def test_pass_through_args_appended(gcovr_action, mock_builder):
    """--pass-through arguments must appear at the end of the gcovr invocation."""
    options = {k: False for k in [
        "--all-sources", "--comp-ac", "--port-ac",
        "--type-ac", "--test-ac", "--test-sources",
    ]}
    pass_through = ["--fail-under-line=80", "--fail-under-branch=60"]
    args = ({}, pass_through, options)

    completed = MagicMock()
    completed.returncode = 0

    with patch("fprime.fbuild.gcovr.shutil.which", return_value="/usr/bin/gcovr"), \
         patch("fprime.fbuild.gcovr.Path.mkdir"), \
         patch("fprime.fbuild.gcovr.subprocess.run", return_value=completed) as mock_run:
        gcovr_action.execute(mock_builder, Path("/fake/context"), args)

    cli_args = mock_run.call_args[0][0]
    assert "--fail-under-line=80" in cli_args
    assert "--fail-under-branch=60" in cli_args


# ---------------------------------------------------------------------------
# Tests: gcovr not found
# ---------------------------------------------------------------------------


def test_gcovr_not_found_returns_early(gcovr_action, mock_builder, execute_args):
    """If gcovr is not on PATH, execute() must return without calling subprocess."""
    with patch("fprime.fbuild.gcovr.shutil.which", return_value=None), \
         patch("fprime.fbuild.gcovr.subprocess.run") as mock_run:
        gcovr_action.execute(mock_builder, Path("/fake/context"), execute_args)

    mock_run.assert_not_called()


# ---------------------------------------------------------------------------
# Tests: exception propagates through CompositeTarget (integration)
# ---------------------------------------------------------------------------


def test_called_process_error_propagates_through_composite(
    gcovr_action, mock_builder, execute_args
):
    """CalledProcessError must bubble through CompositeTarget.execute() unchanged.

    CompositeTarget uses try/finally (not try/except), so exceptions from child
    execute() calls must reach the caller intact — matching the behaviour of the
    check.py CTest step.
    """
    from fprime.fbuild.target import CompositeTarget, TargetScope

    composite = CompositeTarget(
        [gcovr_action],
        mnemonic="coverage",
        desc="coverage",
        scope=TargetScope.LOCAL,
    )

    completed = MagicMock()
    completed.returncode = 1

    with patch("fprime.fbuild.gcovr.shutil.which", return_value="/usr/bin/gcovr"), \
         patch("fprime.fbuild.gcovr.Path.mkdir"), \
         patch("fprime.fbuild.gcovr.subprocess.run", return_value=completed):
        with pytest.raises(subprocess.CalledProcessError):
            composite.execute(mock_builder, Path("/fake/context"), execute_args)
