""" fprime.fpp.common:

Common implementations for FPP tool wrapping.

@author mstarch
"""
import itertools
import subprocess
from pathlib import Path
import shutil
import sys
from typing import Dict, List, Tuple

from fprime.common.error import FprimeException
from fprime.fbuild.builder import Build
from fprime.fbuild.target import ExecutableAction, TargetScope


class FppMissingSupportFiles(FprimeException):
    """FPP is missing its support files and cannot run"""

    def __init__(self, file):
        super().__init__(
            f"Can not find {file}. Does current directory define any FPP files?"
        )


class FppUtility(ExecutableAction):
    """Action built around executing FPP

    When executing FPP, the utilities often require a set of input or dependency FPP files as well as a locations file
    that represents the location of the FPP constructs in the system. These inputs are then supplied to the FPP utility
    in a similar order across utilities. This action executes these utilities via a subprocess using the command line
    format:

    <utility> <user supplied args> [<fpp imports>] <locations file> <fpp inputs>

    Some fpp utilities distinguish between import files (--import flag) and source files. Those utilities should set
    the imports_as_sources flag to False. This will cause the utility to pass the import files as --import arguments.
    If imports_as_sources is True, the import files are passed as inputs just like source files.
    """

    def __init__(self, name, imports_as_sources=True):
        """Construct this utility with the supplied name

        Args:
            name: name of the fpp utility to run
        """
        super().__init__(TargetScope.LOCAL)
        self.utility = name
        self.imports_as_sources = imports_as_sources

    def is_supported(self, _=None, __=None):
        """Returns whether this utility is supported"""
        return bool(shutil.which(self.utility))

    @staticmethod
    def get_locations_file(builder: Build) -> Path:
        """Returns the location of the FPP locations file

        Returns a path to the FPP locations index within the build cache managed by the supplied build object.

        Args:
            builder: build object to use

        Return:
            path to the locations index
        """
        locations_path = Path(builder.build_dir) / "locs.fpp"
        if not locations_path.exists():
            raise FppMissingSupportFiles(locations_path)
        return locations_path

    @staticmethod
    def get_fpp_inputs(builder: Build, context: Path) -> Tuple[List[Path], List[Path]]:
        """Return the necessary inputs to an FPP run to forward to fpp utilities

        Returns two types of FPP files input into FPP utilities: the FPP files associated with the given module and the
        FPP files included by those files (e.g. commands.fpp). These files are output in a file in the build cache
        directory.

        Args:
            builder: build object used to look for output file
            context: context path of module containing the FPP files

        Return:
            tuple of two lists: module source FPP files and included FPP files
        """
        cache_location = builder.get_build_cache_path(context)
        import_file = cache_location / "fpp-import-list"
        source_file = cache_location / "fpp-source-list"
        if not import_file.exists():
            raise FppMissingSupportFiles(import_file)
        if not source_file.exists():
            raise FppMissingSupportFiles(source_file)
        with open(import_file, "r") as file_handle:
            import_list = [
                Path(token) for token in file_handle.read().split(";") if token != ""
            ]
        with open(source_file, "r") as file_handle:
            source_list = [
                Path(token) for token in file_handle.read().split(";") if token != ""
            ]
        return (import_list, source_list)

    def execute(
        self, builder: Build, context: Path, args: Tuple[Dict[str, str], List[str]]
    ):
        """Execute the fpp utility

        Executes the FPP utility wrapped by this class. Executes it with respect to the context path supplied and using
        the builder object. Supplies arguments in args to the utility.

        Args:
            builder: build object to run the utility with
            context: context path of module FPP is running on
            args: extra arguments to supply to the utility
        """
        # First refresh the cache but only if it detects it needs too

        if not self.is_supported():
            print(
                f"[ERROR] Cannot find executable: {self.utility}.",
                file=sys.stderr,
            )
            return 1

        builder.cmake.cmake_refresh_cache(builder.build_dir, False)

        # Read files and arguments
        locations = self.get_locations_file(builder)
        imports, sources = self.get_fpp_inputs(builder, context)

        if not sources:
            print("[WARNING] No FPP sources found in this module.")

        # Build the input argument list
        input_args = []
        if self.imports_as_sources:
            input_args.extend(
                str(item) for item in itertools.chain([locations] + imports + sources)
            )
        else:
            input_args.extend(["-i", ",".join(map(str, imports))] if imports else [])
            input_args.extend(
                str(item) for item in itertools.chain([locations] + sources)
            )

        user_args = args[1]
        app_args = [self.utility] + user_args + input_args
        if builder.cmake.verbose:
            print(f"[FPP] '{' '.join(app_args)}'")
        return subprocess.run(app_args, cwd=context, capture_output=False).returncode
