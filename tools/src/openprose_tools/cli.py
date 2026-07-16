"""Command-line interface: ``openprose-tools inspect|verify <run-dir>``."""

import argparse
import json
import sys
from pathlib import Path

from .inspect_run import inspect_run, render_text
from .ir import check_ir, default_ir_path
from .ledger import LedgerLoadError, load_run
from .lint import lint_file
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

    p_lint = sub.add_parser(
        "lint",
        help="deterministic .prose lint (mechanical subset of compiler.md)",
    )
    p_lint.add_argument("files", nargs="+", help=".prose files to lint")

    p_ir = sub.add_parser(
        "ir-check",
        help="validate a compiled IR: schema, hashes, freshness, consistency",
    )
    p_ir.add_argument("source", help="the .prose source file")
    p_ir.add_argument(
        "--ir",
        default=None,
        help="IR path (default: <source-dir>/dist/<stem>.ir.json)",
    )

    args = parser.parse_args(argv)

    if args.command == "ir-check":
        source = Path(args.source)
        try:
            source.read_bytes()  # exit 2 covers missing AND unreadable
        except OSError as exc:
            print(f"error: source unreadable: {exc}", file=sys.stderr)
            return 2
        result = check_ir(source, args.ir)
        for warning in result.warnings:
            print(f"warning: {warning}")
        for error in result.errors:
            print(f"error: {error}")
        ir_path = Path(args.ir) if args.ir else default_ir_path(source)
        print(f"ir-check: {'OK' if result.ok else 'FAIL'} ({ir_path})")
        return 0 if result.ok else 1

    if args.command == "lint":
        errors = warnings = 0
        for file_path in args.files:
            try:
                diagnostics = lint_file(file_path)
            except OSError as exc:
                print(f"error: {exc}", file=sys.stderr)
                return 2
            for diag in diagnostics:
                print(diag.render())
                if diag.severity == "error":
                    errors += 1
                else:
                    warnings += 1
        verdict = "OK" if errors == 0 else "FAIL"
        print(
            f"lint: {verdict} ({len(args.files)} files, "
            f"{errors} errors, {warnings} warnings)"
        )
        return 0 if errors == 0 else 1

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
