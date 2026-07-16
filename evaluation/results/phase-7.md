# Phase 7: Stdlib and Meta-Analysis — Results

## Environment

- **Date:** 2026-07-16
- **Claude model (VM):** claude-opus-4-8; stdlib programs set their own per-agent tiers
- **Platform:** macOS Darwin 25.5.0
- **Tooling:** Claude Code with open-prose plugin (local marketplace)
- **State backend:** filesystem (default)
- **Target of analysis:** the Phase 5 Captain's Chair run `20260715-144402-64bf89` (inspector + cost-analyzer) and the Phase 3 fan-out program (program-improver)

## Runs

| Stdlib program | Run ID | Sessions | Result |
|----------------|--------|----------|--------|
| `lib/inspector.prose` | `20260716-053914-7ca2cc` | 9 | vm=pass (10/10), task=pass (9/9), fidelity 10, efficiency 8; no undetected issues |
| `lib/cost-analyzer.prose` | `20260716-054439-d72464` | 5 | 51.3% orchestration overhead quantified; opus captains = 51% of cost from 17% of tokens |
| `lib/program-improver.prose` | `20260716-055102-30d0e9` | 2 + skip | 8 actionable improvement opportunities for `evaluation/phase3/atp-workspace-fanout.prose` |

## 1. Inspector — does it produce meaningful fidelity scores? Detect issues we missed?

**Meaningful scores: yes.** Deep inspection of the Phase 5 Captain's Chair run returned vm completion 10/10, binding_integrity 10/10, fidelity 10/10, task output_substance/goal_alignment 9/9, efficiency 8/10. The efficiency 8 (not 10) is a defensible judgment — it docked the ~717K-token Captain's Chair cost, independently matching the evaluation's own Phase 5 conclusion that the pattern is expensive for its output.

