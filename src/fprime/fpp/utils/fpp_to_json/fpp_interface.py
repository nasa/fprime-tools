import subprocess
import os


def fpp_depend(cache_folder, input_file, locs_files) -> str:
    """
    This function calculates the dependencies for an fpp file using fprime-util to get
    the location of the build cache fpp-depend.

    Args:
        input_file: The input fpp file to calculate dependencies for
        locs_file: The locs.fpp file to use for dependency calculation

    Returns:
        A string of dependencies for the input file
    """

    print(f"[fpp] Calculating fpp dependencies for {os.path.basename(input_file)}...")

    try:
        fppDep = subprocess.run(
            ["fpp-depend", input_file]
            + locs_files
            + [
                "-d",
                f"{cache_folder}/direct.txt",
                "-m",
                f"{cache_folder}/missing.txt",
                "-f",
                f"{cache_folder}/framework.txt",
                "-g",
                f"{cache_folder}/generated.txt",
                "-i",
                f"{cache_folder}/include.txt",
                "-u",
                f"{cache_folder}/unittest.txt",
                "-a",
            ],
            check=True,
            stdout=subprocess.PIPE,
        )

        with open(f"{cache_folder}/stdout.txt", "w") as f:
            f.write(fppDep.stdout.decode("utf-8"))

    except subprocess.CalledProcessError as e:
        print(f"[ERR] fpp-depend failed with error: {e}")
        return 1
    
    raise Exception("fpp-depend failed")


def compute_simple_dependencies(locs_file, input):
    print(f"[fpp] Calculating simple fpp dependencies for {os.path.basename(input)}...")

    try:
        fppDep = subprocess.run(
            ["fpp-depend", locs_file, input],
            check=True,
            stdout=subprocess.PIPE,
        )

        return fppDep.stdout.decode("utf-8")
    except subprocess.CalledProcessError as e:
        print(f"[ERR] fpp-depend failed with error: {e}")
        return 1


def fpp_to_json(input_file):
    """
    This function runs fpp-to-json on an fpp file to generate a JSON AST.

    Args:
        input_file: The input fpp file to run fpp-to-json on

    Returns:
        None
    """

    # run fpp
    print(f"[fpp] Running fpp-to-json for {os.path.basename(input_file)}...")

    cmdS = ["fpp-to-json", input_file, "-s"]

    try:
        subprocess.run(cmdS, check=True, stdout=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        raise Exception(f"[ERR] fpp-to-json pt2 failed with error: {e}")


def fpp_format(input_file):
    """
    This function runs fpp-format on an fpp file to format the file.

    Args:
        input_file: The input fpp file to run fpp-format on

    Returns:
        None
    """

    # run fpp-format
    print(f"[fpp] Running fpp-format for {os.path.basename(input_file)}...")

    try:
        fppFormat = subprocess.run(
            ["fpp-format", input_file], check=True, stdout=subprocess.PIPE
        )
        return fppFormat.stdout.decode("utf-8")
    except subprocess.CalledProcessError as e:
        print(f"[ERR] fpp-format failed with error: {e}")
        return 1


def fpp_locate_defs(input_file):
    """
    This function runs fpp-locate-defs on an fpp file to locate definitions.

    Args:
        input_file: The input fpp file to run fpp-locate-defs on
        locs_file:  The locs.fpp file used to find the base directory to base def locations
                    off of
    """

    print(f"[fpp] Running fpp-locate-defs for {os.path.basename(input_file)}...")

    base_dir = os.path.dirname(input_file)

    try:
        fppLocateDefs = subprocess.run(
            ["fpp-locate-defs", input_file, "-d", base_dir],
            check=True,
            stdout=subprocess.PIPE,
        )
        return fppLocateDefs.stdout.decode("utf-8")
    except subprocess.CalledProcessError as e:
        print(f"[ERR] fpp-locate-defs failed with error: {e}")
        return 1
