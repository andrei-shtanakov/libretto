# Libretto Evaluation Roadmap — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Systematically evaluate Libretto as a practical orchestration tool by running built-in examples, writing custom .libretto programs against atp-platform, and comparing results with plain Claude Code prompts.

**Architecture:** Each of 7 phases follows a spiral pattern: (1) run built-in examples, (2) write and run custom .libretto targeting atp-platform, (3) run the same task as a plain prompt baseline, (4) record findings. Phases 6-7 add syntax experiments and stdlib meta-analysis.

**Tech Stack:** Libretto VM (specification-as-VM via `libretto.md`), Claude Code with Task tool, atp-platform as test target (local at `../atp-platform`, live at `https://pr0sto.space`).

---

## How This Plan Works

This is a **research/evaluation** plan, not a traditional coding project. Each task produces:
- `.libretto` program files in `evaluation/` directory
- Run artifacts in `.libretto/runs/`
- Findings logged in `evaluation/results/phase-N.md`

**Running a .libretto program** means invoking the Libretto skill: type `libretto run <file>` in Claude Code. The VM loads `libretto.md` + `state/filesystem.md` and executes. Each `session` becomes a real Task tool call spawning a subagent.

**Baseline comparison** means performing the same task as a plain Claude Code prompt (no .libretto), then comparing quality, cost, and approach.

**Important:** After each `libretto run`, inspect `.libretto/runs/` for the latest run directory. Check `state.md` for execution trace and `bindings/` for outputs.

### File structure

```
evaluation/
├── phase1/
│   ├── atp-architecture-summary.libretto     # Custom: simple one-step
│   ├── atp-adapters-patterns.libretto        # Custom: two-step sequential
│   └── baseline-prompts.md               # Plain prompts for baseline comparison
├── phase2/
│   ├── atp-evaluator-refactoring.libretto    # Custom: dependency chain with variables
│   ├── atp-module-review.libretto            # Custom: reusable block
│   └── baseline-prompts.md
├── phase3/
│   ├── atp-workspace-fanout.libretto         # Custom: parallel across 4 packages
│   ├── atp-multi-audit.libretto              # Custom: parallel security+perf+quality
│   └── baseline-prompts.md
├── phase4/
│   ├── atp-iterative-refactor.libretto       # Custom: loop + error handling
│   ├── atp-conditional-pipeline.libretto     # Custom: conditional branching
│   └── baseline-prompts.md
├── phase5/
│   ├── atp-docstring-evaluator.libretto      # Custom: Captain's Chair for real feature
│   ├── atp-architecture-doc.libretto         # Custom: RLM self-refine
│   └── baseline-prompts.md
├── phase6/
│   ├── atp-docstring-borges.libretto         # Borges syntax version
│   ├── atp-docstring-kafka.libretto          # Kafka syntax version
│   ├── atp-docstring-homer.libretto          # Homer syntax version
│   └── syntax-comparison.md              # Side-by-side analysis
└── results/
    ├── phase-1.md
    ├── phase-2.md
    ├── phase-3.md
    ├── phase-4.md
    ├── phase-5.md
    ├── phase-6.md
    ├── phase-7.md
    └── final-verdict.md
```

### Results template

Every `results/phase-N.md` uses this structure:

```markdown
# Phase N: [Title] — Results

## Built-in Examples

| Example | Ran successfully? | Fidelity notes |
|---------|-------------------|----------------|
| `NN-name.libretto` | yes/no/partial | ... |

## Custom .libretto Programs

| Program | Ran successfully? | Output quality (1-10) | Notes |
|---------|-------------------|----------------------|-------|
| `name.libretto` | yes/no/partial | N | ... |

## Baseline Comparison

| Task | .libretto quality | Baseline quality | .libretto cost (approx) | Baseline cost (approx) | Winner |
|------|---------------|-----------------|---------------------|----------------------|--------|
| ... | N/10 | N/10 | ~tokens | ~tokens | ... |

## Key Findings
- ...

## Issues / Surprises
- ...
```

---

## Task 1: Setup and Phase 1 — Sequential Foundations

**Files:**
- Create: `evaluation/phase1/atp-architecture-summary.libretto`
- Create: `evaluation/phase1/atp-adapters-patterns.libretto`
- Create: `evaluation/phase1/baseline-prompts.md`
- Create: `evaluation/results/phase-1.md`

### Part A: Run built-in examples

- [ ] **Step 1: Run hello-world**

```
libretto run examples/01-hello-world.libretto
```

After it completes, inspect the run:

```bash
ls .libretto/runs/
# Find the latest directory, then:
ls .libretto/runs/<latest>/
cat .libretto/runs/<latest>/state.md
```

Record: Did the VM boot? Was a subagent spawned? Was state.md created?

- [ ] **Step 2: Run research-and-summarize**

```
libretto run examples/02-research-and-summarize.libretto
```

Inspect: Are there two entries in state.md (two sequential sessions)? Check `.libretto/runs/<latest>/bindings/` for any outputs.

- [ ] **Step 3: Run write-and-refine**

```
libretto run examples/04-write-and-refine.libretto
```

Inspect: Does the second session's output show evidence of improving the first session's work?

- [ ] **Step 4: Record built-in example results**

