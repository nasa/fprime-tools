"""Report execution-time annotations from fpp-to-json AST files."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

_DURATION_RE = re.compile(
    r"(?i)(?:wcet|deadline|execution\s*time(?:\s*limit)?)"
    r"[^\d]*(\d+)\s*(us|ms|s)\b|(\d+)\s*(us|ms|s)\b"
)


def _annotation_text(node: Dict[str, Any]) -> str:
    parts: List[str] = []
    for key in ("preannot", "postannot", "annotation"):
        value = node.get(key)
        if isinstance(value, str):
            parts.append(value)
        elif isinstance(value, list):
            parts.extend(str(item) for item in value)
    return "\n".join(parts).strip()


def _parse_duration(annotation: str) -> str | None:
    match = _DURATION_RE.search(annotation)
    if not match:
        return None
    if match.group(1) and match.group(2):
        return f"{match.group(1)}{match.group(2).lower()}"
    if match.group(3) and match.group(4):
        return f"{match.group(3)}{match.group(4).lower()}"
    return None


def _walk(node: Any, component: str | None, rows: List[Tuple[str, str, str, str]]) -> None:
    if isinstance(node, dict):
        kind = node.get("kind") or node.get("type")
        name = node.get("name") or node.get("id")
        if kind in {"active component", "passive component", "queued component", "component"}:
            component = str(name) if name else component
        elif kind in {"async input port", "sync input port", "output port", "port"} and name:
            annotation = _annotation_text(node)
            duration = _parse_duration(annotation)
            if duration:
                port_kind = str(kind)
                rows.append((component or "<unknown>", str(name), port_kind, duration))
        for value in node.values():
            _walk(value, component, rows)
    elif isinstance(node, list):
        for item in node:
            _walk(item, component, rows)


def collect_wcet_rows(json_paths: Iterable[Path]) -> List[Tuple[str, str, str, str]]:
    rows: List[Tuple[str, str, str, str]] = []
    for path in json_paths:
        with path.open(encoding="utf-8") as handle:
            data = json.load(handle)
        _walk(data, None, rows)
    return sorted(set(rows))


def print_wcet_report(rows: List[Tuple[str, str, str, str]]) -> None:
    if not rows:
        print("[INFO] No execution-time annotations found.")
        return
    print(f"{'Component':<32} {'Port':<24} {'Kind':<20} {'Budget':<10}")
    print("-" * 90)
    for component, port, kind, budget in rows:
        print(f"{component:<32} {port:<24} {kind:<20} {budget:<10}")


def run_wcet_report(build, parsed, *_args, **_kwargs) -> int:
    return run_wcet_report_impl(parsed)


def run_wcet_report_impl(parsed) -> int:
    json_paths: List[Path] = []
    if parsed.json:
        json_paths.extend(Path(p) for p in parsed.json)
    if parsed.json_dir:
        json_paths.extend(sorted(Path(parsed.json_dir).rglob("*.json")))
    if not json_paths:
        print("[ERROR] Supply --json and/or --json-dir", flush=True)
        return 1
    rows = collect_wcet_rows(json_paths)
    print_wcet_report(rows)
    return 0
