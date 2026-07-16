# Baseline Prompts for Phase 1

These are the plain Claude Code prompts used for baseline comparison against the .libretto programs.

## Task 1: Architecture Summary

**Prompt:**
"Read the README.md and key configuration files in ../atp-platform. Produce a concise architecture summary covering: project purpose, tech stack, package structure (atp-core, atp-adapters, atp-dashboard, atp-sdk), and key design decisions."

**Result:**

ATP (Agent Test Platform) is a framework-agnostic platform for testing and evaluating AI agents.

- **Purpose:** Unified testing protocol for any AI agent (LangGraph, CrewAI, AutoGen, HTTP endpoints, CLI, containers, cloud providers). Includes game-theoretic evaluation and statistical rigor.
- **Tech stack:** Python 3.12+, Pydantic models, FastAPI dashboard, HTMX + Pico CSS frontend, SQLite/PostgreSQL storage, OpenTelemetry tracing.
- **Package structure (uv workspace):**
  - `atp-core` — Protocol models (ATPRequest/ATPResponse/ATPEvent), core config, loader, scoring, statistics
  - `atp-adapters` — 11 agent adapters (HTTP, Container, CLI, LangGraph, CrewAI, AutoGen, MCP, Bedrock, Vertex, Azure OpenAI, SDK)
  - `atp-dashboard` — FastAPI web UI with benchmark API, tournament API, GitHub OAuth, RBAC
  - `atp-sdk` — Python SDK (AsyncATPClient + sync wrapper) for benchmark platform participants
- **Key design decisions:**
  - Protocol-driven: all agent communication goes through ATP Request/Response/Event models
  - Adapter pattern: AgentAdapter ABC with typed config (AdapterConfig subclasses)
  - Statistical rigor: multiple runs, confidence intervals, Welch's t-test regression detection
  - Game-theoretic evaluation as first-class feature (Prisoner's Dilemma, Auction, etc.)
  - Security-conscious: URL validation, SSRF protection, environment variable filtering

## Task 2: Adapters Pattern Analysis

**Prompt 1:** "Explore the directory structure of ../atp-platform/packages/atp-adapters/. List all adapter implementations, their file organization, and the base classes they extend."

**Prompt 2:** "Based on the exploration above, write a summary of common patterns across all adapters."

**Result:**

### Adapter Implementations Found

| Adapter | File(s) | Organization |
|---------|---------|-------------|
| HTTP | `http.py` | Single file |
| CLI | `cli.py` | Single file |
| Container | `container.py` | Single file |
| LangGraph | `langgraph.py` | Single file |
| CrewAI | `crewai.py` | Single file |
| AutoGen | `autogen.py` | Single file |
| Fallback | `fallback.py` | Single file |
| SDK | `sdk_adapter.py` | Single file |
| MCP | `mcp/` | Multi-file (adapter.py, transport.py) |
| Bedrock | `bedrock/` | Multi-file (adapter.py, auth.py, models.py) |
| Vertex | `vertex/` | Multi-file (adapter.py, auth.py, models.py) |
| Azure OpenAI | `azure_openai/` | Multi-file (adapter.py, auth.py, models.py) |

### Common Patterns

1. **Shared interface:** All extend `AgentAdapter` ABC from `base.py`, implementing `execute()` and optionally `execute_streaming()`.
2. **Typed config:** Each adapter defines a `*AdapterConfig(AdapterConfig)` Pydantic model with adapter-specific fields and validators.
3. **Error handling:** All use the same exception hierarchy from `exceptions.py`: `AdapterError`, `AdapterConnectionError`, `AdapterTimeoutError`, `AdapterResponseError`.
4. **Imports:** All import from `atp.protocol` (ATPRequest, ATPResponse, ATPEvent, EventType).
5. **Cloud adapters** (Bedrock, Vertex, Azure) share a common 3-file pattern: adapter.py + auth.py + models.py.
6. **Inconsistency:** Simple adapters are single files while complex ones use subdirectories. The MCP adapter uses a subdirectory but lacks the auth.py/models.py pattern of cloud adapters.
