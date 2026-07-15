# Baseline: Architecture Document (single-shot, no refine loop)

- Model: opus-class (session default), general-purpose agent, no OpenProse VM
- Cost: 87.4K tokens, 24 tool calls, 221s wall time
- Prompt: see baseline-prompts.md, Task 2
- Scored post-hoc by the same evaluator rubric as the RLM run for comparability
  (see phase-5.md).

## Output

### ATP Platform — Architecture Document

**Repo:** `../atp-platform` · **Version:** 2.1.0 · **Python:** ≥3.12 · **License:** MIT

#### 1. Project Purpose

ATP (Agent Test Platform) is a **framework-agnostic platform for testing and evaluating AI agents**. Any agent — LangGraph, CrewAI, AutoGen, an HTTP endpoint, a CLI binary, a Docker container, an MCP server, or a cloud-hosted model (Bedrock / Vertex / Azure OpenAI) — is exercised through a single wire protocol and scored by a pluggable evaluator pipeline. Distinguishing capabilities:

- **Game-theoretic evaluation** (Prisoner's Dilemma, Public Goods, Auction, El Farol, etc.) via the `atp-games` plugin and standalone `game-environments` package, including tournaments with Elo ratings.
- **Statistical rigor**: multiple runs per test, 95% confidence intervals, Welch's t-test regression detection (`atp/statistics`, `atp/baseline`).
- **Production tooling**: FastAPI web dashboard with SQLite/PostgreSQL storage, JUnit XML for CI, HTML reports, cost tracking, security evaluation, OpenTelemetry tracing, and a benchmark/leaderboard pipeline with its own SDK.

#### 2. Package Structure

The repo is a **uv workspace** (`[tool.uv.workspace] members = ["packages/*", "game-environments", "atp-games"]`) publishing several distributions that all contribute to a shared **`atp` namespace package**. The root `atp/` tree holds the platform-owned modules and contains **symlinks** into `packages/*` for the modules owned by sub-distributions (e.g. `atp/core -> ../packages/atp-core/atp/core`), so the source tree reads as one package while shipping as many.

| Distribution | Location | Contents |
|---|---|---|
| **atp-platform** (root, v2.1.0) | `atp/` | CLI (~20 commands), test runner (`atp/runner`), evaluators, reporters, plugin system, benchmarks registry, suite generator, baseline comparison, trace record/replay, test catalog, TUI, mock tools, performance |
| **atp-core** (v1.0.0) | `packages/atp-core` | ATP wire protocol, core utilities (telemetry, metrics, logging, security, settings), suite loader, scoring, statistics, cost tracking + model catalog, chaos, streaming |
| **atp-adapters** | `packages/atp-adapters` | `AgentAdapter` base + registry; HTTP, CLI, Container, LangGraph, CrewAI, AutoGen, MCP, Bedrock, Vertex, Azure OpenAI, SDK (pull-model), fallback adapters |
| **atp-dashboard** | `packages/atp-dashboard` | FastAPI app (v2 factory), SQLAlchemy async ORM, auth/RBAC/tenancy, tournament engine, MCP server for tournament gameplay, webhooks, analytics |
| **atp-platform-sdk** (v2.0.0) | `packages/atp-sdk` | Standalone participant SDK: httpx client, auth, retry, benchmark helpers |
| **atp-method** (v0.1.0) | `packages/atp-method` | Plugin running "agent-eval-case" methodology cases (registers via `atp.plugins` entry point) |
| **atp-games** / **game-environments** | `atp-games/`, `game-environments/` | Game-theoretic evaluation plugin and the standalone game environments library it wraps |

Supporting directories: `tests/` (unit / integration / e2e / contract / ci / ops), `docs/` (ADRs, guides, plans, runbooks), `examples/`, `demo/`, `deploy/` + `infra/terraform/`, `action.yml` + `ci-templates/`, `migrations/` (Alembic), `method/` (methodology SSOT), `dashboards/`.

#### 3. Key Abstractions

- **ATP Protocol** (`atp/protocol/models.py`, versioned): pydantic models `ATPRequest` (Task + Context + constraints), `ATPResponse` (status, `Metrics`, artifacts: `ArtifactFile`/`ArtifactStructured`/`ArtifactReference`), and `ATPEvent` (typed stream events). The single contract every adapter speaks.
- **`AgentAdapter`** (`packages/atp-adapters/atp/adapters/base.py`): ABC with `execute(request) -> ATPResponse`, `stream_events()`, `health_check()`, `cleanup()`, plus tracing/cost-tracking wrappers. The **`SDKAdapter`** inverts control: the platform enqueues requests, a participant agent pulls tasks (`pull_task()`/`resolve_task()`) — the pull-model benchmark bridge.
- **`TestOrchestrator`** (`atp/runner/orchestrator.py`): per-test/per-suite runs, N runs per test, semaphore-bounded parallelism, soft/hard timeouts, event collection, sandbox workspaces, progress callbacks, OTel spans.
- **`Evaluator`** + **`EvaluatorRegistry`**: async `evaluate()`; built-ins artifact, behavior, llm_judge, code_exec, security, factuality, performance, style, filesystem, composite, findings_match, plus deterministic `checkers/`. Suite YAML assertions map to evaluator types.
- **`ScoreAggregator`**: weighted aggregation of quality/completeness/efficiency/cost.
- **Reporters** (registry-based): console, JSON, HTML, JUnit XML, summary, benchmark (`report_benchmark-v1` payloads for the Maestro/arbiter pipeline), game reporters.
- **Plugin system** (`atp/plugins`): `Protocol`-typed interfaces discovered through setuptools entry points (`atp.evaluators`, `atp.reporters`, `atp.adapters`, `atp.plugins`); `atp-method`/`atp-games` also register suite-format/suite-source handlers.
- **Dashboard ORM**: `User`, `Agent`, `SuiteExecution`, `TestExecution`, `RunResult`, `Artifact`, `EvaluationResult`, `ScoreComponent`, `PublishedResult` + RBAC/token models; async SQLAlchemy with Alembic.

#### 4. Data Flow

**Primary path — `atp test suite.yaml`**: (1) suite-format registry may route to a plugin, else loader parses YAML into `TestSuite`; (2) adapter resolved from merged config; (3) `TestOrchestrator.run_suite()` builds `ATPRequest` per run, executes with timeouts/sandboxing, collects events (optionally recording for `atp replay`); (4) assertions → evaluators → `ScoreAggregator`; multiple runs → statistics (CIs); (5) reporter renders output; `ResultStorage` persists into the dashboard DB; `--save-results` feeds `atp compare`/`atp trend`/baseline regression.

**Dashboard path**: `atp dashboard` starts the FastAPI v2 app (REST, WebSocket, Jinja+SPA, JWT/RBAC auth, tournament service, MCP server through which agents play tournament games). SQLite at `~/.atp/dashboard.db` by default; PostgreSQL via `ATP_DATABASE_URL`.

**Benchmark path**: participants use `atp-platform-sdk` to pull tasks and submit results; in-process the `SDKAdapter` bridges runner and SDK; leaderboards + `report_benchmark-v1` integrate with the Maestro/arbiter ecosystem.

**Observability** is cross-cutting: OTel tracing (OTLP gRPC) + Prometheus metrics instrument adapters, orchestrator, evaluators end-to-end.

#### 5. Deployment Model

- **Library/CLI**: PyPI (`uv add atp-platform`, console script `atp`); separate publish workflows for root, `atp-method`, `atp-sdk`.
- **Docker**: root `Dockerfile` (python:3.12-slim + `uv sync --no-dev --all-packages --extra llm --extra bedrock`); `docker-compose.yml` with runner + dashboard (:8080) services.
- **Production VPS**: `deploy/` targets a VPS behind nginx, deployed by `.github/workflows/deploy.yml` on push to main. Documented host constraints: pre-Nehalem QEMU CPU forces `numpy<2.0`; tournament deadline worker requires a single uvicorn worker.
- **AWS (Terraform)**: `infra/terraform/` provisions EC2 runner, ECR, IAM, Bedrock access, budget guards.
- **CI/CD**: composite GitHub Action (`action.yml`) + `ci-templates/`; the repo runs 9 GitHub workflows.

#### 6. Notable Design Decisions

1. **Namespace-package workspace with symlinks** — one importable `atp` package, independently versioned distributions.
2. **Protocol-first decoupling** — everything upstream of `ATPRequest/ATPResponse/ATPEvent` is framework-agnostic; adding a framework = a new adapter.
3. **Registry + entry-point extensibility everywhere** — adapters, evaluators, reporters, suite formats/sources pluggable without touching core.
4. **Two execution topologies** — push (platform drives agent via adapter) and pull (agent drives via SDK, used for benchmarks/tournaments).
