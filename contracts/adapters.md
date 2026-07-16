# OpenProse Host Port — adapter contract

OpenProse's portability claim is that any AI harness able to spawn
subagents can run `.prose` programs ("Prose Complete"). This document
makes that claim precise: the **host port** is the complete set of
primitives a substrate must provide, with their semantics. Everything
else in `prose.md` is substrate-independent VM logic.

A **substrate adapter** is one document per host —
`contracts/adapters/{host}.md` — that binds each primitive to concrete
host capabilities and declares its degradations. Bundled adapters:

| Adapter | Substrate |
| ------- | --------- |
| `adapters/claude-code.md` | Claude Code (Task tool) — the reference substrate |
| `adapters/openclaw.md` | OpenClaw (`sessions_spawn`) |

An adapter must bind every primitive or explicitly declare it
unsupported with the resulting capability loss (see Degradations).

## Primitives

### spawn_session

```
spawn_session(prompt, config) -> confirmation
  config: {model, agent_name, memory_ref?, binding_target, context_refs,
           permissions?, skills?}
```

Spawn one isolated subagent, blocking until completion. The subagent
receives: the resolved prompt, the binding target location (where to
write its output), context **references** (locations, not values), and —
for persistent agents — its memory location. Returns the subagent's
confirmation message (pointer + summary, never the full value):

```
Binding written: {name}
Location: {binding target location}
Summary: {one line}
```

Binding target locations follow the active state backend's layout (the
filesystem default: `.prose/runs/{run_id}/bindings/{name}.md`, frame
locals suffixed `__{execution_id}` — `state/filesystem.md`).
Concurrency: the VM may issue several spawns at once for `parallel:`;
the adapter states its real concurrency model and caps.

### read_state / write_state

```
read_state(location) -> bytes
write_state(location, bytes)
```

VM-side state I/O for the files the VM owns: `state.md`, `run.json`,
`program.prose` copies. Subagent outputs are NOT written through this —
subagents write their own bindings (see `spawn_session`); the VM only
reads confirmations and locations.

### copy_binding

```
copy_binding(source_location, target_location) -> fingerprint
```

Byte-exact copy of a binding (used by skip semantics — `prose.md`),
returning the copy's `sha256:` fingerprint so the VM can verify it
against the reused receipt's `output_fingerprint`.

### check_env

```
check_env(requirement) -> {available: bool, detail}
  requirement: state_backend | shell | network | registry | tool name
```

Capability probe, used by `prose doctor` and before constructs that
need optional capabilities (e.g. remote `use`, sqlite backend).

### run_shell

```
run_shell(command, {timeout_ms, sandbox}) -> {exit_code, stdout, stderr}
```

Shell execution on behalf of the program (agent `permissions:` allowing
`bash`). The adapter MUST state: whether a timeout is enforceable, what
sandboxing applies (working-directory confinement, network isolation),
and what happens on timeout. If the host cannot enforce timeouts, the
adapter says so — the VM then treats `timeout:` properties as advisory
and notes it in `state.md`.

### ask_user

```
ask_user(prompt) -> answer
```

Blocking user interaction (`input` declarations without caller-supplied
values, approval gates). Adapters for headless contexts (CI, cron) MUST
bind this to a failure or a declared default policy — never to silent
auto-approval.

### emit_receipt

```
emit_receipt(run_dir, receipt) -> content_hash
```

Append one receipt to the run ledger and update the manifest anchor —
exact algorithm in `primitives/session.md` (§8). This primitive is
VM-exclusive: no adapter may expose it to subagents.

## Referenced contracts

An adapter author needs, besides this file: `primitives/session.md` §8
(the `emit_receipt` algorithm), `contracts/receipt.md` (`usage.basis`
honesty rules the adapter's usage reporting feeds), and the active state
backend doc (`state/*.md`) for storage layout — including agent memory
(`persist:` scoping). What the **VM** does when a primitive fails
(abort vs fail-one-statement) is VM semantics (`prose.md`), deliberately
out of the port's scope.

## Degradations

Adapters declare degradations instead of hiding them. A degradation is a
named, documented gap plus the fallback the VM must apply. The canonical
example (observed throughout the original evaluation): a Claude Code
hook intermittently blocking subagent binding writes → fallback:
the VM persists the binding from the subagent's returned text via
`write_state`, and marks `usage.basis` accordingly. See
`adapters/claude-code.md`.

If a primitive is entirely unsupported, the adapter lists which language
constructs stop working (e.g. no `run_shell` → agents with `bash`
permissions fail at compile-gate, not mid-run).

## Security Contract

Postures are named and explicit. A configuration that weakens one of
these guarantees MUST be called **unsafe/trusted** in the adapter and in
`state.md` — silence is non-compliance.

1. **Remote `use` / registry fetch.** Fetching a program is code intake:
   pin what you ran (the run dir keeps the fetched copy; receipts carry
   its fingerprint via the compile IR). Adapters MUST NOT auto-execute
   remotely fetched programs without the user seeing what was fetched.
   No registry write-back of any run data.
2. **Shell and tool permissions.** `permissions:` in the program is the
   *maximum* grant; the adapter maps it onto the host's own permission
   system and the *intersection* applies. `run_shell` without sandbox
   metadata is an unsafe posture and must be named.
3. **State backends with credentials.** Connection strings for
   sqlite/postgres backends never appear in receipts, state.md, bindings,
   or IRs (contracts already exclude values — this extends to
   configuration). Adapters state where credentials live (env only).
4. **Agent memory leakage.** User-scoped agent memory (`~/.prose/agents/`)
   crosses projects by design — adapters MUST NOT wire user-scoped
   memory into a session unless the program declared `persist: user`.
   Project memory stays in the project.
5. **Subagent write surface.** Exactly: its binding target and (for
   persistent agents) its memory files. Receipts, run.json, state.md,
   other bindings are off-limits (`primitives/session.md` §8); adapters
   enforce what they can and declare what they cannot.
6. **No ambient network for subagents** unless the agent's declared
   permissions include it; an adapter that cannot restrict subagent
   network access declares that as an unsafe posture.

## Writing a new adapter

Copy this checklist into `contracts/adapters/{host}.md` and answer every
line against the host's real behavior — the port above is deliberately
sufficient to write an adapter without reading `prose.md`:

1. Bind each of the seven primitives (mechanism, limits, failure modes).
2. Concurrency: real parallelism? caps? queueing?
3. Timeouts: enforceable for sessions and shell?
4. Sandbox: what confinement applies to `run_shell` and subagent writes?
5. Degradations: known gaps + mandated fallbacks.
6. Security posture: answer contract points 1–6; name unsafe postures.
7. Usage reporting: what token/cost data the host exposes →
   what `usage.basis` the VM can honestly claim (`exact`/`estimated`).
