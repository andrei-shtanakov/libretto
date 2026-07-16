# Libretto Development Plan (2026-07-16)

> **For agentic workers:** This is a roadmap-level development plan. Individual
> phases should be broken into per-task implementation plans (in this directory)
> before execution. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Evolve `libretto` from a spec-only research repo into an active
downstream of upstream `openprose/prose` — keeping the zero-dependency
spec-as-VM core, adopting upstream *protocols* (receipts, IR, materiality),
and adding a thin deterministic tooling layer in Python that fits the
surrounding ecosystem.

**Architecture:** Two-layer model. Layer 1 (unchanged identity): markdown
specs + `.libretto` programs that an LLM embodies — no runtime binary required
to *run* a program. Layer 2 (new): machine-readable artifacts the VM is
required to emit (receipts, compile IR) plus a small Python package that
deterministically *verifies* those artifacts offline — replay, inspect,
chain-check, CI gates. We port **schemas and discipline** from `prose`, not
its TypeScript runtime.

**Tech Stack:** Markdown specs (core), JSON/JSONL contracts, Python 3.12+
(`uv`, `pydantic`, `pytest`, `ruff`, `pyrefly`) for tooling. Rust is
deliberately deferred (see Non-Goals) until a performance-critical verifier
justifies it.

## Sources / inputs

- **External** (dev-workspace analyses, not shipped in this repo — they live
  in the polyrepo coordination workspace and are unavailable in a standalone
  clone): *"Libretto — lessons from prose"* (2026-07-16) — what to adopt
  from upstream `prose` (receipts, IR, materiality, fixtures, doctor); and
  *"prose / libretto comparison"* (2026-07-16) — provenance, divergence,
  governance gaps. Their actionable conclusions are restated in this plan,
  which is self-contained without them.
- `evaluation/results/final-verdict.md` — 7-phase empirical evaluation:
  faithful execution, but ~2–6× token premium, ~51% session-boundary
  overhead, concrete spec gaps.
- `ROADMAP.md` — existing P0–P5 feature roadmap (this plan sequences and
  extends it; ROADMAP.md stays as the feature backlog).

## Strategic decision (locked in by this plan)

**Status: active downstream / research fork of `openprose/prose`** — not an
archive. Rationale:

- The evaluation proved the spec-as-VM concept executes faithfully and has a
  real niche: **reliable, auditable, reproducible multi-agent work** (multi-lens
  review, compliance pipelines, fan-out latency wins, context isolation).
- Upstream `prose` solved the problems this repo's own roadmap names
  (deterministic replay, structured errors, cost control, inspect) — but in a
  TypeScript/npm monorepo. This ecosystem is Python/Rust; blindly porting the
  Reactor runtime would destroy the zero-dependency identity *and* add a
  foreign toolchain.
- Therefore: **vendor upstream contracts (pinned copies), reimplement the thin
  deterministic layer in Python, keep the language spec-first.**

## Global Constraints

- Zero-dependency rule applies to the *spec core*: running a `.libretto` program
  must never require the Python tooling. Tooling is for verification, CI, and
  inspection only.
- All Python code **introduced by this plan** (the `tools/` package,
  Phase 1 onward — the repo has none today) must follow the workspace
  standards: `uv` only (never pip), type hints everywhere, `pyrefly check`
  clean, `ruff` clean, 88-char lines, `pytest` with anyio for async.
- Cross-repo contracts from `prose` are **vendored as pinned copies** under
  `contracts/vendored/` with source commit hash recorded — never referenced by
  path into `../prose/` (repo-boundaries rule).
- Neighbor repos (`../atp-platform/`, `../prograph-vault/`, `../prose/`, …)
  are read-only; anything requiring their change becomes a handoff note in
  `../prograph-vault/authored/notes/`.
- All changes land via feature branches + PRs; no direct commits to `main`;
  merge is done by a human (git-workflow rule).
- Every spec change must be checked against the 51 examples (implicit test
  suite) until Phase 2 replaces this with explicit fixtures.

## Non-Goals

