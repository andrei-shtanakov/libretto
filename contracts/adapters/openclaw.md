# Adapter: OpenClaw

Binds the host port (`contracts/adapters.md`) to OpenClaw. Extracted
from the inline "OpenClaw Runtime Mapping" that previously lived in
`SKILL.md`/`prose.md`; this document is now the canonical mapping.

## Primitive bindings

| Primitive | Binding |
| --------- | ------- |
| `spawn_session` | `sessions_spawn` |
| `read_state` / `write_state` | `read` / `write` |
| `copy_binding` | `read` + `write` (+ `exec` shasum for the fingerprint) |
| `check_env` | `exec` probes |
| `run_shell` | `exec` |
| `ask_user` | conversation turn (interactive contexts only) |
| `emit_receipt` | VM-side append per `primitives/session.md` §8 via `write` (or `exec` helper for hashing) |

Remote fetch (for `use`): `web_fetch`, or `exec` with `curl` when POST
is required.

## Unverified-binding notice

Unlike `adapters/claude-code.md`, this mapping has **not** been
exercised against the committed run corpus. Concurrency limits, timeout
enforceability, sandbox behavior, and usage reporting are unconfirmed —
before relying on this adapter, complete the "Writing a new adapter"
checklist in `contracts/adapters.md` against a real OpenClaw host and
replace this notice with findings. Until then, treat every checklist
item as *undeclared* (which per the security contract means: name the
posture unsafe/trusted where it matters).
