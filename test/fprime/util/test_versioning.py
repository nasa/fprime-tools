"""Tests for exact package matching in requirements-file version lookup."""

import subprocess
import sys

import pytest

from fprime.util.versioning import VersionException, get_version


@pytest.mark.parametrize("package", ["fprime-tools", "fprime-gds", "fprime-fpp"])
@pytest.mark.parametrize(
    "distractor",
    [
        "# {package}==1.0.0",
        "other-{package}==1.0.0",
        "{package}-plugin==1.0.0",
        "other @ git+https://example.com/{package}.git@old-revision",
    ],
)
def test_ignores_unrelated_requirements(tmp_path, package, distractor):
    """Comments and substring matches must not introduce version conflicts."""
    requirements = tmp_path / "requirements.txt"
    requirements.write_text(
        distractor.format(package=package) + f"\n{package}==4.2.1\n"
    )
    assert get_version(package, requirements) == "4.2.1"


@pytest.mark.parametrize(
    "text",
    [
        "# fprime-tools==1.0.0\n",
        "other-fprime-tools==1.0.0\n",
        "fprime-tools-extra==1.0.0\n",
        "fprime-tools.extra==1.0.0\n",
        "other==1.0.0 # fprime-tools\n",
    ],
)
def test_missing_package_is_not_satisfied_by_another_line(tmp_path, text):
    """A version is unavailable when the actual package is absent."""
    requirements = tmp_path / "requirements.txt"
    requirements.write_text(text)
    with pytest.raises(VersionException, match="Could not find fprime-tools"):
        get_version("fprime-tools", requirements)


@pytest.mark.parametrize(
    "text,expected",
    [
        ("fprime-tools == 4.2.1 # active release\n", "4.2.1"),
        ("  fprime-tools[dev]==4.2.1\n", "4.2.1"),
        ("fprime-tools==4.2.1\nfprime-tools == 4.2.1 # repeated pin\n", "4.2.1"),
        (
            "fprime-tools @ git+https://example.com/tools.git@abcdef123 # local branch\n",
            "abcdef123",
        ),
        (
            "fprime-tools @ git+https://example.com/tools.git@abcdef123#subdirectory=tools\n",
            "abcdef123#subdirectory=tools",
        ),
    ],
)
def test_whitespace_comments_and_existing_requirement_forms(tmp_path, text, expected):
    """Clean surrounding comments without treating URL fragments as comments."""
    requirements = tmp_path / "requirements.txt"
    requirements.write_text(text)
    assert get_version("fprime-tools", requirements) == expected


@pytest.mark.parametrize(
    "text,message",
    [
        ("fprime-tools>=4.0\n", "inexact version"),
        ("fprime-tools\n", "inexact version"),
        ("fprime-tools==4.0\nfprime-tools==5.0\n", "Conflicting versions"),
    ],
)
def test_invalid_or_conflicting_actual_requirements_still_raise(
    tmp_path, text, message
):
    """Filtering unrelated lines must not weaken existing validation."""
    requirements = tmp_path / "requirements.txt"
    requirements.write_text(text)
    with pytest.raises(VersionException, match=message):
        get_version("fprime-tools", requirements)


@pytest.mark.parametrize(
    "text,expected",
    [
        ("# fprime-tools==3.0\nfprime-tools==4.2.1 # selected\n", "v4.2.1"),
        (
            "fprime-tools-plugin==8.0\nfprime-tools @ git+https://example.com/tools.git@abcdef123\n",
            "gabcdef123",
        ),
    ],
)
def test_cli_reports_the_actual_package_version(tmp_path, text, expected):
    """Exercise the command-line entry point using a real requirements file."""
    requirements = tmp_path / "requirements.txt"
    requirements.write_text(text)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "fprime.util.versioning",
            "fprime-tools",
            str(requirements),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == expected
    assert result.stderr == ""


def test_cli_rejects_comment_only_requirement(tmp_path):
    """The command must fail rather than return a disabled version."""
    requirements = tmp_path / "requirements.txt"
    requirements.write_text("# fprime-tools==4.2.1\n")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "fprime.util.versioning",
            "fprime-tools",
            str(requirements),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode != 0
    assert result.stdout == ""
    assert "Could not find fprime-tools" in result.stderr
