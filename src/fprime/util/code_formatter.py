"""fprime.fbuild.code_formatter

Wrappers for the clang-format and fpp-format utilities.

@author thomas-bc
"""

import re
import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple

from fprime.fbuild.target import ExecutableAction, TargetScope

# clang-format will try to format everything it is given - restrict for the time being
ALLOWED_EXTENSIONS = [
    ".cpp",
    ".c++",
    ".cxx",
    ".cc",
    ".c",
    ".hpp",
    ".h++",
    ".hxx",
    ".hh",
    ".h",
]

# fpp-format formats FPP source files. Only whole `.fpp` files are staged
# directly; `.fppi` include fragments are reached (and formatted with the
# correct entrypoint rule) via fpp-format's --recursive-includes option, since
# a bare fragment carries no context to infer its grammar rule from.
FPP_ALLOWED_EXTENSIONS = [
    ".fpp",
]


class ClangFormatter(ExecutableAction):
    """Class encapsulating the clang-format logic for fprime-util"""

    def __init__(self, executable: str, style_file: "Path", options: Dict):
        super().__init__(TargetScope.LOCAL)
        self.executable = executable
        self.style_file = style_file
        self.backup = options.get("backup", False)
        self.verbose = options.get("verbose", False)
        self.quiet = options.get("quiet", False)
        self.check = options.get("check", False)
        self.validate_extensions = options.get("validate_extensions", True)
        self.allowed_extensions = ALLOWED_EXTENSIONS.copy()
        self._files_to_format: List[Path] = []

    def is_supported(self, _=None, __=None) -> bool:
        return bool(shutil.which(self.executable))

    def allow_extension(self, file_ext: str) -> None:
        """Add a file extension str to the list of allowed extension"""
        self.allowed_extensions.append(file_ext)

    def stage_file(self, filepath: Path) -> None:
        """Request ClangFormatter to consider the file for formatting.
        If the file exists and its extension matches a known C/C++ format,
        it will be passed to clang-format when the execute() function is called.

        Args:
            filepath (str): file path to file to be staged.
        """
        if not filepath.is_file():
            if self.verbose:
                print(f"[INFO] Skipping {filepath} : is not a file.")
        elif self.validate_extensions and (
            filepath.suffix not in self.allowed_extensions
        ):
            if self.verbose:
                print(
                    f"[INFO] Skipping {filepath} : unrecognized C/C++ file extension "
                    f"('{filepath.suffix}'). Use --allow-extension or --force."
                )
        else:
            self._files_to_format.append(filepath)

    def exclude_file(self, filepath: Path) -> None:
        """Request ClangFormatter to exclude the file for formatting.
        If the file exists and its extension matches a known C/C++ format,
        it will be excluded to clang-format when the execute() function is called.

        Args:
            filepath (str): file path to be excluded.
        """
        if filepath in self._files_to_format:
            if self.verbose:
                print(f"[INFO] Excluding {filepath} from formatting.")
            self._files_to_format.remove(filepath)
        elif self.verbose:
            print(f"[INFO] {filepath} was not staged for formatting. Skipping.")

    def execute(
        self, builder: "Build", context: "Path", args: Tuple[Dict[str, str], List[str]]
    ):
        """Execute clang-format on the files that were staged.

        Args:
            builder (Build): build object to run the utility with
            context (Path): context path of module clang-format can run on if --module is provided
            args (Tuple[Dict[str, str], List[str]]): extra arguments to supply to the utility
        """
        combined_env = os.environ.copy()
        combined_env.update(builder.settings.get("environment", {}))

        if len(self._files_to_format) == 0:
            print("[INFO] No files were formatted.")
            return 0
        if not self.style_file.is_file():
            print(
                f"[ERROR] No .clang-format file found in {self.style_file.parent}. "
                "Override location with --pass-through --style=file:<path>."
            )
            return 1
        # Backup files unless --no-backup is requested or running only a --check
        if self.backup and not self.check:
            for file in self._files_to_format:
                shutil.copy2(file, file.parent / f"{file.stem}.bak{file.suffix}")
        pass_through = args[1]
        clang_args = [
            self.executable,
            "-i",
            f"--style=file",
            *(["--verbose"] if not self.quiet else []),
            *(["--dry-run", "--Werror"] if self.check else []),
            *pass_through,
            *self._files_to_format,
        ]
        if self.verbose:
            print("[INFO] Clang format executable:")
            print(f"[INFO]    {self.executable}")
            print("[INFO] Clang format arguments:")
            print(f"[INFO]    {clang_args[1:]}")
            print("[INFO] Clang format style file:")
            print(f"[INFO]    {self.style_file}")
        status = subprocess.run(clang_args, env=combined_env)
        return status.returncode


