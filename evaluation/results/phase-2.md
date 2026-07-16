# Phase 2: Variables, Context, Composition — Results

## Environment

- **Date:** 2026-07-15
- **Claude model (VM):** claude-fable-5; sessions per program `model:` property (sonnet/opus), default = inherit
- **Platform:** macOS Darwin 25.5.0
- **Claude Code with libretto plugin (local marketplace)**
- **State backend:** filesystem (default)

## Built-in Examples

| Example | Sessions | Result | Fidelity notes |
|---------|----------|--------|----------------|
| `13-variables-and-context.libretto` | 7 | PASS | let/const bindings, `context: []` fresh start, `context: [a,b,c]` array form, and 3x variable reassignment (draft) all worked; reassignment overwrites `draft.md` in place |
| `14-composition-blocks.libretto` | 8 | PASS | 3 named blocks + anonymous `do:`; execution_ids 1-3 assigned; scoped bindings `anon_NNN__id.md` created correctly; review block found 4 real accuracy issues later fixed by the feedback session |
| `15-inline-sequences.libretto` | 12 | PASS | `->` chains executed sequentially with implicit context; `let x = chain` binds the final session's output; block + chain combination worked |

### Observations

- **Context wiring works in all four forms** (`var`, `[a, b, c]`, `{ a, b }`, `[]`). Subagents read exactly the referenced binding files; the `context: []` session produced independent research with no leakage from prior sessions.
- **Variable reassignment** (ex13, `draft` x3) is a genuine improvement chain: v2 fixed concrete precision issues from v1 (defined the error-suppression factor, named Shor's algorithm), v3 was a light polish. Overwrite-in-place loses intermediate versions — inspectability gap vs Phase 1's expectations.
- **Block scoping** (ex14): per-invocation `__execution_id` suffixes prevented collisions exactly as specified in `state/filesystem.md`.
- **Examples 14/15 are topic-free** — the programs contain no subject matter at all ("Gather information on the topic", "Analyze data", "Step 1"). The VM must invent a coherent domain via discretion. This makes them poor fidelity tests: two runs of the same program share almost nothing. Recorded VM discretion choices in each run's `state.md`.

## Custom .libretto Programs

| Program | Sessions | Result | Output quality (1-10) | Notes |
|---------|----------|--------|----------------------|-------|
| `atp-evaluator-refactoring.libretto` | 3 | PASS | 9 | Dependency chain survey→interface→refactoring; `context: { survey, interface }` passed both refs; survey session discovered the program's premise was wrong (evaluators live in `atp/evaluators/`, not `packages/atp-core/`) and adapted instead of failing |
| `atp-module-review.libretto` | 7 | PASS | 9 | Block invoked 3x with different args; bindings correctly scoped per invocation (`analysis__1..3`, `result__1..3`); reviewers ran actual pytest+coverage (measured 88%/82%, found 22 real failing tests in atp-core); final summary synthesized strong cross-cutting concerns |

### Key check results (from the plan)

- **Does each binding contain substantive content?** Yes — survey/interface/refactoring are all substantive and build on each other.
- **Does `context: { survey, interface }` actually pass both?** Yes — the refactoring session referenced both files.
- **Does the block execute 3 times with different arguments?** Yes.
- **Are bindings scoped per invocation (`result__<execution_id>.md`)?** Yes — 6 scoped bindings across 3 frames, no collisions.

## Baseline Comparison

| Task | .libretto quality | Baseline quality | .libretto cost | Baseline cost | .libretto tool calls / wall | Baseline tool calls / wall | Winner |
|------|---------------|-----------------|-------------|---------------|--------------------------|---------------------------|--------|
| Evaluator Refactoring | 9/10 | 9/10 | 314K tok (3 sessions) | 170K tok (1 session) | 30 / ~228s | 33 / 217s | Baseline on cost; tie on quality |
| Module Review (x3) | 9/10 | 8/10 | 462K tok (7 sessions) | 72K tok (1 session) | 84 / ~530s | 7 / 232s | .libretto on depth; baseline on cost (6.4x cheaper) |

### Analysis

- **The token-overhead picture inverted vs Phase 1.** Phase 1 measured ~5-10% overhead; Phase 2's composition patterns cost **1.8x-6.4x** the baseline. Cause: every session re-loads codebase context from scratch. The 3-session dependency chain read atp-platform 3 times (188K + 66K + 60K); the baseline read it once (170K). The effect compounds with session count — exactly the "46K fixed floor per session" that example 15's self-analysis session independently derived from run-13 metrics.
- **But .libretto bought measurably deeper evidence in the review task.** The .libretto reviewers *ran the test suites with coverage* (measured 88%/82%, found 22 real failing tests, per-file coverage numbers); the single-session baseline rated coverage by reading test files (estimated, and diverged: rated atp-adapters coverage 9/10 where measurement showed 82% with a 0%-covered tracing wrapper). Separate focused sessions went deeper per package; the monolithic baseline economized by skimming.
- **Both approaches caught the wrong premise** ("evaluators in atp-core") and corrected it — this robustness is model-level, not orchestration-level.
- **Inspectability difference is unchanged from Phase 1:** .libretto runs left full audit trails (state.md + 26 binding files across 5 runs); baselines left only their final message.
- **Baseline contamination note:** the plain-prompt baseline agent saw the session task list and referenced the completed .libretto runs — plain sessions inherit ambient conversation context, .libretto sessions are cleanly isolated. An underappreciated .libretto benefit for reproducible evaluation.

## Token Cost Summary

| Run | Program | Sessions | Total tokens | Wall time |
|-----|---------|----------|-------------|-----------|
| 1 | 13-variables-and-context | 7 | 360.6K | ~8.9 min |
| 2 | 14-composition-blocks | 8 | 403.7K | ~9.0 min |
| 3 | 15-inline-sequences | 12 | 572.0K | ~10.5 min |
| 4 | atp-evaluator-refactoring | 3 | 314.3K | ~3.8 min |
| 5 | atp-module-review | 7 | 462.1K | ~8.8 min |
| B1 | baseline evaluator refactoring | 1 | 170.1K | 3.6 min |
| B2 | baseline module review | 1 | 72.4K | 3.9 min |

## Key Findings

1. **Variables, context forms, reassignment, blocks, parameters, and scoped bindings all work as specified.** Phase 2's core language features are fully functional on the filesystem backend.
2. **Session count is the dominant cost driver** (~46K token floor per session). Composition patterns multiply sessions; authors should merge steps that don't need isolation. This matches ROADMAP P1's cost-budget motivation.
3. **Multi-session decomposition trades cost for depth and auditability** — the .libretto module review produced measured (not estimated) coverage data and 26 inspectable artifacts for 6.4x the tokens.
4. **Spec gaps found:**
   - `let x = do block` has no defined return semantics in `libretto.md` (VM aliased x to the block's last session binding).
   - `context: { result }` at root scope, where `result` only exists as scoped bindings in 3 completed frames, is unresolvable by the spec's scope-resolution rules; VM passed all three frames' results (which was clearly the program's intent).
   - Variable reassignment semantics for binding files (overwrite vs version) are unspecified; overwrite loses audit trail.
5. **Substrate interference is real:** a Claude Code hook intermittently blocked subagents' binding writes ("return findings as text"); the VM fell back to persisting bindings from returned text (4 of 7 bindings in run 5). Violates the "VM never holds full values" invariant — the RLM-style pass-by-reference design degrades when the substrate polices subagent file writes.
6. **Resilience:** one session aborted mid-run on a substrate session limit; filesystem state made retry trivial (binding absent → re-spawn was idempotent). First real validation of the resumption story.

## Issues / Surprises

1. **Examples 14 and 15 are under-specified as tests** — no topics/agents, so the VM invents the domain. Suggest examples carry concrete micro-topics.
2. **The `.libretto` premise error** (evaluators claimed to be in packages/atp-core) was silently absorbed by capable subagents — good for robustness, but a program author would not learn their spec is wrong unless they read the bindings. Structured error/warning reporting (ROADMAP P2) would surface this.
3. **Example 15's data-analysis chain analyzed this very evaluation's run-13 metrics** (VM discretion choice) and derived the same cost model this report reaches — a neat self-referential validation.
4. **Anonymous binding numbering across mixed root/block scopes** is easy to get wrong; the `anon_NNN` counter resets per scope in our runs (anon_001__1 vs anon_001) — spec silent on whether the counter is global or per-scope.

## Conclusion

Phase 2 passes. Variables, context passing (all forms), composition blocks with parameters and per-invocation scoping, inline `->` sequences, and `output` bindings all execute correctly. The headline learning is economic, not functional: composition multiplies sessions, and each session carries a ~46K-token floor, so .libretto programs should reserve multi-session decomposition for tasks that need isolation, depth, or auditability — where they demonstrably outperform single-prompt baselines.

**Ready for Phase 3: Parallelism.**

## Files

- `evaluation/phase2/atp-evaluator-refactoring.libretto` — custom program
- `evaluation/phase2/atp-module-review.libretto` — custom program
- `evaluation/phase2/baseline-prompts.md` — baseline prompts
- `evaluation/phase2/baseline-evaluator-refactoring.md` — baseline 1 output + cost
- `evaluation/phase2/baseline-module-review.md` — baseline 2 output + cost
- `evaluation/results/phase-2.md` — this report
- `.libretto/runs/20260715-081601-307884/` — example 13 run (gitignored, local)
- `.libretto/runs/20260715-082705-e93674/` — example 14 run
- `.libretto/runs/20260715-083736-72d299/` — example 15 run
- `.libretto/runs/20260715-085306-23faa8/` — atp-evaluator-refactoring run
- `.libretto/runs/20260715-085800-a07346/` — atp-module-review run