Fill in the "Built-in Examples" table in `evaluation/results/phase-1.md` with findings from steps 1-3.

### Part B: Write and run custom .libretto for atp-platform

- [ ] **Step 5: Create the evaluation directory**

```bash
mkdir -p evaluation/phase1
```

- [ ] **Step 6: Write atp-architecture-summary.libretto**

```prose
# ATP Architecture Summary
# Simple one-step: read the project and summarize

session "Read the README.md and key configuration files in ../atp-platform. Produce a concise architecture summary covering: project purpose, tech stack, package structure (atp-core, atp-adapters, atp-dashboard, atp-sdk), and key design decisions."
```

Save to `evaluation/phase1/atp-architecture-summary.libretto`.

- [ ] **Step 7: Run atp-architecture-summary.libretto**

```
libretto run evaluation/phase1/atp-architecture-summary.libretto
```

Inspect `.libretto/runs/<latest>/state.md` and any bindings. Rate the output quality 1-10.

- [ ] **Step 8: Write atp-adapters-patterns.libretto**

```prose
# ATP Adapters Pattern Analysis
# Two-step sequential: explore structure, then analyze patterns

session "Explore the directory structure of ../atp-platform/packages/atp-adapters/. List all adapter implementations, their file organization, and the base classes they extend."

session "Based on the exploration above, write a summary of common patterns across all adapters. Include: shared interface, initialization conventions, error handling approach, and any inconsistencies between adapters."
```

Save to `evaluation/phase1/atp-adapters-patterns.libretto`.

- [ ] **Step 9: Run atp-adapters-patterns.libretto**

```
libretto run evaluation/phase1/atp-adapters-patterns.libretto
```

Check: Does the second session's output reference findings from the first? Is context passed implicitly or lost?

### Part C: Baseline comparison

- [ ] **Step 10: Write baseline-prompts.md**

Document the plain prompts you will use for comparison:

```markdown
# Phase 1 Baseline Prompts

## Task 1: Architecture Summary
"Read the README.md and key configuration files in ../atp-platform. Produce a concise architecture summary covering: project purpose, tech stack, package structure (atp-core, atp-adapters, atp-dashboard, atp-sdk), and key design decisions."

## Task 2: Adapters Pattern Analysis
"Explore the directory structure of ../atp-platform/packages/atp-adapters/. List all adapter implementations, then write a summary of common patterns: shared interface, initialization conventions, error handling, and inconsistencies."
```

Save to `evaluation/phase1/baseline-prompts.md`.

- [ ] **Step 11: Run baselines**

Execute each prompt above as a plain Claude Code request (no .libretto). Save the outputs mentally for comparison.

- [ ] **Step 12: Record Phase 1 results**

Fill in `evaluation/results/phase-1.md` using the results template. Key questions to answer:
- Did the VM correctly spawn subagents?
- Was `.libretto/runs/` state written?
- How does output quality compare to plain prompts?
- What was the approximate token overhead of the VM layer?

- [ ] **Step 13: Commit Phase 1**

```bash
git add evaluation/phase1/ evaluation/results/phase-1.md
git commit -m "evaluation: Phase 1 — sequential foundations results"
```

---

## Task 2: Phase 2 — Variables, Context, Composition

**Files:**
- Create: `evaluation/phase2/atp-evaluator-refactoring.libretto`
- Create: `evaluation/phase2/atp-module-review.libretto`
- Create: `evaluation/phase2/baseline-prompts.md`
- Create: `evaluation/results/phase-2.md`

### Part A: Run built-in examples

- [ ] **Step 1: Run variables-and-context**

```
libretto run examples/13-variables-and-context.libretto
```

Inspect: Are `bindings/` files created with named outputs? Does `context: { a, b }` wire correctly?

- [ ] **Step 2: Run composition-blocks**

```
libretto run examples/14-composition-blocks.libretto
```

Inspect: Are blocks invoked correctly? Do parameterized blocks receive arguments?

- [ ] **Step 3: Run inline-sequences**

```
libretto run examples/15-inline-sequences.libretto
```

- [ ] **Step 4: Record built-in results**

### Part B: Write and run custom .libretto

- [ ] **Step 5: Create phase2 directory**

```bash
mkdir -p evaluation/phase2
```

- [ ] **Step 6: Write atp-evaluator-refactoring.libretto**

```prose
# ATP Evaluator Refactoring Analysis
# Dependency chain: research -> extract interface -> propose refactoring

agent analyst:
  model: sonnet
  prompt: "You are a Python code architecture analyst. Focus on design patterns and abstractions."

let survey = session: analyst
  prompt: "Read the evaluator implementations in ../atp-platform/packages/atp-core/. List all evaluator classes, their base classes, and the methods each one implements. Focus on the evaluate() method signatures."

let interface = session: analyst
  prompt: "Based on the survey, extract the common interface shared by all evaluators. Identify: required methods, optional methods, shared parameters, return types."
  context: survey

output refactoring = session: analyst
  prompt: "Propose a refactoring plan: define an ideal base class that captures the common interface, list which evaluators would need changes, and estimate the impact of each change."
  context: { survey, interface }
```

Save to `evaluation/phase2/atp-evaluator-refactoring.libretto`.

