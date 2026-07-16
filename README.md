# Libretto

A programming language for AI sessions — zero-dependency, pure-specification.

There is no runtime binary, no package manager, no build system. The entire project is markdown and `.libretto` files that an LLM reads to become the Libretto VM. Simulation with sufficient fidelity is implementation.

## Status

This repository is an **active downstream / research fork** of upstream
[`openprose/prose`](https://github.com/openprose/prose). Upstream has since
evolved into a responsibility-based model with a TypeScript runtime
(Reactor); this repo keeps the original spec-as-VM `.libretto` language and
adopts upstream *protocols* (receipts, compile IR, materiality) on a
Python verification toolchain instead. See
`docs/plans/2026-07-16-development-plan.md` for the roadmap.

**What to expect (measured, not aspirational):** a seven-phase empirical
evaluation (`evaluation/results/final-verdict.md`) found the VM executes the
full language faithfully, with output quality matching plain single-session
work — at a **2–6× token premium**, of which roughly half is session-boundary
overhead (~46K tokens of context floor per session). Libretto buys
**reliability, auditability, and reproducibility** — independent critic
sessions, complete replayable run trails, context isolation — not efficiency.
Use it when those properties matter; use a plain session when they don't.

## Quick Start

```
libretto run examples/01-hello-world.libretto
```

Or try something ambitious:

```
libretto run examples/37-the-forge.libretto
```

## How It Works

1. You write a `.libretto` program — structured instructions for orchestrating AI agents
2. The LLM reads the VM specification (`libretto.md`) and *becomes* the virtual machine
3. Each `session` statement spawns a real subagent via the Task tool
4. State persists in files, databases, or conversation context

The syntax is intentionally familiar (Python-like indentation) but the semantics are entirely different — agents, sessions, and control flow instead of functions, classes, and general-purpose computation.

## Project Structure

| Path | Purpose |
|------|---------|
| `SKILL.md` | Activation triggers, command routing |
| `libretto.md` | VM specification — execution semantics |
| `compiler.md` | Full grammar, validation rules |
| `help.md` | FAQs, onboarding, syntax reference |
| `state/` | 4 state backends (filesystem, in-context, sqlite, postgres) |
| `primitives/` | Session context management |
| `guidance/` | Best practices and antipatterns |
| `lib/` | Standard library (9 programs) |
| `examples/` | 51 example programs |
| `examples/runs/` | Committed real runs — keyless replay/verification corpus |
| `alts/` | 5 alternative syntax registers |
| `contracts/` | Machine contracts (receipt ledger) + pinned upstream schemas |
| `tools/` | Optional Python verification tooling (`libretto-tools inspect\|verify`) |

## Commands

| Command | What it does |
|---------|-------------|
| `libretto run <file>` | Execute a .libretto program |
| `libretto compile <file>` | Validate syntax without running |
| `libretto help` | Interactive help and onboarding |
| `libretto examples` | Browse example programs |
| `libretto update` | Migrate legacy workspace files |

## Examples

51 examples from hello-world to "build a browser from scratch":

- **01-08**: Basics (research, code review, debugging)
- **09-12**: Agents and skills
- **13-27**: Variables, parallel execution, loops, pipelines, error handling, conditionals
- **28-31**: Orchestration systems (Gas Town, Captain's Chair)
- **32-37**: Production workflows (PR review, content pipeline, The Forge)
- **38-39**: Skill scan, architecture patterns
- **40-43**: Recursive Language Models (self-refine, divide-conquer, filter-recurse, pairwise)
- **44-51**: Meta / self-hosting (endpoint tests, plugin release, crystallizer, self-improvement)

## Learn More

- `libretto help` — Interactive onboarding
- `examples/README.md` — Full example catalog with patterns
- `guidance/patterns.md` — Best practices for writing .libretto programs
- `ROADMAP.md` — Development roadmap

## License

MIT