- **No port of the Reactor runtime** (TS or otherwise). We adopt its receipt/
  IR/materiality *schemas*, not its engine.
- **No npm/pnpm toolchain** in this repo.
- **No Rust yet.** Rust enters only if/when a deterministic verifier becomes a
  hot path shared by other ecosystem projects (e.g. a `receipts-verify` crate
  used by atp-platform). Revisit at end of Phase 4. YAGNI until then.
- **No HTTP serve / network surface.** Upstream documents this as trusted-
  network-only; we simply don't build it.
- **No breaking change to `.libretto` v1 syntax** in Phases 0–4. Responsibility-
  style `*.libretto.md` (Phase 6) is additive.

---

## Phase 0 — Spec hygiene (close known defects; no new tech)

Direct output of the evaluation's "For the Libretto project" recommendations.
Cheap, high-confidence, all inside existing `.md` files.

**Files:** Modify `compiler.md`, `libretto.md`, `guidance/antipatterns.md`,
`guidance/patterns.md`, `README.md`, `ANALYSIS.md`, 2 broken example files.

- [ ] **0.1** Close the `output`-as-return-inside-blocks spec gap in
  `compiler.md` — define block-level `output` as the block's return value,
  reconcile with top-level register-only `output`, specify that `output` does
  NOT break `repeat` (or specify that it does — decide once, document, and
  update the RLM examples 40–43 to match). *This is load-bearing for the RLM
  family; highest-priority spec fix.*
- [ ] **0.2** Specify cross-frame `context: { x }` resolution (currently
  unspecified; evaluation flagged it).
