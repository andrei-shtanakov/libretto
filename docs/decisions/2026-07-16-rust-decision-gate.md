# ADR: Rust decision gate — re-affirm Python-only tooling (2026-07-16)

**Status:** accepted
**Context:** `docs/plans/2026-07-16-development-plan.md`, task 4.6 — the
plan deferred Rust behind an explicit decision gate at the end of
Phase 4: adopt a shared Rust crate only if fingerprint/chain verification
is (a) needed by neighbor ecosystem projects as a hot path, or (b) too
slow in Python.

## Decision

**Python-only stands.** No Rust crate, no handoff.

## Evidence

- **Performance:** the full deterministic suite — 57 tests covering
  canonical hashing, chain verification, lint over 60 programs, IR
  checks, and cost rollups — runs in well under a second locally; each CI
  job completes in 7–11 s, dominated by checkout/setup, not verification.
  The largest committed ledger is 9 receipts; even thousand-receipt
  ledgers are trivially within Python's envelope for sha256-over-bytes
  work (hashlib is C already).
- **Ecosystem demand:** no neighbor project consumes
  `receipts.jsonl`/`ir.json` today. The Phase 5 handoff note will
  *offer* the contracts to atp-platform/proctor/arbiter; none has asked
  for a native library.

## Revisit criteria (any one suffices)

1. A neighbor project starts verifying ledgers in a latency- or
   throughput-sensitive path (e.g. per-request verification in
   atp-platform).
2. Ledgers grow to a size where `verify` exceeds ~1 s in CI on realistic
   corpora.
3. A second language needs the canonicalization logic (the contract is
   deliberately portable — sorted keys, integers only, UTF-8 — so a Rust
   reference implementation with shared fixtures would then be the right
   vehicle, vendored per workspace rules).

Until then: less code, one toolchain, `uv`-only — per the plan's
Non-Goals.