- [ ] **Step 7: Run atp-evaluator-refactoring.libretto**

```
libretto run evaluation/phase2/atp-evaluator-refactoring.libretto
```

Inspect `bindings/survey.md`, `bindings/interface.md`, `bindings/refactoring.md`. Check: Does each binding contain substantive content? Does `context: { survey, interface }` actually pass both?

- [ ] **Step 8: Write atp-module-review.libretto**

```prose
# ATP Module Review — Reusable Block Pattern
# Tests block reusability: same review block applied to different packages

agent reviewer:
  model: sonnet
  prompt: "You are a code quality reviewer. Be concise and specific."

block review-module(package_path, package_name):
  let analysis = session: reviewer
    prompt: "Review the code in {package_path}. Assess: code organization, naming conventions, test coverage, error handling, and documentation quality. Rate each aspect 1-10."

  output result = session: reviewer
    prompt: "Write a one-paragraph summary of {package_name} quality with the top 3 improvement recommendations."
    context: analysis

do review-module("../atp-platform/packages/atp-core", "atp-core")
do review-module("../atp-platform/packages/atp-adapters", "atp-adapters")
do review-module("../atp-platform/packages/atp-sdk", "atp-sdk")

output summary = session: reviewer
  prompt: "Compare the three package reviews and identify cross-cutting concerns."
  context: { result }
```

Save to `evaluation/phase2/atp-module-review.libretto`.

- [ ] **Step 9: Run atp-module-review.libretto**

```
libretto run evaluation/phase2/atp-module-review.libretto
```

Key check: Does the block execute 3 times with different arguments? Are bindings scoped per invocation (look for `result__<execution_id>.md` files)?

- [ ] **Step 10: Write baseline-prompts.md, run baselines, record results**

```markdown
# Phase 2 Baseline Prompts

## Task 1: Evaluator Refactoring
"Read the evaluator implementations in ../atp-platform/packages/atp-core/. List all evaluator classes and their interfaces. Then extract the common interface. Finally, propose a refactoring plan with an ideal base class."

## Task 2: Module Review (x3)
"Review code quality in ../atp-platform/packages/atp-core/: organization, naming, test coverage, error handling, docs. Rate 1-10 each. Then do the same for atp-adapters and atp-sdk. Finally, compare all three."
```

Run baselines. Fill in `evaluation/results/phase-2.md`.

- [ ] **Step 11: Commit Phase 2**

```bash
git add evaluation/phase2/ evaluation/results/phase-2.md
git commit -m "evaluation: Phase 2 — variables, context, composition results"
```

---

## Task 3: Phase 3 — Parallelism

**Files:**
- Create: `evaluation/phase3/atp-workspace-fanout.libretto`
- Create: `evaluation/phase3/atp-multi-audit.libretto`
- Create: `evaluation/phase3/baseline-prompts.md`
- Create: `evaluation/results/phase-3.md`

### Part A: Run built-in examples

- [ ] **Step 1: Run parallel-reviews**

```
libretto run examples/16-parallel-reviews.libretto
```

- [ ] **Step 2: Run parallel-research**

```
libretto run examples/17-parallel-research.libretto
```

Check: Were 3 Task calls dispatched concurrently (look at state.md timestamps)?

- [ ] **Step 3: Run advanced-parallel**

```
libretto run examples/19-advanced-parallel.libretto
```

Check: Does `on-fail: "continue"` work when a branch fails?

- [ ] **Step 4: Record built-in results**

### Part B: Write and run custom .libretto

- [ ] **Step 5: Create phase3 directory**

```bash
mkdir -p evaluation/phase3
```

- [ ] **Step 6: Write atp-workspace-fanout.libretto**

```prose
# ATP Workspace Fan-Out Review
# Parallel analysis of all 4 workspace packages, then synthesis

agent reviewer:
  model: sonnet
  prompt: "You are a code reviewer focused on architecture and quality."

parallel:
  core = session: reviewer
    prompt: "Review ../atp-platform/packages/atp-core/. Summarize: purpose, key modules, code quality, test coverage. Keep to 200 words."
  adapters = session: reviewer
    prompt: "Review ../atp-platform/packages/atp-adapters/. Summarize: purpose, adapter count, shared patterns, quality. Keep to 200 words."
  dashboard = session: reviewer
    prompt: "Review ../atp-platform/packages/atp-dashboard/. Summarize: purpose, UI approach, API integration, quality. Keep to 200 words."
  sdk = session: reviewer
    prompt: "Review ../atp-platform/packages/atp-sdk/. Summarize: purpose, public API surface, documentation, quality. Keep to 200 words."

output synthesis = session: reviewer
  prompt: "Synthesize the four package reviews into a unified workspace health report. Identify: strongest package, weakest package, shared issues, and top 3 cross-cutting recommendations."
  context: { core, adapters, dashboard, sdk }
```

Save to `evaluation/phase3/atp-workspace-fanout.libretto`.

- [ ] **Step 7: Run atp-workspace-fanout.libretto**

```
libretto run evaluation/phase3/atp-workspace-fanout.libretto
```

Measure: wall-clock time. Check state.md to see if parallel branches ran concurrently. Verify all 4 bindings exist before synthesis runs.

- [ ] **Step 8: Write atp-multi-audit.libretto**

