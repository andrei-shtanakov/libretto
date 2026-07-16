"""Chain-consistency verification against valid and corrupted runs."""

import json
from pathlib import Path

from conftest import build_chain, make_receipt, write_run
from libretto_tools.canonical import canonical_json
from libretto_tools.ledger import load_run
from libretto_tools.verify import verify_ledger


def test_valid_run_passes(valid_run: Path) -> None:
    result = verify_ledger(load_run(valid_run))
    assert result.ok
    assert result.warnings == []


def test_legacy_openprose_schema_tags_still_verify(tmp_path: Path) -> None:
    receipt = make_receipt("s001", prev=None, v="openprose.receipt.v1")
    manifest = {
        "v": "openprose.run.v1",
        "run_id": "20260716-120000-test01",
        "program": "examples/test.prose",
        "state_backend": "filesystem",
        "status": "completed",
        "receipt_count": 1,
        "ledger_head": receipt["content_hash"],
    }
    run_dir = write_run(tmp_path / "run", [receipt], manifest=manifest)

    result = verify_ledger(load_run(run_dir))
    assert result.ok
    assert result.warnings == []


def test_corrupted_content_hash_detected(tmp_path: Path, valid_run: Path) -> None:
    ledger = (valid_run / "receipts.jsonl").read_text().splitlines()
    middle = json.loads(ledger[1])
    middle["agent"] = "tampered"  # content no longer matches its hash
    ledger[1] = canonical_json(middle)
    (valid_run / "receipts.jsonl").write_text("\n".join(ledger) + "\n")

    result = verify_ledger(load_run(valid_run))
    assert not result.ok
    assert any("content_hash mismatch" in error for error in result.errors)


def test_broken_prev_chain_detected(tmp_path: Path) -> None:
    first = make_receipt("s001", prev=None)
    second = make_receipt("s002", prev="sha256:" + "ab" * 32)  # wrong link
    run_dir = write_run(tmp_path / "run", [first, second], manifest=True)

    result = verify_ledger(load_run(run_dir))
    assert not result.ok
    assert any("prev broken" in error for error in result.errors)


def test_truncation_detected_via_ledger_head(tmp_path: Path) -> None:
    receipts = build_chain(
        [{"statement_id": "s001"}, {"statement_id": "s002"}, {"statement_id": "s003"}]
    )
    run_dir = write_run(tmp_path / "run", receipts)
    # Truncate the tail: internally consistent, but head no longer matches.
    kept = [canonical_json(receipt) for receipt in receipts[:2]]
    (run_dir / "receipts.jsonl").write_text("\n".join(kept) + "\n")

    result = verify_ledger(load_run(run_dir))
    assert not result.ok
    assert any("ledger_head" in error for error in result.errors)


def test_torn_write_is_warning_not_error(tmp_path: Path) -> None:
    receipts = build_chain([{"statement_id": "s001"}, {"statement_id": "s002"}])
    stale_manifest = {
        "v": "libretto.run.v1",
        "run_id": "20260716-120000-test01",
        "program": "examples/test.libretto",
        "state_backend": "filesystem",
        "status": "running",
        "receipt_count": 1,
        "ledger_head": receipts[0]["content_hash"],
    }
    run_dir = write_run(tmp_path / "run", receipts, manifest=stale_manifest)

    result = verify_ledger(load_run(run_dir))
    assert result.ok
    assert any("torn write" in warning for warning in result.warnings)


def test_torn_write_on_first_receipt_is_warning(tmp_path: Path) -> None:
    receipts = build_chain([{"statement_id": "s001"}])
    fresh_manifest = {
        "v": "libretto.run.v1",
        "run_id": "20260716-120000-test01",
        "program": "examples/test.libretto",
        "state_backend": "filesystem",
        "status": "running",
        "receipt_count": 0,
        "ledger_head": None,
    }
    run_dir = write_run(tmp_path / "run", receipts, manifest=fresh_manifest)

    result = verify_ledger(load_run(run_dir))
    assert result.ok
    assert any("torn write" in warning for warning in result.warnings)


def test_unavailable_basis_with_nonzero_tokens_rejected(tmp_path: Path) -> None:
    receipt = make_receipt(
        "s001",
        prev=None,
        usage={
            "basis": "unavailable",
            "input_tokens": 5,
            "output_tokens": 0,
            "model": "none",
        },
    )
    run_dir = write_run(tmp_path / "run", [receipt], manifest=False)

    result = verify_ledger(load_run(run_dir))
    assert not result.ok
    assert any("unavailable" in error for error in result.errors)


def test_missing_manifest_is_warning(tmp_path: Path) -> None:
    receipts = build_chain([{"statement_id": "s001"}])
    run_dir = write_run(tmp_path / "run", receipts, manifest=False)

    result = verify_ledger(load_run(run_dir))
    assert result.ok
    assert any("run.json missing" in warning for warning in result.warnings)


def test_unknown_schema_version_rejected(tmp_path: Path) -> None:
    receipt = make_receipt("s001", prev=None)
    receipt["v"] = "openprose.receipt.v99"
    run_dir = write_run(tmp_path / "run", [receipt], manifest=False)

    result = verify_ledger(load_run(run_dir))
    assert not result.ok
    assert any("unknown schema tag" in error for error in result.errors)


def test_float_smuggling_rejected(tmp_path: Path) -> None:
    receipt = make_receipt("s001", prev=None)
    receipt["usage"]["input_tokens"] = 1  # keep model-valid
    raw = json.loads(canonical_json(receipt))
    raw["usage"]["input_tokens"] = 1.0  # float sneaks into the file
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "receipts.jsonl").write_text(json.dumps(raw, sort_keys=True) + "\n")

    result = verify_ledger(load_run(run_dir))
    assert not result.ok
