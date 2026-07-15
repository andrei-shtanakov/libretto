# Baseline: Docstring Evaluator (single session vs Captain's Chair)

- Model: sonnet, general-purpose agent, no OpenProse VM
- Cost: 157.8K tokens, 63 tool calls, 657s wall time (11 min)
- Prompt: see baseline-prompts.md, Task 1
- Proposal-only; verified `git status` clean in atp-platform afterwards

## Key observations

1. **The single session delivered the full pipeline alone**: researched existing
   evaluator patterns, designed, implemented, wired the registry, wrote 21
   tests — and **actually executed them**: it built a `sys.modules` injection
   shim in the scratchpad (never touching the repo) and ran the real
   atp-platform `.venv` interpreter, real pydantic models, and ruff against its
   own code, iterating until 21/21 passed and ruff was clean.
2. **Self-verification here was execution-grounded, not self-grading.** Unlike
   Phase 4's baseline (where the author *judged* its own fix), this baseline
   validated against an external oracle (pytest/ruff). That neutralizes much of
   the fixer≠verifier advantage the Captain's Chair had — when the task's
   correctness is machine-checkable, a single session with test execution
   reaches verification quality close to an independent critic.
3. **What it did NOT have**: an adversarial reviewer hunting for semantic
   gaps. The .prose critic found the empty-docstring bug by *thinking* about
   edge cases and then proving it live; the baseline covered placeholder
   docstrings via its own `min_docstring_length` design choice — the same
   class of issue, prevented by design rather than caught by review. Honest
   verdict: comparable quality via different mechanisms.

## Design summary (as delivered)

- `atp/evaluators/docstring.py`: AST-based `DocstringEvaluator` following the
  single-file convention (like `style.py`), scanning both whole-file `.py`
  artifacts (path glob or content-type) and fenced ```python blocks in any
  artifact text — including string leaves of `ArtifactStructured.data`
  (joined rather than `json.dumps`-ed, to preserve real newlines for the fence
  regex — a subtle correctness point).
- Pydantic `DocstringConfig`: require module/class/function docstrings,
  `min_docstring_length` (placeholder detection — covers the empty-docstring
  case), `exclude_private`/`exclude_dunder`, `check_code_blocks`,
  `file_patterns`, `min_coverage` threshold, `require_code_present`,
  `ignore_syntax_errors`.
- Emits one graded `EvalCheck` (`docstring_coverage`, score = coverage) with a
  `details` dict listing missing constructs — matches the platform's graded-
  check idiom.
- Registry wiring: `register("docstring", ...)` + assertion mapping; exports
  added to `atp/evaluators/__init__.py`.
- `tests/unit/evaluators/test_docstring.py`: 21 tests across 9 classes
  (properties, no-code vacuous/required, file artifacts incl. content-type
  detection, fenced blocks, structured artifacts, exclusions, module
  docstrings, min-length placeholders, syntax errors, config defaults) — all
  passing against the real `.venv`.

The complete proposed files live in the baseline agent's scratchpad output
(`docstring_proposal/`: `docstring.py`, `test_docstring.py`, `conftest.py`
shim); the full text is reproduced in the run transcript. Not vendored here to
keep the evaluation record readable — the comparison verdict is what matters.

## Comparison hook

See phase-5.md, Baseline Comparison — the Captain's Chair (.prose) version of
this same task cost ~717K tokens across 8 sessions; this baseline cost 158K in
one. Both produced complete, validated proposals of comparable quality.
