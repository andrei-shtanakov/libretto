# Syntax Comparison — Docstring Evaluator

## Runs

| Syntax | Run ID | Completed? | Steps executed | Retries | Approx tokens |
|--------|--------|-----------|----------------|---------|---------------|
| Functional (Phase 5) | `20260715-144402-64bf89` | yes | 8 (research×2, plan, implement, review, fix, test, summary) | 0 | ~717K |
| Borges | `20260715-211108-db2a03` | yes | 8 (if-branch fired: fixer ran) | 0 | ~528K |
| Kafka | `20260715-213339-9d8358` | yes | 7 (else-branch fired: no fixer) | 0 | ~572K |
| Homer | `20260715-220107-487dc0` | yes | 7 (else-branch fired: no fixer) | 0 | ~610K |

All four runs completed with **zero VM-level misparses** — every translated keyword (in all three registers) resolved to the correct functional construct on the first attempt. Session-count variance (7 vs 8) is entirely explained by whether the critic found a critical issue that session, not by register.

## Output Quality Comparison

| Aspect | Functional | Borges | Kafka | Homer |
|--------|-----------|--------|-------|-------|
| Code correctness | 9/10 | 9/10 | 9/10 | 9/10 |
| Test coverage | 9/10 (10 classes) | 9/10 (43 tests, 13 classes) | 9/10 (~35 tests, 15 classes) | 8/10 (proposed suite, less exhaustively enumerated) |
| Plan quality | 9/10 | 9/10 | 9/10 | 9/10 |
| Critic depth | 10/10 (found+fixed real empty-docstring bug) | 10/10 (found+fixed real pyrefly type bug) | 8/10 (verified clean, no bug to find) | 6/10 (found the SAME empty-docstring bug as functional, called it "minor" not critical) |

Every register's implementation independently arrived at essentially the same design (AST-walk over `Evaluator` subclass, artifact-file + fenced-code-block scanning, configurable coverage threshold) — strong evidence that the underlying task-solving capability is unaffected by keyword surface.

## Subagent Communication Style

**Did the keyword framing affect how subagents communicated? Barely, and not in the way the registers' own design intent suggests.**

- None of the transcripts adopted the register's *narrative voice* (no "dreaming a dream," no bureaucratic "petitioner," no epic "the hero's charge") — every subagent wrote in the same plain, professional engineering register regardless of which alias set summoned it. The keyword translation is purely **syntactic sugar for the VM's own parsing**, not a framing device subagents pick up on, because subagents never see the raw `.libretto` source — they receive the VM's *own* dispatch prompts (which this VM wrote in plain functional language: "Find all evaluator implementations...", "Review the implementation...") regardless of register.
- This is itself a finding: **register only affects the human-facing program text, not subagent behavior**, because the VM translates before dispatch. A register would only change subagent voice if the VM's dispatch prompts *themselves* echoed the register's vocabulary — which none of Phase 6's runs did, and which libretto.md gives no instruction to do.
- One indirect effect observed: response length/formatting varied session-to-session (Kafka's implementation ran the deepest live-verification: 22 tool calls, 464s), but this tracks normal LLM variance, not register.

## Verdict

**Syntax choice does not matter for practical use, on the dimension that matters most: whether the VM correctly executes the program.** All three registers are semantically transparent skins — `libretto.md`'s execution semantics are 100% preserved under translation; the "structured but self-evident" design goal each register document claims for itself is empirically true (zero misparses across 22 translated sessions, 8 distinct keyword categories × 3 registers).

Syntax choice **does matter for the humans reading/writing the program** — that's a separate, subjective axis this evaluation cannot measure without human subjects (see each register's own "Case For/Against" sections, which are the more honest source for that question).

The evaluation's more consequential finding is orthogonal to syntax: **critic severity judgment is not consistent across runs even on the same defect class** (empty/whitespace docstrings: CRITICAL in the functional run, "minor, non-blocking" in Homer). This is a property of LLM-as-judge review, not of any register — but it surfaced only because Phase 6 happened to run the same task 3 more times and could compare.

## Minor spec note

The roadmap's own keyword summary table (line 872-884 of the evaluation plan) lists `if` as unchanged across all three registers, but the authoritative `alts/{borges,kafka,homer}.md` spec files all translate `if`/`elif`/`else` (Borges: `should`/`or should`/`otherwise`; Kafka: `in the event that`/`or in the event that`/`otherwise`; Homer: `should`/`or should`/`otherwise`). This translation followed the authoritative `alts/*.md` files, not the roadmap's simplified table — a small but real inconsistency between the plan and the register specs it references.
