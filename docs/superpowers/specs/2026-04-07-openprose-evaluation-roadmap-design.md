# Libretto Evaluation Roadmap

Systematic evaluation of Libretto as a practical tool for multi-agent orchestration. The roadmap progresses from language primitives to production patterns, using atp-platform (`../atp-platform`) as a real-world test target.

## Approach: Spiral

Each phase follows the same formula:

1. **Run built-in examples** — verify the language construct works
2. **Write custom .libretto for atp-platform** — test practical value
3. **Baseline comparison** — same task via plain Claude Code prompt (no .libretto)

Phases 6-7 add experiments with alternative syntaxes and stdlib self-analysis.

## Evaluation Criteria (all phases)

| Criterion | How to measure |
|-----------|---------------|
| **Fidelity** | Does the VM correctly interpret constructs? Are subagents actually spawned via Task tool? Does `.libretto/runs/` state get written? |
| **Result quality** | Side-by-side comparison of .libretto output vs plain prompt output |
| **Cost** | Token count and number of tool calls for the same task |
| **Reproducibility** | Does a second run produce a comparable result? |

## Test Target: atp-platform

ATP is a framework-agnostic AI agent testing platform. Python 3.12+, uv workspace monorepo with 4 packages (atp-core, atp-adapters, atp-dashboard, atp-sdk), FastAPI backend, 10+ agent adapters, 12+ evaluators, game-theoretic evaluation library. High complexity, well-documented — ideal for realistic orchestration tests.

---

## Phase 1: Foundations — Sequential Sessions + Agents

**Goal:** Verify the VM boots, spawns sessions, writes state. Establish baseline workflow.

### Built-in examples

| Example | What it tests |
|---------|--------------|
| `01-hello-world.libretto` | Minimal VM boot — single session |
| `02-research-and-summarize.libretto` | Two sequential sessions, implicit context passing |
| `04-write-and-refine.libretto` | Write-then-improve cycle |

### Custom .libretto for atp-platform

1. **Simple:** "Read the atp-platform README and produce a concise architecture summary"
2. **Two-step:** "Explore the `adapters/` directory structure, then write a summary of common patterns across adapters"

### Baseline

Same tasks as plain Claude Code prompts.

### What to check

- `.libretto/runs/{timestamp}/` directory created with state files
- Subagents actually spawned (not simulated inline)
- Result quality comparable to baseline
- Any overhead from VM interpretation

---

## Phase 2: Variables, Context, Composition

**Goal:** Test named bindings, context passing between sessions, and reusable blocks.

### Built-in examples

| Example | What it tests |
|---------|--------------|
| `13-variables-and-context.libretto` | Named bindings, `context: { a, b }` |
| `14-composition-blocks.libretto` | Reusable blocks (function analogue) |
| `15-inline-sequences.libretto` | Chains inside blocks |

### Custom .libretto for atp-platform

1. **Dependency chain:** "Research evaluators/ -> extract common interface -> propose refactoring with base class" — each step consumes the previous step's output
2. **Reusable block:** Define `review-module(path)` block, invoke it for atp-core, atp-adapters, atp-sdk — test that the same block produces tailored results per input

### Baseline

Same multi-step analysis as a single structured prompt.

### What to check

- `bindings/{name}.md` files written correctly
- `context: { a, b }` actually passes content (not just references)
- Blocks execute correctly when called multiple times with different arguments
- Whether formal variable binding improves result coherence vs free-form prompt

---

## Phase 3: Parallelism

**Goal:** Verify parallel execution, join strategies, and failure policies.

### Built-in examples

| Example | What it tests |
|---------|--------------|
| `16-parallel-reviews.libretto` | Basic `parallel:` block |
| `17-parallel-research.libretto` | Parallel data gathering with join |
| `19-advanced-parallel.libretto` | `on-fail` strategies, nested parallelism |

### Custom .libretto for atp-platform

1. **Fan-out review:** Analyze 4 workspace packages (atp-core, atp-adapters, atp-dashboard, atp-sdk) in parallel, then synthesize findings
2. **Multi-aspect audit:** Security + performance + code quality review of one module simultaneously

### Baseline

Sequential prompt for the same 4 packages.

### What to check

- Are Task calls actually dispatched in parallel (or serialized)?
- Execution time: parallel .libretto vs sequential baseline
- Join behavior: does the synthesis step receive all parallel outputs?
- `on-fail: "continue"` — does VM proceed when one subagent fails?
- Token cost of parallel overhead

---

## Phase 4: Control Flow — Loops, Conditionals, Error Handling

**Goal:** Test non-linear execution: iteration, branching, recovery.

### Built-in examples

| Example | What it tests |
|---------|--------------|
| `20-fixed-loops.libretto` | `repeat`, `for-each` |
| `22-error-handling.libretto` | `try`/`catch`/`finally` |
| `25-conditionals.libretto` | Branching based on results |

### Custom .libretto for atp-platform