class FppFormatter(ExecutableAction):
    """Class encapsulating the fpp-format logic for fprime-util

    Formats FPP source files using the `fpp-format` executable shipped by the
    `fprime-fpp-format` package. It mirrors the staging interface of
    ``ClangFormatter`` so both formatters can be driven uniformly by
    ``run_code_format``, but delegates check/in-place semantics to
    ``fpp-format`` itself (``--check`` reports without writing; in-place is the
    default). ``--recursive-includes`` is passed so that `.fppi` include
    fragments reachable from staged `.fpp` roots are formatted with the correct
    context-derived entrypoint rule.
    """

    def __init__(self, executable: str, options: Dict):
        super().__init__(TargetScope.LOCAL)
        self.executable = executable
        self.backup = options.get("backup", False)
        self.verbose = options.get("verbose", False)
        self.quiet = options.get("quiet", False)
        self.check = options.get("check", False)
        self.validate_extensions = options.get("validate_extensions", True)
        self.allowed_extensions = FPP_ALLOWED_EXTENSIONS.copy()
        self._files_to_format: List[Path] = []

    def is_supported(self, _=None, __=None) -> bool:
        return bool(shutil.which(self.executable))

    def allow_extension(self, file_ext: str) -> None:
        """Add a file extension str to the list of allowed extension"""
        self.allowed_extensions.append(file_ext)

    def stage_file(self, filepath: Path) -> None:
        """Request FppFormatter to consider the file for formatting.
        If the file exists and its extension matches a known FPP format,
        it will be passed to fpp-format when the execute() function is called.

        Args:
            filepath (str): file path to file to be staged.
        """
        if not filepath.is_file():
            if self.verbose:
                print(f"[INFO] Skipping {filepath} : is not a file.")
        elif self.validate_extensions and (
            filepath.suffix not in self.allowed_extensions
        ):
            if self.verbose:
                print(
                    f"[INFO] Skipping {filepath} : unrecognized FPP file extension "
                    f"('{filepath.suffix}'). Use --allow-extension or --force."
                )
        else:
            self._files_to_format.append(filepath)

    def exclude_file(self, filepath: Path) -> None:
        """Request FppFormatter to exclude the file from formatting.

        Args:
            filepath (str): file path to be excluded.
        """
        if filepath in self._files_to_format:
            if self.verbose:
                print(f"[INFO] Excluding {filepath} from formatting.")
            self._files_to_format.remove(filepath)
        elif self.verbose:
            print(f"[INFO] {filepath} was not staged for formatting. Skipping.")

    def execute(
        self, builder: "Build", context: "Path", args: Tuple[Dict[str, str], List[str]]
    ):
        """Execute fpp-format on the files that were staged.

        Args:
            builder (Build): build object to run the utility with
            context (Path): unused; present for interface parity with ClangFormatter
            args (Tuple[Dict[str, str], List[str]]): extra arguments to supply to the utility
        """
        combined_env = os.environ.copy()
        combined_env.update(builder.settings.get("environment", {}))

        if len(self._files_to_format) == 0:
            print("[INFO] No FPP files were formatted.")
            return 0
        # Backup files unless running only a --check
        if self.backup and not self.check:
            for file in self._files_to_format:
                shutil.copy2(file, file.parent / f"{file.stem}.bak{file.suffix}")
        pass_through = args[1]
        fpp_args = [
            self.executable,
            # Follow include specifiers so reachable .fppi fragments are
            # formatted with the correct context-derived entrypoint rule.
            "--recursive-includes",
            # --check reports unformatted files (non-zero exit) without writing;
            # in-place formatting is fpp-format's default otherwise.
            *(["--check"] if self.check else []),
            *pass_through,
            *self._files_to_format,
        ]
        if self.verbose:
            print("[INFO] fpp-format executable:")
            print(f"[INFO]    {self.executable}")
            print("[INFO] fpp-format arguments:")
            print(f"[INFO]    {fpp_args[1:]}")
        status = subprocess.run(fpp_args, env=combined_env)
        return status.returncode
