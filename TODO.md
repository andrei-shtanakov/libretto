# TODO — libretto (opened 2026-07-30)

> Role in the ecosystem: **specification-as-VM** — a language for AI sessions whose
> runtime is an LLM reading `libretto.md`, plus a thin deterministic tooling layer
> (`libretto-tools lint|verify|inspect|cost|ir-check|doctor`) that checks the
> machine-readable artifacts a run must emit. Project overview: `README.md` and
> `CLAUDE.md`.
>
> **This file is the operational SSOT** — accepted commitments only, and it is
> deliberately short. The strategic backlog lives in `ROADMAP.md`; its bullets are
> candidates, not commitments, and are not tracked here until accepted.
> `docs/plans/2026-07-16-development-plan.md` is a finished execution record of a
> completed programme, not current state — see the banner at its head.
>
> The three items below were accepted by the owner on 2026-07-30 after an audit of
> both planning documents. Everything else either shipped or stays a candidate.

## Conventions

- Completed item — `[x]` plus the PR number / commit hash.
- Item no longer relevant — `~~strike it through~~` with the reason; **do not delete
  the line**: delta counters read a vanished line as "closed".
- Item fields are inline tags `@owner:` / `@blocked_by:<repo>#<slug>` /
  `@trigger:"…"`, all optional: an empty field means "unknown", which is measurable
  and more honest than an invented value.
- `@id:<node-id>` — the item's canonical identifier (ADR-ECO-005 PF-2B): lowercase
  grammar `[a-z0-9][a-z0-9._-]{0,63}`, from which the URI `todo://libretto/<id>` is
  built.
- **Tags and the substance of an item go on the same line as `- [ ]`**: the parser
  reads items strictly line by line and does not see continuation lines below.
  Indented lines under an item are context for humans.
- A change in a neighbouring repo is never planned here as our own work — a
  cross-repo item is a **handoff** (see `CLAUDE.md`, repo scope & boundaries).

---

## Runtime semantics

- [ ] Finish deterministic replay: a VM replay mode that substitutes recorded discretion outcomes instead of re-evaluating them @owner:github:andrei-shtanakov @id:deterministic-replay-vm-mode
      The recording half shipped in Phase 1: every discretion (`**...**`) emits a
      receipt carrying its condition, outcome and taken branch (`contracts/receipt.md`,
      `discretion` kind; `libretto.md` → Receipts). What does not exist is the
      consuming half — a mode in which the VM reads those receipts back and replays
      the recorded decision rather than asking the model again. Until it exists, a
      re-run of the same program can legitimately take a different branch, so the
      committed run corpus is reproducible only in its ledger, not in its control
      flow. Scope includes: where the mode is declared (`libretto.md`), how a replay
      receipt is distinguished from a fresh one, and what happens when the program
      has drifted from the recorded run (the `--resume` freshness comparison already
      answers a related question and should not be re-answered differently).
      Described in `ROADMAP.md` → P2, "Deterministic replay".

- [ ] Add line context and agent state to structured errors @owner:github:andrei-shtanakov @id:error-line-context-agent-state
      The receipt `error` object shipped in Phase 1 with `type` / `message` /
      `retry_count` (`contracts/receipt.md`). Line context and agent-state capture do
      not exist, so a failure receipt today says what went wrong but not where in the
      program, nor what the failing agent was holding. Both additions touch
      `contracts/receipt.md` (new fields, and whether they are required or optional)
      before they touch the VM spec. The statement ID already resolves to a statement;
      line context is the human-facing complement to it, not a replacement.
      Described in `ROADMAP.md` → P2, "Structured error reporting".

## Spec decisions surfaced by the linter (P2.5)

- [x] Rewrite the four P2.5 cases onto already-canonical syntax, verifying each warning class separately (#24) @owner:github:andrei-shtanakov @id:p25-rewrite-noncanonical-constructs
      Decision taken and executed: the bundled programs were rewritten, the grammar
      was **not** grown — `compiler.md` and `libretto.md` are untouched. All four
      classes landed; lint over the CI scope went from 8 OP009 warnings to **0, with
      0 errors over all 60 programs**, and each class was counted separately before
      and after rather than in a single sweep. What each became:
      (1) `import "skill" from "source"` — 4 warnings → `use "@handle/slug"` plus the
      existing `skills:` agent property, in
      `skills/libretto/examples/11-skills-and-imports.libretto` (3) and
      `skills/libretto/examples/12-secure-agent-permissions.libretto` (1). Each slug
      equals the old skill name, so the `skills: [...]` arrays are unchanged. One
      teaching was lost and is *not* recovered by this item: `use` resolves only
      `@handle/slug` from `p.libretto.md`, so the old example's three source schemes
      (`github:`, `npm:`, a relative path) are now three publisher handles. Whether
      the registry should express non-registry sources is a separate spec decision,
      unopened.
      (2) `return` — 2 warnings → `output <expr>`, the documented block return, in
      `skills/libretto/examples/50-run-endpoint-ux-test-with-remediation.libretto`.
      The `output name = expr` line each `return` followed is the root-scope-only,
      register-only form (an E029 in a block body) and never returned, so the pair
      collapsed into one statement; the block's final return was converted with them.
      (3) `break` — 1 warning → the loop restructured so its `until` condition
      carries the exit: verify once ahead of the loop, then refine and re-verify per
      iteration. Same exit signal, now named concretely
      (`**verification.diagnosis_sound is true**`), same bound of 3 refinements; in
      the never-sound path it spends one extra verification and, unlike the original,
      verifies the final diagnosis.
      (4) `assert <expr>:` — 1 warning → `if **...**:` + `throw` at
      `skills/libretto/lib/profiler.libretto`, with the condition inverted, since
      `assert` states what must hold and a guard states what must not.
      Described in `ROADMAP.md` → P2.5.

- [ ] Audit the nine block-body `output NAME = expr` sites against the grammar's root-scope-only rule, before any spec decision @owner:github:andrei-shtanakov @id:output-scope-audit
      `compiler.md:3130-3131` and `libretto.md:490-491` both state
      `outputBinding → "output" IDENTIFIER "=" expression` is root-scope-only and
      `outputReturn → "output" expression` is for block bodies only. Nine sites in
      the shipped corpus use the root-scope form inside block bodies, unflagged by
      `libretto-tools lint` (it checks keyword canonicality, not `output`'s scope
      placement):
      `skills/libretto/examples/44-run-endpoint-ux-test.libretto:102,139,186` and
      `skills/libretto/examples/50-run-endpoint-ux-test-with-remediation.libretto:274,303,365,380,434,453`.
      The P2.5 rewrite (#24, above) converted three sites paired with a
      non-canonical `return` into the canonical block return, leaving the corpus
      internally inconsistent — three sites now use the block return, nine still
      use the named form inside blocks — this is the "adjacent gap" `ROADMAP.md` →
      P2.5 flags but does not resolve. This item is the audit only, not the fix:
      establish, per site, (1) the author's intended semantics, (2) the
      compiler's actual behaviour per spec (the runtime is an LLM reading
      `libretto.md`, so this means what the specs prescribe and what a
      conforming run would produce), and (3) whether an equivalent root-scope
      formulation exists. The audit's output feeds a later spec decision;
      neither the grammar nor the programs change here.
