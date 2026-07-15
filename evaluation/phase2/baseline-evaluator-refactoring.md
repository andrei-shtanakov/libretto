# Baseline: Evaluator Refactoring (plain prompt, single session)

- Model: sonnet, general-purpose agent, no OpenProse VM
- Cost: 170.1K tokens, 33 tool calls, 217s wall time
- Prompt: see baseline-prompts.md, Task 1

## Output

## Findings: Evaluator implementations in the ATP platform

**Important path correction first.** The task asked me to read evaluators in `atp-platform/packages/atp-core/`, but that package contains no evaluator code — it only holds `protocol/`, `core/`, `loader/`, `chaos/`, `cost/`, `scoring/`, `statistics/`, `streaming/` (confirmed via `find` + directory listing; `packages/atp-core/atp/` has none of these dirs). The actual evaluators live in `/Users/Andrei_Shtanakov/labs/all_ai_orchestrators/atp-platform/atp/evaluators/`, a **real directory** (not a symlink) directly inside the top-level `atp` namespace package — everything else in `atp/` that *does* belong to atp-core (`core`, `loader`, `chaos`, `cost`, `scoring`, `statistics`, `streaming`) is a symlink into `packages/atp-core/atp/...`, but `evaluators/` is not. This is confirmed by the project's own `CLAUDE.md`, component #4. I analyzed the real location since that's unambiguously what "evaluator implementations" refers to.

---

### 1. Evaluator classes and their interfaces

All concrete evaluators subclass `atp.evaluators.base.Evaluator` (ABC):

```python
class Evaluator(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    async def evaluate(self, task: TestDefinition, response: ATPResponse,
                        trace: list[ATPEvent], assertion: Assertion) -> EvalResult: ...

    def _create_check(self, name, passed, message=None, details=None) -> EvalCheck:
        # score is always 1.0 if passed else 0.0 — binary only
    def _create_result(self, checks: list[EvalCheck]) -> EvalResult:
        # evaluator=self.name; does NOT thread assertion.critical
    async def evaluate_with_tracing(...) -> EvalResult:
        # OTel span + metrics wrapper around evaluate()
```

**Registered evaluators** (`atp/evaluators/registry.py`, `EvaluatorRegistry.__init__`), 11 total:

| Class | File | `__init__` | Assertion types handled | Dispatch style |
|---|---|---|---|---|
| `ArtifactEvaluator` | `artifact.py` | none (implicit) | `artifact_exists`, `contains`, `schema`, `sections` | if/elif on `assertion.type` |
| `BehaviorEvaluator` | `behavior.py` | none | `behavior`, `must_use_tools`, `max_tool_calls`, `min_tool_calls`, `no_errors`, `forbidden_tools` (+ nested `expected_tool_calls`/`forbidden_tool_calls`) | if/elif, single-config-block variant produces multiple checks |
| `LLMJudgeEvaluator` | `llm_judge.py` | `(config: LLMJudgeConfig \| None, cost_tracker: CostTracker \| None)` — resolves provider/model from config→env→settings | `llm_eval` only | single-purpose, pydantic `LLMJudgeConfig` |
| `CodeExecEvaluator` | `code_exec.py` | `(sandbox_manager, container_runtime, container_default_image="python:3.12-slim")` | `pytest`, `npm`, `custom_command`/`code_exec`, `lint` | if/elif, subprocess-based, has its own `_create_scored_check` duplicating the base helper |
| `SecurityEvaluator` | `security/evaluator.py` | none, but builds `self._checkers = [PIIChecker(), PromptInjectionChecker(), CodeSafetyChecker(), SecretLeakChecker()]` | `security` only | delegates to internal `SecurityChecker` sub-interface (see below) |
| `FactualityEvaluator` | `factuality.py` | `(config: FactualityConfig \| None, cost_tracker)` — builds 5 collaborator objects (`ClaimExtractor`, `CitationExtractor`, `HallucinationDetector`, `GroundTruthVerifier`, `LLMFactVerifier`) | `factuality` only | single-purpose, pydantic `FactualityConfig` |
| `PerformanceEvaluator` | `performance.py` | `() -> None: pass` (explicit no-op) | `performance` only | single-purpose, pydantic `PerformanceConfig` |
| `StyleEvaluator` | `style.py` | none | `style`, `tone`, `readability`, `passive_voice`, `sentence_length`, `style_rules` | if/elif, pydantic `StyleConfig` built per-call from dict |
| `FilesystemEvaluator` | `filesystem.py` | none | `file_exists`, `file_not_exists`, `file_contains`, `dir_exists`, `file_count` | **dict-based dispatch table** (`handlers.get(assertion.type)`) — the only evaluator using this cleaner pattern |
| `CompositeEvaluator` | `composite.py` | none | `composite` (boolean `and`/`or`/`not`/`threshold` over nested conditions, recursively delegating to `registry.create_for_assertion`) | recursive, not a flat dispatch |
| `FindingsMatchEvaluator` | `findings/evaluator.py` | none | `findings_match` only | delegates entirely to `grade_findings()`; **only evaluator that manually threads `assertion.critical` into `EvalResult`** |

