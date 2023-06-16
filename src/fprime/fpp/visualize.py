""" fprime.fpp.visualize: Command line targets for fprime-viz

@author thomas-bc
"""
import argparse
import os
import subprocess
from pathlib import Path
from typing import Callable, Dict, List, Tuple

from fprime.fpp.common import FppUtility

from fprime_visual.flask.app import construct_app


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
    - start fprime-visual Flask app to serve visualization

    Args:
        build: build directory output
        parsed: parsed input arguments
        _: unused cmake_args
        __: unused make_args
        ___: unused pass-through arguments
    """
    
    # We could use the build directory, but it's quirky because not managed by CMake ??
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
    
    print(f"Generated topology XML file: {topology_xml.resolve()}")

    topology_txt = viz_cache / "Topology.txt"
    topology_json = viz_cache / "Topology.json"

    # Execute: fpl-convert-xml Topology.xml > Topology.txt
    with open(topology_txt.resolve(), "w") as txt_file:
        subprocess.run(["fpl-convert-xml", topology_xml.resolve()], stdout=txt_file, check=True)
    
    # Execute: fpl-layout < Topology.txt > Topology.json
    with open(topology_json.resolve(), "w") as json_file:
        with open(topology_txt.resolve(), "r") as txt_file: 
            subprocess.run(["fpl-layout"], stdin=txt_file, stdout=json_file, check=True)

    print("Extracting subtopologies...")
    # Extract subtopologies from Topology.xml
    extract_cache = viz_cache / "extracted"
    extract_cache.mkdir(parents=True, exist_ok=True)
    # Execute: fpl-extract-xml -d extracted/ Topology.xml
    subprocess.run(["fpl-extract-xml", "-d", extract_cache.resolve(), topology_xml.resolve()], check=True)
    subtopologies = list(extract_cache.glob("*.xml"))
    for subtopology in subtopologies:
        # Execute: fpl-convert-xml subtopology.xml > subtopology.txt
        subtopology_txt = extract_cache / f"{subtopology.stem}.txt"
        with open(subtopology_txt.resolve(), "w") as txt_file:
            subprocess.run(["fpl-convert-xml", subtopology.resolve()], stdout=txt_file, check=True)
        # Execute: fpl-layout < subtopology.txt > subtopology.json
        subtopology_json = viz_cache / f"{subtopology.stem}.json"
        with open(subtopology_json.resolve(), "w") as json_file:
            with open(subtopology_txt.resolve(), "r") as txt_file: 
                subprocess.run(["fpl-layout"], stdin=txt_file, stdout=json_file, check=True)

    print("[INFO] Starting fprime-visual server...")
    config = {"SOURCE_DIRS": [str(viz_cache.resolve())]}
    app = construct_app(config)
    try:
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
        "visualize", help="Runs visualization pipeline", parents=[common], add_help=False
    )
    viz_parser.add_argument(
        "--gui-port", help="Set the GUI port for fprime-visual [default: 7000]", required=False, default=7000
    )
    return {"visualize": run_fpp_viz}, {"visualize": viz_parser}