**Detect issues we missed: no — and that is the honest, correct result.** The opus evaluator was explicitly instructed to be a skeptic and surface undetected VM issues. It found the two known caveats (the researcher's wrong-path premise; the unrun WI-4 validation gate) but correctly classified them as *already self-disclosed* by the run's own state.md/result.md — informational, not new defects. Critically, **it did not hallucinate novel problems to appear useful.** For a meta-inspector, corroborating a manual assessment without inventing findings is exactly the desired behavior. The `persist: user` index agent worked: first invocation created `~/.prose/agents/index/`, the register step appended `memory.md` + `index-001.md` — the compounding substrate the self-improvement loop depends on.

## 2. Cost-Analyzer — per-session breakdown? Orchestration overhead visible?

**Per-session breakdown: yes** — a clean 8-row table (agent, model, tokens, $ estimate, % of run), correctly attributing the two opus captain sessions as 51.1% of cost from 17.3% of tokens.

**Orchestration overhead quantified — the single most valuable stdlib output of the phase.** The analyzer put a hard number on the ~46K-token/session "context floor" that Phases 2–5 had only established qualitatively: **51.3% of the run's 717,909 tokens (368K) is session-boundary re-loading overhead, not task-productive work.** This quantitatively confirms the evaluation's running thesis that session count — not prompt size — is the dominant cost driver.

Its top recommendation (downgrade the two opus captain sessions to sonnet, ~41% cost savings) is directly validated by **this evaluation's own Phase 6**, which re-ran the same program with sonnet captains at comparable quality. The analyzer cross-referenced a sibling phase's empirical result rather than guessing — and it included an honest methodology caveat (flat 55/45 in/out split, list pricing, caching unmodeled), not overclaiming dollar precision.

## 3. Program-Improver — real, applicable suggestions?

**Yes — genuinely actionable and program-specific, not generic filler.** Run against `evaluation/phase3/atp-workspace-fanout.prose`, it surfaced 8 opportunities (1 high, 4 medium, 3 low). The top finding is a real design flaw in that program: the four fan-out branches request *divergent* review dimensions (core→test coverage, adapters→adapter count, dashboard→UI approach, sdk→API surface), yet the synthesis step is asked to rank "strongest/weakest package" — an unanchored comparison across non-aligned axes. That is a correct, source-derived critique.

Two signals it *understood* the program rather than pattern-matching:
- Its model-tier-split recommendation (haiku for the bounded 200-word branches, sonnet/opus only for synthesis) is the **same lever the cost-analyzer independently reached** for a different program — two stdlib tools converging on one optimization.
- It flagged a **load-bearing mitigation not to remove** (the 200-word branch caps that keep synthesis context cheap) — grasping the program's cost structure, not just listing smells.

The mid-program `input selection` pause fired correctly; per an operator decision (evaluation scope is *assessing* suggestion quality, not autonomously mutating an eval artifact or opening a second PR), the selection was answered "none", the `**user selected none**` discretion resolved TRUE, and the VM took the skip-output path with the analysis preserved.

## Key Findings

1. **The self-improvement loop produces actionable insights — this phase's headline answer is YES.** All three stdlib tools returned substantive, grounded, cross-corroborating output on real runs: inspector scored fidelity without inventing issues, cost-analyzer quantified the 51.3% orchestration tax, program-improver found a real design flaw plus 7 more opportunities.
2. **Two stdlib tools independently converged on the same optimization** (model-tier splitting: expensive tier only where open-ended reasoning is needed). Independent convergence from different inputs is strong evidence the suggestions track real structure, not tool-specific bias.
3. **`persist: user` cross-project memory works end-to-end** — both the inspector's index agent and the cost-analyzer's tracker agent created and updated user-scoped memory (`~/.prose/agents/{index,tracker}/`), the substrate the stdlib's compounding self-analysis depends on.
4. **The meta-tools inherit every VM property established in Phases 1–6** — parallel synthesis (inspector Phase 3), pmap (cost-analyzer), mid-program input pause + discretion branching (program-improver), and the persistent substrate hook interference (subagent binding writes blocked → VM persists from returned text, as in Phases 2–6). The stdlib is not a special case; it is ordinary .prose exercising the same semantics on .prose runs as input.
5. **Meta-honesty is the notable qualitative result**: the inspector declined to fabricate findings, and the cost-analyzer flagged its own estimation caveats. A self-improvement loop that inflates problems to justify itself would be worse than useless; these tools did not.

## Issues / Surprises

1. **Grounding matters as much for meta-tools as for object-level programs.** The cost-analyzer's output was only trustworthy because it was fed the *actual* recorded per-session token counts (the collector otherwise estimates from content length, which the evaluation's earlier phases showed is unreliable). A cost-analyzer run on estimated tokens alone would be a much softer artifact — worth noting for anyone relying on it without real telemetry.
2. **program-improver's `can_pr: true` on an evaluation artifact is a small footgun** — the program would, if driven past the selection gate, try to open a PR that mutates an eval file. The selection gate is the safety valve, and the operator "none" answer used it correctly. A production use should be careful that `can_pr` reflects intent, not just repo-has-a-remote.
3. **Cost of meta-analysis is itself non-trivial**: the three stdlib runs cost ~16 sessions combined to analyze ~2 object-level runs. The self-improvement loop is worth running on high-value or frequently-reused programs, not on every run — the analysis pays for itself only when the target is re-executed enough to amortize the optimization.

## Conclusion

Phase 7 passes. The OpenProse standard library closes the self-improvement loop the project's design promises: inspector → (VM-improver / program-improver) → PR, plus cost-analyzer for the economic axis. On real runs the tools produced meaningful fidelity scores, a quantified orchestration-overhead figure (51.3%) that confirms the evaluation's central cost thesis, and specific, applicable, cross-corroborating improvement suggestions — all without hallucinating problems to appear useful. The loop is real, and its output is trustworthy when fed real telemetry.

**This completes all 7 phases. See `final-verdict.md` for the synthesis.**

## Files

- `evaluation/results/phase-7.md` — this report
- `evaluation/results/final-verdict.md` — cross-phase synthesis
- `.prose/runs/20260716-053914-7ca2cc/` — inspector run (gitignored, local only)
- `.prose/runs/20260716-054439-d72464/` — cost-analyzer run (gitignored, local only)
- `.prose/runs/20260716-055102-30d0e9/` — program-improver run (gitignored, local only)
- `~/.prose/agents/index/`, `~/.prose/agents/tracker/` — user-scoped persistent agent memory created this phase (cross-project, outside the repo)
