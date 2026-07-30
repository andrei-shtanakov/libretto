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

- [ ] Rewrite the four P2.5 cases onto already-canonical syntax, verifying each warning class separately @owner:github:andrei-shtanakov @id:p25-rewrite-noncanonical-constructs
      Decision taken: the bundled programs are rewritten, the grammar is **not**
      grown. `libretto-tools lint` reports these today as exactly **8 OP009 warnings
      across 4 files**, which is the acceptance signal — the count must fall to 0 for
      the rewritten constructs, and lint must stay at 0 errors over all 60 programs.
      The four classes, to be handled and verified one at a time rather than in a
      single sweep, because each has a different canonical replacement:
      (1) `import "skill" from "source"` — 4 warnings, in
      `examples/11-skills-and-imports.libretto` and
      `examples/12-secure-agent-permissions.libretto`; the grammar's existing means
      are `use` for programs and the `skills:` agent property.
      (2) `return` — 2 warnings, at `examples/50-…:477` and `:503`; Phase 0 defined
      block-level `output` as the block-return form, which is the replacement.
      (3) `break` — 1 warning, at `examples/50-…:576`; no loop-control statement
      exists, so the loop has to be restructured rather than translated.
      (4) `assert <expr>:` — 1 warning, at `lib/profiler.libretto:194`.
      These files are documentation users have read, so each rewrite must keep the
      example's teaching intent, not merely silence the linter.
      Described in `ROADMAP.md` → P2.5.
