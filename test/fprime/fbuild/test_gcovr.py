"""Tests for fprime.fbuild.gcovr"""

from unittest.mock import MagicMock, patch

from fprime.fbuild.gcovr import Gcovr
from fprime.fbuild.target import TargetScope


def _mock_builder(tmp_path):
    """A builder mock with just enough surface for Gcovr.execute() to run"""
    builder = MagicMock()
    builder.build_dir = tmp_path
    builder.get_settings.side_effect = lambda key, default=None: default
    builder.is_project_root.return_value = True
    builder.settings = {}
    builder.cmake.verbose = False
    return builder


def _gcovr_args():
    """A minimal (make_args, pass_through_args, options) tuple accepted by Gcovr.execute()"""
    options = {
        "--all-sources": False,
        "--comp-ac": False,
        "--port-ac": False,
        "--type-ac": False,
        "--test-ac": False,
        "--test-sources": False,
    }
    return ({}, [], options)


def test_gcovr_reports_nonzero_return_code(tmp_path, capsys):
    """A failing gcovr invocation is reported to stderr, not silently discarded"""
    builder = _mock_builder(tmp_path)
    gcovr = Gcovr(TargetScope.LOCAL)

    with (
        patch("fprime.fbuild.gcovr.shutil.which", return_value="/usr/bin/gcovr"),
        patch("fprime.fbuild.gcovr.subprocess.call", return_value=1) as mock_call,
    ):
        gcovr.execute(builder, tmp_path, _gcovr_args())

    mock_call.assert_called_once()
    captured = capsys.readouterr()
    assert "[ERROR]" in captured.err
    assert "gcovr exited with code 1" in captured.err


def test_gcovr_silent_on_success(tmp_path, capsys):
    """A successful gcovr invocation prints no error"""
    builder = _mock_builder(tmp_path)
    gcovr = Gcovr(TargetScope.LOCAL)

    with (
        patch("fprime.fbuild.gcovr.shutil.which", return_value="/usr/bin/gcovr"),
        patch("fprime.fbuild.gcovr.subprocess.call", return_value=0) as mock_call,
    ):
        gcovr.execute(builder, tmp_path, _gcovr_args())

    mock_call.assert_called_once()
    captured = capsys.readouterr()
    assert "[ERROR]" not in captured.err