```prose
# ATP Multi-Aspect Audit
# Parallel security + performance + code quality on one module

agent security-auditor:
  model: sonnet
  prompt: "You are a security specialist. Find vulnerabilities, injection risks, auth issues."

agent perf-analyst:
  model: sonnet
  prompt: "You are a performance engineer. Find bottlenecks, N+1 queries, memory issues."

agent quality-reviewer:
  model: sonnet
  prompt: "You are a code quality expert. Find DRY violations, complexity issues, missing tests."

parallel (on-fail: "continue"):
  security = session: security-auditor
    prompt: "Audit ../atp-platform/packages/atp-core/ for security issues. Focus on: input validation, auth checks, SQL injection, path traversal. List findings with severity (critical/high/medium/low)."
  performance = session: perf-analyst
    prompt: "Analyze ../atp-platform/packages/atp-core/ for performance issues. Focus on: database queries, caching opportunities, async patterns, resource cleanup. List findings with impact (high/medium/low)."
  quality = session: quality-reviewer
    prompt: "Review ../atp-platform/packages/atp-core/ for code quality. Focus on: DRY violations, cyclomatic complexity, test coverage gaps, documentation. List findings with priority."

output report = session: quality-reviewer
  prompt: "Combine all three audit perspectives into a unified report. Group by file/module. Prioritize: security-critical first, then performance, then quality."
  context: { security, performance, quality }
```

Save to `evaluation/phase3/atp-multi-audit.libretto`.

- [ ] **Step 9: Run atp-multi-audit.libretto**

```
libretto run evaluation/phase3/atp-multi-audit.libretto
```

Check: Does `on-fail: "continue"` allow the report to generate even if one auditor fails?

- [ ] **Step 10: Run baselines and record results**

Baseline: run the same 4-package review as a single sequential prompt. Time it. Compare quality.

Fill in `evaluation/results/phase-3.md`. Key metric: parallel .libretto time vs sequential baseline time.

- [ ] **Step 11: Commit Phase 3**

```bash
git add evaluation/phase3/ evaluation/results/phase-3.md
git commit -m "evaluation: Phase 3 — parallelism results"
```

---

## Task 4: Phase 4 — Control Flow

**Files:**
- Create: `evaluation/phase4/atp-iterative-refactor.libretto`
- Create: `evaluation/phase4/atp-conditional-pipeline.libretto`
- Create: `evaluation/phase4/baseline-prompts.md`
- Create: `evaluation/results/phase-4.md`

### Part A: Run built-in examples

- [ ] **Step 1: Run fixed-loops**

```
libretto run examples/20-fixed-loops.libretto
```

Check: Does `repeat 3` create exactly 3 sessions? Does `for-each` iterate correctly?

- [ ] **Step 2: Run error-handling**

```
libretto run examples/22-error-handling.libretto
```

Check: Does `try/catch` spawn a different subagent on failure? Does `throw` propagate?

- [ ] **Step 3: Run conditionals**

```
libretto run examples/25-conditionals.libretto
```

Check: How does the VM evaluate `**condition**` — does it use LLM judgment? Is the branch choice reasonable?

- [ ] **Step 4: Record built-in results**

### Part B: Write and run custom .libretto

- [ ] **Step 5: Create phase4 directory**

```bash
mkdir -p evaluation/phase4
```

- [ ] **Step 6: Write atp-iterative-refactor.libretto**

```prose
# ATP Iterative Refactoring
# Loop with error handling: find smell, fix, test, retry if needed

agent detector:
  model: sonnet
  prompt: "You find code smells. Be specific: file path, line number, smell type."

agent fixer:
  model: sonnet
  prompt: "You fix code smells with minimal, targeted changes. Show exact diffs."

agent tester:
  model: sonnet
  prompt: "You verify code changes by reading tests and checking logic."

let smell = session: detector
  prompt: "Find the single worst code smell in ../atp-platform/packages/atp-core/src/. Return: file path, line range, smell type, why it's bad."

repeat 2:
  try:
    let fix = session: fixer
      prompt: "Fix this code smell with a minimal change. Show the exact diff."
      context: smell

    let verification = session: tester
      prompt: "Verify this fix: does it preserve behavior? Could it break anything? Check if related tests would still pass."
      context: { smell, fix }

    if **verification found problems**:
      # NOTE (2026-07-16, Phase 0): bare reassignment — a second
      # `let smell` here violated the flat-namespace rule (E019)
      smell = session: detector
        prompt: "The previous fix had problems. Find a different approach to fix the same smell."
        context: { smell, fix, verification }
    else:
      output result = fix
  catch as err:
    session "Log the error and continue to next iteration"
      context: err
```

Save to `evaluation/phase4/atp-iterative-refactor.libretto`.

- [ ] **Step 7: Run atp-iterative-refactor.libretto**

```
libretto run evaluation/phase4/atp-iterative-refactor.libretto
```

Key checks:
- Does `repeat 2` run 2 iterations?
- Does `if **verification found problems**` make a reasonable judgment call?
- Does `try/catch` activate if a subagent fails?
- Does the loop terminate early when `output result = fix` is reached?

- [ ] **Step 8: Write atp-conditional-pipeline.libretto**