**Un-registered `Evaluator` subclass:**
- `GitCommitEvaluator` (`git_commit.py`) — implements the same ABC, name=`"git_commit"`, but is **not** wired into `EvaluatorRegistry`. It's a complete, working evaluator (4-dimension diff comparison) that's simply orphaned from the registration/dispatch story.

**Two adjacent-but-distinct interfaces in the same package** (not `Evaluator` subclasses — worth noting because they look similar and a refactor could accidentally conflate them):

1. `SecurityChecker` (ABC, `security/base.py`) — a **sync**, content-scanning sub-interface consumed internally by `SecurityEvaluator`:
   ```python
   class SecurityChecker(ABC):
       @property
       @abstractmethod
       def name(self) -> str: ...
       @property
       @abstractmethod
       def check_types(self) -> list[str]: ...
       @abstractmethod
       def check(self, content: str, location: str | None = None,
                  enabled_types: list[str] | None = None) -> list[SecurityFinding]: ...
   ```
   Four concrete checkers implement it: `PIIChecker`, `PromptInjectionChecker`, `CodeSafetyChecker`, `SecretLeakChecker`.

2. `checkers.registry.Checker` (`checkers/registry.py`) — a plain function type used by the newer agent-eval-case methodology:
   ```python
   Checker = Callable[[dict[str, Any], str | None], CaseVerdict]
   ```
   Registered instances: `citation_grounding_check`, `json_path` checker, a `findings_match` checker variant (`findings/checker.py`) — distinct from `FindingsMatchEvaluator` which uses `findings/matcher.py`'s `grade_findings` instead. `CaseVerdict` (in `atp/core/results.py`) is structurally close to `EvalCheck`/`EvalResult` (`critical_pass`↔`passed`, `rubric_score`↔`score`) but is a separate model.

3. `guardrails.py` — not a class hierarchy at all: three plain functions returning a `CheckResult` dataclass (`name`, `passed`, `reason`) that run *before* the evaluator pipeline to short-circuit empty/timed-out/over-budget responses. Structurally a third near-duplicate of the `(name, passed, message)` triple.

---

### 2. Common interface (what's actually shared across the 12 `Evaluator` subclasses)

- **Contract**: `name: str` (property) + `async evaluate(task, response, trace, assertion) -> EvalResult`. Every evaluator honors this exactly.
- **Result shape**: every evaluator ends by calling `self._create_result([...checks])`, itself built from one or more `self._create_check(name, passed, message, details)` calls (or, in a minority of cases, hand-rolled `EvalCheck(...)` for non-binary scores).
- **Assertion routing**: `assertion.type` is read and switched on inside `evaluate()`. 5 of 11 registered evaluators (Artifact, Behavior, CodeExec, Style, Filesystem) handle *multiple* assertion types via an internal dispatch; the rest are single-purpose.
- **Config access**: `config = assertion.config` (`dict[str, Any]`), then ad-hoc `.get(key, default)` — used untyped in Artifact/Behavior/Filesystem/CodeExec/Security/Composite; wrapped in a pydantic model in LLMJudge/Factuality/Performance/Style (inconsistently — Style rebuilds `StyleConfig(**config_dict)` per call rather than at construction).
- **Recurring duplicated logic** (same code, 3-4 independent copies):
  - Artifact lookup-by-path with `getattr(a, "path", None) or getattr(a, "name", None)) == path` fallback — duplicated in `ArtifactEvaluator`, `LLMJudgeEvaluator` (twice), `SecurityEvaluator`.
  - Artifact content extraction (`content` attr, else `json.dumps(data)`) — duplicated verbatim in `ArtifactEvaluator._get_artifact_content`, `LLMJudgeEvaluator._get_artifact_content`, `FactualityEvaluator` (same pattern), `SecurityEvaluator._get_artifact_content`.
  - "Unknown assertion type → failed check" fallback — duplicated verbatim in Artifact, Behavior, CodeExec (and a near-identical `"unknown_assertion"` variant in Style).
  - "Nothing configured → vacuous pass" checks — repeated ad hoc across Behavior, Composite, Filesystem-adjacent evaluators.
