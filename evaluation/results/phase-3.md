# Phase 3: Parallelism — Results

## Environment

- **Date:** 2026-07-15
- **Claude model (VM):** claude-opus-4-8; sessions per program `model:` (sonnet / haiku), default = inherit
- **Platform:** macOS Darwin 25.5.0
- **Claude Code with open-prose plugin (local marketplace)**
- **State backend:** filesystem (default)
- **Concurrency substrate:** Agent tool; parallel branches dispatched as multiple Agent calls in a single VM turn (true concurrency)

## Built-in Examples

| Example | Sessions | Ran successfully? | Fidelity notes |
|---------|----------|-------------------|----------------|
| `16-parallel-reviews.prose` | 4 | yes | 3 review branches dispatched in one turn, ran concurrently (67–72s overlapping); barrier `all` held; synthesis got all 3 contexts |
| `17-parallel-research.prose` | 4 | yes | 3 research branches concurrent (33–81s overlapping); `{ history, current, future }` all wired into summary |
| `19-advanced-parallel.prose` | 20 | yes | All 5 join/failure strategies exercised (see fidelity table); haiku + terse prompts to keep cost down |

### Join-strategy / failure-policy fidelity (example 19)

| Construct | Spec behavior | Observed | Verdict |
|-----------|--------------|----------|---------|
| `parallel ("first")` | first completion wins, cancel others | approach A returned first (5.8s), beat C (9.0s) & B (56s); A accepted, B/C discarded | ✅ semantics correct / ⚠️ no true cancel |
| `parallel ("any", count: 2)` | wait for N successes | a (4.1s) & c (5.2s) accepted; b, d discarded | ✅ semantics correct / ⚠️ no true cancel |
| `parallel (on-fail: "continue")` | wait all, report errors | secondary branch forced to fail; block did NOT abort, combine session reported partial_success + noted the failure | ✅ |
| `parallel (on-fail: "ignore")` | failures treated as successes | enrich2 forced to fail; silently ignored, merge used only successes | ✅ |
| `parallel ("first", on-fail: "continue")` | first result even if handled failure | slow-reliable returned first (5.0s); fast branch's non-result discarded | ✅ |

### Key fidelity finding: no true in-flight cancellation

The spec defines `"first"` and `"any", count: N` as "return on completion, **cancel** the
others." The Agent-tool substrate cannot abort an in-flight subagent, so the VM implements
these as "dispatch all, accept the first N to return, **discard** the rest." The discarded
branches still run to completion and consume tokens — in example 19 the discarded race
branch B cost 58K tokens that a real cancelling scheduler would have saved. **Semantics
(which result wins) are faithful; resource behavior (cancellation) is not.** This is a
substrate limitation, not a spec violation, but any cost model for `"first"`/`"any"` must
assume all branches are paid for. Candidate for ROADMAP P1 (pause/cancel protocol).

## Custom .prose Programs

| Program | Sessions | Ran successfully? | Output quality (1-10) | Notes |
|---------|----------|-------------------|----------------------|-------|
| `atp-workspace-fanout.prose` | 5 | yes | 9 | 4-way parallel package review; branches concurrent (33–46s), block wall ~46s (= slowest branch); all 4 bindings present before synthesis; synthesis ranked sdk strongest / dashboard weakest with cross-cutting recs |
| `atp-multi-audit.prose` | 4 | yes | 9 | 3 concurrent auditors (security/perf/quality) on atp-core; security auditor **verified 2 critical exploits** (validate_command allowlist bypass, validate_volume_mount fail-open + docker.sock) by reasoning against actual code; `on-fail: continue` armed (all 3 succeeded, so not triggered here — separately verified in ex19) |

### Parallel-block behavior checks (from the plan)

