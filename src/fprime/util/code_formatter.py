""" fprime.fbuild.code_formatter

Wrapper for clang-format utility.

@author thomas-bc
"""

from typing import Dict, List, Tuple

from fprime.fbuild.target import ExecutableAction, TargetScope
from pathlib import Path

import subprocess
import shutil
import re


# MARKER is needed to differentiate at postprocess between access specifiers
# that were previously MACRO'ed uppercase, and those that were originally lowercase.
# MARKER *MUST* be a comment for the formatting to behave - so might as well make it
# a meaningful warning in case it's not postprocessed correctly
MARKER = "// WARNING: fprime-util format mishap"

# POST pattern is different because the formatting will likely introduce whitespaces
PRIVATE_PRE_PATTERN    = f"private:{MARKER}"
PRIVATE_POST_PATTERN   = f"private:[\s]*{MARKER}"
PROTECTED_PRE_PATTERN  = f"protected:{MARKER}"
PROTECTED_POST_PATTERN = f"protected:[\s]*{MARKER}"
STATIC_PRE_PATTERN     = f"static:{MARKER}"
STATIC_POST_PATTERN    = f"static:[\s]*{MARKER}"

# clang-format will try to format everything it is given - restrict for the time being
VALID_EXTENSIONS = [".cpp", ".c++", ".cxx", ".cc", ".c", ".hpp", ".h++", ".hxx", ".hh", ".h"]



class ClangFormatter(ExecutableAction):
    """Class encapsulating the clang-format logic for fprime-util
    """

    def __init__(
            self,
            executable: str,
            style_file: "Path",
            options: Dict
    ):
        super().__init__(TargetScope.LOCAL)
        self.executable = executable
        self.style_file = style_file
        self.backup = options["backup"]
        self.verbose = options["verbose"]
        self.validate_extensions = options["validate_extensions"]
        self._files_to_format: List[Path] = []

    def is_supported(self) -> bool:
        return bool(shutil.which(self.executable))

    def stage_file(self, filepath: Path) -> None:
        """Request ClangFormatter to consider the file for formatting.
        If the file exists and its extension matches a known C/C++ format,
        it will be passed to clang-format when the execute() function is called.

        Args:
            filepath (str): file path to file to be staged.
        """
        if not filepath.is_file():
            print(f"[INFO] Skipping {filepath} : is not a file.")
        elif self.validate_extensions and (filepath.suffix not in VALID_EXTENSIONS):
            print(f"[INFO] Skipping {filepath} : unrecognized C/C++ file extension "
                  f"('{filepath.suffix}'). Use --force to force format.""")
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
            content = re.sub("PROTECTED:", PROTECTED_PRE_PATTERN, content)
            content = re.sub("PRIVATE:",   PRIVATE_PRE_PATTERN,   content)
            content = re.sub("STATIC:",    STATIC_PRE_PATTERN,    content)
            # Write the file out to the same location, seemingly in-place
            with open(filepath, "w") as file:
                file.write(content)

    def _postprocess_files(self) -> None:
        """Postprocess a file to restore the access specifier macros.
        """
        for filepath in self._files_to_format:
            # Same logic as _preprocess_files()
            with open(filepath, "r") as file:
                content = file.read()
            content = re.sub(PROTECTED_POST_PATTERN, "PROTECTED:", content)
            content = re.sub(PRIVATE_POST_PATTERN,   "PRIVATE:",   content)
            content = re.sub(STATIC_POST_PATTERN,    "STATIC:",    content)
            with open(filepath, "w") as file:
                file.write(content)

    def execute(self, builder: "Build", context: "Path", args: Tuple[Dict[str, str], List[str]]):
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
            print(f"[ERROR] No .clang-format file found in {self.style_file.parent}. "
                    "Override location with --pass-through --style=file:<path>.")
            return 1
        # Backup files unless --no-backup is requested
        if self.backup:
            for file in self._files_to_format:
                shutil.copy2(file, file.parent / (file.stem + ".bak" + file.suffix))
        pass_through = args[1]
        self._preprocess_files()
        clang_args = [
            self.executable,
            "-i",
            f"--style=file:{self.style_file}",
            *(["--verbose"] if self.verbose else []),
            *pass_through,
            *self._files_to_format,
        ]
        subprocess.run(clang_args)
        self._postprocess_files()
        return 0
