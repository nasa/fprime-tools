"""Tests for fprime.fbuild.check"""

from fprime.fbuild.check import Check


def test_resolve_test_directory_with_file(tmp_path):
    """When test-dir.fprime-util exists, its content is used as the test directory"""
    test_dir = tmp_path / "actual_test_dir"
    test_dir.mkdir()

    test_dir_file = tmp_path / Check.TEST_DIR_FILE
    test_dir_file.write_text(str(test_dir))

    result = Check._resolve_test_directory(tmp_path)
    assert result == test_dir


def test_resolve_test_directory_relative_path(tmp_path):
    """When test-dir.fprime-util contains a relative path, it resolves against build cache path"""
    test_dir = tmp_path / "subdir" / "tests"
    test_dir.mkdir(parents=True)

    test_dir_file = tmp_path / Check.TEST_DIR_FILE
    test_dir_file.write_text("subdir/tests")

    result = Check._resolve_test_directory(tmp_path)
    assert result == test_dir.resolve()


def test_resolve_test_directory_no_file(tmp_path):
    """When test-dir.fprime-util does not exist, falls back to build cache path"""
    result = Check._resolve_test_directory(tmp_path)
    assert result == tmp_path


def test_resolve_test_directory_parent_relative(tmp_path):
    """When test-dir.fprime-util contains a parent-relative path (e.g. ../..), it resolves correctly"""
    # Simulate: build_cache_path is tmp_path/deploy, test dir is tmp_path (the parent)
    deploy_dir = tmp_path / "deploy"
    deploy_dir.mkdir()

    test_dir_file = deploy_dir / Check.TEST_DIR_FILE
    test_dir_file.write_text("..")

    result = Check._resolve_test_directory(deploy_dir)
    assert result == tmp_path.resolve()


def test_execute_all_root_context(tmp_path):
    """Test CTest runs from the build cache root when the enumerated context path is None (check --project)"""
    from unittest.mock import MagicMock, patch
    from fprime.fbuild.target import TargetScope

    builder = MagicMock()
    builder.build_dir = tmp_path
    builder.is_verbose.return_value = False
    check = Check(TargetScope.GLOBAL)

    with patch("fprime.fbuild.check.subprocess.run") as mock_run:
        check.execute_all(builder, ([".*"], None), ({"--jobs": 4}, [], {}))

    builder.get_build_cache_path.assert_not_called()
    mock_run.assert_called_once_with(
        [
            "ctest",
            "--test-dir",
            str(tmp_path),
            "--no-tests=error",
            "--parallel",
            "4",
            "-R",
            "^(.*)$",
        ],
        check=True,
    )
