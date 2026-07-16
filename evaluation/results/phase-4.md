# Phase 4: Control Flow — Results

## Environment

- **Date:** 2026-07-15
- **Claude model (VM):** claude-fable-5; sessions per program `model:` (sonnet / haiku), default = inherit
- **Platform:** macOS Darwin 25.5.0
- **Claude Code with libretto plugin (local marketplace)**
- **State backend:** filesystem (default)

## Built-in Examples

| Example | Sessions | Ran successfully? | Fidelity notes |
|---------|----------|-------------------|----------------|
| `20-fixed-loops.libretto` | 11 | yes | `repeat 3` → exactly 3 sessions; `for feature in [...]` → 3 iterations with binding; `parallel for topic in [...]` → 3 concurrent (+1 VM retry after a branch spontaneously launched a nested workflow); synthesis joined all |
| `22-error-handling.libretto` | ~15 | yes | All of try/catch, catch-as-err, try/finally on success, nested re-raise (`throw`), parallel try/catch, and top-level unhandled throw verified (see table below) |
| `25-conditionals.libretto` | 9 | yes (representative subset) | 3 of 8 discretion forms run (multi-branch, multi-line AND, discretion-over-parallel); every VM branch choice correct. Subset declared in the run's state.md, not silent |

### Loops (example 20)

