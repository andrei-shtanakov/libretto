"""Inspection summary: dispositions, rollups, failures, determinism."""

import json
from pathlib import Path

from conftest import build_chain, write_run
from openprose_tools.cli import main
from openprose_tools.inspect_run import inspect_run, render_text
from openprose_tools.ledger import load_run


def _mixed_run(tmp_path: Path) -> Path:
    receipts = build_chain(
        [
            {
                "statement_id": "run",
                "kind": "control",
                "agent": None,
                "detail": {"event": "run_start"},
                "usage": {
                    "basis": "unavailable",
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "model": "none",
                },
            },
            {
                "statement_id": "s002",
                "agent": "researcher",
                "usage": {
                    "basis": "exact",
                    "input_tokens": 1000,
                    "output_tokens": 200,
                    "model": "haiku",
                },
            },
            {
                "statement_id": "s003.d1",
                "kind": "discretion",
                "agent": None,
                "detail": {
                    "condition": "results look complete",
                    "outcome": "true",
                    "branch": "if",
                },
                "usage": {
                    "basis": "estimated",
                    "input_tokens": 50,
                    "output_tokens": 5,
                    "model": "vm",
                },
            },
            {
                "statement_id": "s004",
                "agent": "writer",
                "status": "failed",
                "error": {
                    "type": "SessionError",
                    "message": "subagent returned no confirmation",
                    "retry_count": 2,
                },
            },
        ]
    )
    return write_run(tmp_path / "run", receipts)


def test_summary_counts_and_rollups(tmp_path: Path) -> None:
    summary = inspect_run(load_run(_mixed_run(tmp_path)))

    assert summary["receipt_count"] == 4
    assert summary["dispositions"] == {"failed": 1, "rendered": 3}
    assert summary["kinds"] == {"control": 1, "discretion": 1, "session": 2}
    assert summary["usage_total"] == {"input_tokens": 1150, "output_tokens": 225}
    assert summary["usage_by_basis"]["exact"]["input_tokens"] == 1000
    assert summary["usage_by_agent"]["researcher"]["receipts"] == 1
    assert summary["chain"]["ok"] is True

    (failure,) = summary["failed_statements"]
    assert failure["statement_id"] == "s004"
    assert failure["retry_count"] == 2

    (discretion,) = summary["discretion_outcomes"]
    assert discretion["outcome"] == "true"
    assert discretion["branch"] == "if"


def test_json_output_is_deterministic(tmp_path: Path) -> None:
    run_dir = _mixed_run(tmp_path)
    first = json.dumps(inspect_run(load_run(run_dir)), sort_keys=True)
    second = json.dumps(inspect_run(load_run(run_dir)), sort_keys=True)
    assert first == second


def test_text_rendering_mentions_key_facts(tmp_path: Path) -> None:
    text = render_text(inspect_run(load_run(_mixed_run(tmp_path))))
    assert "chain: OK" in text
    assert "s004" in text
    assert "basis=exact" in text


def test_cli_verify_ok(valid_run: Path, capsys) -> None:
    assert main(["verify", str(valid_run)]) == 0
    assert "chain: OK" in capsys.readouterr().out


def test_cli_inspect_json_parses(valid_run: Path, capsys) -> None:
    assert main(["inspect", str(valid_run), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["receipt_count"] == 3
    assert payload["chain"]["ok"] is True


def test_cli_missing_run_dir_exits_2(tmp_path: Path, capsys) -> None:
    assert main(["verify", str(tmp_path / "missing")]) == 2
    assert "error:" in capsys.readouterr().err
