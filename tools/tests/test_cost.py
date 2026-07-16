"""Cost rollups, skip accounting, run comparison, reuse verification."""

import json
from pathlib import Path

from conftest import build_chain, make_receipt, write_run
from openprose_tools.cli import main
from openprose_tools.cost import compare_runs, cost_run
from openprose_tools.ledger import load_run
from openprose_tools.verify import verify_ledger

ZERO_EXACT = {
    "basis": "exact",
    "input_tokens": 0,
    "output_tokens": 0,
    "model": "none",
}
FP = "sha256:" + "ab" * 32


def _rendered_run(tmp_path: Path) -> Path:
    receipts = build_chain(
        [
            {
                "statement_id": "s001",
                "agent": "researcher",
                "usage": {
                    "basis": "exact",
                    "input_tokens": 40000,
                    "output_tokens": 500,
                    "model": "sonnet",
                },
            },
            {
                "statement_id": "s002",
                "agent": "writer",
                "usage": {
                    "basis": "estimated",
                    "input_tokens": 30000,
                    "output_tokens": 800,
                    "model": "haiku",
                },
            },
        ]
    )
    return write_run(tmp_path / "baseline", receipts)


def _skipped_run(tmp_path: Path) -> Path:
    receipts = build_chain(
        [
            {
                "statement_id": "s001",
                "status": "skipped",
                "agent": "researcher",
                "output_fingerprint": FP,
                "reused_from": {
                    "run_id": "20260716-120000-test01",
                    "statement_id": "s001",
                    "output_fingerprint": FP,
                },
                "usage": ZERO_EXACT,
            },
            {
                "statement_id": "s002",
                "status": "skipped",
                "agent": "writer",
                "output_fingerprint": FP,
                "reused_from": {
                    "run_id": "20260716-120000-test01",
                    "statement_id": "s002",
                    "output_fingerprint": FP,
                },
                "usage": ZERO_EXACT,
            },
        ]
    )
    run = write_run(tmp_path / "resumed", receipts)
    manifest = json.loads((run / "run.json").read_text())
    manifest["reuse_source_run"] = "20260716-120000-test01"
    (run / "run.json").write_text(json.dumps(manifest, indent=2))
    return run


def test_cost_rollup(tmp_path: Path) -> None:
    summary = cost_run(load_run(_rendered_run(tmp_path)))
    assert summary["totals"]["input_tokens"] == 70000
    assert summary["by_model"]["sonnet"]["input_tokens"] == 40000
    assert summary["by_agent"]["writer"]["output_tokens"] == 800
    assert summary["by_basis"]["estimated"]["receipts"] == 1
    assert summary["skip"] == {
        "spendable_statements": 2,
        "skipped": 0,
        "skipped_percent": 0,
    }


def test_skipped_run_costs_zero_and_verifies(tmp_path: Path) -> None:
    run = _skipped_run(tmp_path)
    assert verify_ledger(load_run(run)).ok
    summary = cost_run(load_run(run))
    assert summary["totals"]["input_tokens"] == 0
    assert summary["skip"]["skipped_percent"] == 100
    assert summary["reuse_source_run"] == "20260716-120000-test01"
    assert len(summary["reused"]) == 2


def test_compare_runs(tmp_path: Path) -> None:
    baseline = cost_run(load_run(_rendered_run(tmp_path)))
    candidate = cost_run(load_run(_skipped_run(tmp_path)))
    comparison = compare_runs(baseline, candidate)
    assert comparison["delta_tokens"] == -71300
    assert comparison["saved_percent"] == 100
    assert comparison["candidate"]["skipped"] == 2


def test_reused_from_on_rendered_receipt_rejected(tmp_path: Path) -> None:
    receipt = make_receipt(
        "s001",
        prev=None,
        status="rendered",
        output_fingerprint=FP,
        reused_from={
            "run_id": "x",
            "statement_id": "s001",
            "output_fingerprint": FP,
        },
        usage=ZERO_EXACT,
    )
    run = write_run(tmp_path / "bad", [receipt])
    result = verify_ledger(load_run(run))
    assert not result.ok
    assert any("only valid on skipped" in error for error in result.errors)


def test_skipped_with_nonzero_usage_rejected(tmp_path: Path) -> None:
    receipt = make_receipt(
        "s001",
        prev=None,
        status="skipped",
        output_fingerprint=FP,
        reused_from={
            "run_id": "x",
            "statement_id": "s001",
            "output_fingerprint": FP,
        },
        usage={
            "basis": "exact",
            "input_tokens": 5,
            "output_tokens": 0,
            "model": "none",
        },
    )
    run = write_run(tmp_path / "bad", [receipt])
    result = verify_ledger(load_run(run))
    assert not result.ok
    assert any("zero usage" in error for error in result.errors)


def test_skipped_with_real_model_or_surprise_rejected(tmp_path: Path) -> None:
    reused = {"run_id": "x", "statement_id": "s001", "output_fingerprint": FP}
    bad_model = make_receipt(
        "s001",
        prev=None,
        status="skipped",
        output_fingerprint=FP,
        reused_from=reused,
        usage={
            "basis": "exact",
            "input_tokens": 0,
            "output_tokens": 0,
            "model": "sonnet",  # must be "none" on skipped reuse
        },
    )
    run = write_run(tmp_path / "bad-model", [bad_model])
    result = verify_ledger(load_run(run))
    assert not result.ok
    assert any("model 'none'" in error for error in result.errors)

    bad_surprise = make_receipt(
        "s001",
        prev=None,
        status="skipped",
        output_fingerprint=FP,
        reused_from=reused,
        surprise_cause="input",  # must be null on skipped
        usage=ZERO_EXACT,
    )
    run = write_run(tmp_path / "bad-surprise", [bad_surprise])
    result = verify_ledger(load_run(run))
    assert not result.ok
    assert any("surprise_cause must be null" in error for error in result.errors)


def test_cli_cost_and_compare(tmp_path: Path, capsys) -> None:
    baseline = _rendered_run(tmp_path)
    resumed = _skipped_run(tmp_path)
    assert main(["cost", str(resumed), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["skip"]["skipped"] == 2
    assert main(["cost", str(resumed), "--compare", str(baseline)]) == 0
    out = capsys.readouterr().out
    assert "saved 100%" in out
