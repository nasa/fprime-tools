import json
from pathlib import Path

from fprime.util.cosmos_plugin import generate_cosmos_plugin


def test_generate_cosmos_plugin_minimal(tmp_path: Path):
    dictionary = {
        "metadata": {"frameworkVersion": "v4.0.0"},
        "typeDefinitions": [],
        "commands": [
            {
                "name": "PING",
                "opcode": 1,
                "annotation": "Ping command",
                "formalParams": [],
            }
        ],
        "events": [],
        "telemetryChannels": [
            {
                "name": "Demo.Counter",
                "id": 10,
                "annotation": "Counter channel",
                "type": {"kind": "integer", "size": 32, "signed": False},
            }
        ],
    }
    dictionary_path = tmp_path / "dict.json"
    dictionary_path.write_text(json.dumps(dictionary), encoding="utf-8")
    output_dir = tmp_path / "plugin"
    generate_cosmos_plugin(dictionary_path, output_dir, "DEMO")
    assert (output_dir / "plugin.txt").is_file()
    assert (output_dir / "targets" / "DEMO" / "cmd_tlm" / "cmd.txt").is_file()
    assert (output_dir / "targets" / "DEMO" / "cmd_tlm" / "tlm.txt").is_file()
