""" fprime.fpp.visualize: Command line targets for fprime-util visualize

@author thomas-bc
"""

import argparse
import shutil
import subprocess
import tempfile
import webbrowser
from pathlib import Path
from typing import Callable, Dict, List, Tuple

from fprime.fpp.common import FppUtility

try:
    from fprime_visual.flask.app import construct_app
except ImportError:
    construct_app = None


def run_fprime_visualize(
    build: "Build",
    parsed: argparse.Namespace,
    _: Dict[str, str],
    __: Dict[str, str],
    ___: List[str],
):
    """Run pipeline of utilities to generate visualization. This includes:
    - fpp-to-layout
    - fpl-layout
    - start fprime-visual Flask app to serve visualization

    Args:
        build: build directory output
        parsed: parsed input arguments
        _: unused cmake_args
        __: unused make_args
        ___: unused pass-through arguments
    """
    if construct_app is None:
        raise ModuleNotFoundError(
            "fprime-visual is not installed. Please install with `pip install fprime-visual`"
        )

    if not shutil.which("fpl-layout"):
        raise FileNotFoundError(
            "fpl-layout is not installed. Please install with `pip install fprime-fpp>1.2.0`"
        )

    # Set up working directory using specified directory, or create a temporary one
    if parsed.working_dir:
        viz_cache_base = Path(parsed.working_dir).resolve()
    else:
        viz_cache_base = Path(
            tempfile.TemporaryDirectory(prefix="fprime-visual-").name
        ).resolve()

    # Set sub-paths for different types of generated files
    txt_cache = (viz_cache_base / "txt").resolve()
    try:
        txt_cache.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        raise PermissionError(
            f"Unable to write to {viz_cache_base.resolve()}. Use --working-dir to set a different location."
        )

    # Run fpp-to-layout
    FppUtility("fpp-to-layout").execute(
        build,
        parsed.path,
        args=(
            {},
            ["--directory", str(txt_cache)],
        ),
    )
    topology_dirs = list(txt_cache.glob("*Layout"))
    source_dirs = []
    for dir in topology_dirs:
        layout_txt_file_match = list(dir.glob("*.txt"))
        if not layout_txt_file_match:
            raise Exception(f"Did not generate any '*.txt' layout files")
        topology_name = dir.name.replace("Layout", "")
        viz_cache = viz_cache_base / topology_name
        topology_json = viz_cache / f"{topology_name}Topology.json"
        # keep track of all connections in the topology (used in topology layout JSON file)
        topology_connections = ""
        try:
            viz_cache.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            raise PermissionError(
                f"Unable to write to {viz_cache_base.resolve()}. Use --working-dir to set a different location."
            )
        for layout_txt in layout_txt_file_match:
            print(f"Generated layout TXT file: {layout_txt.resolve()}")
            connection_graph_json = viz_cache / f"{layout_txt.stem}.json"
            # Execute: fpl-layout < ConnectionGraph.txt > ConnectionGraph.json
            with open(connection_graph_json.resolve(), "w") as json_file:
                with open(layout_txt.resolve(), "r") as txt_file:
                    txt_contents = txt_file.read()
                    topology_connections += txt_contents
                    subprocess.run(
                        ["fpl-layout"],
                        stdout=json_file,
                        input=txt_contents.encode(),
                        check=True,
                    )
        # Generate layout JSON for entire topology (all connections graphs in one layout)
        with open(topology_json.resolve(), "w") as json_file:
            subprocess.run(
                ["fpl-layout"],
                stdout=json_file,
                input=topology_connections.encode(),
                check=True,
            )
        source_dirs.append(viz_cache)
    source_resolved = [str(source.resolve()) for source in source_dirs]
    print("[INFO] Starting fprime-visual server...")
    print(f"[INFO] Serving files in {source_resolved}")
    config = {"SOURCE_DIRS": source_resolved}
    app = construct_app(config)
    try:
        webbrowser.open(f"http://localhost:{parsed.gui_port}")
        app.run(port=parsed.gui_port)
    except KeyboardInterrupt:
        print("[INFO] CTRL-C received. Exiting.")
    return 0


def add_fpp_viz_parsers(
    subparsers, common: argparse.ArgumentParser
) -> Tuple[Dict[str, Callable], Dict[str, argparse.ArgumentParser]]:
    """Sets up the fprime-viz command line parsers

    Creates command line parsers for fprime-viz commands and associates these commands to processing functions for those fpp
    commands.

    Args:
        subparsers: subparsers to add to
        common: common parser for all fprime-util commands

    Returns:
        Tuple of dictionary mapping command name to processor, and command to parser
    """
    viz_parser = subparsers.add_parser(
        "visualize",
        help="Visualize FPP model in a web GUI",
        parents=[common],
        add_help=False,
    )
    viz_parser.add_argument(
        "--gui-port",
        help="Set the GUI port for fprime-visual [default: %(default)s]",
        required=False,
        default=7000,
    )
    viz_parser.add_argument(
        "--working-dir",
        help="Set the directory to store layout files in (default to ephemeral location)",
        required=False,
    )
    return {"visualize": run_fprime_visualize}, {"visualize": viz_parser}