- **Registry construction gap**: `EvaluatorRegistry.create()`/`create_for_assertion()` both accept `config: dict[str, Any] | None = None` but the docstring admits it's "currently unused" — they always call `evaluator_class()` with zero args. Any evaluator that needs config or dependencies at construction time (`LLMJudgeEvaluator`, `FactualityEvaluator`, `CodeExecEvaluator`, and even `SecurityEvaluator`'s checker list) can only get non-default behavior by being instantiated manually, bypassing the registry entirely — undermining the registry's stated role as the extensibility surface (`register_assertion_mapping`'s docstring explicitly frames it as the plugin API).
- **`critical` flag gap**: `Assertion.critical: bool` exists (`atp/loader/models.py:146`, "hard gate: if this assertion fails, the test fails with score 0") and `EvalResult.critical` exists to carry it, but the base `Evaluator._create_result()` helper never sets it — only `FindingsMatchEvaluator` manually constructs `EvalResult(..., critical=assertion.critical)` instead of using the shared helper. Every other evaluator silently drops `assertion.critical`.
- **Binary-vs-graded score mismatch**: `_create_check()` only supports binary 1.0/0.0 scores, but LLMJudge, Factuality, Composite's summary check, and CodeExec all need graded (0.0–1.0) scores and each independently bypasses the helper — CodeExec even reimplements a second near-identical helper, `_create_scored_check`, purely because the base one can't take a `score` argument.

---

### 3. Refactoring plan with an ideal base class

**Target base class** (additive — no behavior change on day one):

```python
class Evaluator(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    def supported_assertion_types(self) -> frozenset[str]:
        """Default empty = evaluator doesn't opt into router-level validation
        yet. Multi-type evaluators declare their set; single-type evaluators
        can declare {self.name} or override entirely."""
        return frozenset()

    async def evaluate(self, task, response, trace, assertion) -> EvalResult:
        """Template method: unknown-type fallback + critical threading are
        handled once here instead of in every subclass."""
        if self.supported_assertion_types and assertion.type not in self.supported_assertion_types:
            return self._create_result(
                [self._create_check(f"unknown_{assertion.type}", False,
                                     f"Unknown assertion type: {assertion.type}")],
                critical=assertion.critical,
            )
        checks = await self._evaluate_checks(task, response, trace, assertion)
        return self._create_result(checks, critical=assertion.critical)

    @abstractmethod
    async def _evaluate_checks(self, task, response, trace, assertion) -> list[EvalCheck]:
        """Subclasses implement only the actual logic; unknown-type handling
        and critical-flag threading move to the base."""

    def _create_check(self, name, passed, score: float | None = None,
                       message=None, details=None) -> EvalCheck:
        """score now optional (defaults to 1.0/0.0) — kills CodeExec's
        duplicate _create_scored_check."""

    def _create_result(self, checks, critical: bool = False) -> EvalResult: ...

    def _get_artifact(self, response, path: str | None = None) -> Any | None:
        """Single implementation of the path==artifact.path/name lookup,
        replacing 3+ duplicated copies."""

    def _get_artifact_content(self, response, path: str | None = None) -> str | None:
        """Built on _get_artifact(); replaces the 4 duplicated versions in
        Artifact/LLMJudge/Factuality/Security."""

    def _vacuous_pass(self, name: str, message: str) -> EvalCheck:
        """Names the extremely common 'nothing configured → pass' shape."""
```

