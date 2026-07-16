# Libretto Help

Load this file when a user invokes `libretto help` or asks about Libretto.

---

## Welcome

Libretto is a programming language for AI sessions. You write structured programs that orchestrate AI agents, and the VM (this session) executes them by spawning real subagents.

**A long-running AI session is a Turing-complete computer. Libretto is a programming language for it.**

---

## What Do You Want to Automate?

When a user invokes `libretto help`, guide them toward defining what they want to build. Use the AskUserQuestion tool:

```
Question: "What would you like to automate with Libretto?"
Header: "Goal"
Options:
  1. "Run a workflow" - "I have a .libretto file to execute"
  2. "Build something new" - "Help me create a program for a specific task"
  3. "Learn the syntax" - "Show me examples and explain how it works"
  4. "Explore possibilities" - "What can Libretto do?"
```

**After the user responds:**

- **Run a workflow**: Ask for the file path, then load `libretto.md` and execute
- **Build something new**: Ask them to describe their task, then help write a .libretto program (load `guidance/patterns.md`)
- **Learn the syntax**: Show examples from `examples/`, explain the VM model
- **Explore possibilities**: Walk through key examples like `37-the-forge.libretto` or `28-gas-town.libretto`

---

## Available Commands

| Command                | What it does                            |
| ---------------------- | --------------------------------------- |
| `libretto help`           | This help - guides you to what you need |
| `libretto run <file>`     | Execute a .libretto program                |
| `libretto compile <file>` | Validate syntax without running         |
| `libretto update`         | Migrate legacy workspace files          |
| `libretto examples`       | Browse and run example programs         |

---

## Quick Start

**Run an example:**

```
libretto run examples/01-hello-world.libretto
```

**Create your first program:**

```
libretto help
→ Select "Build something new"
→ Describe what you want to automate
```

---

## FAQs

### What AI assistants are supported?

Claude Code, OpenCode, and Amp. Any harness that runs a sufficiently intelligent model and supports primitives like subagents are considered "Prose Complete".

### How is this a VM?

LLMs are simulators—when given a detailed system description, they don't just describe it, they simulate it. The `libretto.md` spec describes a VM with enough fidelity that reading it induces simulation. But simulation with sufficient fidelity is implementation: each session spawns a real subagent, outputs are real artifacts, state persists in conversation history or files. The simulation is the execution.

### What's "intelligent IoC"?

Traditional IoC containers (Spring, Guice) wire up dependencies from configuration files. Libretto's container is an AI session that wires up agents using understanding. It doesn't just match names—it understands context, intent, and can make intelligent decisions about execution.

### This looks like Python.

The syntax is intentionally familiar—Python's indentation-based structure is readable and self-evident. But the semantics are entirely different. Libretto has no functions, no classes, no general-purpose computation. It has agents, sessions, and control flow. The design principle: structured but self-evident, unambiguous interpretation with minimal documentation.

### Why not English?

English is already an agent framework—we're not replacing it, we're structuring it. Plain English doesn't distinguish sequential from parallel, doesn't specify retry counts, doesn't scope variables. Libretto uses English exactly where ambiguity is a feature (inside `**...**`), and structure everywhere else. The fourth wall syntax lets you lean on AI judgment precisely when you want to.

### Why not YAML?

We started with YAML. The problem: loops, conditionals, and variable declarations aren't self-evident in YAML—and when you try to make them self-evident, it gets verbose and ugly. More fundamentally, YAML optimizes for machine parseability. Libretto optimizes for intelligent machine legibility. It doesn't need to be parsed—it needs to be understood. That's a different design target entirely.

### Why not LangChain/CrewAI/AutoGen?

Those are orchestration libraries—they coordinate agents from outside. Libretto runs inside the agent session—the session itself is the IoC container. This means zero external dependencies and portability across any AI assistant. Switch from Claude Code to Codex? Your .libretto files still work.

---

## Syntax at a Glance

```prose
session "prompt"              # Spawn subagent
agent name:                   # Define agent template
let x = session "..."         # Capture result
parallel:                     # Concurrent execution
repeat N:                     # Fixed loop
for x in items:               # Iteration
loop until **condition**:     # AI-evaluated loop
try: ... catch: ...           # Error handling
if **condition**: ...         # Conditional
choice **criteria**: option   # AI-selected branch
block name(params):           # Reusable block
do blockname(args)            # Invoke block
items | map: ...              # Pipeline
```

For complete syntax and validation rules, see `compiler.md`.

---

## Examples

The `examples/` directory contains 51 example programs:

| Range | Category                                                                          |
| ----- | --------------------------------------------------------------------------------- |
| 01-08 | Basics (hello world, research, code review, debugging)                            |
| 09-12 | Agents and skills                                                                 |
| 13-15 | Variables and composition                                                         |
| 16-19 | Parallel execution                                                                |
| 20-21 | Loops and pipelines                                                               |
| 22-23 | Error handling                                                                    |
| 24-27 | Advanced (choice, conditionals, blocks, interpolation)                            |
| 28    | Gas Town (multi-agent orchestration)                                              |
| 29-32 | Captain's chair pattern + automated PR review                                     |
| 33-37 | Production workflows (PR auto-fix, content pipeline, feature factory, bug hunter, The Forge) |
| 38    | Skill scan (skill discovery and analysis)                                         |
| 39    | Architect by simulation (design through simulated implementation)                 |
| 40-43 | Recursive Language Models (self-refine, divide-conquer, filter-recurse, pairwise) |
| 44-51 | Meta / self-hosting (endpoint tests, plugin release, crystallizer, self-improvement, habit-miner, retrospective) |

**Recommended starting points:**

- `01-hello-world.libretto` - Simplest possible program
- `16-parallel-reviews.libretto` - See parallel execution
- `37-the-forge.libretto` - Watch AI build a web browser
- `40-rlm-self-refine.libretto` - Recursive Language Model pattern
