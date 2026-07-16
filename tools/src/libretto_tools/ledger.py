"""Loading of run artifacts: receipts.jsonl and run.json."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class LedgerLoadError(ValueError):
    """Raised when run artifacts are missing or not parseable as JSON."""


@dataclass(frozen=True)
class RawLedger:
    """Parsed-but-unvalidated run artifacts.

    ``lines`` are raw dicts (unknown fields preserved — hashing needs
    them); ``manifest`` is the raw run.json dict or None if absent.
    """

    run_dir: Path
    lines: list[dict[str, Any]]
    manifest: dict[str, Any] | None


def load_run(run_dir: str | Path) -> RawLedger:
    """Load receipts.jsonl and run.json from *run_dir*.

    Raises LedgerLoadError when the directory or ledger is missing, or
    when any line/manifest is not a JSON object.
    """
    root = Path(run_dir)
    if not root.is_dir():
        raise LedgerLoadError(f"run directory not found: {root}")

    ledger_path = root / "receipts.jsonl"
    if not ledger_path.is_file():
        raise LedgerLoadError(f"receipts.jsonl not found in {root}")

    lines: list[dict[str, Any]] = []
    with ledger_path.open(encoding="utf-8") as fh:
        for lineno, raw in enumerate(fh, start=1):
            if not raw.strip():
                continue
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise LedgerLoadError(
                    f"receipts.jsonl line {lineno}: invalid JSON ({exc.msg})"
                ) from exc
            if not isinstance(parsed, dict):
                raise LedgerLoadError(
                    f"receipts.jsonl line {lineno}: expected a JSON object"
                )
            lines.append(parsed)

    manifest: dict[str, Any] | None = None
    manifest_path = root / "run.json"
    if manifest_path.is_file():
        try:
            loaded = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise LedgerLoadError(f"run.json: invalid JSON ({exc.msg})") from exc
        if not isinstance(loaded, dict):
            raise LedgerLoadError("run.json: expected a JSON object")
        manifest = loaded

    return RawLedger(run_dir=root, lines=lines, manifest=manifest)