```prose
# ATP Conditional Pipeline
# Different actions based on module analysis results

agent analyst:
  model: sonnet
  prompt: "You analyze Python code quality. Be quantitative where possible."

agent test-writer:
  model: sonnet
  prompt: "You write pytest tests. Follow existing test patterns in the project."

agent bug-hunter:
  model: sonnet
  prompt: "You find bugs through careful code reading. Focus on edge cases and error paths."

let analysis = session: analyst
  prompt: "Analyze ../atp-platform/packages/atp-core/src/. Estimate test coverage percentage. List modules with poorest coverage."

# NOTE (2026-07-16, Phase 0): declare-once + reassign — `output result` in
# every branch was a duplicate declaration (E019/E024)
let triage = ""
if **test coverage appears below 60%**:
  triage = session: test-writer
    prompt: "Write 3 new test cases for the least-covered module identified in the analysis."
    context: analysis
elif **test coverage is between 60-80%**:
  triage = session: bug-hunter
    prompt: "The code has moderate coverage. Look for bugs in edge cases that existing tests might miss."
    context: analysis
else:
  triage = session: analyst
    prompt: "Coverage looks good. Identify the top 3 opportunities for improving code quality beyond testing."
    context: analysis

output result = triage
```

Save to `evaluation/phase4/atp-conditional-pipeline.libretto`.

- [ ] **Step 9: Run atp-conditional-pipeline.libretto**

```
libretto run evaluation/phase4/atp-conditional-pipeline.libretto
```

Check: Which branch was taken? Was the LLM's condition evaluation reasonable given the actual state of atp-platform?

- [ ] **Step 10: Run baselines and record results**

Baseline: describe the same iterative logic in a plain prompt. Compare: does the .libretto structure produce more reliable branching?

Fill in `evaluation/results/phase-4.md`. **Key finding:** Does formal control flow in .libretto add reliability over natural language instructions?

- [ ] **Step 11: Commit Phase 4**

```bash
git add evaluation/phase4/ evaluation/results/phase-4.md
git commit -m "evaluation: Phase 4 — control flow results"
```

---

## Task 5: Phase 5 — Captain's Chair + RLM

**Files:**
- Create: `evaluation/phase5/atp-docstring-evaluator.libretto`
- Create: `evaluation/phase5/atp-architecture-doc.libretto`
- Create: `evaluation/phase5/baseline-prompts.md`
- Create: `evaluation/results/phase-5.md`

### Part A: Run built-in examples

- [ ] **Step 1: Run captains-chair-simple**

```
libretto run examples/30-captains-chair-simple.libretto
```

This requires an `input task`. The VM should prompt for it. Provide: "Review the test infrastructure in ../atp-platform"

Check: Does captain plan before executor acts? Does critic actually find issues?

- [ ] **Step 2: Run rlm-self-refine**

```
libretto run examples/40-rlm-self-refine.libretto
```

Provide inputs: artifact = "A brief explanation of the atp-platform architecture", criteria = "Technical accuracy, completeness, clarity"

Check: Does the recursive block actually recurse? Does it terminate on score >= 85 or depth 0?

- [ ] **Step 3: Record built-in results**

### Part B: Write and run custom .libretto

- [ ] **Step 4: Create phase5 directory**

```bash
mkdir -p evaluation/phase5
```

- [ ] **Step 5: Write atp-docstring-evaluator.libretto**

This is the full Captain's Chair pattern applied to a real feature task.

```prose
# ATP Docstring Evaluator — Captain's Chair Pattern
# Build a new evaluator for atp-platform that checks Python docstrings

input task: "Add a DocstringEvaluator to atp-platform that evaluates whether agent outputs include proper Python docstrings in any generated code"
input codebase: "../atp-platform"

agent captain:
  model: opus
  prompt: """You are a senior engineering manager. You NEVER write code directly.
Break down tasks, dispatch to specialists, validate results.
Focus on: what context each specialist needs, what can run in parallel."""

agent researcher:
  model: sonnet
  prompt: "You are a research specialist. Find specific code patterns quickly. Cite file paths and line numbers."

agent coder:
  model: sonnet
  prompt: "You are an expert Python engineer. Write clean, idiomatic code following existing patterns."

agent critic:
  model: sonnet
  prompt: "You are a code reviewer. Find logic errors, missing edge cases, and deviations from project conventions."

agent tester:
  model: sonnet
  prompt: "You are a QA engineer. Write comprehensive pytest tests with edge cases."

# Phase 1: Research
parallel:
  evaluators = session: researcher
    prompt: "Find all evaluator implementations in {codebase}/packages/atp-core/. List their base class, evaluate() signature, and how they're registered."
  tests = session: researcher
    prompt: "Find all evaluator test files in {codebase}. Show the test patterns: fixtures used, how evaluators are instantiated, assertion patterns."

# Phase 2: Plan
let plan = session: captain
  prompt: """Create an implementation plan for the DocstringEvaluator based on research.
Specify: file to create, class structure, evaluate() implementation, test file, test cases.
Follow existing evaluator patterns exactly."""
  context: { evaluators, tests }

# Phase 3: Implement + Review
let implementation = session: coder
  prompt: "Implement the DocstringEvaluator according to the plan. Write the complete file."
  context: { plan, evaluators }

let review = session: critic
  prompt: "Review the implementation. Check: follows base class interface, handles edge cases (no code in output, empty docstrings, partial docstrings), matches project conventions."
  context: { implementation, evaluators }

# NOTE (2026-07-16, Phase 0): declare-once + reassign — dual `let final_code`
# in both branches violated the flat-namespace rule; found in Phase 5
# (see evaluation/results/phase-5.md)
let final_code = implementation
if **review found critical issues**:
  let fixed = session: coder
    prompt: "Fix the critical issues identified in the review."
    context: { implementation, review }
  final_code = fixed

# Phase 4: Test
let test_code = session: tester
  prompt: "Write pytest tests for the DocstringEvaluator. Cover: code with good docstrings (pass), code with missing docstrings (fail), code with partial docstrings, non-code output (skip). Follow existing test patterns."
  context: { final_code, tests }

# Phase 5: Integration summary
output result = session: captain
  prompt: "Summarize: what was built, where files go, how to integrate, any remaining items."
  context: { final_code, test_code, review }
```

