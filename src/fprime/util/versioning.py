""" FPP tools to requirements file version check """
import argparse
import sys
from pathlib import Path


class VersionException(Exception):
    pass


def get_version(package: str, requirements: Path):
    """Get the version as specified in the requirements file

    This will read all requirements from the requirements file and attempt to print the version of the package that is
    listed within. This can handle multiple styles of requirements. Firm requirements designated by a "==" and developer
    requirements designated with an "@".

    Args:
        package: name of package to look for
        requirements: path to requirements file to parse
    """
    with open(requirements, "r") as file_handle:
        matching_lines = [
            line.strip() for line in file_handle.readlines() if package in line
        ]
    if not matching_lines:
        msg = f"Could not find {package} in requirements file"
        raise VersionException(msg)
    valid_lines = [line for line in matching_lines if "==" in line or "@" in line]
    if not valid_lines:
        msg = f"{package} has inexact version, use '==' or '@' format. Found: {matching_lines}"
        raise VersionException(
            msg
        )

    # Collapse versions that match
    versions = list({line.split("==")[-1].split("@")[-1] for line in valid_lines})
    if len(versions) != 1:
        msg = f"Conflicting versions specified for {package}: {versions}"
        raise VersionException(
            msg
        )
    return versions[0]


def main():
    """Parses arguments and acts as entry point for the tool"""
    parser = argparse.ArgumentParser(
        description="Detects the required package using a requirements file"
    )
    parser.add_argument("package", help="Package to check for version")
    parser.add_argument(
        "requirements", help="Python formatted requirements file to parse"
    )

    try:
        args_ns = parser.parse_args()
        python_version = get_version(args_ns.package, Path(args_ns.requirements))

        # Add expected v at the front, if missing
        if "." in python_version and not python_version.lower().startswith("v"):
            python_version = f"v{python_version}"
        # Add in a g as a version-control tag for hash versions:
        elif "." not in python_version:
            python_version = f"g{python_version}"
        print(python_version)
    except (IOError, VersionException) as exc:
        print(f"[ERROR] Could not detect expected version: {exc}", file=sys.stderr)
        sys.exit(-1)
    sys.exit(0)


if __name__ == "__main__":
    main()
