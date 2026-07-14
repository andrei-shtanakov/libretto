# ATP Platform -- Architecture Summary

## Purpose

ATP (Agent Test Platform) is a framework-agnostic platform for testing and evaluating AI agents. It treats every agent as a black box communicating through a standard protocol, allowing teams to test agents built with any framework (LangGraph, CrewAI, AutoGen, HTTP endpoints, CLI tools, containers, cloud providers) through one unified interface. The platform provides statistical rigor (confidence intervals, Welch's t-test regression detection), game-theoretic evaluation, a web dashboard, and CI/CD integration.

**License:** MIT | **Status:** GA (General Availability) | **Python:** 3.12+

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.12+ |
| Data models | Pydantic v2, Pydantic-Settings |
| CLI | Click, Rich |
| Web dashboard | FastAPI + HTMX + Pico CSS |
| Database | SQLAlchemy (async), SQLite (default) / PostgreSQL |
| Auth | GitHub OAuth (OIDC), Device Flow, JWT (PyJWT), bcrypt, Authlib |
| HTTP client | httpx |
| Observability | OpenTelemetry (API + SDK + OTLP exporter), Prometheus client, structlog |
| Test config | YAML (PyYAML, ruamel-yaml), JSON Schema validation |
| Build system | Hatchling, uv workspaces |
| Code quality | Ruff (format + lint), pyrefly (type checking), pytest + pytest-anyio |
| Rate limiting | slowapi |
| Templating | Jinja2 |

## Package Structure (uv Workspace)

The monorepo is decomposed into four packages under `packages/` plus two standalone game-theory packages, all sharing the `atp` implicit namespace (PEP 420).

### atp-core

**Path:** `packages/atp-core/` | **Version:** 1.0.0

Foundation library with zero framework dependencies. Ships:
- `atp.protocol` -- ATP Request/Response/Event models (the universal agent contract)
- `atp.core` -- Configuration, exceptions, security primitives
- `atp.loader` -- YAML/JSON test suite parsing, Pydantic models, tag filtering, JSON Schema validation
- `atp.scoring` -- Score aggregation
- `atp.statistics` -- Statistical calculations (mean, CI, Welch's t-test)
- `atp.streaming` -- Event streaming support
- `atp.chaos` -- Chaos testing primitives
- `atp.cost` -- Cost tracking

**Key deps:** pydantic, pyyaml, ruamel-yaml, jsonschema, structlog, cryptography, opentelemetry-*

### atp-adapters

**Path:** `packages/atp-adapters/` | **Version:** 1.0.0

All agent adapters, registered via `atp.adapters` entry points. Depends on atp-core.

| Adapter | Transport |
|---------|-----------|
| HTTPAdapter | REST/SSE endpoints |
| CLIAdapter | Subprocess/command-line agents |
| ContainerAdapter | Docker-based agents |
| LangGraphAdapter | Native LangGraph |
| CrewAIAdapter | CrewAI framework |
| AutoGenAdapter | AutoGen framework |
| MCPAdapter | Model Context Protocol |
| BedrockAdapter | AWS Bedrock (optional: boto3) |
| VertexAdapter | Google Vertex AI (optional: google-cloud-aiplatform) |
| AzureOpenAIAdapter | Azure OpenAI (optional: openai) |
| SDKAdapter | Pull-model for SDK benchmark participants |

Cloud adapters are behind optional extras (`atp-adapters[bedrock]`, `[vertex]`, `[azure-openai]`, `[cloud]`).

### atp-dashboard

**Path:** `packages/atp-dashboard/` | **Version:** 1.0.0

Web interface and analytics. Depends on atp-core. Ships:
- `atp.dashboard` -- FastAPI app with HTMX + Pico CSS frontend
- `atp.analytics` -- Cost tracking, agent rankings, stats

Pages: Benchmarks, Runs (with HTMX auto-refresh), Leaderboard, Games, Suites, Analytics.

APIs: `/api/v1/benchmarks`, `/api/v1/runs`, `/api/v1/tournaments`, suite upload, event streaming, webhooks.

Optional extras: `[enterprise]` (SAML via python3-saml, Authlib), `[analytics]` (openpyxl exports), `[postgres]` (asyncpg).

### atp-sdk (atp-platform-sdk)

**Path:** `packages/atp-sdk/` | **Version:** 2.0.0 | **PyPI:** `atp-platform-sdk`

Lightweight Python SDK for benchmark platform participants. Minimal deps (httpx, pydantic only). Provides `AsyncATPClient` and sync `ATPClient` wrapper with `BenchmarkRun` iteration, batch API (`next_batch(n)`), event streaming (`emit()`), Device Flow auth, and exponential-backoff retry.

### Standalone Game Packages

- **game-environments/** -- Zero-dependency game theory library (Prisoner's Dilemma, Stag Hunt, Public Goods, Auction, Colonel Blotto, etc.) with strategies, Nash equilibrium analysis, and exploitability metrics.
- **atp-games/** -- ATP plugin that bridges game-environments into the test runner with GameRunner, game-specific evaluators (Payoff, Exploitability, Cooperation, Equilibrium), YAML suite support, and tournaments.

## Dependency Graph

```
atp-core                game-environments
    ^                        ^
    |--- atp-adapters        |
    |        ^               |
    |        |               |
    atp-platform -------> atp-games
        ^
        |
    atp-dashboard

atp-platform-sdk (independent, httpx + pydantic only)
```

## Key Design Decisions

1. **Agent-as-black-box protocol.** Every agent interaction goes through a standard ATP Request/Response/Event protocol. Adapters translate this protocol to framework-specific calls. This is the core abstraction that enables framework-agnosticism.

2. **Plugin architecture via entry points.** Adapters, evaluators, and reporters are all registered through Python entry points (`atp.adapters`, `atp.evaluators`, `atp.reporters`). Third-party packages can register new implementations without modifying ATP source.

3. **Immutable, unidirectional data flow.** Test Definition -> Runner -> Agent -> Response -> Evaluators -> Report. No back-channels or mutable shared state between stages.

4. **Monorepo with namespace packages (ADR-003).** The ~95K-line codebase is split into 4 packages sharing the `atp` implicit namespace via PEP 420. This enables independent release cycles, lighter installs, and clearer ownership while preserving all existing `from atp.X import Y` imports. Managed with uv workspaces.

5. **Statistical rigor as a first-class concern.** Multiple runs per test, 95% confidence intervals via t-distribution, Welch's t-test for regression detection. Baselines can be saved and compared across releases.

6. **YAML-driven test suites.** Test definitions are declarative YAML with Pydantic validation. Suites specify agents, tests, assertions, constraints, and scoring weights. Supports variable substitution and tag-based filtering.

7. **Game-theoretic evaluation as a separate layer.** The game theory library (`game-environments`) has zero ATP dependency, making it reusable outside the platform. The ATP integration (`atp-games`) is a plugin that bridges games into the test runner.

8. **Dashboard as optional, independently deployable.** The dashboard is behind the `[dashboard]` extra and can run as a standalone FastAPI service. Uses HTMX + Pico CSS for a lightweight frontend without a JS build step.

9. **Fail-safe defaults.** The system works with minimal configuration. Sandbox is off by default, single run per test, 300s timeout, console output. Progressive disclosure of advanced features.

10. **Cloud adapters behind optional extras.** Heavy cloud SDKs (boto3, google-cloud-aiplatform, openai) are not installed by default. Users opt in via `atp-adapters[bedrock]` etc., keeping the base install lightweight.
