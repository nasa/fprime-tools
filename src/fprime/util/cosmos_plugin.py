"""Generate an OpenC3 COSMOS plugin skeleton from an F Prime dictionary JSON file."""

from __future__ import annotations

import json
import pprint
import re
from pathlib import Path
from typing import Any, Dict


def _flatten_type(t: Dict[str, Any], types: Dict[str, Any]) -> Dict[str, Any]:
    kind = t["kind"]
    if kind == "qualifiedIdentifier":
        resolved = types[t["name"]]
        rkind = resolved["kind"]
        if rkind == "enum":
            states = {c["value"]: c["name"] for c in resolved["enumeratedConstants"]}
            return {
                "kind": "enum",
                "representationType": resolved["representationType"],
                "states": states,
            }
        if rkind == "array":
            return {
                "kind": "array",
                "size": resolved["size"],
                "elementType": _flatten_type(resolved["elementType"], types),
            }
        if rkind == "alias":
            return _flatten_type(resolved["underlyingType"], types)
        if rkind == "struct":
            members = sorted(resolved["members"].items(), key=lambda kv: kv[1]["index"])
            flat_members = []
            for mname, member in members:
                flat = _flatten_type(member["type"], types)
                flat["name"] = mname
                flat_members.append(flat)
            return {"kind": "struct", "members": flat_members}
        raise RuntimeError(f"Unhandled typeDefinition kind: {rkind}")
    if kind == "integer":
        return {"kind": "integer", "size": t["size"], "signed": t.get("signed", False)}
    if kind == "float":
        return {"kind": "float", "size": t["size"]}
    if kind == "string":
        return {"kind": "string", "size": t["size"]}
    if kind == "bool":
        return {"kind": "bool", "size": t.get("size", 8)}
    raise RuntimeError(f"Unhandled type kind: {kind}")


def _emit_command_param(f, name: str, t: Dict[str, Any], types: Dict[str, Any], annotation: str) -> None:
    kind = t["kind"]
    if kind == "qualifiedIdentifier":
        resolved = types[t["name"]]
        rkind = resolved["kind"]
        if rkind == "alias":
            _emit_command_param(f, name, resolved["underlyingType"], types, annotation)
            return
        if rkind == "struct":
            for mname, member in sorted(resolved["members"].items(), key=lambda kv: kv[1]["index"]):
                _emit_command_param(
                    f, f"{name}_{mname}", member["type"], types, member.get("annotation", "")
                )
            return
        if rkind == "enum":
            states = {c["name"]: c["value"] for c in resolved["enumeratedConstants"]}
            default = states[resolved["default"].split(".")[-1]]
            rep = resolved["representationType"]
            ts = "INT" if rep["signed"] else "UINT"
            print(f"  APPEND_PARAMETER {name} {rep['size']} {ts} MIN MAX {default} \"{annotation}\"", file=f)
            for key, value in states.items():
                print(f"    STATE {key} {value}", file=f)
            return
    if kind == "string":
        print(f"  APPEND_PARAMETER {name} {t['size'] * 8} STRING \"\" \"{annotation}\"", file=f)
        return
    if kind == "integer":
        ts = "INT" if t["signed"] else "UINT"
        print(f"  APPEND_PARAMETER {name} {t['size']} {ts} MIN MAX 0 \"{annotation}\"", file=f)
        return
    if kind == "float":
        print(f"  APPEND_PARAMETER {name} {t['size']} FLOAT MIN MAX 0 \"{annotation}\"", file=f)
        return
    if kind == "bool":
        print(f"  APPEND_PARAMETER {name} {t['size']} UINT 0 1 0 \"{annotation}\"", file=f)
        print("    STATE FALSE 0", file=f)
        print("    STATE TRUE 1", file=f)


def _emit_channel_value(f, name: str, t: Dict[str, Any], types: Dict[str, Any], annotation: str) -> None:
    kind = t["kind"]
    if kind == "qualifiedIdentifier":
        resolved = types[t["name"]]
        rkind = resolved["kind"]
        if rkind == "alias":
            _emit_channel_value(f, name, resolved["underlyingType"], types, annotation)
            return
        if rkind == "enum":
            states = {c["name"]: c["value"] for c in resolved["enumeratedConstants"]}
            rep = resolved["representationType"]
            ts = "INT" if rep["signed"] else "UINT"
            print(f"  APPEND_ITEM {name} {rep['size']} {ts} \"{annotation}\"", file=f)
            for key, value in states.items():
                print(f"    STATE {key} {value}", file=f)
            return
    if kind == "integer":
        ts = "INT" if t["signed"] else "UINT"
        print(f"  APPEND_ITEM {name} {t['size']} {ts} \"{annotation}\"", file=f)
        return
    if kind == "float":
        print(f"  APPEND_ITEM {name} {t['size']} FLOAT \"{annotation}\"", file=f)
        return
    if kind == "bool":
        print(f"  APPEND_ITEM {name} {t['size']} UINT \"{annotation}\"", file=f)
        print("    STATE FALSE 0", file=f)
        print("    STATE TRUE 1", file=f)


def _convert_event_format(fmt: str) -> str:
    def replace(match: re.Match[str]) -> str:
        spec = match.group(1)
        if spec == "":
            return "{}"
        if spec.startswith(":"):
            return "{" + spec + "}"
        return "{:" + spec + "}"

    return re.sub(r"\{([^}]*)\}", replace, fmt)