**Staged migration** (each phase independently shippable/testable, since 12 evaluators + the registry + call sites in `runner/` depend on this ABC):

1. **Additive helpers only** — add `_get_artifact`, `_get_artifact_content`, `_vacuous_pass`, and make `_create_check`'s `score` optional, on the existing base class. Zero behavior change; nothing is required to use them yet.
2. **Dedupe the 4 artifact-content extractors** — migrate `ArtifactEvaluator`, `LLMJudgeEvaluator`, `FactualityEvaluator`, `SecurityEvaluator` one at a time onto the shared helper, each verified against its existing test file before moving to the next.
3. **Fix the `critical` gap** — change `_create_result` to accept `critical`, update `evaluate()` in the base template (once evaluators adopt it) or, as a smaller first step, just have every evaluator pass `assertion.critical` into `_create_result` explicitly and delete `FindingsMatchEvaluator`'s one-off manual `EvalResult(...)` construction now that the shared helper covers it.
4. **Fix `EvaluatorRegistry.create()`** — give `Evaluator` (or a small `ConfiguredEvaluator` mixin) a `@classmethod from_config(cls, config, **deps) -> Self` hook with a default that just calls `cls()`, and have `LLMJudgeEvaluator`, `FactualityEvaluator`, `CodeExecEvaluator`, `SecurityEvaluator` override it. Then make `create()`/`create_for_assertion()` actually call `evaluator_class.from_config(config)` instead of `evaluator_class()`, closing the "config param is silently dropped" gap without forcing every evaluator's `__init__` signature to match.
5. **Adopt the template `evaluate()`/`supported_assertion_types`** — migrate multi-type evaluators (Artifact, Behavior, CodeExec, Style) to declare their type set and drop their hand-rolled "unknown assertion" fallback; `FilesystemEvaluator`'s existing dict-dispatch is the closest fit and should be the reference implementation for this step. Single-type evaluators (LLMJudge, Factuality, Performance, FindingsMatch, GitCommit) need only declare `{self.name}` or the one assertion string they handle.
6. **Register `GitCommitEvaluator`** — either add it to `EvaluatorRegistry` with an appropriate assertion-type mapping, or, if it's intentionally excluded (e.g. still experimental), document that explicitly in `registry.py` so it doesn't look like a dangling orphan.
7. **(Stretch, don't couple to the above)** — document the relationship between the three "evaluator-shaped" interfaces (`Evaluator`, `SecurityChecker`, `checkers.Checker`) and `guardrails.py`'s bare `CheckResult` functions. They serve genuinely different granularities (whole-assertion vs. content-scanner vs. deterministic-grader-function vs. pre-pipeline short-circuit) so merging them is not obviously correct, but the field-naming drift between `EvalCheck` (`passed`/`score`) and `CaseVerdict` (`critical_pass`/`rubric_score`) is worth resolving or explicitly justifying so future contributors don't treat it as an oversight.

**Note on prior work**: the task list for this session already shows two completed items — `atp-evaluator-refactoring.prose` and `atp-module-review.prose` — that sound like they cover exactly this ground. It may be worth diffing this analysis against whatever those OpenProse runs produced before acting on the plan above, in case some of these findings (or a differing refactor design) were already reached.

**Key files referenced** (all under `/Users/Andrei_Shtanakov/labs/all_ai_orchestrators/atp-platform/atp/evaluators/`): `base.py`, `registry.py`, `__init__.py`, `artifact.py`, `behavior.py`, `composite.py`, `filesystem.py`, `llm_judge.py`, `code_exec.py`, `factuality.py`, `performance.py`, `style.py`, `security/evaluator.py`, `security/base.py`, `findings/evaluator.py`, `git_commit.py`, `guardrails.py`, `checkers/registry.py`, `json_path/checker.py`, `citation_grounding/checker.py`; plus `atp-platform/packages/atp-core/atp/core/results.py` (`EvalCheck`/`EvalResult`/`CaseVerdict`) and `atp-platform/packages/atp-core/atp/loader/models.py` (`Assertion.critical`).