Save to `evaluation/phase5/atp-docstring-evaluator.libretto`.

- [ ] **Step 6: Run atp-docstring-evaluator.libretto**

```
libretto run evaluation/phase5/atp-docstring-evaluator.libretto
```

This is the most complex run yet. Check:
- Does captain stay in coordinator role (no code writing)?
- Do researchers find actual evaluator patterns in atp-platform?
- Does the parallel research block dispatch concurrently?
- Is the review meaningful (catches real issues)?
- Does the conditional revision work?

- [ ] **Step 7: Write atp-architecture-doc.libretto**

```prose
# ATP Architecture Document — RLM Self-Refine
# Recursively improve an architecture document until quality threshold

input target: "../atp-platform"

agent writer:
  model: opus
  prompt: "You write clear, accurate technical architecture documents."

agent evaluator:
  model: sonnet
  prompt: "Score documents 0-100 on: technical accuracy, completeness, clarity, actionability. List specific issues."

block refine(doc, depth):
  if depth <= 0:
    output doc

  let eval = session: evaluator
    prompt: "Evaluate this architecture document. Score 0-100. List the top 3 specific issues to fix."
    context: doc

  if **score >= 80**:
    output doc

  let improved = session: writer
    prompt: "Improve the document by addressing the specific issues identified. Keep what works. Only fix what was flagged."
    context: { document: doc, evaluation: eval }

  output do refine(improved, depth - 1)

let draft = session: writer
  prompt: "Write an architecture document for {target}. Cover: project purpose, package structure, data flow, key abstractions, deployment model. Read the actual code — don't guess."

output final = do refine(draft, 3)
```

Save to `evaluation/phase5/atp-architecture-doc.libretto`.

- [ ] **Step 8: Run atp-architecture-doc.libretto**

```
libretto run evaluation/phase5/atp-architecture-doc.libretto
```

Check: How many refinement iterations occurred? Did quality actually improve across iterations? Did it converge or oscillate?

- [ ] **Step 9: Run baselines and record results**

Baseline for docstring evaluator: "Add a DocstringEvaluator to atp-platform. Research existing evaluators first, then implement following their patterns, then write tests."

Baseline for architecture doc: "Write an architecture document for ../atp-platform."

Compare: Does the Captain's Chair pattern produce better code than plain Claude Code? Does RLM self-refine produce a better document than a single-shot prompt?

Fill in `evaluation/results/phase-5.md`.

- [ ] **Step 10: Commit Phase 5**

```bash
git add evaluation/phase5/ evaluation/results/phase-5.md
git commit -m "evaluation: Phase 5 — Captain's Chair and RLM results"
```

---

## Task 6: Phase 6 — Alternative Syntaxes

**Files:**
- Create: `evaluation/phase6/atp-docstring-borges.libretto`
- Create: `evaluation/phase6/atp-docstring-kafka.libretto`
- Create: `evaluation/phase6/atp-docstring-homer.libretto`
- Create: `evaluation/phase6/syntax-comparison.md`
- Create: `evaluation/results/phase-6.md`

**Prerequisite:** Phase 5 completed (the functional syntax version is the baseline).

### Keyword reference for translation

| Functional | Borges | Kafka | Homer |
|-----------|--------|-------|-------|
| `agent` | `dreamer` | `clerk` | `hero` |
| `session` | `dream` | `proceeding` | `trial` |
| `parallel` | `forking` | `departments` | `host` |
| `block` | `chapter` | `regulation` | `book` |
| `input` | `axiom` | `petition` | `omen` |
| `output` | `theorem` | `verdict` | `glory` |
| `let` | `inscribe` | `file` | `decree` |
| `const` | `zahir` | `statute` | `fate` |
| `context` | `memory` | `dossier` | `tidings` |
| `if` | `if` | `if` | `if` |
| `do` | `recite` | `invoke` | `summon` |

- [ ] **Step 1: Create phase6 directory**

```bash
mkdir -p evaluation/phase6
```

- [ ] **Step 2: Write atp-docstring-borges.libretto**

Translate the Captain's Chair program from Phase 5 into Borges register. The logic stays identical — only keywords change. Also load the Borges register: the VM needs `alts/borges.md` loaded alongside `libretto.md`.

