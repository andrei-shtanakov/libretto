"""Headless run inspection: dispositions, cost rollups, failures.

Deterministic reader over receipts.jsonl + run.json. Output is stable
across invocations (sorted keys, no timestamps), suitable for CI and
for agents consuming ``--json``.
"""

from collections import Counter
from typing import Any

from .ledger import RawLedger
from .verify import verify_ledger


def inspect_run(raw: RawLedger) -> dict[str, Any]:
    """Build the inspection summary for a loaded run."""
    verification = verify_ledger(raw)

    dispositions = Counter(str(line.get("status")) for line in raw.lines)
    kinds = Counter(str(line.get("kind")) for line in raw.lines)

    by_agent: dict[str, dict[str, int]] = {}
    by_basis: dict[str, dict[str, int]] = {}
    total = {"input_tokens": 0, "output_tokens": 0}
    failed: list[dict[str, Any]] = []
    discretions: list[dict[str, Any]] = []

    for line in raw.lines:
        usage = line.get("usage") or {}
        in_tok = _int(usage.get("input_tokens"))
        out_tok = _int(usage.get("output_tokens"))
        basis = str(usage.get("basis", "unavailable"))

        total["input_tokens"] += in_tok
        total["output_tokens"] += out_tok

        basis_row = by_basis.setdefault(
            basis, {"receipts": 0, "input_tokens": 0, "output_tokens": 0}
        )
        basis_row["receipts"] += 1
        basis_row["input_tokens"] += in_tok
        basis_row["output_tokens"] += out_tok

        agent = line.get("agent")
        if isinstance(agent, str):
            agent_row = by_agent.setdefault(
                agent, {"receipts": 0, "input_tokens": 0, "output_tokens": 0}
            )
            agent_row["receipts"] += 1
            agent_row["input_tokens"] += in_tok
            agent_row["output_tokens"] += out_tok

        if line.get("status") == "failed":
            error = line.get("error") or {}
            failed.append(
                {
                    "statement_id": line.get("statement_id"),
                    "kind": line.get("kind"),
                    "agent": agent,
                    "error_type": error.get("type"),
                    "message": error.get("message"),
                    "retry_count": error.get("retry_count"),
                }
            )

        if line.get("kind") == "discretion":
            detail = line.get("detail") or {}
            discretions.append(
                {
                    "statement_id": line.get("statement_id"),
                    "condition": detail.get("condition"),
                    "outcome": detail.get("outcome"),
                    "branch": detail.get("branch"),
                    "reason": detail.get("reason"),
                }
            )

    manifest = raw.manifest or {}
    return {
        "run_id": manifest.get("run_id") or _first_run_id(raw),
        "program": manifest.get("program"),
        "run_status": manifest.get("status"),
        "receipt_count": len(raw.lines),
        "dispositions": dict(sorted(dispositions.items())),
        "kinds": dict(sorted(kinds.items())),
        "usage_total": total,
        "usage_by_basis": {k: by_basis[k] for k in sorted(by_basis)},
        "usage_by_agent": {k: by_agent[k] for k in sorted(by_agent)},
        "failed_statements": failed,
        "discretion_outcomes": discretions,
        "chain": {
            "ok": verification.ok,
            "errors": verification.errors,
            "warnings": verification.warnings,
        },
    }


def render_text(summary: dict[str, Any]) -> str:
    """Render the inspection summary as human-readable text."""
    lines: list[str] = []
    chain = summary["chain"]
    lines.append(f"run: {summary['run_id']}  program: {summary['program']}")
    lines.append(
        f"status: {summary['run_status']}  receipts: {summary['receipt_count']}"
    )
    lines.append(f"dispositions: {_fmt_counts(summary['dispositions'])}")
    lines.append(f"kinds: {_fmt_counts(summary['kinds'])}")

    total = summary["usage_total"]
    lines.append(f"tokens: in={total['input_tokens']} out={total['output_tokens']}")
    for basis, row in summary["usage_by_basis"].items():
        lines.append(
            f"  basis={basis}: receipts={row['receipts']} "
            f"in={row['input_tokens']} out={row['output_tokens']}"
        )
    for agent, row in summary["usage_by_agent"].items():
        lines.append(
            f"  agent={agent}: receipts={row['receipts']} "
            f"in={row['input_tokens']} out={row['output_tokens']}"
        )

    if summary["failed_statements"]:
        lines.append("failed statements:")
        for item in summary["failed_statements"]:
            lines.append(
                f"  {item['statement_id']} [{item['kind']}] "
                f"{item['error_type']}: {item['message']} "
                f"(retries: {item['retry_count']})"
            )
    else:
        lines.append("failed statements: none")

    if summary["discretion_outcomes"]:
        lines.append("discretion outcomes:")
        for item in summary["discretion_outcomes"]:
            lines.append(
                f"  {item['statement_id']}: {item['condition']!r} "
                f"-> {item['outcome']!r}"
                + (f" [branch: {item['branch']}]" if item["branch"] else "")
            )

    lines.append(f"chain: {'OK' if chain['ok'] else 'BROKEN'}")
    for err in chain["errors"]:
        lines.append(f"  error: {err}")
    for warn in chain["warnings"]:
        lines.append(f"  warning: {warn}")
    return "\n".join(lines)


def _int(value: Any) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) else 0


def _first_run_id(raw: RawLedger) -> Any:
    return raw.lines[0].get("run_id") if raw.lines else None


def _fmt_counts(counts: dict[str, int]) -> str:
    return " ".join(f"{key}={val}" for key, val in counts.items()) if counts else "none"
