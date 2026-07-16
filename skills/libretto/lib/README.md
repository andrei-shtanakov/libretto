# Libretto Standard Library

Core programs that ship with Libretto. Production-quality, well-tested programs for common tasks.

## Programs

### Evaluation & Improvement

| Program                  | Description                                                    |
| ------------------------ | -------------------------------------------------------------- |
| `inspector.libretto`        | Post-run analysis for runtime fidelity and task effectiveness  |
| `vm-improver.libretto`      | Analyzes inspections and proposes PRs to improve the VM        |
| `program-improver.libretto` | Analyzes inspections and proposes PRs to improve .libretto source |
| `cost-analyzer.libretto`    | Token usage and cost pattern analysis                          |
| `profiler.libretto`         | Performance profiling and token usage analysis                 |
| `calibrator.libretto`       | Validates light evaluations against deep evaluations           |
| `error-forensics.libretto`  | Root cause analysis for failed runs                            |

### Memory

| Program                | Description                              |
| ---------------------- | ---------------------------------------- |
| `user-memory.libretto`    | Cross-project persistent personal memory |
| `project-memory.libretto` | Project-scoped institutional memory      |

## The Improvement Loop

The evaluation programs form a recursive improvement cycle:

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   Run Program  ──►  Inspector  ──►  VM Improver ──► PR     │
│        ▲                │                                   │
│        │                ▼                                   │
│        │         Program Improver ──► PR                    │
│        │                │                                   │
│        └────────────────┘                                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

Supporting analysis:

- **cost-analyzer** — Where does the money go? Optimization opportunities.
- **calibrator** — Are cheap evaluations reliable proxies for expensive ones?
- **error-forensics** — Why did a run fail? Root cause analysis.

## Usage

```bash
# Inspect a completed run
libretto run lib/inspector.libretto
# Inputs: run_path, depth (light|deep), target (vm|task|all)

# Propose VM improvements
libretto run lib/vm-improver.libretto
# Inputs: inspection_path, prose_repo

# Propose program improvements
libretto run lib/program-improver.libretto
# Inputs: inspection_path, run_path

# Analyze costs
libretto run lib/cost-analyzer.libretto
# Inputs: run_path, scope (single|compare|trend)

# Validate light vs deep evaluation
libretto run lib/calibrator.libretto
# Inputs: run_paths, sample_size

# Investigate failures
libretto run lib/error-forensics.libretto
# Inputs: run_path, focus (vm|program|context|external)

# Memory programs (recommend sqlite+ backend)
libretto run lib/user-memory.libretto --backend sqlite+
# Inputs: mode (teach|query|reflect), content

libretto run lib/project-memory.libretto --backend sqlite+
# Inputs: mode (ingest|query|update|summarize), content
```

## Memory Programs

The memory programs use persistent agents to accumulate knowledge:

**user-memory** (`persist: user`)

- Learns your preferences, decisions, patterns across all projects
- Remembers mistakes and lessons learned
- Answers questions from accumulated knowledge

**project-memory** (`persist: project`)

- Understands this project's architecture and decisions
- Tracks why things are the way they are
- Answers questions with project-specific context

Both recommend `--backend sqlite+` for durable persistence.

## Design Principles

1. **Production-ready** — Tested, documented, handles edge cases
2. **Composable** — Can be imported via `use` in other programs
3. **User-scoped state** — Cross-project utilities use `persist: user`
4. **Minimal dependencies** — No external services required
5. **Clear contracts** — Well-defined inputs and outputs
6. **Incremental value** — Useful in simple mode, more powerful with depth
