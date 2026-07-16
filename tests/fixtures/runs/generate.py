"""Regenerate the corrupted-run fixtures (deterministic, no timestamps).

Run from this directory:
    uv run --project ../../../tools python generate.py

Each fixture is a minimal run directory that must FAIL (or warn) in
``openprose-tools verify`` in a specific way. Expected outcomes live in
``expected.json`` per fixture and are asserted by
``tools/tests/test_fixtures.py``.
"""

import json
import sys
from pathlib import Path
from typing import Any

from openprose_tools.canonical import canonical_json, receipt_content_hash

HERE = Path(__file__).resolve().parent
RUN_ID = "20260101-000000-fixtur"


def receipt(statement_id: str, prev: str | None, **overrides: Any) -> dict:
    body: dict[str, Any] = {
        "v": "openprose.receipt.v1",
        "run_id": RUN_ID,
        "statement_id": statement_id,
        "kind": "session",
        "agent": "worker",
        "input_fingerprints": {},
        "output_fingerprint": None,
        "status": "rendered",
        "surprise_cause": None,
        "usage": {
            "basis": "estimated",
            "input_tokens": 100,
            "output_tokens": 10,
            "model": "haiku",
        },
        "error": None,
        "detail": None,
        "reused_from": None,
        "prev": prev,
        "hash_algorithm": "sha256",
    }
    body.update(overrides)
    body["content_hash"] = receipt_content_hash(body)
    return body


def chain(n: int) -> list[dict]:
    receipts: list[dict] = []
    prev: str | None = None
    for i in range(1, n + 1):
        item = receipt(f"s{i:03d}", prev)
        receipts.append(item)
        prev = item["content_hash"]
    return receipts


def write(
    name: str, receipts: list[dict], manifest: dict | None, expected: dict
) -> None:
    run_dir = HERE / name
    run_dir.mkdir(exist_ok=True)
    (run_dir / "receipts.jsonl").write_text(
        "\n".join(canonical_json(r) for r in receipts) + "\n"
    )
    if manifest is not None:
        (run_dir / "run.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (run_dir / "expected.json").write_text(json.dumps(expected, indent=2) + "\n")


def manifest_for(receipts: list[dict], **overrides: Any) -> dict:
    base = {
        "v": "openprose.run.v1",
        "run_id": RUN_ID,
        "program": "fixture.prose",
        "state_backend": "filesystem",
        "status": "completed",
        "receipt_count": len(receipts),
        "ledger_head": receipts[-1]["content_hash"],
    }
    base.update(overrides)
    return base


def main() -> None:
    # 1. tampered-content: a field edited after hashing.
    tampered = chain(3)
    manifest = manifest_for(tampered)
    tampered[1]["agent"] = "tampered"  # hash no longer matches
    write(
        "tampered-content",
        tampered,
        manifest,
        {"ok": False, "error_contains": "content_hash mismatch"},
    )

    # 2. broken-chain: second receipt points at the wrong prev.
    first = receipt("s001", None)
    second = receipt("s002", "sha256:" + "ab" * 32)
    write(
        "broken-chain",
        [first, second],
        manifest_for([first, second]),
        {"ok": False, "error_contains": "prev broken"},
    )

    # 3. truncated-ledger: tail removed; manifest still anchors old head.
    full = chain(3)
    write(
        "truncated-ledger",
        full[:2],
        manifest_for(full),
        {"ok": False, "error_contains": "ledger_head"},
    )

    # 4. torn-write: append succeeded, head update did not (warning only).
    torn = chain(2)
    write(
        "torn-write",
        torn,
        manifest_for(torn[:1], status="running"),
        {"ok": True, "warning_contains": "torn write"},
    )

    print("fixtures regenerated")


if __name__ == "__main__":
    sys.exit(main())