def generate_cosmos_plugin(dictionary_path: Path, output_dir: Path, target_name: str) -> None:
    with dictionary_path.open(encoding="utf-8") as handle:
        data = json.load(handle)

    types = {item["qualifiedName"]: item for item in data["typeDefinitions"]}
    commands = data["commands"]
    events = data["events"]
    channels = data["telemetryChannels"]

    target_dir = output_dir / "targets" / target_name
    cmd_tlm_dir = target_dir / "cmd_tlm"
    lib_dir = target_dir / "lib"
    cmd_tlm_dir.mkdir(parents=True, exist_ok=True)
    lib_dir.mkdir(parents=True, exist_ok=True)

    framework_version = data["metadata"]["frameworkVersion"]
    headers = "SPACE_PACKET" if framework_version.startswith("v4") else "FPRIME"

    with (cmd_tlm_dir / "cmd.txt").open("w", encoding="utf-8") as f:
        print("# Generated by fprime-util export cosmos", file=f)
        for index, command in enumerate(commands):
            if index:
                print(file=f)
            annotation = command.get("annotation", "").replace("\n", " ")
            print(
                f'COMMAND {target_name} {command["name"]} BIG_ENDIAN "{annotation}"',
                file=f,
            )
            if headers == "FPRIME":
                print("  APPEND_PARAMETER FPRIME_SYNC 32 UINT MIN MAX 0", file=f)
                print("  APPEND_PARAMETER FPRIME_SIZE 32 UINT MIN MAX 0", file=f)
                print("  APPEND_ID_PARAMETER FPRIME_PACKET_ID 32 UINT 0 0 0", file=f)
            else:
                print("  APPEND_PARAMETER CCSDS_VERSION 3 UINT 0 0 0", file=f)
                print("  APPEND_PARAMETER CCSDS_TYPE 1 UINT 1 1 1", file=f)
                print("  APPEND_PARAMETER CCSDS_SHF 1 UINT 0 0 0", file=f)
                print("  APPEND_ID_PARAMETER CCSDS_APID 11 UINT 0 0 0", file=f)
                print("  APPEND_PARAMETER CCSDS_SEQ_FLAGS 2 UINT MIN MAX 0", file=f)
                print("  APPEND_PARAMETER CCSDS_SEQ_CNT 14 UINT MIN MAX 0", file=f)
                print("  APPEND_PARAMETER CCSDS_LENGTH 16 UINT MIN MAX 0", file=f)
                print("  APPEND_PARAMETER FPRIME_APID 16 UINT 0 0 0", file=f)
            print(
                f'  APPEND_ID_PARAMETER FPRIME_OPCODE 32 UINT {command["opcode"]} '
                f'{command["opcode"]} {command["opcode"]}',
                file=f,
            )
            for param in command["formalParams"]:
                _emit_command_param(
                    f,
                    param["name"],
                    param["type"],
                    types,
                    param.get("annotation", ""),
                )
            if headers == "FPRIME":
                print("  APPEND_PARAMETER FPRIME_CRC32 32 UINT MIN MAX 0", file=f)

    with (cmd_tlm_dir / "tlm.txt").open("w", encoding="utf-8") as f:
        print("# Generated by fprime-util export cosmos", file=f)
        for channel in channels:
            print(file=f)
            annotation = channel.get("annotation", "").replace("\n", " ")
            print(
                f'TELEMETRY {target_name} {channel["name"]} BIG_ENDIAN "{annotation}"',
                file=f,
            )
            print("  SUBPACKET", file=f)
            print(f'  APPEND_ID_ITEM FPRIME_CHANNEL_ID 32 UINT {channel["id"]}', file=f)
            channel_name = channel["name"].split(".")[-1]
            _emit_channel_value(f, channel_name, channel["type"], types, annotation)

    events_lookup = {}
    for event in events:
        flat_params = []
        for param in event.get("formalParams", []):
            flat = _flatten_type(param["type"], types)
            flat["name"] = param["name"]
            flat_params.append(flat)
        events_lookup[event["id"]] = {
            "name": event["name"],
            "severity": event["severity"],
            "format": _convert_event_format(event.get("format", "")),
            "params": flat_params,
        }

    (lib_dir / "fprime_event_conversion.py").write_text(
        "# Generated by fprime-util export cosmos\n"
        f"EVENTS = {pprint.pformat(events_lookup, indent=2, width=120, sort_dicts=False)}\n",
        encoding="utf-8",
    )

    (output_dir / "plugin.txt").write_text(
        "\n".join(
            [
                "VARIABLE target_name",
                f'DEFAULT target_name "{target_name}"',
                "",
                f"TARGET {target_name} {target_dir}",
                "",
                "# Load cmd/tlm definitions from generated targets tree",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    readme = output_dir / "README.md"
    readme.write_text(
        "\n".join(
            [
                f"# OpenC3 COSMOS plugin for {target_name}",
                "",
                "Generated from an F Prime dictionary JSON file via `fprime-util export cosmos`.",
                "",
                "## Layout",
                "",
                "- `plugin.txt` — plugin entrypoint",
                f"- `targets/{target_name}/cmd_tlm/` — command and telemetry definitions",
                f"- `targets/{target_name}/lib/` — helper conversion modules",
                "",
                "Adapt paths and add OpenC3 interface/target wiring before deploying.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def run_export_cosmos(build, parsed, *_args, **_kwargs) -> int:
    if parsed.export_target != "cosmos":
        raise NotImplementedError(f"export target '{parsed.export_target}' is not implemented")
    dictionary = Path(parsed.dictionary)
    output_dir = Path(parsed.output)
    if not dictionary.is_file():
        print(f"[ERROR] Dictionary not found: {dictionary}", flush=True)
        return 1
    output_dir.mkdir(parents=True, exist_ok=True)
    generate_cosmos_plugin(dictionary, output_dir, parsed.target_name)
    print(f"[INFO] OpenC3 COSMOS plugin scaffold written to {output_dir}")
    return 0
