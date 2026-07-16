"""Cost rollups over receipt ledgers: by statement, agent, model, status.

Deterministic reader (no LLM). Percentages are integer percent (the
canonical form forbids floats and so does this tool's output).
"""

from typing import Any

from .ledger import RawLedger


def _tokens(line: dict[str, Any]) -> tuple[int, int, str, str]:
    usage = line.get("usage") or {}
    in_tok = usage.get("input_tokens")
    out_tok = usage.get("output_tokens")
    in_tok = in_tok if isinstance(in_tok, int) and not isinstance(in_tok, bool) else 0
    out_tok = (
        out_tok if isinstance(out_tok, int) and not isinstance(out_tok, bool) else 0
    )
    return (
        in_tok,
        out_tok,
        str(usage.get("basis", "unavailable")),
        str(usage.get("model", "none")),
    )


def _bucket(target: dict[str, dict[str, int]], key: str, i: int, o: int) -> None:
    row = target.setdefault(key, {"receipts": 0, "input_tokens": 0, "output_tokens": 0})
    row["receipts"] += 1
    row["input_tokens"] += i
    row["output_tokens"] += o


def cost_run(raw: RawLedger) -> dict[str, Any]:
    """Build the cost summary for one loaded run."""
    manifest = raw.manifest or {}
    totals = {"input_tokens": 0, "output_tokens": 0}
    by_status: dict[str, dict[str, int]] = {}
    by_agent: dict[str, dict[str, int]] = {}
    by_model: dict[str, dict[str, int]] = {}
    by_basis: dict[str, dict[str, int]] = {}
    statements: list[dict[str, Any]] = []
    reused: list[dict[str, Any]] = []
    spend_kinds = {"session", "parallel_branch", "discretion"}
    spendable = skipped = 0

    for line in raw.lines:
        i, o, basis, model = _tokens(line)
        totals["input_tokens"] += i
        totals["output_tokens"] += o
        status = str(line.get("status"))
        kind = str(line.get("kind"))

        _bucket(by_status, status, i, o)
        _bucket(by_basis, basis, i, o)
        if isinstance(line.get("agent"), str):
            _bucket(by_agent, str(line["agent"]), i, o)
        if model != "none":
            _bucket(by_model, model, i, o)

        if kind in spend_kinds:
            spendable += 1
            if status == "skipped":
                skipped += 1

        statements.append(
            {
                "statement_id": line.get("statement_id"),
                "kind": kind,
                "agent": line.get("agent"),
                "model": model,
                "status": status,
                "input_tokens": i,
                "output_tokens": o,
            }
        )
        if line.get("reused_from"):
            reused.append(
                {
                    "statement_id": line.get("statement_id"),
                    "from_run": line["reused_from"].get("run_id"),
                }
            )

    return {
        "run_id": manifest.get("run_id"),
        "program": manifest.get("program"),
        "reuse_source_run": manifest.get("reuse_source_run"),
        "totals": {**totals, "receipts": len(raw.lines)},
        "by_status": {k: by_status[k] for k in sorted(by_status)},
        "by_basis": {k: by_basis[k] for k in sorted(by_basis)},
        "by_agent": {k: by_agent[k] for k in sorted(by_agent)},
        "by_model": {k: by_model[k] for k in sorted(by_model)},
        "skip": {
            "spendable_statements": spendable,
            "skipped": skipped,
            "skipped_percent": (skipped * 100) // spendable if spendable else 0,
        },
        "reused": reused,
        "statements": statements,
    }


def compare_runs(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    """Compare two cost summaries (a = baseline, b = candidate)."""
    a_total = a["totals"]["input_tokens"] + a["totals"]["output_tokens"]
    b_total = b["totals"]["input_tokens"] + b["totals"]["output_tokens"]
    return {
        "baseline": {"run_id": a["run_id"], "tokens": a_total},
        "candidate": {
            "run_id": b["run_id"],
            "tokens": b_total,
            "skipped": b["skip"]["skipped"],
        },
        "delta_tokens": b_total - a_total,
        "saved_percent": ((a_total - b_total) * 100) // a_total if a_total else 0,
    }


def render_cost_text(summary: dict[str, Any]) -> str:
    """Human-readable cost report."""
    lines = [
        f"run: {summary['run_id']}  program: {summary['program']}",
        f"tokens: in={summary['totals']['input_tokens']} "
        f"out={summary['totals']['output_tokens']} "
        f"receipts={summary['totals']['receipts']}",
    ]
    if summary["reuse_source_run"]:
        lines.append(f"reuse source: {summary['reuse_source_run']}")
    skip = summary["skip"]
    lines.append(
        f"skip: {skip['skipped']}/{skip['spendable_statements']} spendable "
        f"statements skipped ({skip['skipped_percent']}%)"
    )
    for label in ("by_status", "by_basis", "by_model", "by_agent"):
        for key, row in summary[label].items():
            lines.append(
                f"  {label[3:]}={key}: receipts={row['receipts']} "
                f"in={row['input_tokens']} out={row['output_tokens']}"
            )
    for item in summary["reused"]:
        lines.append(f"  reused {item['statement_id']} <- {item['from_run']}")
    return "\n".join(lines)