1. **Iterative refactoring:** "Find code smell -> fix -> run tests -> if tests fail, revert and try differently" (loop + error handling)
2. **Conditional pipeline:** "Analyze module. If test coverage < 60% -> write tests. If > 60% -> hunt for bugs in existing tests"

### Baseline

Same logic described in natural language in a plain prompt.

### What to check

- How VM evaluates conditions (LLM judgment, not deterministic) — is it reliable?
- Loop termination: does `repeat 3` actually repeat 3 times?
- Error recovery: does `catch` actually get a different subagent approach?
- **Key question:** Does formal .libretto structure produce more reliable branching than verbal instructions?

---

## Phase 5: Advanced Orchestration — Captain's Chair + RLM

**Goal:** Test production-grade patterns: role separation, recursive improvement.

### Built-in examples

| Example | What it tests |
|---------|--------------|
| `30-captains-chair-simple.libretto` | Minimal captain + executor + critic |
| `29-captains-chair.libretto` | Full pattern: research-sweep, review-cycle, parallel implementation |
| `40-rlm-self-refine.libretto` | Recursive self-improvement of output |
| `41-rlm-divide-conquer.libretto` | Task decomposition into subtasks |

### Custom .libretto for atp-platform

1. **Captain's Chair for a real feature:** "Add a new evaluator for checking docstrings" — captain plans, researcher studies existing evaluators, coder implements, critic reviews, tester writes tests
2. **RLM self-refine:** "Write an architecture document for atp-platform" -> critic evaluates -> author improves -> repeat until acceptable quality

### Baseline

Same feature implemented via standard Claude Code (which implicitly does captain's chair).

### What to check

- Does explicit role formalization (captain/coder/critic) produce better results than when Claude decides roles implicitly?
- Cost of multi-agent overhead — how many extra tokens for the orchestration layer?
- Does RLM actually converge to a better result, or does it spin without improvement?
- Context isolation: do subagents receive targeted context or get overloaded?

---

## Phase 6: Alternative Syntaxes — Style Impact on Agent Behavior

**Goal:** Determine whether keyword framing (metaphor) affects LLM agent behavior.

### Experiment design

Take **one fixed task** from Phase 5 (Captain's Chair for new evaluator) and run it in **4 syntaxes**:

| Syntax | Atmosphere | Hypothesis |
|--------|-----------|------------|
| **Functional** (standard) | Neutral-technical | Baseline |
| **Borges** (dreamer, labyrinth, zahir) | Metaphysical | May provoke more abstract, creative reasoning |
| **Kafka** (clerk, proceeding, appeal) | Bureaucratic | May strengthen formality and thoroughness |
| **Homer** (hero, trial, glory) | Epic-heroic | May produce more ambitious, "heroic" solutions |

### Metrics

- Code quality (subjective + test pass rate)
- Completeness (all steps executed?)
- Communication style (do subagent responses change tone?)
- Token cost per syntax

### What to check

- Are differences purely cosmetic, or does keyword framing measurably change LLM behavior?
- Does any syntax consistently outperform functional on quality or cost?
- This is effectively a mini prompt-engineering-through-metaphor study

---

## Phase 7: Stdlib and Meta-Capabilities

**Goal:** Test Libretto's self-improvement loop.

### Built-in stdlib programs

| Program | Purpose |
|---------|---------|
| `lib/inspector.libretto` | Post-run fidelity analysis |
| `lib/cost-analyzer.libretto` | Cost breakdown per step |
| `lib/profiler.libretto` | Step-by-step profiling |
| `lib/program-improver.libretto` | Auto-improve .libretto programs |

### Application to our work

1. Run **inspector** on results from Phases 1-6 — how faithfully did the VM follow specs?
2. Run **cost-analyzer** on Captain's Chair runs — quantify orchestration overhead
3. Run **program-improver** on our custom .libretto programs — does it suggest improvements that actually increase quality?

### What to check

- Does the self-improvement loop produce actionable suggestions?
- Can inspector detect fidelity issues that we missed manually?
- Is the stdlib itself executable by the VM, or does it fail on its own complexity?

---

## Deliverables

After completing all phases, produce:

1. **Results log** per phase: examples run, custom programs written, baseline comparisons, metrics
2. **Comparative summary table:** .libretto vs plain prompt across all phases (quality, cost, reproducibility)
3. **Syntax experiment report:** Phase 6 findings on metaphor impact
4. **Verdict:** Is Libretto practically useful, or is the specification-as-VM concept more interesting than its execution?

## Progression dependencies

```
Phase 1 (foundations)
  -> Phase 2 (variables, context)
    -> Phase 3 (parallelism)
      -> Phase 4 (control flow)
        -> Phase 5 (orchestration patterns)
          -> Phase 6 (syntax experiments)  [can run after Phase 5]
          -> Phase 7 (stdlib/meta)         [can run after Phase 5]
```

Phases 6 and 7 are independent of each other and can run in parallel after Phase 5.
