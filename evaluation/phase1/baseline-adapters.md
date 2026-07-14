# ATP Adapters -- Baseline Analysis

Baseline analysis of `atp-platform/packages/atp-adapters/` produced without OpenProse,
as a plain-prompt comparison point for Phase 1 evaluation.

---

## 1. Directory Structure

```
atp/adapters/
  __init__.py            # lazy-import facade, __all__ re-exports
  base.py                # AgentAdapter ABC + AdapterConfig + tracing wrappers
  exceptions.py          # exception hierarchy (AdapterError and subclasses)
  registry.py            # AdapterRegistry -- lazy-resolve, YAML/dict config loading
  fallback.py            # FallbackAdapter -- chain-of-adapters resilience wrapper

  # --- single-file adapters ---
  http.py                # HTTPAdapter      (httpx, SSE streaming)
  cli.py                 # CLIAdapter       (subprocess, stdin/stdout/stderr)
  container.py           # ContainerAdapter  (Docker/Podman subprocess)
  langgraph.py           # LangGraphAdapter  (in-process LangGraph graph)
  crewai.py              # CrewAIAdapter     (in-process CrewAI crew)
  autogen.py             # AutoGenAdapter    (in-process AutoGen agents)
  sdk_adapter.py         # SDKAdapter        (in-process queue for ATP SDK)

  # --- multi-file cloud adapter packages ---
  mcp/
    __init__.py          # re-exports
    adapter.py           # MCPAdapter        (MCP protocol over stdio/SSE)
    transport.py         # MCPTransport ABC, StdioTransport, SSETransport

  bedrock/
    __init__.py          # re-exports
    adapter.py           # BedrockAdapter    (AWS Bedrock Agents via boto3)
    models.py            # BedrockAdapterConfig
    auth.py              # create_boto3_client helper

  vertex/
    __init__.py          # re-exports
    adapter.py           # VertexAdapter     (Google Vertex AI / Gemini)
    models.py            # VertexAdapterConfig
    auth.py              # initialize_vertexai helper

  azure_openai/
    __init__.py          # re-exports
    adapter.py           # AzureOpenAIAdapter (Azure OpenAI chat completions)
    models.py            # AzureOpenAIAdapterConfig
    auth.py              # get_openai_client, get_azure_ad_token_provider
```

## 2. Adapter Inventory

| Adapter           | Type string      | File(s)                  | Transport           | Optional dep         |
|-------------------|------------------|--------------------------|---------------------|----------------------|
| HTTPAdapter       | `http`           | `http.py`                | HTTP POST / SSE     | (httpx, core dep)    |
| CLIAdapter        | `cli`            | `cli.py`                 | subprocess stdio    | --                   |
| ContainerAdapter  | `container`      | `container.py`           | Docker/Podman stdio | --                   |
| LangGraphAdapter  | `langgraph`      | `langgraph.py`           | in-process          | langgraph            |
| CrewAIAdapter     | `crewai`         | `crewai.py`              | in-process          | crewai               |
| AutoGenAdapter    | `autogen`        | `autogen.py`             | in-process          | autogen-agentchat    |
| SDKAdapter        | `sdk`            | `sdk_adapter.py`         | in-process queue    | --                   |
| MCPAdapter        | `mcp`            | `mcp/`                   | stdio / SSE (MCP)   | --                   |
| BedrockAdapter    | `bedrock`        | `bedrock/`               | boto3 SDK           | boto3                |
| VertexAdapter     | `vertex`         | `vertex/`                | vertexai SDK        | google-cloud-aiplatform |
| AzureOpenAIAdapter| `azure_openai`   | `azure_openai/`          | openai SDK          | openai               |
| FallbackAdapter   | `fallback`       | `fallback.py`            | wraps chain         | --                   |

## 3. Base Class and Shared Interface

### `AgentAdapter` (ABC in `base.py`)

All adapters extend `AgentAdapter`. The contract:

| Member                       | Kind        | Required | Purpose                             |
|------------------------------|-------------|----------|-------------------------------------|
| `adapter_type`               | property    | abstract | returns type string (e.g. `"http"`) |
| `execute(request)`           | method      | abstract | ATPRequest -> ATPResponse           |
| `stream_events(request)`     | method      | abstract | ATPRequest -> AsyncIterator[ATPEvent | ATPResponse] |
| `health_check()`             | method      | optional | returns bool, default True          |
| `cleanup()`                  | method      | optional | release resources, default no-op    |
| `execute_with_tracing()`     | method      | provided | wraps execute() with OTel span      |
| `stream_events_with_tracing()`| method     | provided | wraps stream_events() with OTel span|
| `__aenter__` / `__aexit__`   | method      | provided | async context manager (calls cleanup)|

