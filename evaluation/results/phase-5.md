# Phase 5: Captain's Chair + RLM — Results

## Environment

- **Date:** 2026-07-15
- **Claude model (VM):** claude-fable-5; sessions per program `model:` (opus/sonnet), default = inherit
- **Platform:** macOS Darwin 25.5.0
- **Claude Code with open-prose plugin (local marketplace)**
- **State backend:** filesystem (default)
- **VM policy (new this phase):** every leaf session carries an explicit "do the work yourself — no sub-agents/skills/workflows" constraint, after three nested-orchestration breakouts in earlier phases

## Built-in Examples

| Example | Sessions | Ran successfully? | Fidelity notes |
|---------|----------|-------------------|----------------|
| `30-captains-chair-simple.prose` | 5 (+1 retry) | yes | input bound from caller; captain planned first (no code); executor+critic parallel; discretion TRUE → integrate branch |
| `40-rlm-self-refine.prose` | 6 | yes | 3 recursive frames (execution_id 1→2→3), scores 58→64→93, terminated on score gate (93 ≥ 85) with depth budget left |

### Captain's Chair (example 30)

- **Does captain plan before executor acts?** Yes — plan.md written first, captain produced only work items.
- **Does critic actually find issues?** Yes — 4 major (stale test-count anchor 301 vs 417 actual files, 82 unowned test files outside `tests/`, an "inspect-don't-run" rule banning safe `--collect-only`, no synthesis output contract), and it verified the plan's repo-layout assumptions itself.
- **Recurring breakout, 3rd occurrence:** the executor's first attempt spawned its OWN "wave-1 specialist" teammates and returned "waiting for them". The VM detected the missing binding and retried with the no-delegation constraint; the retry did the work itself (417 test files / ~7,088 test functions catalogued). **The captain's-chair prompt style ("dispatch to specialists") primes leaf sessions toward delegation — role language leaks.** Orphaned teammates from the aborted attempt kept reporting idle into the session afterwards.

### RLM self-refine (example 40)

- **Does the recursive block recurse?** Yes — 3 frames with per-frame scoped bindings (`eval__N`, `improved__N`), depth decremented 5→4→3.
- **Does it terminate correctly?** Yes — on the score gate (93 ≥ 85), not depth exhaustion.
- **Did quality improve?** Monotonically: 58 → 64 → 93, with each evaluator running fresh-eyes against the real codebase. Iteration 2 rose only 6 points because the fresh evaluator found a NEW major gap (root package missing) the first evaluator hadn't flagged — evidence the evaluations are independent, not echoes.

## Custom .prose Programs

| Program | Sessions | Ran successfully? | Output quality (1-10) | Notes |
|---------|----------|-------------------|----------------------|-------|
| `atp-docstring-evaluator.prose` | 8 | yes | 9 | Full 5-phase Captain's Chair; **critic executed the proposed code live against real atp models and proved a real critical bug** (empty/whitespace docstrings counted as documented); conditional fix branch fired; regression-tested |
| `atp-architecture-doc.prose` | 2 | yes | 9 | RLM refine(draft, 3): the grounded opus draft scored **85 on the first evaluation** — gate (≥80) fired immediately, **zero refine iterations** |

### Captain's Chair checks (from the plan)

