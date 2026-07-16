# OpenProse Roadmap

## P0 — Infrastructure (quick wins)

- [x] Root README.md
- [x] Fix example numbering collisions (51 unique files)
- [x] Synchronize documentation counters

## P1 — Runtime Reliability

- **Cost budgets** — `budget: $5.00` at program level. VM tracks spend via token counting and halts on overage. Add property to grammar (`compiler.md`) + enforcement logic in VM (`prose.md`)
- **Concurrency limits** — `parallel (max_concurrent: N):` for rate limiting. Currently parallel launches all branches simultaneously without limits
- **Pause/cancel protocol** — standardize substrate interaction for graceful stop. Format: marker in `state.md` + VM check before each session spawn

## P2 — Developer Experience

- **Deterministic replay** — save all discretion evaluations (`**...**`) and their outcomes in state. On replay, substitute saved decisions instead of re-evaluating.
  *Recording half done (Phase 1, 2026-07-16): every discretion emits a receipt with condition/outcome/branch (`contracts/receipt.md`). Remaining: a VM replay mode that substitutes recorded outcomes.*
- **Structured error reporting** — on runtime failure emit: statement, line context, agent state, retry count. Currently errors depend on substrate.
  *Partially done (Phase 1): failed statements emit receipts with `error.type/message/retry_count`. Remaining: line context + agent state capture.*
- [x] **`prose inspect <run>`** — done (Phase 1, 2026-07-16): deterministic `openprose-tools inspect|verify` over the receipt ledger; `lib/inspector.prose` remains the no-tooling fallback

## P2.5 — Spec decisions surfaced by the linter (2026-07-16)

Bundled programs use four constructs absent from `compiler.md` (reported
as OP009 warnings by `openprose-tools lint`). Each needs a decision —
adopt into the grammar or rewrite the programs:

- **`import "skill" from "source"`** — examples 11, 12 (skill imports;
  grammar only has `use` for programs and the `skills:` agent property)
- **`return`** — example 50 (early exit at root scope / inside blocks;
  overlaps with the Phase 0 `output`-as-block-return semantics)
- **`break`** — example 50 (loop exit; no loop-control statements exist)
- **`assert <expr>:`** — lib/profiler (guard with error message)

## P3 — Language Extensions

- **Type annotations for bindings** — optional typing: `let research: ResearchReport = session "..."`. Compile-time validation via `compiler.md`
- **`timeout:` property** — native timeout for sessions (`timeout: 60s`). Currently no way to limit subagent execution time
- **`watch:` event blocks** — react to external events (filesystem, webhooks). New primitive for event-driven workflows

## P4 — Ecosystem

- **Registry governance** — p.prose.md: program versioning, SLA, namespacing, discovery. Currently no versions — `use "alice/research"` always fetches latest
- **Stdlib expansion** — add: test runner (run .prose as tests), deploy helper, notification integrations
- **Pluggable observability** — observer pattern: backends Noop/Log/File/Webhook. VM emits events, observer processes them

## P5 — Research

- **Syntax register benchmarking** — formal A/B testing of 6 syntax registers (functional, Borges, Folk, etc.) on learnability and memorability
- **Multi-VM coordination** — protocol for multiple VMs working in parallel on a single task (distributed execution)
- **Formal verification** — can .prose programs be proven correct? Identify a subset of the language amenable to formal verification