### `AdapterConfig` (Pydantic BaseModel)

Base fields inherited by every config:

- `timeout_seconds` (float, default 300, >0)
- `retry_count` (int, default 0, >=0)
- `retry_delay_seconds` (float, default 1.0, >=0)
- `enable_cost_tracking` (bool, default True)

Each adapter defines its own `*AdapterConfig` subclass adding adapter-specific fields.

## 4. Initialization Conventions

### Single-file adapters (http, cli, container, langgraph, crewai, autogen, sdk)

- Constructor takes its typed config (e.g. `HTTPAdapterConfig`), falls back to default if None.
- Calls `super().__init__(config)`.
- Stores a typed `self._config` reference.
- Lazily creates clients/connections on first `execute()` call (e.g. `_get_client()`, `_load_graph()`).

### Multi-file cloud adapters (bedrock, vertex, azure_openai)

- Same constructor pattern; config class lives in `models.py`.
- Authentication logic is factored into `auth.py` (`create_boto3_client`, `initialize_vertexai`, `get_openai_client`).
- External SDK imports are guarded with try/except ImportError and raise `AdapterError` with install instructions (e.g. `"uv add boto3"`).

### MCP adapter

- Has an explicit `initialize()` method that performs the MCP handshake (distinct from other adapters).
- Creates a `MCPTransport` (stdio or SSE) internally.
- `execute()` auto-calls `initialize()` if not yet connected.

### FallbackAdapter

- Takes a `list[AgentAdapter]` chain instead of a typed config.
- Validates chain is non-empty.

## 5. Error Handling Approach

### Exception hierarchy (`exceptions.py`)

```
ATPError (from atp.core.exceptions)
  AdapterError(message, adapter_type?, cause?)
    AdapterTimeoutError(message?, timeout_seconds?, adapter_type?)
    AdapterConnectionError(message?, endpoint?, adapter_type?, cause?)
    AdapterResponseError(message?, status_code?, response_body?, adapter_type?)
    AdapterNotFoundError(adapter_type)
```

All exceptions carry `adapter_type` for diagnostics.

### Error handling patterns across adapters

**Consistent patterns:**

1. **Timeout handling** -- all adapters wrap their main execution in `asyncio.wait_for()` and catch `TimeoutError`, re-raising as `AdapterTimeoutError`.

2. **Connection errors** -- `FileNotFoundError` (missing binary), `OSError` (process start failure), `httpx.ConnectError` are caught and wrapped as `AdapterConnectionError`.

3. **Response validation** -- JSON parse failures and Pydantic validation failures on the response are wrapped as `AdapterResponseError`.

4. **Fallback to failed response** -- in-process adapters (langgraph, crewai, autogen) and cloud adapters (bedrock, vertex, azure_openai) catch generic `Exception` in `execute()` and return an `ATPResponse` with `status=FAILED` instead of raising, while subprocess/HTTP adapters raise exceptions. This is a meaningful design inconsistency (see section 7).

5. **Cloud provider error classification** -- bedrock, vertex, and azure_openai all implement `_handle_*_error()` methods that inspect error strings/types to classify AWS/GCP/Azure errors (auth, not-found, rate-limit, permission) into appropriate adapter exceptions.

6. **Error message sanitization** -- CLI and Container adapters use `sanitize_error_message()` from `atp.core.security` to redact secrets from stderr before propagating error messages.

## 6. Registry and Lazy Loading

`AdapterRegistry` in `registry.py`:

- Pre-registers all 11 adapters as `_LazyEntry` objects (module path + class names).
- Resolves lazily on first `create()` / `get_adapter_class()` call.
- On `ImportError`, provides user-friendly install hint via `_ADAPTER_EXTRAS` mapping.
- Supports dynamic registration via `register()`, `load_from_config()`, and `load_from_yaml()`.
- Global singleton accessed via `get_registry()`.

The `__init__.py` also uses `__getattr__` for lazy module-level imports, so `from atp.adapters import BedrockAdapter` only loads bedrock when accessed.

## 7. Cross-Adapter Inconsistencies

### 7.1 Error propagation strategy (raise vs return-failed)

