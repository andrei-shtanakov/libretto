# openprose-tools

Deterministic verification tooling for OpenProse runs — the reader side of
`contracts/receipt.md` (`openprose.receipt.v1`). No LLM involved; output is
byte-stable across invocations.

**This package is optional.** Running `.prose` programs never requires it —
the spec core stays zero-dependency. The tools exist for CI, audit, and
inspection of run artifacts after the fact.

## Commands

```sh
uv run openprose-tools inspect <run-dir> [--json]
uv run openprose-tools verify <run-dir>
uv run openprose-tools lint <file.prose> [...]
```

- **inspect** — headless summary of a run: dispositions
  (rendered/skipped/failed), token rollups per agent and per `usage.basis`
  (exact/estimated/unavailable — estimates are labeled, never laundered),
  failed statements, recorded discretion outcomes, chain status. `--json`
  emits machine-readable output for agents and CI.
- **verify** — chain-consistency check: schema validity, canonical
  hashability, `content_hash` correctness, `prev` linkage, and the
  `run.json` `ledger_head` anchor. Exit 0 = consistent, 1 = broken,
  2 = unreadable. A manifest that trails the ledger by exactly one receipt
  is reported as a torn-write **warning**, not an error.

- **lint** — deterministic check of the mechanically decidable subset of
  `compiler.md`: indentation, known keywords (canonical + all five
  alternative registers), balanced blocks, root-scope flat-namespace
  duplicates, agent/block reference resolution. **A linter, not the
  compiler** — semantic validation stays with `prose compile` (LLM).
  Diagnostics OP001–OP008 are errors; OP009 marks constructs bundled
  programs use that the grammar doesn't define yet (warning; see
  ROADMAP P2.5). Exit 0 = no errors.

`<run-dir>` is a `.prose/runs/{run-id}/` directory containing
`receipts.jsonl` (+ `run.json`). Committed sample runs live in
`examples/runs/` and verify keylessly. The regression corpus for lint and
verify lives in `tests/fixtures/` (repo checkout only, not shipped).

## Development

```sh
cd tools
uv sync
uv run pytest
uv run ruff check .
uv run pyrefly check
```
