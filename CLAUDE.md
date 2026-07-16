# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

OpenProse is a programming language for AI sessions — zero-dependency, pure-specification. There is no runtime binary, no package.json, no build system. The entire project is markdown (`.md`) and prose program (`.prose`) files that an LLM reads to become the OpenProse VM. "Simulation with sufficient fidelity is implementation."

**License:** MIT

## Architecture

The project has a layered documentation architecture where each layer builds on the previous:

| Layer | Files | Purpose |
|-------|-------|---------|
| **Skill entry** | `SKILL.md` | Activation triggers, command routing, file locations |
| **VM spec** | `prose.md` (36KB) | Execution semantics — how to run programs |
| **Language spec** | `compiler.md` (83KB) | Full grammar, validation rules, compilation |
| **State backends** | `state/filesystem.md`, `state/in-context.md`, `state/sqlite.md`, `state/postgres.md` | Four state management strategies |
| **Session primitives** | `primitives/session.md` | Subagent context management, compaction guidelines |
| **Authoring guidance** | `guidance/patterns.md`, `guidance/antipatterns.md` | Best practices for writing .prose programs |
| **Standard library** | `lib/*.prose` (9 programs) | Inspector, profiler, cost-analyzer, memory, etc. |
| **Examples** | `examples/*.prose` (51 programs) | From hello-world to "build a browser from scratch" |
| **Alternative syntaxes** | `alts/*.md` (5 files) | Borges, Folk, Arabian Nights, Homer, Kafka keyword skins |

### Key Concept: Specification-as-VM

The LLM reads `prose.md` and becomes the VM. Each `session` statement triggers a real `Task` tool call spawning a real subagent. The VM never holds full binding values — only pointers to where outputs are stored (filesystem paths or DB coordinates).

### Command Routing (via SKILL.md)

| Command | What loads |
|---------|-----------|
| `prose run <file>` | `prose.md` + `state/filesystem.md` (default) |
| `prose compile <file>` | `compiler.md` only |
| `prose help` | `help.md` |
| `prose examples` | `examples/` listing |
| `prose update` | Migration logic (in SKILL.md) |

### Context Budget Warning

`compiler.md` is 83KB (~2971 lines). Only load it when the user explicitly requests compilation/validation. After compiling, recommend `/compact` before running — don't keep both `compiler.md` and `prose.md` in context simultaneously.

## Working With This Codebase

### Editing Specifications

Changes to `prose.md` or `compiler.md` affect ALL `.prose` programs. These are the core VM and language specs — edit with care. Verify changes against examples.

### Writing New .prose Programs

Load `guidance/patterns.md` and `guidance/antipatterns.md` before authoring. Key patterns: captain's chair (examples 29-31), fan-out-fan-in, RLM recursive processing (examples 40-43).

### Standard Library (`lib/`)

The stdlib forms a self-improvement loop:
```
Run Program -> Inspector -> VM Improver -> PR
                         -> Program Improver -> PR
                         -> Cost Analyzer -> optimizations
```

### State Backends

Default is filesystem (`state/filesystem.md`). State lives in `.prose/runs/{YYYYMMDD}-{HHMMSS}-{random6}/`. Four backends available — filesystem, in-context, sqlite (experimental), postgres (experimental). Each is a separate `.md` spec the VM loads.

### Alternative Syntaxes (`alts/`)

These map the same semantics to different keyword sets (e.g., `agent` -> `dreamer`, `session` -> `dream` in Borges register). Used for learnability research, not production.

## File Conventions

- `.prose` — executable programs (Python-like indentation, no actual Python)
- `.md` — specifications, documentation, state files
- `.prose/` directory (in user projects) — runtime state, agent memory, config
- `bindings/{name}.md` — subagent outputs (written by subagents, not the VM)
- `agents/{name}/memory.md` — persistent agent state with segment files `{name}-NNN.md`

## Validation

Two tiers — deterministic (CI-enforced, keyless) and LLM-driven:

**Deterministic (`.github/workflows/ci.yml`, required on every PR):**
1. `openprose-tools lint <file.prose>` — mechanical subset of `compiler.md`
   (indentation, keywords across all 6 registers, balanced blocks, flat
   namespace, agent/block references). Errors fail CI; OP009 warnings mark
   constructs pending a spec decision. It is a linter, not the compiler.
2. `openprose-tools verify <run-dir>` — receipt-ledger chain consistency
   (`contracts/receipt.md`) over the committed runs in `examples/runs/`.
3. `tests/fixtures/` — regression corpus (lint cases with expected
   diagnostics; corrupted run ledgers) exercised by `tools/tests/`.
4. Python quality gates on `tools/`: pytest, ruff, pyrefly.

**LLM-driven (manual, advisory):**
1. `prose compile <file>` — full semantic validation against `compiler.md`
2. The 51 examples as the implicit interpretation suite — all must also
   lint clean
3. `lib/inspector.prose` — post-run evaluation of execution fidelity
4. Model smoke before releases: `prose run examples/01-hello-world.prose`
   in an OpenProse-capable host (deliberately not automated in CI)

## Repo scope & boundaries

- **Этот репо:** `open-prose` — git-корень `all_ai_orchestrators/open-prose/`, remote `git@github.com:andrei-shtanakov/open-prose.git`.
- **Соседи (READ-ONLY reference):** `../arbiter/`, `../atp-platform/`, `../deployer/`, `../dispatcher/`, `../Maestro/`, `../proctor/`, `../prograph/`, `../prograph-vault/`, `../robin-runtime/`, `../robin-toolkit/`, `../spec-runner/`, `../spec-runner-vscode/`, `../steward/` — их код не редактировать.
- Нужна правка у соседа → **стоп**: запиши handoff в `../prograph-vault/authored/notes/`
  (кросс-проектное) или `../_cowork_output/` (черновик), не трогай его файлы.
- Кросс-репные контракты — **вендорить пиненой копией внутрь**, не ссылаться наружу.
- Полное правило (SSOT): `../prograph-vault/authored/rules/repo-boundaries.md`.

## Git workflow (у репо есть remote)

- Ветка `<type>/<slug>` → push → `gh pr create`. **Прямые коммиты в `main` запрещены.**
- После открытия PR — прочитать ревью **GitHub Copilot**: валидные замечания исправлять
  новыми коммитами в ту же ветку; невалидные — ответить с обоснованием, **не применять
  вслепую**; итерировать, пока не останется открытых замечаний.
- **Не мержить.** Мерж делает пользователь.
- После мержа пользователем: `git switch main && git pull --ff-only`, затем удалить
  влитую ветку (`git branch -d <branch>`) и `git fetch --prune`; убрать прочие влитые ветки.
- Никогда не делать force-push в общие ветки; не трогать другие репо (см. scope выше).
- Полное правило (SSOT): `../prograph-vault/authored/rules/git-workflow.md`.