- `repeat 3` produced **exactly 3** sessions. `for-each` bound the loop variable correctly each of 3 iterations. `parallel for` fanned out 3 concurrent branches.
- **Finding:** stateless loop bodies produce near-identical outputs unless differentiated — the VM added "produce a DIFFERENT idea" nudges on `repeat` iterations 2-3 (spec-silent, but necessary; loop-iteration context is the VM's responsibility).
- **Finding (unplanned):** one `parallel for` branch spontaneously invoked a deep-research *workflow* and returned "waiting for the workflow to complete" — a non-result. The VM detected the malformed return and re-ran the branch with an explicit "do NOT invoke skills/workflows/sub-agents" constraint. **Subagents can trigger nested orchestration on their own; the VM needs return-shape validation + retry.**

### Error handling (example 22) — all constructs verified

| Block | Construct | Forced outcome | Verdict |
|-------|-----------|----------------|---------|
| 1 | `try(FAIL)→catch` | API try failed (nonexistent file) | ✅ catch ran (1 retry — first catch subagent gave a non-result) |
| 2 | `try(FAIL)→catch as err` | config try failed | ✅ err detail passed into handler |
| 3 | `try(SUCCEED)→finally` | DB try succeeded | ✅ **finally ran on the SUCCESS path** (no catch) |
| 4 | nested `try{try(FAIL)→catch→throw}→catch` | inner op failed | ✅ inner catch re-raised; **outer** catch handled |
| 5 | `parallel{ try(FAIL)→fallback ; try(SUCCEED) }` | A failed, B ok | ✅ A's fallback ran; continue merged both |
| 6 | top-level `throw` (unhandled) | no enclosing try | ✅ program terminates per spec |

### Conditionals (example 25) — discretion evaluation

| Form | Setup state | VM branch | Correct? |
|------|-------------|-----------|----------|
| `if/elif/elif/else` | milestone 2/5 done, 1 blocked, behind pace | elif "slightly delayed" | ✅ |
| multi-line `all pass AND cov>80% AND no lint` | 214 pass, 76% cov, 2 lint warnings | **FALSE → else** (2 of 3 clauses fail) | ✅ |
| discretion over `parallel` results | security=HIGH, perf/style ok | "fix security" (first branch) | ✅ |

- **Discretion uses genuine LLM judgment and picks correctly** across single multi-branch, compound multi-line AND, and priority-ordered parallel conditions.
- **Subagent character-break finding:** given a *simulated* scenario, several branch subagents used their filesystem tools to investigate the REAL workspace instead of role-playing (one refused: "this project has no tests, which project do you mean?"). The VM's branch **selection** was correct every time; only leaf-session **content** wandered. A subagent with tools will not reliably stay inside a hypothetical — discretion/control-flow fidelity is robust, but leaf outputs need scenario isolation or real targets.

## Custom .libretto Programs

| Program | Sessions | Ran successfully? | Output quality (1-10) | Notes |
|---------|----------|-------------------|----------------------|-------|
| `atp-iterative-refactor.libretto` | 6 | yes | 9 | `repeat 2` + `try/catch` + `if **verification found problems**`; iter 1: fix→verify **found a real regression**→re-detect; iter 2: safer fix→verify **SAFE**→`output result`. Self-correcting loop worked on real code (proposal-only, atp-platform read-only) |
| `atp-conditional-pipeline.libretto` | 2 | yes | 9 | analyst measured **88%** via real `pytest --cov`; `if <60%`/`elif 60-80%` both FALSE → `else` branch. Discretion matched measured reality (and matched Phase 2/3's 88%) |

### Iterative-refactor control-flow checks (from the plan)

- **Does `repeat 2` run 2 iterations?** Yes.
- **Does `if **verification found problems**` make a reasonable call?** Yes — TRUE on iter 1 (independent tester found an untested regression in the first fix), FALSE on iter 2 (revised fix verified safe). Opposite outcomes on real evidence.
- **Does `try/catch` activate if a subagent fails?** The try succeeded both iterations (fixer/tester didn't error), so catch wasn't entered here — separately verified in example 22.
- **Does the loop terminate early when `output result = fix` is reached?** **No — and there is no spec basis for early exit.** `output result` only registers the output; it does not break `repeat`. Here iter 2 was the last iteration anyway. A program needing stop-on-success must use `loop until **...**`, not `repeat N`. (Candidate note for compiler.md.)

## Baseline Comparison

| Task | .libretto quality | Baseline quality | .libretto cost | Baseline cost | Winner |
|------|---------------|-----------------|-------------|---------------|--------|
| Iterative refactor | 9/10 | 9/10 | ~449K tok / 6 sessions | 105K tok / 1 session | **Reliability: .libretto** (independent verify caught a regression); cost: baseline (4.3x cheaper) |
| Conditional pipeline | 9/10 | 9/10 | ~138K tok / 2 sessions | 92K tok / 1 session | Tie — both measured 88% and took the correct `else` branch |

### Analysis — does formal control flow add reliability over natural language?

**This is the central Phase 4 question, and the answer is: it depends on the construct.**

- **Conditionals: no measurable reliability gain.** Both the `if/elif/else` .libretto and the NL "if below 60%… if 60-80%…" baseline resolved to the *same* branch (>80% → quality) because both grounded the decision in a real `pytest --cov` run. When the setup produces real data, natural-language branching is just as reliable as formal discretion. Formal `if/elif/else` buys inspectability (the branch decision is a recorded state transition) but not correctness here.

- **Iterative refactor: formal control flow DID add reliability — via session separation, not syntax.** The decisive difference wasn't `repeat`/`try`/`if` vs. NL loop instructions; it was that .libretto runs the fixer and the verifier as **separate sessions with independent context**. The .libretto tester (fresh perspective) caught a real regression the first fix introduced, triggering the retry. The baseline's single agent verified *its own* fix — a non-adversarial check that passed only because its fix happened to be safe. **The reliability win is the fixer≠verifier boundary that .libretto's structure enforces, which a single-session NL prompt cannot.** A single agent grading its own work shares its own blind spots.

- **Cost of that reliability is real:** the .libretto iterative run cost 4.3x the baseline tokens (6 sessions vs 1), consistent with the ~46K/session floor established in Phase 2. Formal control flow with separate verifier agents is a reliability-for-tokens trade, in the same family as Phase 2 (depth-for-tokens) and Phase 3 (latency-for-tokens).

- **Both approaches found real, corroborating defects** — the list-redaction secret-leak (both), and the baseline independently surfaced the `EvalResult.critical`-drop bug that echoes Phase 2's critical-flag finding. Model-level analysis quality is high regardless of orchestration; orchestration changes *how the work is checked*, not how good each step is.

## Token Cost Summary

| Run | Program | Sessions | Total tokens | Wall time |
|-----|---------|----------|-------------|-----------|
| 1 | 20-fixed-loops | 11 | ~290K | ~4 min |
| 2 | 22-error-handling | ~15 | ~380K | ~4 min |
| 3 | 25-conditionals | 9 | ~290K | ~4 min |
| 4 | atp-iterative-refactor | 6 | ~449K | ~13 min |
| 5 | atp-conditional-pipeline | 2 | ~138K | ~4 min |
| B1 | baseline iterative refactor | 1 | 105K | 3.6 min |
| B2 | baseline conditional pipeline | 1 | 92K | 2.5 min |

## Key Findings

1. **All Phase 4 control-flow constructs execute faithfully:** `repeat N` (exact count), `for`/`parallel for` (correct binding + fan-out), `try`/`catch`/`catch as err`/`finally` (incl. finally-on-success), nested `throw` re-raise, top-level unhandled throw, and `if`/`elif`/`else` discretion (single, compound multi-line, and over-parallel).
2. **Discretion evaluation is genuine LLM judgment and lands correctly** — especially when the setup session produces real data (the conditional-pipeline branch was checked against a real 88% coverage measurement, not a guess).
3. **`output` does not break a `repeat` loop** — no early-exit semantics exist; use `loop until **...**` for stop-on-success. Spec gap for compiler.md.
4. **The reliability advantage of .libretto over NL is session separation, not syntax.** Independent fixer/verifier sessions catch regressions that single-session self-verification misses — the clearest Phase 4 result. It costs ~4x the tokens.
5. **Subagents can break out of their intended scope:** they spontaneously launch nested workflows (example 20) or investigate the real workspace during simulated scenarios (example 25). The VM needs return-shape validation + retry, and leaf sessions need real targets or hard scenario isolation.
6. **Substrate hook interference persists** (subagent binding writes intermittently blocked → VM persists from returned text) and **terse haiku prompts occasionally return non-results** (needed 1 retry each in examples 20 and 22) — both carried over from Phases 2-3.

## Issues / Surprises

1. **The iterative-refactor loop produced genuinely useful engineering on real code:** a real security-relevant redaction gap found, a real regression in the first fix caught by independent verification, and a verified-safe second approach — exactly the self-correcting behavior the pattern promises, on a live codebase.
2. **The `EvalResult.critical`-drop bug** surfaced by the conditional baseline corroborates Phase 2's independent finding that the critical flag is inconsistently threaded — two different evaluation phases, via different programs, converged on the same real defect.
3. **Discretion is only as grounded as its setup session.** The conditional pipeline's branch was trustworthy because the analyst *measured*; example 25's discretion was correct but its leaf content drifted because the setup was hypothetical. The lesson for .libretto authors: give discretion conditions real data to judge.
4. **`repeat` with stateless bodies needs differentiation** — without VM-added "make it different" nudges, N iterations converge on N near-copies. Worth a patterns.md note.

## Conclusion

Phase 4 passes. Every control-flow construct — fixed loops, for-each, parallel-for, try/catch/finally, nested throw/re-raise, and if/elif/else discretion — executes with faithful semantics. The headline result answers the plan's central question: **formal control flow adds reliability over natural-language instructions primarily by enforcing session boundaries (independent verifier ≠ author), not through the branching syntax itself** — and that reliability costs roughly 4x the tokens of a single-session equivalent. For pure branching where the condition is grounded in real data, NL and formal discretion are equally reliable; for verify-and-retry loops, the fixer≠verifier separation is a genuine, structural advantage.

**Ready for Phase 5: Captain's Chair + RLM.**

## Files

- `evaluation/phase4/atp-iterative-refactor.libretto` — custom program (loop + try/catch + discretion)
- `evaluation/phase4/atp-conditional-pipeline.libretto` — custom program (if/elif/else discretion)
- `evaluation/phase4/baseline-prompts.md` — baseline prompts
- `evaluation/phase4/baseline-iterative-refactor.md` — baseline 1 output + cost
- `evaluation/phase4/baseline-conditional-pipeline.md` — baseline 2 output + cost
- `evaluation/results/phase-4.md` — this report
- `.libretto/runs/20260715-130312-f1ede6/` — example 20 run
- `.libretto/runs/20260715-130807-00a044/` — example 22 run
- `.libretto/runs/20260715-131145-66655e/` — example 25 run
- `.libretto/runs/20260715-131616-87c159/` — atp-iterative-refactor run
- `.libretto/runs/20260715-133058-240ad8/` — atp-conditional-pipeline run
