# Libretto Evaluation — Final Verdict

*Seven-phase systematic evaluation of Libretto as a practical AI-orchestration tool, run 2026-04-07 (Phase 1) through 2026-07-16 (Phase 7) against the real `atp-platform` codebase, with plain-Claude-Code baselines at every phase.*

## Summary Table

| Phase | Feature | .libretto vs Baseline | Key Finding |
|-------|---------|-------------------|-------------|
| 1 | Sequential foundations | Quality tie; ~5–10% token overhead | VM boots, spawns real subagents, passes context by reference through binding files. Overhead modest. Inspectability + composability are the differentiators. |
| 2 | Variables / context / composition | Quality tie; .libretto **1.8–6.4× cost** | All context forms, reassignment, blocks + params, scoped bindings work. Cost picture *inverts* Phase 1: ~46K-token floor per session; composition multiplies sessions. Buys measured depth + audit trail + clean context isolation. |
| 3 | Parallelism | Quality tie; **2.6× faster wall-clock, 2.6× more tokens** | Concurrent dispatch genuine; all join strategies (all/first/any-N) + failure policies (fail-fast/continue/ignore) faithful. Parallelism is a *latency* tool, not a cost tool. Gap: no in-flight cancellation (first/any pay for all branches); no `max_concurrent`. |
| 4 | Control flow | Quality tie; reliability win via **session separation**, ~4× cost | Loops (exact counts), try/catch/finally (incl. finally-on-success), nested throw, if/elif/else discretion all faithful. The reliability edge over natural-language instructions comes from *independent verifier ≠ author sessions*, not the branching syntax. Spec gap: `output` doesn't break `repeat`. |
| 5 | Orchestration (Captain's Chair + RLM) | Quality tie; Captain's Chair **4.5× cost** | Both patterns faithful. The **adversarial execution-grounded critic is the single highest-value session shape** — it live-ran proposed code and proved a real critical bug. RLM refinement value is **inversely proportional to seed quality** (58→93 for a weak seed; 85≈87 tie for a strong one). |
| 6 | Alternative syntaxes | Identical output; zero misparses | Borges/Kafka/Homer are transparent skins — 100+ keyword resolutions, 0 errors, identical semantics & output. Register does *not* propagate to subagent voice (VM dispatch prompts stay plain). Incidental finding: **critic severity labeling is inconsistent across runs** on the same defect. |
| 7 | Stdlib / meta-analysis | N/A (analyzes .libretto runs) | Self-improvement loop is real and trustworthy: inspector scored fidelity without hallucinating issues; cost-analyzer quantified **51.3% orchestration overhead**; program-improver found real, applicable design flaws. Two tools independently converged on the same optimization. |

## Verdict

**Is Libretto practically useful, or is the concept more interesting than its execution?**

**It is practically useful — but for a narrower purpose than "a programming language for AI," and its dominant cost is structural, not incidental.** The specification-as-VM concept is not a gimmick: across 7 phases and ~30 program runs, the VM executed every language construct faithfully — sequential chains, all context-passing forms, parallelism with correct join/failure semantics, loops, try/catch/finally, discretion-based branching, recursive blocks, program composition, three alternative keyword registers, and its own stdlib analyzing its own runs. Output quality matched plain Claude Code at every phase where they were comparable. **The execution lives up to the concept.**

But the same 7 phases established, with increasing precision, that **Libretto's value and its cost both come from the same thing: it turns one AI session into many bounded, isolated, inspectable sessions.** That decomposition is what buys the real benefits (audit trails, independent verification, context isolation, reproducibility, composability) — and it is also what makes it expensive: Phase 7 quantified that **~51% of a representative run's tokens are session-boundary re-loading overhead**, and every multi-session pattern costs 2–6× its single-prompt baseline. Libretto is not a way to do AI work *cheaper* or *better per token*; it is a way to do AI work *more reliably, auditably, and reproducibly* by paying a structural tax for session boundaries.

### Strengths

- **Faithful execution of a genuinely broad feature set** — nothing in the language is aspirational; it all runs. Zero keyword misparses even under three alternative syntax registers.
- **Independent verification is the killer feature** (Phases 4–5). A separate critic session — especially one that *executes* the proposed artifact — catches bugs that a single self-verifying session structurally cannot. This surfaced real, exploitable defects in real code (empty-docstring security gap; type-narrowing failure).
- **Inspectability & reproducibility** — every run leaves a complete, replayable audit trail (`state.md` + per-binding files). Plain prompts leave nothing. The stdlib can then analyze those trails (Phase 7).
- **Context isolation** — each subagent gets exactly the context wired to it, nothing ambient. Phase 2 showed plain baselines get contaminated by conversation context; .libretto sessions don't. This matters for reproducible evaluation.
- **Composability** — programs are reusable, versionable artifacts; the register experiment (Phase 6) and the stdlib self-analysis (Phase 7) both exploit this.
- **Robust self-correction** — the "wrong research path" premise was silently corrected by capable subagents in 4 independent runs; the RLM and Captain's Chair loops genuinely improved their outputs.

### Weaknesses

- **Cost scales with session count, and ~half of it is pure orchestration overhead** (Phase 7: 51.3%). The ~46K-token/session floor is the dominant economic fact of the system.
- **No in-flight cancellation** (Phase 3) — `parallel("first")` / `("any", count:N)` *discard* losing branches rather than cancelling them, so you pay for every branch regardless. Real cost of a race = sum of all branches.
- **No concurrency throttle** — `parallel:` has no `max_concurrent`; fine for 4 branches, a real cliff for large fan-outs (only the substrate's own cap saved large runs).
- **Spec gaps that bite:** `output`-as-return inside blocks (load-bearing for the entire RLM family) contradicts the register-only `output` semantics at top level; `output` doesn't break a `repeat` loop; cross-frame `context: { x }` resolution is unspecified. Two of the roadmap's own example programs don't compile under `compiler.md`'s flat-namespace rule.
- **LLM-judge inconsistency** (Phase 6) — critic *severity* labeling varied across near-identical runs (same defect called CRITICAL once, "minor" another time). Any pattern that gates on a single critic's severity inherits this noise.
- **Substrate coupling** — a Claude Code hook intermittently blocked subagent binding writes throughout, forcing the VM to persist bindings from returned text. The pass-by-reference design degrades when the substrate polices subagent file writes; and subagents can spontaneously launch *nested* orchestration unless explicitly constrained (observed 3×).

### When to use Libretto

- **Multi-lens review / audit** where you want independent verifier sessions that can't share the author's blind spots (the Phase 5 critic pattern) — the strongest demonstrated use.
- **Work that must be auditable or reproducible** — evaluations, compliance-sensitive pipelines, anything where "show your work" matters. The `.libretto/runs/` trail is the product as much as the output.
- **Fan-out over independent items** where wall-clock latency matters more than token cost (Phase 3) — parallel package review, multi-file analysis.
- **Reusable, shareable workflows** run repeatedly — the composability and the stdlib self-improvement loop pay off only when a program is re-executed enough to amortize its cost.
- **Cross-context isolation** — when ambient conversation contamination would corrupt results.

### When NOT to use Libretto

- **One-shot tasks with an execution oracle** — if the task is machine-checkable (code + tests) and you'll run it once, a single plain session that executes its own tests reaches comparable quality at ~4× less cost (Phase 5 baseline).
- **Cost-sensitive work** — you pay a ~2–6× token multiple and ~50% orchestration overhead for the session decomposition. If reliability/auditability aren't required, that tax buys nothing.
- **Pure branching where the condition is grounded in real data** — natural-language "if coverage <60%…" is as reliable as formal `if/elif/else` when the setup measures first (Phase 4). The formal syntax adds inspectability, not correctness, there.
- **Large unbounded fan-outs** until `max_concurrent` exists — the missing throttle is a real hazard.
- **Latency-critical single tasks** — VM overhead adds 2–5s per session boundary.

## Recommendations

**For Libretto authors (using the language):**
1. **Reserve multi-session decomposition for tasks that need isolation, depth, or auditability** — the value is real there and absent elsewhere. Default to fewer sessions; each one costs ~46K tokens of floor before doing any work.
2. **Always pair a builder with an independent critic session** for correctness-sensitive work — ideally a critic that *executes* the artifact. This is the highest-ROI pattern the evaluation found.
3. **Choose model tier per role, not per program** — expensive tiers only where open-ended reasoning happens (synthesis, planning-that-needs-it); cheap tiers for bounded/mechanical steps. The cost-analyzer and program-improver both independently confirmed this saves ~40%.
4. **Ground discretion conditions in real data** — a `**score >= 80**` gate is only as trustworthy as the session that produced the score; have it measure, not guess.
5. **Add an explicit "do the work yourself, no sub-agents" constraint to leaf prompts** — coordination-flavored role prompts otherwise prime subagents to spawn nested orchestration.

**For the Libretto project (improving the language/VM):**
1. **Close the `output`-as-return-inside-blocks spec gap in `compiler.md`** — it is load-bearing for the entire RLM example family yet contradicts top-level `output` semantics. Highest-priority spec fix.
2. **Ship `max_concurrent` for `parallel:`** (already ROADMAP P1) — the missing throttle is the most concrete correctness/safety gap.
3. **Fix the two roadmap example programs that don't compile** under the flat-namespace rule (dual `let` in both branches of a conditional) — and run `libretto compile` over all bundled examples in CI.
4. **Document that `"first"`/`"any"` do not cancel** (no in-flight cancellation on current substrates) so authors cost them correctly.
5. **Treat critic-severity noise as a known limitation** — for high-stakes gates, use multiple critics or a rubric, not a single severity label (this evaluation's Phase 6 finding).

## One-line verdict

**Libretto works as advertised and is genuinely useful for reliable, auditable, reproducible multi-agent work — provided you understand you are buying structure and trust at a ~2–6× token premium, roughly half of which is unavoidable session-boundary overhead. It is a reliability-and-auditability tool, not an efficiency tool.**