- **Subprocess/HTTP adapters** (http, cli, container): always **raise** adapter exceptions on failure.
- **In-process adapters** (langgraph, crewai, autogen): catch generic exceptions and **return** `ATPResponse(status=FAILED)` instead of raising. Only timeout and adapter-specific errors are re-raised.
- **Cloud adapters** (bedrock, vertex, azure_openai): same pattern as in-process -- catch-all returns FAILED response.
- **SDK adapter**: raises `TimeoutError` directly (not wrapped in `AdapterTimeoutError`).

This means callers get different behavior depending on adapter type. A failed HTTP call raises, but a failed LangGraph call returns a response object.

### 7.2 Streaming error handling divergence

- **Bedrock and Vertex** `stream_events()`: on timeout, yield an ERROR event + TIMEOUT response instead of raising. On generic exception, yield ERROR event + FAILED response.
- **HTTP and CLI** `stream_events()`: raise exceptions directly.
- **CrewAI and AutoGen** `stream_events()`: catch exceptions and yield FAILED response (no ERROR event emitted before the response).

### 7.3 Deprecated event loop access

- `cli.py` line 258 uses `asyncio.get_event_loop().time()` (deprecated since Python 3.10).
- `container.py` line 427 uses `asyncio.get_running_loop().time()` (correct).

### 7.4 `_create_event()` helper duplication

- `langgraph.py`, `crewai.py`, and `autogen.py` each define an identical `_create_event()` helper method. This could be factored into the base class.

### 7.5 `stream_events` return type annotation

- The base class annotates `stream_events` as returning `AsyncIterator`, but the method body just has `...` (ellipsis) and no `yield`, making it technically not a generator. Subclasses implement it correctly as async generators.

### 7.6 Timeout source in constraints vs config

- In-process adapters (langgraph, crewai, autogen) read timeout from `request.constraints.get("timeout_seconds", self._config.timeout_seconds)`.
- Subprocess/HTTP/cloud adapters use `self._config.timeout_seconds` directly.
- The constraints-based override is not consistently available.

### 7.7 Session management scope

- Cloud adapters (bedrock, vertex, azure_openai) provide `reset_session()` and `set_session_id()` methods.
- SDKAdapter, MCP, and framework adapters do not have session management.
- There is no session management interface in the base class.

### 7.8 `health_check()` depth varies

- **HTTPAdapter**: makes a real HTTP GET to the endpoint.
- **CLIAdapter**: checks `shutil.which()` (command exists in PATH).
- **ContainerAdapter**: runs `docker info` + `docker image inspect`.
- **LangGraph/CrewAI/AutoGen**: try to load the module/graph/crew.
- **Cloud adapters**: only verify client construction succeeds (no network call).
- **MCPAdapter**: delegates to transport `health_check()` (process running or SSE connected).

### 7.9 Config field naming

- `timeout_seconds` is the base field name.
- Bedrock uses `timeout_seconds` from base but also `session_ttl_seconds` as a separate field.
- `retry_count` and `retry_delay_seconds` exist on AdapterConfig but no adapter implements retry logic. The MCP transport has its own `reconnect_attempts` / `reconnect_delay` / `reconnect_backoff` that does not reuse base fields.

## 8. Common Patterns Summary

1. **Adapter = Config + Adapter class**: every adapter ships a Pydantic config model and an adapter class extending `AgentAdapter`.

2. **Lazy client creation**: all adapters defer expensive initialization (HTTP clients, SDK clients, module imports) until first use.

3. **ATPRequest in, ATPResponse out**: both `execute()` (single response) and `stream_events()` (event stream + final response) accept `ATPRequest` and produce `ATPResponse`.

4. **Security throughout**: URL validation (SSRF prevention), environment variable filtering, Docker capability dropping, error message sanitization.

5. **OpenTelemetry integration**: base class provides `execute_with_tracing()` / `stream_events_with_tracing()` wrappers that create spans with adapter type, task ID, and response metrics.

6. **Cost tracking**: base module provides `track_response_cost()` utility; config has `enable_cost_tracking` flag.

7. **Pydantic validation**: configs use `field_validator` and `model_validator` for input validation (URLs, credentials, enums).

8. **Three adapter tiers**: (a) subprocess/HTTP adapters for external processes, (b) in-process adapters for Python framework integration, (c) cloud SDK adapters for managed services. Each tier has slightly different error handling and lifecycle semantics.
