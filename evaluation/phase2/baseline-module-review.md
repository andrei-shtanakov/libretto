# Baseline: Module Review x3 (plain prompt, single session)

- Model: sonnet, general-purpose agent, no OpenProse VM
- Cost: 72.4K tokens, 7 tool calls, 232s wall time
- Prompt: see baseline-prompts.md, Task 2

## Output

### Code Quality Review — atp-core, atp-adapters, atp-sdk

Scope note: tests for all three packages live centrally in `../atp-platform/tests/` (mirrored subdirectories under `unit/`), not colocated with the source packages. No files were modified.

---

## 1. `atp-core`

| Dimension | Score |
|---|---|
| Organization | 6/10 |
| Naming | 8/10 |
| Test coverage | 7/10 |
| Error handling | 8/10 |
| Docs | 9/10 |

- **Organization (6/10):** Most submodules (`protocol/`, `chaos/`, `model_catalog/`) are cohesive, but `atp/core/` is a god-module (settings, logging, telemetry, metrics, security, exceptions, results all flat; `core/security.py` alone is ~1,550 lines covering path/URL/Docker validation and secret redaction). More notable: real boundary violations — `atp/scoring/aggregator.py:5` imports `from atp.evaluators.base import EvalResult` and `atp/statistics/reporter.py:5` imports `from atp.runner.models import ...`, both outside the atp-core wheel's declared `packages` list, undermining the package's stated goal of being installable standalone.
- **Naming (8/10):** Consistent PEP 8, descriptive domain names, enums used well. Minor trap: `core/result.py` (singular) vs `core/results.py` (plural) hold unrelated content.
- **Test coverage (7/10):** Every submodule has a mirrored test dir with genuine depth (24 test classes for security edge cases, monkeypatched fakes for pricing errors). Weak spot: `cost/tracker.py`'s async queue/batch/backpressure logic has no dedicated unit tests.
- **Error handling (8/10):** Clean hierarchy (`ATPError → LoaderError → {ValidationError, ParseError}`), pydantic-first validation, no bare `except:`. `statistics/calculator.py:114` silently returns `0.0` on insufficient data — defensible but under-documented.
- **Docs (9/10):** Near-universal module and function docstrings, complete modern type hints (PEP 604, PEP 695). Gap: `CHANGELOG.md` is essentially empty despite being versioned 1.0.0.

**Character:** mature, disciplined, pydantic-first — rough edges are structural (a god-module and boundary leaks) rather than sloppy.

---

## 2. `atp-adapters`

| Dimension | Score |
|---|---|
| Organization | 9/10 |
| Naming | 8/10 |
| Test coverage | 9/10 |
| Error handling | 8/10 |
| Docs | 7/10 |

- **Organization (9/10):** `base.py`'s `AgentAdapter` ABC is a strict, consistently-honored contract across every adapter (HTTP, CLI, container, LangGraph, CrewAI, AutoGen, MCP, SDK, and cloud adapters). Cloud subpackages (`azure_openai/`, `bedrock/`, `vertex/`) cleanly split adapter/auth/models; `mcp/` deviates slightly (models inline). Minor duplication: near-identical stderr-JSONL event loops in `cli.py`/`container.py`.
- **Naming (8/10):** Consistent `XAdapter`/`XAdapterConfig` convention; `adapter_type` strings match registry keys. `sdk_adapter.py` filename breaks the module-name pattern used elsewhere (cosmetic).
- **Test coverage (9/10):** Genuinely deep — `test_bedrock.py` (34 tests) and `test_azure_openai.py` (45 tests) cover auth failures, throttling, timeouts; `mcp/test_transport.py` (79 tests) covers concurrent routing, reconnect backoff, SSE parsing. ~10k lines of tests vs ~9.7k source. `sdk_adapter.py` tests are thin but proportionate to a 137-line module.
- **Error handling (8/10):** Clean `AdapterError` hierarchy (`AdapterTimeoutError`, `AdapterConnectionError`, `AdapterResponseError`, `AdapterNotFoundError`) and a sound `fallback.py` chain. Recurring pattern: framework adapters (`langgraph.py:305-314`, `crewai.py:273-280`) catch broad `Exception` and convert to a `FAILED` response **without logging** — deliberate but reduces debuggability of unexpected bugs.
- **Docs (7/10):** Consistent Google-style docstrings, cloud adapters document auth/install requirements. `CHANGELOG.md` is empty despite version 1.0.0 and an active entry-points surface.

