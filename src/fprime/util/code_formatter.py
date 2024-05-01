""" fprime.fbuild.code_formatter

Wrapper for clang-format utility.

@author thomas-bc
"""

import re
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple

from fprime.fbuild.target import ExecutableAction, TargetScope

# MARKER is needed to differentiate at postprocess between access specifiers
# that were previously an uppercase MACRO, and those that were originally lowercase.
# MARKER must be a comment for the formatting to behave - so might as well make it
# a meaningful warning in case it's not postprocessed correctly
MARKER = "// WARNING: fprime-util format mishap"

# POST pattern is different because the formatting will likely introduce whitespaces
PRIVATE_PRE_PATTERN = f"private:{MARKER}"
PRIVATE_POST_PATTERN = f"private:[\s]*{MARKER}"
PROTECTED_PRE_PATTERN = f"protected:{MARKER}"
PROTECTED_POST_PATTERN = f"protected:[\s]*{MARKER}"
STATIC_PRE_PATTERN = f"static:{MARKER}"
STATIC_POST_PATTERN = f"static:[\s]*{MARKER}"

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


class ClangFormatter(ExecutableAction):
    """Class encapsulating the clang-format logic for fprime-util"""

    def __init__(self, executable: str, style_file: "Path", options: Dict):
        super().__init__(TargetScope.LOCAL)
        self.executable = executable
        self.style_file = style_file
        self.backup = options.get("backup", True)
        self.verbose = options.get("verbose", False)
        self.quiet = options.get("quiet", False)
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

    def _preprocess_files(self) -> None:
        """Preprocess a file to ensure that clang-format behaves.
        This is because of the access specifier macros (e.g. PROTECTED)
        that are defined in F', which clang-format does not recognize
        """
        for filepath in self._files_to_format:
            # It is unsafe to write to file while reading from it
            # Better to read in memory, close the file, then re-open to write out from memory
            with open(filepath, "r") as file:
                content = file.read()
            # Replace the strings in the file content
            content = re.sub("PROTECTED[\s]*:", PROTECTED_PRE_PATTERN, content)
            content = re.sub("PRIVATE[\s]*:", PRIVATE_PRE_PATTERN, content)
            content = re.sub("STATIC[\s]*:", STATIC_PRE_PATTERN, content)
            # Write the file out to the same location, seemingly in-place
            with open(filepath, "w") as file:
                file.write(content)

    def _postprocess_files(self) -> None:
        """Postprocess a file to restore the access specifier macros."""
        for filepath in self._files_to_format:
            # Same logic as _preprocess_files()
            with open(filepath, "r") as file:
                content = file.read()
            content = re.sub(PROTECTED_POST_PATTERN, "PROTECTED:", content)
            content = re.sub(PRIVATE_POST_PATTERN, "PRIVATE:", content)
            content = re.sub(STATIC_POST_PATTERN, "STATIC:", content)
            with open(filepath, "w") as file:
                file.write(content)

    def execute(
        self, builder: "Build", context: "Path", args: Tuple[Dict[str, str], List[str]]
    ):
        """Execute clang-format on the files that were staged.

        Args:
            builder (Build): build object to run the utility with
            context (Path): context path of module clang-format can run on if --module is provided
            args (Tuple[Dict[str, str], List[str]]): extra arguments to supply to the utility
        """

        if len(self._files_to_format) == 0:
            print("[INFO] No files were formatted.")
            return 0
        if not self.style_file.is_file():
            print(
                f"[ERROR] No .clang-format file found in {self.style_file.parent}. "
                "Override location with --pass-through --style=file:<path>."
            )
            return 1
        # Backup files unless --no-backup is requested
        if self.backup:
            for file in self._files_to_format:
                shutil.copy2(file, file.parent / f"{file.stem}.bak{file.suffix}")
        pass_through = args[1]
        self._preprocess_files()
        clang_args = [
            self.executable,
            "-i",
            f"--style=file",
            *(["--verbose"] if not self.quiet else []),
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
        status = subprocess.run(clang_args)
        self._postprocess_files()
        return status.returncode
