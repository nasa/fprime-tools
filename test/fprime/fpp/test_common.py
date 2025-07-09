"""
Tests for fprime.fpp.common
"""
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from fprime.fpp.common import FppUtility, FppMissingSupportFiles


@pytest.fixture
def mock_build(tmp_path):
    """Pytest fixture for a mock build object"""
    build = MagicMock()
    build.build_dir = tmp_path
    build.get_build_cache_path.return_value = tmp_path / "cache"
    (tmp_path / "cache").mkdir()
    return build


def test_init():
    """Test FppUtility initialization"""
    utility = FppUtility("fpp-to-xml")
    assert utility.utility == "fpp-to-xml"
    assert utility.imports_as_sources is True

    utility_no_imports = FppUtility("fpp-check", imports_as_sources=False)
    assert utility_no_imports.imports_as_sources is False


def test_get_locations_file(mock_build, tmp_path):
    """Test get_locations_file successfully finds file"""
    expected_path = tmp_path / "locs.fpp"
    expected_path.touch()
    path = FppUtility.get_locations_file(mock_build)
    assert path == expected_path


def test_get_locations_file_missing(mock_build):
    """Test get_locations_file fails when file is missing"""
    with pytest.raises(FppMissingSupportFiles):
        FppUtility.get_locations_file(mock_build)


def test_get_fpp_inputs(mock_build, tmp_path):
    """Test get_fpp_inputs successfully reads files"""
    import_list_file = tmp_path / "cache" / "fpp-import-list"
    source_list_file = tmp_path / "cache" / "fpp-source-list"

    import_list_file.write_text("A.fpp;B.fpp;")
    source_list_file.write_text("C.fpp;D.fpp;")

    imports, sources = FppUtility.get_fpp_inputs(mock_build, tmp_path)

    assert imports == [Path("A.fpp"), Path("B.fpp")]
    assert sources == [Path("C.fpp"), Path("D.fpp")]


def test_get_fpp_inputs_missing(mock_build, tmp_path):
    """Test get_fpp_inputs fails when a file is missing"""
    with pytest.raises(FppMissingSupportFiles):
        FppUtility.get_fpp_inputs(mock_build, tmp_path)


@patch("subprocess.run")
@patch("shutil.which", return_value="/path/to/fpp-to-xml")
def test_execute_imports_as_sources(mock_which, mock_run, mock_build, tmp_path):
    """Test execute with imports as sources"""
    # Setup
    (tmp_path / "locs.fpp").touch()
    (tmp_path / "cache" / "fpp-import-list").write_text("A.fpp;B.fpp;")
    (tmp_path / "cache" / "fpp-source-list").write_text("C.fpp;D.fpp;")

    utility = FppUtility("fpp-to-xml", imports_as_sources=True)
    utility.execute(mock_build, tmp_path, ({}, []))

    # Check call
    mock_run.assert_called_once()
    call_args = mock_run.call_args[0][0]
    assert call_args == [
        "fpp-to-xml",
        str(tmp_path / "locs.fpp"),
        "A.fpp",
        "B.fpp",
        "C.fpp",
        "D.fpp",
    ]


@patch("subprocess.run")
@patch("shutil.which", return_value="/path/to/fpp-check")
def test_execute_imports_as_flag(mock_which, mock_run, mock_build, tmp_path):
    """Test execute with imports as -i flag"""
    # Setup
    (tmp_path / "locs.fpp").touch()
    (tmp_path / "cache" / "fpp-import-list").write_text("A.fpp;B.fpp;")
    (tmp_path / "cache" / "fpp-source-list").write_text("C.fpp;D.fpp;")

    utility = FppUtility("fpp-check", imports_as_sources=False)
    utility.execute(mock_build, tmp_path, ({}, []))

    # Check call
    mock_run.assert_called_once()
    call_args = mock_run.call_args[0][0]
    assert call_args == [
        "fpp-check",
        "-i",
        "A.fpp,B.fpp",
        str(tmp_path / "locs.fpp"),
        "C.fpp",
        "D.fpp",
    ]
