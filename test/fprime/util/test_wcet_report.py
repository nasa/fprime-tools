from pathlib import Path

from fprime.util.wcet_report import collect_wcet_rows


def test_collect_wcet_rows_from_ast(tmp_path: Path):
    ast = {
        "kind": "active component",
        "name": "Demo",
        "members": [
            {
                "kind": "sync input port",
                "name": "schedIn",
                "preannot": "@ WCET 200 us",
            }
        ],
    }
    json_path = tmp_path / "demo.json"
    json_path.write_text(__import__("json").dumps(ast), encoding="utf-8")
    rows = collect_wcet_rows([json_path])
    assert rows == [("Demo", "schedIn", "sync input port", "200us")]
