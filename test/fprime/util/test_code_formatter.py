"""
Tests for fprime.util.code_formatter
"""

from pathlib import Path

import shutil
from unittest.mock import MagicMock

import pytest
from fprime.util.code_formatter import ClangFormatter, FppFormatter


def test_init():
    """Test initialization"""
    options = {
        "backup": True,
        "verbose": True,
        "quiet": False,
        "check": False,
        "validate_extensions": True,
    }
    formatter = ClangFormatter("clang-format", Path(".clang-format"), options)
    assert formatter is not None


def test_stage_file(tmp_path):
    """Test staging files for formatting"""
    # Create dummy files
    cpp_file = tmp_path / "test.cpp"
    cpp_file.touch()
    txt_file = tmp_path / "test.txt"
    txt_file.touch()
    non_existent_file = tmp_path / "does_not_exist.cpp"

    options = {"validate_extensions": True, "verbose": True}
    formatter = ClangFormatter("clang-format", Path(".clang-format"), options)

    # Stage files
    formatter.stage_file(cpp_file)
    formatter.stage_file(txt_file)
    formatter.stage_file(non_existent_file)

    # Check that only the valid C++ file was staged
    assert len(formatter._files_to_format) == 1
    assert formatter._files_to_format[0] == cpp_file


def test_stage_file_no_validation(tmp_path):
    """Test staging files with extension validation disabled"""
    # Create dummy files
    cpp_file = tmp_path / "test.cpp"
    cpp_file.touch()
    txt_file = tmp_path / "test.txt"
    txt_file.touch()

    options = {"validate_extensions": False}
    formatter = ClangFormatter("clang-format", Path(".clang-format"), options)

    # Stage files
    formatter.stage_file(cpp_file)
    formatter.stage_file(txt_file)

    # Check that both files were staged
    assert len(formatter._files_to_format) == 2
    assert cpp_file in formatter._files_to_format
    assert txt_file in formatter._files_to_format


def test_allow_extension(tmp_path):
    """Test allowing a new extension"""
    txt_file = tmp_path / "test.txt"
    txt_file.touch()

    options = {"validate_extensions": True}
    formatter = ClangFormatter("clang-format", Path(".clang-format"), options)
    formatter.allow_extension(".txt")
    formatter.stage_file(txt_file)

    assert len(formatter._files_to_format) == 1
    assert formatter._files_to_format[0] == txt_file


DATA_DIR = Path(__file__).parent / "data"


@pytest.fixture
def mock_build():
    """Pytest fixture for a mock build object"""
    build = MagicMock()
    build.settings = {}
    return build


@pytest.fixture
def style_file(tmp_path):
    """Pytest fixture for a style file"""
    clang_format_file = tmp_path / ".clang-format"
    clang_format_file.write_text("BasedOnStyle: LLVM\n")
    return clang_format_file


def test_execute_format(tmp_path, mock_build, style_file):
    """Test that execute formats a file"""
    malformed_src = DATA_DIR / "malformed.cpp"
    malformed_dst = tmp_path / "malformed.cpp"
    shutil.copy(malformed_src, malformed_dst)

    options = {"backup": False, "verbose": False, "quiet": True, "check": False}
    formatter = ClangFormatter("clang-format", style_file, options)
    formatter.stage_file(malformed_dst)

    result = formatter.execute(mock_build, tmp_path, ({}, []))
    assert result == 0

    well_formed_content = (DATA_DIR / "well-formed.cpp").read_text()
    assert malformed_dst.read_text() == well_formed_content


def test_execute_check_fail(tmp_path, mock_build, style_file):
    """Test that execute with --check fails on a malformed file"""
    malformed_src = DATA_DIR / "malformed.cpp"
    malformed_dst = tmp_path / "malformed.cpp"
    shutil.copy(malformed_src, malformed_dst)

    options = {"backup": False, "verbose": False, "quiet": True, "check": True}
    formatter = ClangFormatter("clang-format", style_file, options)
    formatter.stage_file(malformed_dst)

    result = formatter.execute(mock_build, tmp_path, ({}, []))
    assert result != 0


def test_execute_check_pass(tmp_path, mock_build, style_file):
    """Test that execute with --check passes on a well-formed file"""
    well_formed_src = DATA_DIR / "well-formed.cpp"
    well_formed_dst = tmp_path / "well-formed.cpp"
    shutil.copy(well_formed_src, well_formed_dst)

    options = {"backup": False, "verbose": False, "quiet": True, "check": True}
    formatter = ClangFormatter("clang-format", style_file, options)
    formatter.stage_file(well_formed_dst)

    result = formatter.execute(mock_build, tmp_path, ({}, []))
    assert result == 0


# ---------------------------------------------------------------------------
# FppFormatter tests
# ---------------------------------------------------------------------------