```prose
# ATP Docstring Evaluator — Borges Register
# The same Captain's Chair, dreamed through labyrinths

axiom task: "Add a DocstringEvaluator to atp-platform that evaluates whether agent outputs include proper Python docstrings in any generated code"
axiom codebase: "../atp-platform"

dreamer captain:
  model: opus
  prompt: """You are a senior engineering manager. You NEVER write code directly.
Break down tasks, dispatch to specialists, validate results."""

dreamer researcher:
  model: sonnet
  prompt: "You are a research specialist. Find specific code patterns quickly."

dreamer coder:
  model: sonnet
  prompt: "You are an expert Python engineer. Write clean, idiomatic code."

dreamer critic:
  model: sonnet
  prompt: "You are a code reviewer. Find logic errors and missing edge cases."

dreamer tester:
  model: sonnet
  prompt: "You are a QA engineer. Write comprehensive pytest tests."

forking:
  evaluators = dream: researcher
    prompt: "Find all evaluator implementations in {codebase}/packages/atp-core/."
  tests = dream: researcher
    prompt: "Find all evaluator test files in {codebase}."

inscribe plan = dream: captain
  prompt: "Create an implementation plan for the DocstringEvaluator."
  memory: { evaluators, tests }

inscribe implementation = dream: coder
  prompt: "Implement the DocstringEvaluator according to the plan."
  memory: { plan, evaluators }

inscribe review = dream: critic
  prompt: "Review the implementation for issues."
  memory: { implementation, evaluators }

if **review found critical issues**:
  inscribe final_code = dream: coder
    prompt: "Fix the critical issues."
    memory: { implementation, review }
else:
  inscribe final_code = implementation

inscribe test_code = dream: tester
  prompt: "Write pytest tests for the DocstringEvaluator."
  memory: { final_code, tests }

theorem result = dream: captain
  prompt: "Summarize what was built and how to integrate."
  memory: { final_code, test_code, review }
```

Save to `evaluation/phase6/atp-docstring-borges.libretto`.

- [ ] **Step 3: Run with Borges register**

Tell the VM to load the Borges register:
```
libretto run evaluation/phase6/atp-docstring-borges.libretto
```

Note: you may need to tell the VM to load `alts/borges.md` for keyword translation. If the VM doesn't recognize Borges keywords natively, load the register file first.

- [ ] **Step 4: Write atp-docstring-kafka.libretto**

Same translation using Kafka keywords:

```prose
# ATP Docstring Evaluator — Kafka Register
# The same proceeding, filed through the apparatus

petition task: "Add a DocstringEvaluator to atp-platform"
petition codebase: "../atp-platform"

clerk captain:
  model: opus
  prompt: """You are a senior engineering manager. You NEVER write code directly."""

clerk researcher:
  model: sonnet
  prompt: "You are a research specialist."

clerk coder:
  model: sonnet
  prompt: "You are an expert Python engineer."

clerk critic:
  model: sonnet
  prompt: "You are a code reviewer."

clerk tester:
  model: sonnet
  prompt: "You are a QA engineer."

departments:
  evaluators = proceeding: researcher
    prompt: "Find all evaluator implementations in {codebase}/packages/atp-core/."
  tests = proceeding: researcher
    prompt: "Find all evaluator test files in {codebase}."

file plan = proceeding: captain
  prompt: "Create an implementation plan for the DocstringEvaluator."
  dossier: { evaluators, tests }

file implementation = proceeding: coder
  prompt: "Implement the DocstringEvaluator."
  dossier: { plan, evaluators }

file review = proceeding: critic
  prompt: "Review the implementation."
  dossier: { implementation, evaluators }

if **review found critical issues**:
  file final_code = proceeding: coder
    prompt: "Fix the critical issues."
    dossier: { implementation, review }
else:
  file final_code = implementation

file test_code = proceeding: tester
  prompt: "Write pytest tests."
  dossier: { final_code, tests }

verdict result = proceeding: captain
  prompt: "Summarize what was built."
  dossier: { final_code, test_code, review }
```

Save to `evaluation/phase6/atp-docstring-kafka.libretto`.

- [ ] **Step 5: Run with Kafka register**

```
libretto run evaluation/phase6/atp-docstring-kafka.libretto
```

- [ ] **Step 6: Write atp-docstring-homer.libretto**

Same translation using Homer keywords:

```prose
# ATP Docstring Evaluator — Homeric Register
# The same trial, undertaken by heroes

omen task: "Add a DocstringEvaluator to atp-platform"
omen codebase: "../atp-platform"

hero captain:
  model: opus
  prompt: """You are a senior engineering manager. You NEVER write code directly."""

hero researcher:
  model: sonnet
  prompt: "You are a research specialist."

hero coder:
  model: sonnet
  prompt: "You are an expert Python engineer."

hero critic:
  model: sonnet
  prompt: "You are a code reviewer."

hero tester:
  model: sonnet
  prompt: "You are a QA engineer."

host:
  evaluators = trial: researcher
    prompt: "Find all evaluator implementations in {codebase}/packages/atp-core/."
  tests = trial: researcher
    prompt: "Find all evaluator test files in {codebase}."

decree plan = trial: captain
  prompt: "Create an implementation plan for the DocstringEvaluator."
  tidings: { evaluators, tests }

decree implementation = trial: coder
  prompt: "Implement the DocstringEvaluator."
  tidings: { plan, evaluators }

decree review = trial: critic
  prompt: "Review the implementation."
  tidings: { implementation, evaluators }

if **review found critical issues**:
  decree final_code = trial: coder
    prompt: "Fix the critical issues."
    tidings: { implementation, review }
else:
  decree final_code = implementation

decree test_code = trial: tester
  prompt: "Write pytest tests."
  tidings: { final_code, tests }

glory result = trial: captain
  prompt: "Summarize what was built."
  tidings: { final_code, test_code, review }
```