- [ ] **0.3** Add `max_concurrent:` to `parallel:` grammar in `compiler.md` +
  enforcement semantics in `libretto.md` (ROADMAP P1; the evaluation's "most
  concrete correctness/safety gap").
- [ ] **0.4** Fix the specs that currently **promise** cancellation the VM
  cannot deliver: `libretto.md:600` ("Return on first completion, cancel
  others") and `compiler.md:1388` ("cancel others"). Reword to "discard
  losing branches (no in-flight cancellation on current substrates)" and add
  the cost consequence to `guidance/antipatterns.md`: real cost of a race =
  sum of all branches. This is a spec-correctness fix, not just missing
  documentation.
- [ ] **0.5** Fix the two bundled examples that don't compile under the
  flat-namespace rule (dual `let` in both branches of a conditional).
- [ ] **0.6** Add to `guidance/patterns.md`: (a) critic-severity noise —
  high-stakes gates need multiple critics or a rubric, not one severity
  label; (b) "no nested orchestration" leaf-prompt constraint; (c) model-tier-
  per-role guidance (~40% savings, confirmed twice in Phase 7).
- [ ] **0.7** Update `README.md` + `ANALYSIS.md`: state the repo's status
  (active downstream of `openprose/prose`), link the comparison doc's
  conclusions, and set honest cost expectations (2–6× premium, ~51% overhead,
  ~46K token/session floor).
- [ ] **0.8** Write handoff note to `../prograph-vault/authored/notes/`:
  register `prose/` checkout in `COWORK_CONTEXT.md` (external upstream
  clone) and record the `libretto` → `prose` migration relationship.
  *(Handoff only — we do not edit neighbor repos.)*

**Verification:** `libretto compile` (embodied) passes over all 51 examples;
every RLM example (40–43) compiles under the new `output` rule.

---

## Phase 1 — Receipt ledger + deterministic inspect (P0 from lessons doc)

Turns every run into an auditable, replayable, machine-readable artifact.
This is the single highest-leverage adoption from upstream: it makes the
repo's killer feature (auditability) *checkable by code*.

**Files:**
- Create: `contracts/receipt.md` (normative spec, `libretto.receipt.v1`)
- Create: `contracts/vendored/prose-receipt-schema/` (pinned upstream copy +
  `SOURCE.md` with commit hash)
- Modify: `libretto.md`, `state/filesystem.md` (VM must append receipts),
  `primitives/session.md` (minimal `emit_receipt` host primitive)
- Create: `tools/` — `uv init` Python package `libretto-tools`
- Create: `tools/src/libretto_tools/{models.py,inspect.py,verify.py,cli.py}`
- Create: `tools/tests/`
- Create: `examples/runs/` — 2–3 committed sample runs (keyless replay corpus)

**Receipt format (`receipts.jsonl`, one JSON object per line).** A concrete
example instance:

```json
{
  "v": "libretto.receipt.v1",
  "run_id": "20260716-093000-a1b2c3",
  "statement_id": "s014",
  "kind": "session",
  "agent": "researcher",
  "input_fingerprints": {"topic": "sha256:9f2c..."},
  "output_fingerprint": "sha256:4b7e...",
  "status": "rendered",
  "surprise_cause": null,
  "usage": {
    "basis": "exact",
    "input_tokens": 46210,
    "output_tokens": 1840,
    "model": "claude-sonnet-5"
  },
  "error": null,
  "prev_receipt_hash": "sha256:c81d..."
}
```

Allowed enum values (normative list lives in `contracts/receipt.md`):

- `kind`: `session`, `parallel_branch`, `block_call`, `discretion`, `control`
- `status`: `rendered`, `skipped`, `failed`
- `surprise_cause`: `input`, `self`, `external`, or JSON `null`
- `usage.basis`: `exact`, `estimated`, `unavailable`
- `error`: JSON `null`, or a structured object on `status: failed`

`usage.basis` is mandatory and honest: `exact` only when the substrate
reports real token counts; `estimated` when the VM approximates (method
noted in `receipt.md`); `unavailable` otherwise. `inspect`/`cost`/`budget`
must surface the basis — a budget gate fed by estimates says so.

In addition to the per-line chain, the run manifest (`state.md` footer or
`run.json`) records `ledger_head` — the hash of the last receipt — so a
truncated-but-internally-consistent ledger is detectable.

- [ ] **1.1** Write `contracts/receipt.md`: field semantics; hash-chain rule
  (`prev_receipt_hash` = sha256 of previous line's canonical JSON) plus
  `ledger_head` anchoring in the run manifest — and name the guarantee
  honestly: **chain consistency** (detects corruption, reordering, and
  truncation given a trusted head), *not* tamper-proof verification (anyone
  who can rewrite the ledger can rewrite the head; no signatures in v1);
  the rule that receipts are append-only and written *alongside* (not
  instead of) human-readable `state.md`.
- [ ] **1.2** Fix the **minimal statement-ID contract now**, in
  `contracts/receipt.md` (`libretto.statement-id.v1`): deterministic
  derivation from source (e.g. `s{NNN}` in source order after block
  expansion, with a documented rule for loop iterations and parallel
  branches: `s014.i2`, `s014.b1`). Phase 3's IR **adopts** this contract as
  its ID scheme — it must not redefine it, so committed sample runs from
  this phase remain valid post-IR.
- [ ] **1.3** Update `libretto.md` + `state/filesystem.md`: the VM MUST append a
  receipt after every statement completion; discretion evaluations
  (`**...**`) MUST record their outcome (this is the deterministic-replay
  primitive from ROADMAP P2). Define the minimal `emit_receipt` host
  primitive in `primitives/session.md` (append one canonical-JSON line to
  the run's `receipts.jsonl`, update `ledger_head`) so `libretto.md` never
  mandates behavior that isn't a named host capability. The full adapter
  contract still arrives in Phase 5; this is a forward-compatible stub.
- [ ] **1.4** Bootstrap `tools/` with `uv`; pydantic models mirroring
  `receipt.md`; `pyrefly init`.
- [ ] **1.5** Implement `libretto-tools inspect <run-dir> [--json]`:
  headless summary — dispositions (rendered/skipped/failed), token/cost
  rollup per statement and per agent (with `usage.basis` breakdown), failed
  statements, chain-consistency result. Deterministic reader over
  `receipts.jsonl` + `state.md`; no LLM.
- [ ] **1.6** Implement `libretto-tools verify <run-dir>`: schema
  validation + chain consistency + `ledger_head` anchor check; non-zero
  exit on breakage.
- [ ] **1.7** Run 2–3 small `.libretto` programs for real, commit their run dirs
  under `examples/runs/` as the keyless replay corpus (valid under the
  frozen `libretto.statement-id.v1`, so they survive Phase 3).
- [ ] **1.8** Re-point ROADMAP P2 `libretto inspect <run>`: the embodied skill
  command delegates to the deterministic tool when available, falls back to
  `lib/inspector.libretto` otherwise.

**Verification:** `uv run pytest` green; `libretto-tools inspect --json`
over each committed sample run produces stable output (byte-identical across
two invocations); `verify` passes on committed runs and fails on a
deliberately corrupted fixture.

---

## Phase 2 — Offline fixtures + CI (P0 from lessons doc)

Replaces "51 examples as implicit tests" with explicit, tiered, offline gates.
First CI this repo has ever had.

**Files:**
- Create: `tests/fixtures/` (invalid syntax, ambiguous wiring, missing state
  backend, malformed receipts, broken chain, non-compiling namespace cases)
- Create: `tools/src/libretto_tools/lint.py` (deterministic `.libretto` checks)
- Create: `.github/workflows/ci.yml`
- Modify: `CLAUDE.md`, `README.md` (validation story)

- [ ] **2.1** Extract the deterministically checkable subset of `compiler.md`
  into `libretto-tools lint <file.libretto>`: indentation consistency, known
  keyword set (all 6 registers via the alts keyword tables), balanced blocks,
  flat-namespace duplicate-`let` detection, `session`/`agent` reference
  resolution. *Explicitly documented as a linter, not the compiler — the LLM
  remains the semantic compiler.*
- [ ] **2.2** Build the fixture corpus: for each known failure class from the
  evaluation and lessons doc, a minimal `.libretto` (or corrupted run dir) +
  expected diagnostic. Separate `tests/fixtures/` (CI-only) from `examples/`
  (distributable, all must pass lint).
- [ ] **2.3** CI tiers in `.github/workflows/ci.yml`:
  - **required:** `ruff` + `pyrefly` + `pytest` on `tools/`; `lint` over all
    51 examples + stdlib; `verify` over committed sample runs.
  - **advisory (manual/secret-gated):** real model smoke run of one small
    example — never required for merge.
- [ ] **2.4** Update `CLAUDE.md` §Validation to describe the new story
  (lint + fixtures + receipts verify + implicit example suite).

**Verification:** CI green on the PR that introduces it; deliberately broken
fixture PRs fail the required tier.

---

## Phase 3 — Compile IR + `compile --check` (P1 from lessons doc)

Makes `libretto compile` produce a deterministic, content-addressed artifact —
the contract between the intelligent (LLM) compiler and deterministic tooling.

**Files:**
- Create: `contracts/ir.md` (`libretto.compile-ir.v1`)
- Modify: `compiler.md` (compile MUST emit the IR JSON), `SKILL.md` (routing)
- Create: `tools/src/libretto_tools/ir.py` (pydantic model + validator +
  staleness check)
- Create: fixtures for malformed IR in `tests/fixtures/`

**IR content (v1):** source files + content hashes; statement/block graph
with `statement_id`s per the **Phase 1 `libretto.statement-id.v1` contract**
(the IR adopts the existing scheme; it does not redefine it); declared agents
and their prompts' hashes;
sessions with wiring (`context:`, bindings in/out); state backend;
permissions/tools; retry/backoff/timeout properties; diagnostics.

- [ ] **3.1** Write `contracts/ir.md` with full field table and canonical
  JSON serialization rules (sorted keys, no floats for hashes).
- [ ] **3.2** Update `compiler.md`: `libretto compile <file>` writes
  `.libretto/dist/<program>.ir.json` (+ `manifest.active.json` pointer);
  IR is the source of `statement_id`s at run time.
- [ ] **3.3** Implement `libretto-tools ir-check <file.libretto>`: exit
  non-zero if IR missing or stale (source hash mismatch) or schema-invalid.
  Wire into CI required tier for `examples/` that ship committed IR.
- [ ] **3.4** `libretto run` (in `libretto.md`): if fresh IR exists, the VM MUST
  take statement IDs and wiring from it rather than re-deriving.

**Verification:** compile one example (embodied), `ir-check` passes; touch
the source, `ir-check` fails; malformed-IR fixtures rejected in CI.

---

## Phase 4 — Materiality, fingerprints, cost control (P1 from lessons doc)

Attacks the dominant economic fact (~46K token/session floor, ~51% overhead):
expensive LLM work must not run when nothing material changed.

**Files:** Modify `compiler.md` (grammar: `material:`, `budget:`),
`libretto.md` (skip semantics, budget enforcement), `contracts/receipt.md`
(skipped/surprise semantics already reserved in v1);
Modify `tools/` (`inspect` gains cost/skip analytics, `cost <run>` command).

- [ ] **4.1** Grammar: optional `material: [binding.field, ...]` on `session`;
  program-level `budget: $N` (ROADMAP P1) with VM halt-on-overage semantics
  driven by receipt usage rollup.
- [ ] **4.2** VM skip rule in `libretto.md`: before spawning a session, compare
  input fingerprints against the last receipt for the same `statement_id`
  (same run for `repeat` loops; previous run when re-running a program with
  `--resume`); if unmoved → `status: skipped`, binding reused, no spawn.
  **Reuse semantics are fixed, not VM discretion: copy the binding file into
  the new run dir**, and record provenance in the receipt
  (`reused_from: {run_id, statement_id, output_fingerprint}`). Run dirs stay
  self-contained (a committed/archived run never dangles a reference into
  another run); the fingerprint match is verifiable by `libretto-tools
  verify`. Reference-without-copy is rejected for v1 — it breaks the
  keyless-replay corpus and cross-machine reproducibility.
- [ ] **4.3** Fingerprint spec: sha256 over canonical binding content;
  facet = named sub-path of a binding for `material:` granularity. Document
  in `contracts/receipt.md`.
- [ ] **4.4** `libretto-tools cost <run-dir>`: rollup by statement, agent,
  model tier; % skipped; comparison across two runs of the same program.
- [ ] **4.5** Evaluation follow-up: re-run one Phase-2-style composition
  program twice with skip semantics; record measured savings in
  `evaluation/results/` addendum.
- [ ] **4.6** **Decision gate: Rust.** If fingerprint/chain verification is
  now needed by neighbor projects or is too slow in Python — write handoff/
  ADR for a shared Rust crate. Otherwise re-affirm Python-only.

**Verification:** second run of an unchanged program shows all sessions
`skipped` and near-zero model spend in `cost` output; budget overage halts a
run and the receipt trail shows why.

---

## Phase 5 — Host adapter contract + ecosystem integration

Formalizes portability (the repo's strength) and plugs receipts/IR into the
surrounding Python ecosystem as consumable contracts.

**Files:**
- Create: `contracts/adapters.md` — host-port interface: `spawn_session`,
  `read_state`/`write_state`, `copy_binding`, `check_env`, `run_shell`
  (timeout + sandbox metadata), `ask_user`, `emit_receipt`.
- Modify: `SKILL.md`, `libretto.md` — reference the port instead of hard-wiring
  Claude Code's Task tool; Claude Code mapping becomes *one adapter document*.
- Create: `contracts/adapters/claude-code.md` (current behavior, incl. the
  known hook-blocks-binding-writes degradation and its fallback).
- Create: handoff note (prograph-vault) proposing that atp-platform /
  proctor / arbiter consume `receipts.jsonl` + `ir.json` as evaluation
  inputs — *their* side of the integration is their decision.

- [ ] **5.1** Write `contracts/adapters.md` + extract the Claude Code mapping.
- [ ] **5.2** Add a security contract section (lessons §9): remote `use`/
  registry fetch, shell/tool permissions, state backends with credentials,
  agent-memory leakage; unsafe postures must be explicitly named.
- [ ] **5.3** Add `libretto doctor` to `SKILL.md` + `libretto-tools doctor`:
  keyless check of spec files present, state backend writable, expected host
  primitives available, IR freshness.
- [ ] **5.4** Ecosystem handoff note (see Files above).

**Verification:** `doctor` passes in this checkout; a second adapter doc
(e.g. Codex CLI) can be drafted purely against `adapters.md` without reading
`libretto.md` — dry-run this as a review exercise.

---

## Phase 6 — Responsibility v2 (`*.libretto.md`) — research track, gated

Optional, **only after Phases 1–4 are stable**, and only if the standing-work
model proves needed here (the ecosystem already has upstream `prose` for
production standing work — this repo's angle is research/portability).

- [ ] **6.1** ADR first: do we need responsibilities downstream, or is v1
  imperative `.libretto` + receipts the right scope for this repo? (Decision
  input: whether anything in the ecosystem wants standing jobs on a
  Python-verifiable substrate.)
- [ ] **6.2** If yes: additive `*.libretto.md` format (`kind: responsibility`,
  `### Goal/Maintains/Requires/Continuity`), old `.libretto` mapped to
  `function`/`### Execution`; terminology synchronized with upstream
  (`Maintains`, `Requires`, `Continuity`, `Receipt`, `World-model`).
- [ ] **6.3** `watch:`/gateway as external-driven wake (ROADMAP P3) lands
  here, not earlier — it only makes sense with standing responsibilities.

---

## Public surface restructure (rolls out across Phases 1–5)

Target layout (lessons §10), reached incrementally — each phase moves only
the files it touches:

```
SKILL.md                    — router (entry point, unchanged role)
libretto.md                    — VM execution (runtime spec)
compiler.md                 — language spec (normative)
contracts/receipt.md        — audit/replay contract        (Phase 1)
contracts/ir.md             — machine compile contract     (Phase 3)
contracts/adapters.md       — host mapping                 (Phase 5)
contracts/vendored/         — pinned upstream schemas      (Phase 1+)
tools/                      — Python verification package  (Phase 1+)
tests/fixtures/             — CI-only regression corpus    (Phase 2)
examples/                   — learning corpus (+ committed runs)
guidance/, lib/, state/, primitives/, alts/ — unchanged
```

## Sequencing & effort (rough)

| Phase | Depends on | Size | Risk |
|---|---|---|---|
| 0 Spec hygiene | — | S (days) | Low — pure spec edits |
| 1 Receipts + inspect | 0 | M (1–2 wk) | Stable statement IDs (mitigated by Phase 3 IR) |
| 2 Fixtures + CI | 1 | M | Linter scope creep — keep it a linter |
| 3 Compile IR | 1 | M | compiler.md is 83KB; edit surgically |
| 4 Materiality/cost | 1, 3 | M–L | Materiality model design; measure, don't assume |
| 5 Adapters + ecosystem | 1 | S–M | Don't over-abstract the port |
| 6 Responsibility v2 | 1–4 stable | L | Mental-model break; ADR-gated |

Phases 0→1→2 are the committed near-term path (they close every P0 item from
the lessons doc and every "For the Libretto project" recommendation from the
evaluation). Phases 3–5 are planned; Phase 6 is a gated research option.

## Self-review notes

- Every "For the Libretto project" recommendation from
  `evaluation/results/final-verdict.md` maps to a Phase 0 task (0.1–0.6).
- Every P0/P1 row of the lessons doc's priority table maps to Phases 1–5;
  P2 responsibilities → Phase 6; P3 full runtime → explicit Non-Goal.
- ROADMAP.md items covered: P1 budgets (4.1), concurrency (0.3), pause/cancel
  (spec fix 0.4; protocol itself stays in ROADMAP backlog), P2 replay (1.3),
  structured errors (receipts `error` field, 1.1), inspect (1.5/1.8),
  P3 watch (6.3), P4 observability (receipts are the event stream).
- Not covered on purpose: ROADMAP P3 type annotations, P4 registry
  governance, P5 research items — stay in ROADMAP.md backlog, untouched by
  this plan.