**Character:** the most disciplined of the three — strict shared contract, unusually deep tests (especially MCP transport), main gaps are cosmetic/duplication rather than architectural.

---

## 3. `atp-sdk`

| Dimension | Score |
|---|---|
| Organization | 7/10 |
| Naming | 7/10 |
| Test coverage | 8/10 |
| Error handling | 5/10 |
| Docs | 7/10 |

- **Organization (7/10):** Sensible module split; `sync.py`'s `ATPClient` cleanly wraps `AsyncATPClient` via a background thread. But `benchmark.py`'s `BenchmarkRun` reimplements its own separate sync-dispatch mechanism (`_run_sync`, lines 161–178) duck-typed to `ATPClient` internals via `_sync_loop` — a leaky abstraction and duplicate pattern. `__iter__` (lines 128–155) juggles three dispatch code paths in one method.
- **Naming (7/10):** Good `_sync`-suffix convention for paired async/sync methods. Weak spot: `models.py`'s `RunInfo` and `LeaderboardEntry` are exported publicly but never actually returned by any client method (`get_leaderboard`/`status`/`submit` all return raw dicts) — misleading dead API surface.
- **Test coverage (8/10):** Retry logic thoroughly tested (backoff, jitter, `Retry-After`, per-status-code behavior) in `test_retry.py`; 401-renewal edge cases well covered. Gaps: `login()`'s device-flow polling loop (`auth.py:69-140`) has zero coverage; two stale test files ship `skip`-marked ("will be rewritten"); no integration/e2e test touches `atp_sdk` at all.
- **Error handling (5/10) — the clear laggard:** retry semantics themselves are well-reasoned (exponential backoff + jitter, correct 502/503/504-only retry policy), but there is **no custom exception hierarchy** anywhere — callers see raw `httpx.HTTPStatusError` or ad hoc `RuntimeError`s (`auth.py:91,128,130`, `benchmark.py:136,172`). For a public SDK, users can't `except ATPRateLimitError` or `except ATPAuthError` — they must inspect `.response.status_code` themselves.
- **Docs (7/10):** Good docstring coverage on public methods; README has install/quickstart/auth but no error-handling or leaderboard examples; CHANGELOG follows Keep a Changelog format but `[Unreleased]` is empty.

**Character:** solidly engineered with production-grade retry logic, but rough edges (missing exception hierarchy, dead typed models, duplicate dispatch mechanisms, skipped tests) are exactly the kind that erode trust in a package meant for **external** consumption.

---

## Comparison

| Dimension | atp-core | atp-adapters | atp-sdk |
|---|---|---|---|
| Organization | 6 | **9** | 7 |
| Naming | 8 | 8 | 7 |
| Test coverage | 7 | **9** | 8 |
| Error handling | 8 | 8 | **5** |
| Docs | **9** | 7 | 7 |
| **Average** | **7.6** | **8.2** | **6.8** |

**Overall ranking: atp-adapters > atp-core > atp-sdk.**

- **atp-adapters** is the standout — a strictly-enforced adapter contract plus unusually deep, non-trivial tests (especially the MCP transport layer) make it the most consistently high-quality package. Its only real debt is cosmetic (naming outlier, minor duplication) and an empty changelog.
- **atp-core** is the most mature/battle-tested (best docs, solid exceptions) but carries real architectural debt: a bloated `core/` module and cross-package import boundary violations (`scoring/aggregator.py`, `statistics/reporter.py`) that undercut its own "standalone library" design goal.
- **atp-sdk** is the weakest of the three, and notably so on error handling — surprising for a package explicitly meant for external developers, where a structured exception hierarchy matters more than in internal packages. It also has the only outright dead test debt (skip-marked stale test files) and misleading public API surface (unused `RunInfo`/`LeaderboardEntry` models).

**Cross-cutting pattern across all three:** every package's `CHANGELOG.md` is effectively empty/unmaintained despite each being independently versioned (1.0.0, 1.0.0, 2.0.0) — this is a consistent, easy-to-fix gap across the whole `atp-platform` package suite, not isolated to one component.
