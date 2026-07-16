# Adapter: Claude Code (reference substrate)

Binds the host port (`contracts/adapters.md`) to Claude Code. This is
the substrate the committed run corpus (`examples/runs/`) was produced
on and the reference for `usage.basis` judgments.

## Primitive bindings

| Primitive | Binding |
| --------- | ------- |
| `spawn_session` | **Task tool** (`general-purpose` subagent). Prompt carries: task text, binding target path, context reference paths, do-the-work-yourself leaf constraint (`guidance/patterns.md` → leaf-constraint). Model per session/agent `model:` property |
| `read_state` / `write_state` | Read / Write / Edit tools on the `.libretto/` tree |
| `copy_binding` | File copy (`cp`) + `shasum -a 256` verification |
| `check_env` | Bash probes (`command -v`, path checks) |
| `run_shell` | Bash tool. Timeout enforceable (tool-level `timeout`); sandboxing per the host's permission mode — see Security posture |
| `ask_user` | Prompting the user in-conversation (interactive only) |
| `emit_receipt` | VM-side scripted append per `primitives/session.md` §8 (canonical JSON + sha256; a helper script is legitimate — hash mechanics, not judgment) |

## Concurrency

Parallel Task calls in one message run genuinely concurrently. The host
imposes its own cap on simultaneous subagents; large fan-outs queue.
Use `max_concurrent:` for programs with more than a handful of branches.

## Timeouts

- `run_shell`: enforceable (tool parameter).
- Sessions: **not enforceable** — a spawned subagent cannot be killed by
  the VM (this is also why `parallel ("first")` discards rather than
  cancels). `timeout:` on sessions is advisory; note overruns in
  `state.md`.

## Degradations (declared)

1. **Hook-blocked binding writes.** User-configured hooks can
   intermittently deny subagent Write calls to binding paths (observed
   repeatedly during the seven-phase evaluation). Fallback (mandatory):
   the subagent returns its full output in the confirmation; the VM
   persists it via `write_state` and proceeds. Fingerprints stay valid
   (they hash the file as written); note the fallback in `state.md`.
2. **No in-flight cancellation** (see Timeouts) — affects join
   strategies and budget enforcement exactly as specified in `libretto.md`.
3. **Usage split unavailable.** The host reports per-subagent token
   totals without an input/output split → `usage.basis: "estimated"`
   with the estimation method (output ≈ binding bytes / 4) noted in
   `state.md`. `exact` is claimable only for zero (skipped receipts).
4. **Nested orchestration risk.** Subagents can spawn their own
   subagents; the leaf constraint in every spawn prompt is the required
   mitigation (`guidance/patterns.md`).

## Security posture (contract points 1–6)

1. Remote `use`: fetched programs land in the run dir before execution;
   the user sees the fetch in-conversation. No auto-execution from
   registries in headless runs.
2. Permissions: program `permissions:` intersect with the host's
   permission mode. Running with permissions bypassed is an **unsafe
   posture** and must be named in `state.md`.
3. Credentialed backends: connection strings via environment only.
4. Agent memory: user-scoped memory wired only for `persist: user`.
5. Subagent write surface: enforced by prompt contract + hooks where
   configured; not technically guaranteed — declared here per the
   contract.
6. Subagent network: inherits host permissions; not restrictable
   per-agent — **unsafe posture** for programs whose agents must be
   network-isolated; say so in `state.md` if it matters.

## Usage reporting

Token totals per subagent (see Degradations #3): `estimated` basis for
rendered sessions; `exact` zero for skipped; `unavailable` for VM-side
control receipts.
