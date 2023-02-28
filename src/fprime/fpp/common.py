""" fprime.fpp.common:

Common implementations for FPP tool wrapping.

@author mstarch
"""
import itertools
import subprocess
from typing import List, Dict, Tuple
from pathlib import Path

from fprime.common.error import FprimeException
from fprime.fbuild.builder import Build
from fprime.fbuild.target import ExecutableAction, TargetScope


class FppMissingSupportFiles(FprimeException):
    """FPP is missing its support files and cannot run"""

    def __init__(self, file):
        super().__init__(
            f"Current directory does not define any FPP files. Did you intend to run in the topology directory?"
        )


class FppUtility(ExecutableAction):
    """Action built around executing FPP

    When executing FPP, the utilities often require a set of input or dependency FPP files as well as a locations file
    that represents the location of the FPP constructs in the system. These inputs are then supplied to the FPP utility
    in a similar order across utilities. This action executes these utilities via a subprocess using the command line
    format:

    <utility> <user supplied args> <locations file> <fpp inputs>
    """

    def __init__(self, name):
        """Construct this utility with the supplied name

        Args:
            name: name of the fpp utility to run
        """
        super().__init__(TargetScope.LOCAL)
        self.utility = name

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
    def get_fpp_inputs(builder: Build, context: Path) -> List[Path]:
        """Return the necessary inputs to an FPP run to forward to fpp utilities

        Returns two types of FPP files input into FPP utilities: the FPP files associated with the given module and the
        FPP files included by those files (e.g. commands.fpp). These files are output in a file in the build cache
        directory.

        Args:
            builder: build object used to look for output file
            context: context path of module containing the FPP files

        Return:
            list of module FPP files and included FPP files
        """
        cache_location = builder.get_build_cache_path(context)
        input_file = cache_location / "fpp-input-list"
        if not input_file.exists():
            raise FppMissingSupportFiles(input_file)
        with open(input_file, "r") as file_handle:
            return [
                Path(token) for token in file_handle.read().split(";") if token != ""
            ]

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
        builder.cmake.cmake_refresh_cache(builder.build_dir, False)

        # Read files and arguments
        locations = self.get_locations_file(builder)
        inputs = self.get_fpp_inputs(builder, context)

        if not inputs:
            print("[WARNING] No FPP inputs found in this module.")

        user_args = args[1]
        app_args = (
            [self.utility]
            + user_args
            + [str(item) for item in itertools.chain([locations] + inputs)]
        )
        if builder.cmake.verbose:
            print(f"[FPP] '{' '.join(app_args)}'")
        subprocess.run(app_args, capture_output=False)