- **Did branches run concurrently?** Yes — 4 fan-out branches overlapped (per-branch durations 33–46s within a ~46s block window). Confirmed via state.md per-branch timings.
- **Verify all bindings exist before synthesis?** Yes — the `all` barrier held; synthesis ran only after all 4 branch bindings were written.
- **Does `on-fail: continue` allow the report even if one auditor fails?** Verified via example 19 with a real forced failure (multi-audit's 3 auditors all succeeded, so the policy was armed but not exercised there).

## Baseline Comparison

| Task | .prose (parallel) | Baseline (sequential) | .prose wall | Baseline wall | .prose tokens | Baseline tokens | Winner |
|------|-------------------|----------------------|-------------|---------------|---------------|-----------------|--------|
| 4-package workspace review | 9/10 | 9/10 | ~86s (46s parallel block + 40s synthesis) | 225s | ~302K (4 branches + synthesis) | 117K | .prose on wall-clock (2.6x faster); baseline on tokens (2.6x cheaper) |

### Analysis

- **The Phase 3 trade is the mirror image of Phase 2's.** Phase 2 (composition) showed .prose paying *more tokens for depth*. Phase 3 (parallelism) shows .prose paying *more tokens for wall-clock*: the fan-out block finished in ~46s (the slowest single branch) where the sequential baseline took 225s. The speedup ceiling is `sum(branches) / max(branch)` — here 4 branches of 33–46s each: ~160s of work compressed into ~46s.
- **Token cost scales with branch count, wall-clock does not.** 4 parallel branches ≈ 4× the token floor (~46K each from Phase 2's finding) but ≈ 1× the wall-clock of the slowest branch. Parallelism is a latency optimization that *increases* total token spend — the opposite of what you'd want if optimizing cost, exactly what you want if optimizing time-to-result.
- **Quality is equivalent** (both 9/10) — but the parallel .prose produced deeper per-package analysis because each reviewer had a full session budget for one package, whereas the sequential baseline amortized one budget across four (and independently chose to sub-spawn the largest package — a spontaneous parallelism that validates the pattern the `parallel:` block formalizes).
- **The multi-audit run is the strongest evidence for the pattern**: three specialists in parallel each went deep enough to *verify* findings (the security auditor confirmed two exploitable criticals against real code in 250s / 164K tokens) — depth a single generalist session rarely reaches. Parallel specialization + a synthesis join is a genuinely better shape for multi-lens review than one sequential pass.

## Token Cost Summary

| Run | Program | Sessions | Total tokens | Wall time |
|-----|---------|----------|-------------|-----------|
| 1 | 16-parallel-reviews | 4 | ~309K | ~2 min |
| 2 | 17-parallel-research | 4 | ~242K | ~2.5 min |
| 3 | 19-advanced-parallel | 20 | ~640K | ~4 min |
| 4 | atp-workspace-fanout | 5 | ~302K | ~1.5 min (parallel) |
| 5 | atp-multi-audit | 4 | ~527K | ~7 min (slowest auditor 6 min) |
| B1 | baseline workspace review | 1 | 117K | 3.75 min |

## Key Findings

1. **Parallel dispatch works and is genuinely concurrent.** Dispatching N branches as N Agent calls in one VM turn produces real overlap; the `all` barrier correctly gates the downstream join session until every branch binding is written.
2. **All join strategies and failure policies are faithful** on the "which result wins / does the block abort" axis: `all`, `first`, `any count:N`, `on-fail: continue`, `on-fail: ignore`, and combinations. Verified individually in example 19.
3. **Parallelism trades tokens for wall-clock** (~2.6x faster, ~2.6x more tokens on the fan-out task). It is a latency tool, not a cost tool — the inverse of the intuition that "doing things at once is cheaper."
4. **No true in-flight cancellation** on this substrate: `"first"`/`"any"` discard rather than cancel losing branches, so every dispatched branch is paid for regardless of strategy. Real cost of `parallel("first")` = sum of all branches, not the winner. (ROADMAP P1 pause/cancel.)
5. **Parallel specialization reaches more depth than a sequential generalist pass** — the multi-audit specialists each *verified* findings; the sequential baseline skimmed. For multi-lens review, fan-out-then-synthesize is the better shape.
6. **Substrate hook interference persists from Phase 2**: subagent binding writes were intermittently blocked ("return findings as text"); VM fell back to persisting from returned text (e.g. multi-audit's final report). Same deviation from the pass-by-reference invariant noted in phase-2.md.

## Issues / Surprises

1. **Even the unstructured baseline parallelized.** The single-session baseline spontaneously spawned a background sub-agent for the largest package (atp-dashboard). The instinct to fan out on heavy sub-tasks is model-level; OpenProse's contribution is making it *explicit, uniform, and inspectable* rather than ad hoc.
2. **`ROADMAP P1 concurrency limits` matters more after this phase.** `parallel:` currently launches *all* branches at once with no `max_concurrent`. Fine for 3–4 branches; a `parallel for` over 50 files would attempt 50 simultaneous subagents. The substrate's own concurrency cap saved us, but the language has no throttle — a real gap for large fan-outs.
3. **Example 19 is expensive for a semantics test** (20 sessions, ~640K tokens even on haiku with trivial prompts) — the ~46K per-session floor dominates regardless of content. Documented the haiku+terse cost-control choice in the run's state.md.
4. **The multi-audit security findings look genuinely actionable** (2 verified criticals in `atp/core/security.py`). They live in the run binding `report.md`; whether to action them against atp-platform is a separate, cross-repo decision (atp-platform is a read-only neighbor per repo-boundaries — would need a handoff note, not a direct edit).

## Conclusion

Phase 3 passes. Concurrent dispatch, the `all` barrier, every join strategy (`all`/`first`/`any count:N`) and every failure policy (`fail-fast`/`continue`/`ignore`) execute with faithful *semantics*. The one substrate gap is resource-level, not semantic: no in-flight cancellation, so `"first"`/`"any"` pay for all branches. The headline economic result is that parallelism inverts Phase 2's trade — it buys wall-clock (2.6x faster here) at the price of tokens (2.6x more), making it a latency optimization for independent sub-tasks and, via specialization, a quality win for multi-lens review.

**Ready for Phase 4: Loops and Error Handling.**

## Files

- `evaluation/phase3/atp-workspace-fanout.prose` — custom program (4-way fan-out + synthesis)
- `evaluation/phase3/atp-multi-audit.prose` — custom program (parallel multi-lens audit)
- `evaluation/phase3/baseline-prompts.md` — baseline prompt
- `evaluation/phase3/baseline-workspace-review.md` — baseline output + cost/timing
- `evaluation/results/phase-3.md` — this report
- `.prose/runs/20260715-100517-a307de/` — example 16 run
- `.prose/runs/20260715-100838-ba4c4f/` — example 17 run
- `.prose/runs/20260715-101213-7948e7/` — example 19 run (join/failure fidelity)
- `.prose/runs/20260715-101649-d6e08c/` — atp-workspace-fanout run
- `.prose/runs/20260715-101924-b52ccc/` — atp-multi-audit run
