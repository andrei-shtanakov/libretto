# Baseline: Conditional Pipeline (plain prompt, single session, NL branching)

- Model: sonnet, general-purpose agent, no OpenProse VM
- Cost: 91.6K tokens, 16 tool calls, 147s wall time
- Coverage found: **88%** | Branch taken: **>80% → top-3 quality opportunities**
- Prompt: see baseline-prompts.md, Task 2

## Key observation

Same measured coverage (88%) and same branch selection (>80% → quality) as the
.prose `atp-conditional-pipeline` run. The NL-expressed branch condition ("if
below 60%… if 60-80%… if above 80%…") resolved identically to the formal
`if/elif/else` discretion in the .prose version — both grounded the decision in
a real `pytest --cov` run, not a guess. On this task, formal control flow added
no branch-selection reliability over the natural-language conditional: both got
it right because both measured first.

Notably the baseline independently surfaced a real bug (EvalResult.merge/
aggregate silently drop the `critical` flag) that corroborates the "critical
flag gap" finding from Phase 2's evaluator analysis.

## Output

### Coverage Analysis: `atp-core`

**Result: 88% line coverage** (3,772 statements, 458 missed) across `atp/{chaos,core,cost,loader,model_catalog,protocol,scoring,statistics,streaming}`. Per-module (lowest first): `cost/tracker.py` 22%, `cost/models.py` 51%, `core/telemetry.py` 72%, `core/results.py` 75%, `core/logging.py` 85%, `core/security.py` 90%, rest 88–100%. (22 telemetry/settings/metrics tests failed — global-state pollution across test order, not coverage gaps; coverage.py still records line execution on assertion failure.)

**Branch taken: >80% → top-3 code-quality opportunities beyond testing.**

### 1. `EvalResult.merge()` / `EvalResult.aggregate()` silently drop the `critical` flag — likely a real bug
`results.py:110-125`: neither `merge` nor `aggregate` constructs the new instance with `critical=...`, so it defaults to `False`. `scoring/aggregator.py:437` reads `r.critical` to force a hard 0-score gate. Any path that merges/aggregates before scoring loses the critical-gate semantics the class docstring promises. Not caught by the one existing merge test. Fix: thread `critical=self.critical or other.critical` through `merge`, `any(r.critical for r in results)` through `aggregate`.

### 2. `cost/models.py`: pricing table hardcoded as ~180 lines of repetitive dataclass literals
`PricingConfig.default()` (lines 73-262) hand-codes ~30 `ModelPricing(...)` entries, commented "based on public pricing as of early 2026" — a data table masquerading as code, duplicating responsibility with the LiteLLM-backed `cost/cloud_pricer.py`. The repo already loads pricing from TOML in `model_catalog/`; moving this table to a data file would cut ~180 lines and unify the two pricing sources of truth.

### 3. `core/security.py` is a 1,550-line multi-concern module — split by concern
Spans request/size/depth validation, path traversal, URL/SSRF, Docker validation, secret redaction, command validation, and log sanitization in one file. Violates the project's own "focused and small" principle; splitting into `security/{network,container,redaction,validation}.py` would make each independently testable and likely explains the lagging coverage on this file and telemetry.py.