# A deliberately malformed (but valid) FPP module and its fpp-format output.
# fpp-format's default profile is 2-space indent (see fprime-fpp-format).
MALFORMED_FPP = "module   M {\n        constant  x =    1\n   constant y=2\n}\n"
WELL_FORMED_FPP = "module M {\n  constant x = 1\n  constant y = 2\n}\n"

# End-to-end tests need the fpp-format executable (from fprime-fpp-format).
requires_fpp_format = pytest.mark.skipif(
    shutil.which("fpp-format") is None,
    reason="fpp-format executable (fprime-fpp-format) is not installed",
)


def test_fpp_init():
    """Test FppFormatter initialization"""
    options = {
        "backup": True,
        "verbose": True,
        "quiet": False,
        "check": False,
        "validate_extensions": True,
    }
    formatter = FppFormatter("fpp-format", options)
    assert formatter is not None


def test_fpp_stage_file(tmp_path):
    """Test staging files for FPP formatting: only .fpp is staged by default"""
    fpp_file = tmp_path / "model.fpp"
    fpp_file.touch()
    # .fppi fragments are reached via --recursive-includes, not staged directly
    fppi_file = tmp_path / "fragment.fppi"
    fppi_file.touch()
    cpp_file = tmp_path / "test.cpp"
    cpp_file.touch()
    non_existent_file = tmp_path / "does_not_exist.fpp"

    options = {"validate_extensions": True, "verbose": True}
    formatter = FppFormatter("fpp-format", options)

    formatter.stage_file(fpp_file)
    formatter.stage_file(fppi_file)
    formatter.stage_file(cpp_file)
    formatter.stage_file(non_existent_file)

    # Only the valid, existing .fpp file was staged
    assert formatter._files_to_format == [fpp_file]


def test_fpp_stage_file_no_validation(tmp_path):
    """Test staging FPP files with extension validation disabled"""
    fpp_file = tmp_path / "model.fpp"
    fpp_file.touch()
    cpp_file = tmp_path / "test.cpp"
    cpp_file.touch()

    options = {"validate_extensions": False}
    formatter = FppFormatter("fpp-format", options)

    formatter.stage_file(fpp_file)
    formatter.stage_file(cpp_file)

    assert len(formatter._files_to_format) == 2
    assert fpp_file in formatter._files_to_format
    assert cpp_file in formatter._files_to_format


def test_fpp_exclude_file(tmp_path):
    """Test excluding a staged FPP file"""
    fpp_file = tmp_path / "model.fpp"
    fpp_file.touch()

    formatter = FppFormatter("fpp-format", {"validate_extensions": True})
    formatter.stage_file(fpp_file)
    assert formatter._files_to_format == [fpp_file]

    formatter.exclude_file(fpp_file)
    assert formatter._files_to_format == []


@requires_fpp_format
def test_fpp_execute_format(tmp_path, mock_build):
    """Test that execute formats an FPP file in place"""
    malformed_dst = tmp_path / "model.fpp"
    malformed_dst.write_text(MALFORMED_FPP)

    options = {"backup": False, "verbose": False, "quiet": True, "check": False}
    formatter = FppFormatter("fpp-format", options)
    formatter.stage_file(malformed_dst)

    result = formatter.execute(mock_build, tmp_path, ({}, []))
    assert result == 0
    assert malformed_dst.read_text() == WELL_FORMED_FPP


@requires_fpp_format
def test_fpp_execute_check_fail(tmp_path, mock_build):
    """Test that execute with --check fails on a malformed FPP file"""
    malformed_dst = tmp_path / "model.fpp"
    malformed_dst.write_text(MALFORMED_FPP)

    options = {"backup": False, "verbose": False, "quiet": True, "check": True}
    formatter = FppFormatter("fpp-format", options)
    formatter.stage_file(malformed_dst)

    result = formatter.execute(mock_build, tmp_path, ({}, []))
    assert result != 0
    # --check must not modify the file
    assert malformed_dst.read_text() == MALFORMED_FPP


@requires_fpp_format
def test_fpp_execute_check_pass(tmp_path, mock_build):
    """Test that execute with --check passes on a well-formed FPP file"""
    well_formed_dst = tmp_path / "model.fpp"
    well_formed_dst.write_text(WELL_FORMED_FPP)

    options = {"backup": False, "verbose": False, "quiet": True, "check": True}
    formatter = FppFormatter("fpp-format", options)
    formatter.stage_file(well_formed_dst)

    result = formatter.execute(mock_build, tmp_path, ({}, []))
    assert result == 0


def test_fpp_execute_no_files(mock_build, tmp_path):
    """Test that execute is a no-op (success) when no files are staged"""
    formatter = FppFormatter("fpp-format", {})
    result = formatter.execute(mock_build, tmp_path, ({}, []))
    assert result == 0