Save to `evaluation/phase6/atp-docstring-homer.libretto`.

- [ ] **Step 7: Run with Homer register**

```
libretto run evaluation/phase6/atp-docstring-homer.libretto
```

- [ ] **Step 8: Write syntax-comparison.md**

After all 4 runs (functional from Phase 5 + 3 alternative syntaxes), create a comparison:

```markdown
# Syntax Comparison — Docstring Evaluator

## Runs

| Syntax | Run ID | Completed? | Steps executed | Approx tokens |
|--------|--------|-----------|----------------|---------------|
| Functional | ... | ... | ... | ... |
| Borges | ... | ... | ... | ... |
| Kafka | ... | ... | ... | ... |
| Homer | ... | ... | ... | ... |

## Output Quality Comparison

| Aspect | Functional | Borges | Kafka | Homer |
|--------|-----------|--------|-------|-------|
| Code correctness | /10 | /10 | /10 | /10 |
| Test coverage | /10 | /10 | /10 | /10 |
| Plan quality | /10 | /10 | /10 | /10 |

## Subagent Communication Style

Did the keyword framing affect how subagents communicated?
[observations here]

## Verdict

[Does syntax choice matter for practical use?]
```

Save to `evaluation/phase6/syntax-comparison.md`.

- [ ] **Step 9: Record results and commit**

Fill in `evaluation/results/phase-6.md`.

```bash
git add evaluation/phase6/ evaluation/results/phase-6.md
git commit -m "evaluation: Phase 6 — alternative syntax experiment results"
```

---

## Task 7: Phase 7 — Stdlib and Meta-Analysis

**Files:**
- Create: `evaluation/results/phase-7.md`
- Create: `evaluation/results/final-verdict.md`

**Prerequisite:** Phases 1-5 completed (runs exist in `.libretto/runs/` to analyze).

- [ ] **Step 1: Run inspector on a Phase 5 run**

Find the Captain's Chair run from Phase 5:

```bash
ls .libretto/runs/
```

Pick the run from `atp-docstring-evaluator.libretto`. Then:

```
libretto run lib/inspector.libretto
```

When prompted for inputs:
- `run_path`: the path to the Phase 5 Captain's Chair run
- `depth`: "deep"
- `target`: "all"

Check: Does the inspector produce meaningful fidelity scores? Does it detect any VM issues we missed?

- [ ] **Step 2: Run cost-analyzer on Phase 5 run**

```
libretto run lib/cost-analyzer.libretto
```

(Provide the same run_path.) Check: Does it break down cost per session? Can we see the orchestration overhead?

- [ ] **Step 3: Run program-improver on a custom program**

```
libretto run lib/program-improver.libretto
```

Target: `evaluation/phase3/atp-workspace-fanout.libretto` (or another custom program).

Check: Does it suggest real improvements? Are the suggestions applicable?

- [ ] **Step 4: Record Phase 7 results**

Fill in `evaluation/results/phase-7.md`. Key question: Does the self-improvement loop produce actionable insights?

- [ ] **Step 5: Write final-verdict.md**

Synthesize findings from all 7 phases:

```markdown
# Libretto Evaluation — Final Verdict

## Summary Table

| Phase | Feature | .libretto vs Baseline | Key Finding |
|-------|---------|-------------------|-------------|
| 1 | Sequential | ... | ... |
| 2 | Variables/Blocks | ... | ... |
| 3 | Parallelism | ... | ... |
| 4 | Control Flow | ... | ... |
| 5 | Orchestration | ... | ... |
| 6 | Alt Syntaxes | ... | ... |
| 7 | Stdlib/Meta | ... | ... |

## Verdict

Is Libretto practically useful, or is the concept more interesting than its execution?

### Strengths
- ...

### Weaknesses
- ...

### When to use Libretto
- ...

### When NOT to use Libretto
- ...

## Recommendations
- ...
```

- [ ] **Step 6: Commit Phase 7 and final verdict**

```bash
git add evaluation/results/phase-7.md evaluation/results/final-verdict.md
git commit -m "evaluation: Phase 7 — stdlib meta-analysis and final verdict"
```

---

## Dependencies

```
Task 1 (Phase 1)
  -> Task 2 (Phase 2)
    -> Task 3 (Phase 3)
      -> Task 4 (Phase 4)
        -> Task 5 (Phase 5)
          -> Task 6 (Phase 6)  [independent of Task 7]
          -> Task 7 (Phase 7)  [independent of Task 6]
```

Tasks 6 and 7 can run in parallel after Task 5 completes.
