"""
Tests for fprime.util.code_formatter
"""

from pathlib import Path

import shutil
from unittest.mock import MagicMock

import pytest
from fprime.util.code_formatter import ClangFormatter


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
