"""Command-line interface: ``openprose-tools inspect|verify <run-dir>``."""

import argparse
import json
import sys

from .inspect_run import inspect_run, render_text
from .ledger import LedgerLoadError, load_run
from .verify import verify_ledger


def main(argv: list[str] | None = None) -> int:
    """Entry point. Returns the process exit code."""
    parser = argparse.ArgumentParser(
        prog="openprose-tools",
        description=(
            "Deterministic tooling over OpenProse run artifacts (contracts/receipt.md)"
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_inspect = sub.add_parser(
        "inspect", help="summarize a run (dispositions, cost, failures, chain)"
    )
    p_inspect.add_argument("run_dir", help="path to .prose/runs/<run-id>")
    p_inspect.add_argument(
        "--json", action="store_true", help="emit machine-readable JSON"
    )

    p_verify = sub.add_parser(
        "verify", help="verify ledger chain consistency and the manifest anchor"
    )
    p_verify.add_argument("run_dir", help="path to .prose/runs/<run-id>")

    args = parser.parse_args(argv)

    try:
        raw = load_run(args.run_dir)
    except LedgerLoadError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.command == "verify":
        result = verify_ledger(raw)
        for warning in result.warnings:
            print(f"warning: {warning}")
        for error in result.errors:
            print(f"error: {error}")
        print(f"chain: {'OK' if result.ok else 'BROKEN'} ({len(raw.lines)} receipts)")
        return 0 if result.ok else 1

    summary = inspect_run(raw)
    if args.json:
        print(json.dumps(summary, sort_keys=True, ensure_ascii=False, indent=2))
    else:
        print(render_text(summary))
    return 0 if summary["chain"]["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
