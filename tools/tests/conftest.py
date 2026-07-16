"""Test helpers: a minimal emit_receipt-equivalent ledger writer."""

import json
from pathlib import Path
from typing import Any

import pytest

from libretto_tools.canonical import canonical_json, receipt_content_hash

RUN_ID = "20260716-120000-test01"


def make_receipt(
    statement_id: str,
    *,
    kind: str = "session",
    agent: str | None = "worker",
    status: str = "rendered",
    prev: str | None = None,
    **overrides: Any,
) -> dict[str, Any]:
    """Build one valid receipt dict (content_hash computed last)."""
    receipt: dict[str, Any] = {
        "v": "libretto.receipt.v1",
        "run_id": RUN_ID,
        "statement_id": statement_id,
        "kind": kind,
        "agent": agent,
        "input_fingerprints": {},
        "output_fingerprint": None,
        "status": status,
        "surprise_cause": None,
        "usage": {
            "basis": "estimated",
            "input_tokens": 100,
            "output_tokens": 20,
            "model": "haiku",
        },
        "error": None,
        "detail": None,
        "reused_from": None,
        "prev": prev,
        "hash_algorithm": "sha256",
    }
    receipt.update(overrides)
    receipt["content_hash"] = receipt_content_hash(receipt)
    return receipt


def build_chain(specs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Chain a list of receipt-spec dicts (each passed to make_receipt)."""
    chained: list[dict[str, Any]] = []
    prev: str | None = None
    for spec in specs:
        spec = dict(spec)
        statement_id = spec.pop("statement_id")
        receipt = make_receipt(statement_id, prev=prev, **spec)
        chained.append(receipt)
        prev = receipt["content_hash"]
    return chained


def write_run(
    run_dir: Path,
    receipts: list[dict[str, Any]],
    *,
    manifest: dict[str, Any] | None | bool = True,
) -> Path:
    """Write receipts.jsonl (+ run.json unless manifest is False)."""
    run_dir.mkdir(parents=True, exist_ok=True)
    lines = "\n".join(canonical_json(receipt) for receipt in receipts)
    (run_dir / "receipts.jsonl").write_text(lines + "\n", encoding="utf-8")

    if manifest is False:
        return run_dir
    if manifest is True or manifest is None:
        manifest = {
            "v": "libretto.run.v1",
            "run_id": RUN_ID,
            "program": "examples/test.libretto",
            "state_backend": "filesystem",
            "status": "completed",
            "receipt_count": len(receipts),
            "ledger_head": receipts[-1]["content_hash"] if receipts else None,
        }
    (run_dir / "run.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return run_dir


@pytest.fixture
def valid_run(tmp_path: Path) -> Path:
    """A three-receipt valid run with a matching manifest."""
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
            {"statement_id": "s001"},
            {
                "statement_id": "run",
                "kind": "control",
                "agent": None,
                "detail": {"event": "run_end", "outcome": "completed"},
                "usage": {
                    "basis": "unavailable",
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "model": "none",
                },
            },
        ]
    )
    return write_run(tmp_path / "run", receipts)
