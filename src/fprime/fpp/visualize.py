""" fprime.visualize.cli: Command line targets for fprime-viz

@thomas-bc
"""
import argparse
from pathlib import Path
# import os
# import shutil
import subprocess
from typing import Callable, Dict, List, Tuple

from fprime.fpp.common import FppUtility

FPL_INSTALL_DIR = "/Users/chammard/Work/fp/fprime-layout/bin"
FPV_INSTALL_DIR = "/Users/chammard/Work/fp/fprime-visual"

def run_fpp_viz(
    build: "Build",
    parsed: argparse.Namespace,
    _: Dict[str, str],
    __: Dict[str, str],
    ___: List[str],
):
    """Run pipeline of utilities to generate visualization. This includes:
    - fpp-to-xml
    - fpl-convert-xml
    - fpl-layout
    - start nodemon process to serve visualization

    Args:
        build: build directory output
        parsed: parsed input arguments
        _: unused cmake_args
        __: unused make_args
        ___: unused pass-through arguments
    """
    viz_cache = Path(".fpp-viz-cache")
    xml_cache = Path(".fpp-viz-cache/xml")
    xml_cache.mkdir(parents=True, exist_ok=True)
    
    # Run fpp-to-xml
    FppUtility("fpp-to-xml").execute(
        build,
        parsed.path,
        args=({}, ["--directory", ".fpp-viz-cache/xml"]) #["--directory", parsed.directory] if parsed.directory else ["--directory", ".fpp-viz-cache"]),
    )
    topology_match = list(xml_cache.glob("*TopologyAppAi.xml"))
    if len(topology_match) == 1:
        topology_xml = topology_match[0]
    else:
        raise Exception(f"Found {len(topology_match)} '*TopologyAppAi.xml' topology files - expected 1")
    
    print(f"Found topology XML file: {topology_xml.resolve()}")

    topology_txt = viz_cache / "Topology.txt"
    topology_json = viz_cache / "Topology.json"

    # Execute: fpl-convert-xml Topology.xml > Topology.txt
    with open(topology_txt.resolve(), "w") as txt_file:
        subprocess.run([f"{FPL_INSTALL_DIR}/fpl-convert-xml", topology_xml.resolve()], stdout=txt_file, check=True)
    
    # Execute: fpl-layout < Topology.txt > Topology.json
    with open(topology_json.resolve(), "w") as json_file:
        with open(topology_txt.resolve(), "r") as txt_file: 
            subprocess.run([f"{FPL_INSTALL_DIR}/fpl-layout"], stdin=txt_file, stdout=json_file, check=True)

    # Run nodemon - this will eventually be replaced with Flask app so whatevs' is fine for now
    fpv_env = viz_cache / ".fpv-env"
    with open(fpv_env.resolve(), "w") as env_file:
        env_file.write(f"DATA_FOLDER={viz_cache.resolve()}\n")
    print("[INFO] Starting nodemon server...")
    subprocess.run(["nodemon", f"{FPV_INSTALL_DIR}/server/index.js", fpv_env.resolve()], check=True)
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
        "fpp-viz", help="Runs visualization pipeline", parents=[common], add_help=False
    )
    viz_parser.add_argument(
        "-z", "--test", default=None, help="Test"
    )
    return {"fpp-viz": run_fpp_viz}, {"fpp-viz": viz_parser}