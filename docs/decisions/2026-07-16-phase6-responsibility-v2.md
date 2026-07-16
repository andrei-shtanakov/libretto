# ADR: Phase 6 — adopt Responsibility v2, or close the plan at v1 scope?

**Status:** accepted — deferred (2026-07-16)
**Context:** `docs/plans/2026-07-16-development-plan.md`, Phase 6 (explicitly
ADR-gated); lessons-from-prose analysis (P2 priority, "breaking mental
model" risk); seven-phase evaluation verdict.

## Question

Should `open-prose` add the upstream responsibility model — `*.prose.md`
files with `kind: responsibility`, `### Goal / Maintains / Requires /
Continuity`, plus `watch:`/gateway external-driven wake — on top of the
v1 imperative `.prose` language? Or is v1 + the Phase 1–5 contract stack
(receipts, IR, materiality, adapters) this repo's complete scope?

## What adoption would mean (plan tasks 6.2–6.3)

- A second, additive source format: `*.prose.md` responsibilities;
  existing `.prose` programs mapped to `function` / `### Execution`.
- Terminology sync with upstream: `Maintains`, `Requires`, `Continuity`,
  `Receipt`, `World-model`.
- `watch:` / gateway as external wake (ROADMAP P3 item) — deferred until
  here because it only makes sense with standing responsibilities.
- VM semantics for *standing* truth-maintenance: re-evaluation cycles,
  wake sources, facet subscriptions — substantially more spec surface in
  `prose.md`, and a second execution model to keep faithful.

## Arguments FOR adopting (Option A)

1. **Completes protocol parity with upstream.** We already adopted
   receipts (wake/surprise semantics included), materiality, and facet
   fingerprints — the responsibility model is what those concepts were
   designed for. v1 uses them in a narrower (imperative) setting.
2. **Standing jobs on a Python-verifiable substrate** would be unique:
   upstream's Reactor is TypeScript; an ecosystem project wanting
   standing AI work with keyless Python verification has no option today.
3. **Research value.** This is a research fork; comparing an embodied-VM
   responsibility runtime against upstream's deterministic Reactor is a
   genuinely interesting experiment (the same "does simulation suffice?"
   question the original evaluation answered for v1).

## Arguments AGAINST adopting now (Option B — defer)

1. **No demand.** No ecosystem project consumes even the bounded-run
   contracts yet (the Phase 5 offer note is unanswered); nobody has asked
   for standing jobs on this substrate. Same evidence posture as the
   Rust decision gate — and the same conclusion follows.
2. **The niche argument.** The evaluation's verdict was precise: this
   repo's value is *reliable, auditable, reproducible bounded runs*.
   Standing truth-maintenance is upstream's product, with a real runtime,
   CI, and a `runtime_contract` that is still churning (v0.14→0.15 was a
   breaking change). Racing a moving upstream with an embodied VM is the
   thin end of re-implementing Reactor — the plan's explicit Non-Goal.
3. **The interim pattern already works.** Phase 4 makes a scheduled
   re-run of a v1 program with `--resume` behave like a poor-man's
   responsibility: cost scales with surprise (measured: 100% skip on an
   unchanged program), receipts record every wake, and `cost --compare`
   shows the drift. A cron + `--resume` loop covers most "keep this
   fresh" needs without new language surface.
4. **Spec-surface risk.** v1 fidelity was validated by a seven-phase
   evaluation. A second execution model would need its own evaluation
   to make faithful-execution claims — a large investment ahead of any
   consumer.

## Recommendation

**Option B — defer, with revisit criteria.** Close the 2026-07-16
development plan at Phases 0–5; keep Phase 6 gated behind ANY of:

1. An ecosystem project commits to consuming standing-job outputs on
   this substrate (not exploratory interest — a named integration).
2. Upstream's responsibility contract stabilizes (no breaking
   `runtime_contract` change across two consecutive minor releases),
   making terminology/porting durable.
3. The cron + `--resume` interim pattern demonstrably fails a real use
   case (document the failure as the ADR trigger).

Immediate follow-ups if deferred: note the interim pattern in
`guidance/patterns.md` (small, additive), and leave ROADMAP P3 `watch:`
annotated as Phase-6-gated.

## Decision

**Accepted: Option B — defer.**

`open-prose` scope is v1 imperative `.prose` plus the Phase 1–5 contract
stack: receipts, IR, materiality, adapters, and Python verification
tooling. Responsibility v2 (`*.prose.md`, standing jobs,
`watch:`/gateway) remains Phase-6-gated and will only be reconsidered
when one of the revisit criteria above is met.

Rationale (owner, 2026-07-16): the repo's niche is already sharp — v1
bounded runs + contracts/tooling. Responsibility v2 introduces a second
execution model, which would require its own validation story of nearly
the same scale as the original seven-phase evaluation; with zero
confirmed demand that is premature. The 100%-skip interim-pattern claim
is backed by `evaluation/results/phase-4-skip-addendum.md`.