- **Captain stays coordinator?** Yes — both captain sessions (plan, summary) produced zero code.
- **Researchers find actual patterns?** Yes — corrected the wrong-path premise (evaluators live in `atp/evaluators/`, not `packages/atp-core/`), catalogued 11 evaluators + 30 test files with file:line cites.
- **Parallel research concurrent?** Yes.
- **Review meaningful?** Emphatically — the critic went beyond static reading and ran the implementation, proving the bug empirically. Highest-value review of the whole evaluation.
- **Conditional revision works?** Yes — discretion TRUE → fixer → `final_code` reassigned (declare-once + reassign; the roadmap's dual `let final_code` violates the flat-namespace rule, same class of bug Copilot caught in Phase 4).

## Baseline Comparison

| Task | .prose quality | Baseline quality | .prose cost | Baseline cost | Winner |
|------|---------------|-----------------|-------------|---------------|--------|
| Docstring evaluator | 9/10 | 9/10 | ~717K tok / 8 sessions | 158K tok / 1 session | Quality tie; baseline 4.5x cheaper |
| Architecture doc | 9/10 (evaluator score **85**) | 9/10 (same evaluator, same rubric: **87**) | ~146K / 2 sessions | 87K / 1 session | Effective tie (87 vs 85); baseline cheaper |

### Analysis — do the two flagship patterns beat plain prompts?

**Captain's Chair vs plain (docstring evaluator): quality tie, different verification mechanisms.**
The baseline single session was unexpectedly strong: it didn't just self-grade — it **executed its own 21 tests against the real atp-platform `.venv`** via a `sys.modules` shim, iterating until green. When correctness is machine-checkable (code + tests), a single session with an execution oracle reaches verification quality comparable to an independent critic. The Captain's Chair's distinctive win was *semantic*: its critic **thought of** the empty-docstring edge case and proved it live; the baseline **prevented** the same class of issue by a design choice (`min_docstring_length`). One caught the bug, the other didn't write it. What the pattern demonstrably bought: role isolation kept every phase honest (captain wrote no code), the audit trail is complete, and the review was adversarial rather than incidental — at 4.5x the cost.

**RLM self-refine vs single-shot (architecture doc): the loop adds nothing when the seed is strong.**
Scored by the *same evaluator with the same rubric*: single-shot baseline 87, RLM final 85. Both docs are accurate and grounded; the differences are noise around the threshold. Combined with example 40 (poor seed: 58 → 93 in two passes), the phase's cleanest finding emerges: **RLM refinement pays off proportionally to seed weakness.** With a strong model reading real code, the evaluator gate acts as a ~1-session quality *certificate*, not a driver; with a weak seed, the same loop does real work. Authors should spend tokens on grounding the draft, not on refinement rounds, unless the seed is known-weak or the threshold is strict (≥90).

**Both patterns' costs are dominated by session count**, consistent with Phases 2–4: Captain's Chair (8 sessions) is the most expensive shape tested, and its benefit concentrates in the adversarial review session — which suggests a cheaper hybrid (single builder + one independent critic) captures most of the value at ~2 sessions. That hybrid is essentially what Phase 4's iterative-refactor was.

## Token Cost Summary

| Run | Program | Sessions | Total tokens | Wall time |
|-----|---------|----------|-------------|-----------|
| 1 | 30-captains-chair-simple | 5+1 retry | ~302K | ~11 min |
| 2 | 40-rlm-self-refine | 6 | ~323K | ~6 min |
| 3 | atp-docstring-evaluator | 8 | ~717K | ~19 min |
| 4 | atp-architecture-doc | 2 | ~146K | ~6 min |
| B1 | baseline docstring evaluator | 1 | 158K | 11 min |
| B2 | baseline architecture doc | 1 | 87K | 3.7 min |
| — | post-hoc scoring of B2 (same rubric) | 1 | 64K | 1.5 min |

## Key Findings

1. **Both flagship patterns execute faithfully**: Captain's Chair role separation held (captain wrote zero code in 4 captain-sessions across 2 runs), and RLM recursion ran real frames with scoped bindings, correct depth decrement, and correct termination on both exit conditions (score gate; and, in ex40's counterfactual, depth budget remained unused).
2. **The adversarial critic is the single most valuable session shape observed in the entire evaluation**: it live-executed proposed code against real models and empirically proved a critical bug (empty docstrings pass). This generalizes Phase 4's verifier≠author finding — the critic's value comes from independence *plus* execution grounding.
3. **RLM refinement value is inversely proportional to seed quality** (58→93 for a rough seed; 85 vs 87 tie for a grounded seed). The evaluator gate is cheap quality certification either way.
4. **Nested-orchestration breakout is now a confirmed pattern (3 occurrences)** — and this phase showed its cause more precisely: coordination-flavored role prompts ("dispatch to specialists") prime leaf sessions to delegate. Mitigation that worked: an explicit no-delegation constraint in every leaf prompt (zero breakouts in the 2 custom runs after adopting it). Side effect observed: teammates orphaned by an aborted breakout kept emitting idle notifications into the parent session afterwards.
5. **Two roadmap-program bugs found by review/compile-thinking, not execution**: the dual `let final_code` (flat-namespace violation, fixed as declare-once+reassign) — the same class Copilot flagged in Phase 4. The roadmap's example programs would not compile under compiler.md's own rules; `prose compile` on plan-embedded programs would have caught both.
6. **output-as-return inside blocks is load-bearing for the whole RLM family** (examples 40-43 and the roadmap's refine block) yet contradicts the register-only semantics Phase 4 established at top level. This is now the evaluation's most consequential spec gap — compiler.md needs an explicit rule (e.g. "inside a block, `output` registers AND returns").

## Issues / Surprises

1. **The baseline docstring evaluator self-validated with real execution** — building a `sys.modules` shim to run 21 tests against the live `.venv` without touching the read-only repo. Single plain sessions are more capable of rigorous self-verification than the Phase 4 comparison suggested, *when the task has an execution oracle*.
2. **Session-limit interruption handled cleanly again**: both baseline agents died mid-flight on a substrate session limit; filesystem state made re-dispatch trivial (no bindings written → idempotent retry), same as Phase 2.
3. **The RLM run terminating in zero iterations is a feature, not an anticlimax** — it demonstrates the gate correctly measures "good enough" rather than always burning the depth budget. But it also means threshold choice (80 vs 85 vs 90) is the real control knob, and the spec gives authors no guidance on calibrating it.
4. **Captain's Chair produced a genuinely PR-ready artifact** for atp-platform (implementation + registry wiring + regression-tested fix + 10-class test suite + integration summary referencing the handoff convention). Integration remains a cross-repo decision for the atp-platform owner.

## Conclusion

Phase 5 passes. Both flagship orchestration patterns run with full fidelity, and the evaluation's sharpest cost/benefit picture yet emerges: the Captain's Chair's value concentrates in one session — the independent, execution-grounded critic — while its remaining ceremony (5 roles, 8 sessions) mostly buys auditability; RLM self-refine is a quality *certificate* for strong seeds and a quality *driver* only for weak ones. Plain single sessions with execution oracles are stronger than expected. The pragmatic guidance for .prose authors: default to builder + adversarial critic (2 sessions), escalate to full Captain's Chair when auditability or multi-specialist context isolation genuinely matters, and gate documents with one evaluator pass rather than pre-committing to refinement rounds.

**Ready for Phase 6: Alternative Syntaxes.**

## Files

- `evaluation/phase5/atp-docstring-evaluator.prose` — custom program (Captain's Chair)
- `evaluation/phase5/atp-architecture-doc.prose` — custom program (RLM self-refine)
- `evaluation/phase5/baseline-prompts.md` — baseline prompts
- `evaluation/phase5/baseline-docstring-evaluator.md` — baseline 1 record
- `evaluation/phase5/baseline-architecture-doc.md` — baseline 2 output (+ post-hoc score 87)
- `evaluation/results/phase-5.md` — this report
- `.prose/runs/20260715-142448-da8425/` — example 30 run (gitignored, local only)
- `.prose/runs/20260715-143524-bf7cf8/` — example 40 run (gitignored, local only)
- `.prose/runs/20260715-144402-64bf89/` — atp-docstring-evaluator run (gitignored, local only)
- `.prose/runs/20260715-150535-0b6c17/` — atp-architecture-doc run (gitignored, local only)
