# Addendum — Skip-Semantics Measurement (Development-Plan Phase 4)

*2026-07-16. Follow-up to the seven-phase evaluation: re-running a
committed program under the new skip semantics
(`prose.md` → Skip Semantics; `contracts/receipt.md` → Skipped receipts).*

## Setup

- **Program:** `examples/16-parallel-reviews.prose` (3 parallel reviewer
  branches + context-wired synthesis; 4 sessions total).
- **Baseline:** the Phase 1 committed run `20260716-082734-0vx3bm` — all
  four sessions rendered by real subagents.
- **Candidate:** `20260716-094019-fsylki`, executed as
  `prose run … --resume 20260716-082734-0vx3bm` with the program
  byte-unchanged.

## Result

| | Baseline (rendered) | Resume (skip semantics) |
| --- | ---: | ---: |
| Tokens (in+out) | 218,285 | **0** |
| Sessions spawned | 4 | **0** |
| Skipped | 0 | 4/4 (100%) |
| Chain verify | OK | OK |

`openprose-tools cost --compare` reports `saved 100%`.

## Interpretation

- For an **unchanged program with unchanged inputs**, the skip rule
  eliminates the entire model spend of a re-run — including the ~46K
  token/session context floor the original evaluation identified as the
  dominant economic fact. This is the best case by construction: every
  memo identity (program hash, statement_id, material fingerprints) was
  unmoved.
- Real programs re-run because *something* changed; the expected saving
  is proportional to the unmoved fraction of the statement graph.
  `material:` annotations widen that fraction by excluding immaterial
  context from the memo identity.
- The reuse is fully auditable: each skipped receipt carries
  `reused_from` coordinates and the copied binding's fingerprint; the
  resumed run dir remains self-contained (copy-with-provenance) and
  passes keyless `verify`.

## Caveat

This measurement demonstrates the mechanism, not a field distribution of
savings. The original evaluation's cost findings (2–6× premium for
multi-session decomposition on *first* runs) are unchanged — skip
semantics attack repeat runs, which is exactly where the composability
value of `.prose` programs was supposed to pay off.
