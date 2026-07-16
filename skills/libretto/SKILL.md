---
name: libretto
description: Libretto VM skill pack. Activate on any `libretto` command, legacy `prose` command, .libretto files, or Libretto mentions; orchestrates multi-agent workflows.
metadata: { "openclaw": { "emoji": "🪶", "homepage": "https://www.libretto.md" } }
---

# Libretto Skill

Libretto is a programming language for AI sessions. LLMs are simulators—when given a detailed system description, they don't just describe it, they _simulate_ it. The `libretto.md` specification describes a virtual machine with enough fidelity that a Libretto-capable host reading it _becomes_ that VM. Simulation with sufficient fidelity is implementation. **You are the Libretto VM host.**

## Host Port and Adapters

Substrate bindings live in adapter documents, not here:
`contracts/adapters.md` defines the seven host primitives + security
contract; `contracts/adapters/claude-code.md` (reference) and
`contracts/adapters/openclaw.md` bind them. On an unlisted substrate,
follow the "Writing a new adapter" checklist in `contracts/adapters.md`.

## When to Activate

Activate this skill when the user:

- **Uses ANY `libretto` command** (e.g., `libretto boot`, `libretto run`, `libretto compile`, `libretto update`, `libretto help`, etc.)
- Uses the legacy `prose` command during the transition window
- Asks to run a `.libretto` file
- Mentions "Libretto" or "Libretto program"
- Wants to orchestrate multiple AI agents from a script
- Has a file with `session "..."` or `agent name:` syntax
- Wants to create a reusable workflow

## Command Routing

When a user invokes `libretto <command>`, intelligently route based on intent. During the transition window, route `prose <command>` the same way and note that `prose` is a deprecated alias.

| Command                 | Action                                                        |
| ----------------------- | ------------------------------------------------------------- |
| `libretto help`            | Load `help.md`, guide user to what they need                  |
| `libretto run <file>`      | Load VM (`libretto.md` + state backend), execute the program     |
| `libretto run handle/slug` | Fetch from registry, then execute (see Remote Programs below) |
| `libretto compile <file>`  | Load `compiler.md`, validate + emit compile IR (`contracts/ir.md`) |
| `libretto compile --check <file>` | Freshness gate: `libretto-tools ir-check` — never recompiles |
| `libretto inspect <run>`   | Deterministic run summary (see Inspecting Runs below)         |
| `libretto doctor`          | Workspace + host health check (see Doctor below)              |
| `libretto update`          | Run migration (see Migration section below)                   |
| `libretto examples`        | Show or run example programs from `examples/`                 |
| Other                   | Intelligently interpret based on context                      |

### Important: Single Skill

There is only ONE skill: `libretto`. There are NO separate skills like `libretto-run`, `libretto-compile`, or `libretto-boot`. All `libretto` commands and legacy `prose` aliases route through this single skill.

### Resolving Example References

**Examples are bundled in `examples/` (same directory as this file).** When users reference examples by name (e.g., "run the gastown example"):

1. Read `examples/` to list available files
2. Match by partial name, keyword, or number
3. Run with: `libretto run examples/28-gas-town.libretto`

**Common examples by keyword:**
| Keyword | File |
|---------|------|
| hello, hello world | `examples/01-hello-world.libretto` |
| gas town, gastown | `examples/28-gas-town.libretto` |
| captain, chair | `examples/29-captains-chair.libretto` |
| forge, browser | `examples/37-the-forge.libretto` |
| parallel | `examples/16-parallel-reviews.libretto` |
| pipeline | `examples/21-pipeline-operations.libretto` |
| error, retry | `examples/22-error-handling.libretto` |

### Remote Programs

You can run any `.libretto` program from a URL or registry reference:

```bash
# Direct URL — any fetchable URL works
libretto run https://raw.githubusercontent.com/andrei-shtanakov/libretto/main/skills/libretto/examples/48-habit-miner.libretto

# Registry shorthand — handle/slug resolves to p.libretto.md
libretto run irl-danb/habit-miner
libretto run alice/code-review
```

**Resolution rules:**

| Input                               | Resolution                             |
| ----------------------------------- | -------------------------------------- |
| Starts with `http://` or `https://` | Fetch directly from URL                |
| Contains `/` but no protocol        | Resolve to `https://p.libretto.md/{path}` |
| Otherwise                           | Treat as local file path               |

**Steps for remote programs:**

1. Apply resolution rules above
2. Fetch the `.libretto` content
3. Load the VM and execute as normal

This same resolution applies to `use` statements inside `.libretto` files:

```libretto
use "https://example.com/my-program.libretto"  # Direct URL
use "alice/research" as research             # Registry shorthand
```

---

## File Locations

**Do NOT search for Libretto documentation files.** All skill files are co-located with this SKILL.md file:

| File                       | Location                    | Purpose                                        |
| -------------------------- | --------------------------- | ---------------------------------------------- |
| `libretto.md`                 | Same directory as this file | VM semantics (load to run programs)            |
| `help.md`                  | Same directory as this file | Help, FAQs, onboarding (load for `libretto help`) |
| `state/filesystem.md`      | Same directory as this file | File-based state (default, load with VM)       |
| `state/in-context.md`      | Same directory as this file | In-context state (on request)                  |
| `state/sqlite.md`          | Same directory as this file | SQLite state (experimental, on request)        |
| `state/postgres.md`        | Same directory as this file | PostgreSQL state (experimental, on request)    |
| `compiler.md`              | Same directory as this file | Compiler/validator (load only on request)      |
| `guidance/patterns.md`     | Same directory as this file | Best practices (load when writing .libretto)      |
| `guidance/antipatterns.md` | Same directory as this file | What to avoid (load when writing .libretto)       |
| `examples/`                | Same directory as this file | 51 example programs                            |

**User workspace files** (these ARE in the user's project):

| File/Directory   | Location                 | Purpose                           |
| ---------------- | ------------------------ | --------------------------------- |
| `.libretto/.env`    | User's working directory | Config (key=value format)         |
| `.libretto/runs/`   | User's working directory | Runtime state for file-based mode |
| `.libretto/agents/` | User's working directory | Project-scoped persistent agents  |
| `*.libretto` files  | User's project           | User-created programs to execute  |

**User-level files** (in user's home directory, shared across all projects):

| File/Directory     | Location        | Purpose                                       |
| ------------------ | --------------- | --------------------------------------------- |
| `~/.libretto/agents/` | User's home dir | User-scoped persistent agents (cross-project) |

When you need to read `libretto.md` or `compiler.md`, read them from the same directory where you found this SKILL.md file. Never search the user's workspace for these files.

---

## Core Documentation

| File                       | Purpose                         | When to Load                                                          |
| -------------------------- | ------------------------------- | --------------------------------------------------------------------- |
| `libretto.md`                 | VM / Interpreter                | Always load to run programs                                           |
| `state/filesystem.md`      | File-based state                | Load with VM (default)                                                |
| `state/in-context.md`      | In-context state                | Only if user requests `--in-context` or says "use in-context state"   |
| `state/sqlite.md`          | SQLite state (experimental)     | Only if user requests `--state=sqlite` (requires sqlite3 CLI)         |
| `state/postgres.md`        | PostgreSQL state (experimental) | Only if user requests `--state=postgres` (requires psql + PostgreSQL) |
| `compiler.md`              | Compiler / Validator            | **Only** when user asks to compile or validate                        |
| `guidance/patterns.md`     | Best practices                  | Load when **writing** new .libretto files                                |
| `guidance/antipatterns.md` | What to avoid                   | Load when **writing** new .libretto files                                |

### Authoring Guidance

When the user asks you to **write or create** a new `.libretto` file, load the guidance files:

- `guidance/patterns.md` — Proven patterns for robust, efficient programs
- `guidance/antipatterns.md` — Common mistakes to avoid

Do **not** load these when running or compiling—they're for authoring only.

### State Modes

Libretto supports three state management approaches:

| Mode                        | When to Use                                                       | State Location              |
| --------------------------- | ----------------------------------------------------------------- | --------------------------- |
| **filesystem** (default)    | Complex programs, resumption needed, debugging                    | `.libretto/runs/{id}/` files   |
| **in-context**              | Simple programs (<30 statements), no persistence needed           | Conversation history        |
| **sqlite** (experimental)   | Queryable state, atomic transactions, flexible schema             | `.libretto/runs/{id}/state.db` |
| **postgres** (experimental) | True concurrent writes, external integrations, team collaboration | PostgreSQL database         |

**Default behavior:** When loading `libretto.md`, also load `state/filesystem.md`. This is the recommended mode for most programs.

**Switching modes:** If the user says "use in-context state" or passes `--in-context`, load `state/in-context.md` instead.

**Experimental SQLite mode:** If the user passes `--state=sqlite` or says "use sqlite state", load `state/sqlite.md`. This mode requires `sqlite3` CLI to be installed (pre-installed on macOS, available via package managers on Linux/Windows). If `sqlite3` is unavailable, warn the user and fall back to filesystem state.

**Experimental PostgreSQL mode:** If the user passes `--state=postgres` or says "use postgres state":

**⚠️ Security Note:** Database credentials in `LIBRETTO_POSTGRES_URL` are passed to subagent sessions and visible in logs. Advise users to use a dedicated database with limited-privilege credentials. See `state/postgres.md` for secure setup guidance.

1. **Check for connection configuration first:**

   ```bash
   # Check .libretto/.env for LIBRETTO_POSTGRES_URL
   cat .libretto/.env 2>/dev/null | grep LIBRETTO_POSTGRES_URL
   # Or check environment variable
   echo $LIBRETTO_POSTGRES_URL
   ```

2. **If connection string exists, verify connectivity:**

   ```bash
   psql "$LIBRETTO_POSTGRES_URL" -c "SELECT 1" 2>&1
   ```

3. **If not configured or connection fails, advise the user:**

   ```
   ⚠️  PostgreSQL state requires a connection URL.

   To configure:
   1. Set up a PostgreSQL database (Docker, local, or cloud)
   2. Add connection string to .libretto/.env:

      echo "LIBRETTO_POSTGRES_URL=postgresql://user:pass@localhost:5432/prose" >> .libretto/.env

   Quick Docker setup:
      docker run -d --name prose-pg -e POSTGRES_DB=prose -e POSTGRES_HOST_AUTH_METHOD=trust -p 5432:5432 postgres:16
      echo "LIBRETTO_POSTGRES_URL=postgresql://postgres@localhost:5432/prose" >> .libretto/.env

   See state/postgres.md for detailed setup options.
   ```

4. **Only after successful connection check, load `state/postgres.md`**

This mode requires both `psql` CLI and a running PostgreSQL server. If either is unavailable, warn and offer fallback to filesystem state.

**Context warning:** `compiler.md` is large. Only load it when the user explicitly requests compilation or validation. After compiling, recommend `/compact` or a new session before running—don't keep both docs in context.

## Examples

The `examples/` directory contains 51 example programs:

- **01-08**: Basics (hello world, research, code review, debugging)
- **09-12**: Agents and skills
- **13-15**: Variables and composition
- **16-19**: Parallel execution
- **20-21**: Loops and pipelines
- **22-23**: Error handling
- **24-27**: Advanced (choice, conditionals, blocks, interpolation)
- **28**: Gas Town (multi-agent orchestration)
- **29-32**: Captain's chair pattern + automated PR review
- **33-37**: Production workflows (PR auto-fix, content pipeline, feature factory, bug hunter, The Forge)
- **38**: Skill scan (skill discovery and analysis)
- **39**: Architect by simulation (design through simulated implementation)
- **40-43**: Recursive Language Models (self-refine, divide-conquer, filter-recurse, pairwise)
- **44-51**: Meta / self-hosting (endpoint tests, plugin release, crystallizer, self-improvement, habit-miner, retrospective)

Start with `01-hello-world.libretto` or try `37-the-forge.libretto` to watch AI build a web browser.

## Execution

When first invoking the Libretto VM in a session, display this banner:

```
┌─────────────────────────────────────┐
│         ◇ Libretto VM ◇            │
│       A new kind of computer        │
└─────────────────────────────────────┘
```

To execute a `.libretto` file, you become the Libretto VM:

1. **Read `libretto.md`** — this document defines how you embody the VM
2. **You ARE the VM** — your conversation is its memory, your tools are its instructions
3. **Spawn sessions** — each `session` statement triggers a Task tool call
4. **Narrate state** — use the narration protocol to track execution ([Position], [Binding], [Success], etc.)
5. **Evaluate intelligently** — `**...**` markers require your judgment

## Help & FAQs

For syntax reference, FAQs, and getting started guidance, load `help.md`.

---

## Inspecting Runs (`libretto inspect <run>`)

Every run leaves a machine-readable receipt ledger
(`.libretto/runs/{run-id}/receipts.jsonl` + `run.json`; contract:
`contracts/receipt.md`). `libretto inspect` is a **deterministic reader** over
those artifacts — prefer tooling over LLM re-reading:

1. **If the Python tooling is available** (repo checkout with `tools/`, or
   `libretto-tools` installed): run it and relay the output —
   ```sh
   uv run --project <repo>/tools libretto-tools inspect <run-dir> [--json]
   uv run --project <repo>/tools libretto-tools verify <run-dir>
   ```
   Use `--json` when the consumer is a program or CI, text otherwise.
2. **Fallback** (no tooling on this host): run `lib/inspector.libretto` via
   `libretto run` — the LLM-driven inspector. Note in your answer that the
   summary was produced by an LLM pass, not the deterministic reader.

Never recompute or "fix" receipts by hand — the ledger is append-only and
`verify` exists precisely to catch edits.

---

## Doctor (`libretto doctor`)

Two halves — run both and report together:

1. **Deterministic half** (when tooling is available):
   ```sh
   uv run --project <repo>/tools libretto-tools doctor [root]
   ```
   Checks spec/contract files, state-directory writability, compile-IR
   freshness, and run-ledger chain consistency. Keyless, exit 0/1.
2. **Host half** (you, against `contracts/adapters.md`): confirm the
   seven host primitives are actually available on this substrate —
   can you spawn a subagent (`spawn_session`)? read/write `.libretto/`
   files? run shell with a timeout? ask the user (or is this headless —
   then flag `ask_user` as unavailable)? Name the active adapter
   (`contracts/adapters/*.md`) and any of its declared degradations that
   currently apply (e.g. hook-blocked binding writes).

Report failures plainly; never "fix" artifacts to make checks pass.

---

## Migration (`libretto update`)

When a user invokes `libretto update`, check for legacy file structures and migrate them to the current format.

### Legacy Paths to Check

| Legacy Path         | Current Path   | Notes                            |
| ------------------- | -------------- | -------------------------------- |
| `.libretto/state.json` | `.libretto/.env`  | Convert JSON to key=value format |
| `.libretto/execution/` | `.libretto/runs/` | Rename directory                 |

### Migration Steps

1. **Check for `.libretto/state.json`**
   - If exists, read the JSON content
   - Convert to `.env` format:
     ```json
     { "LIBRETTO_TELEMETRY": "enabled", "USER_ID": "user-xxx", "SESSION_ID": "sess-xxx" }
     ```
     becomes:
     ```env
     LIBRETTO_TELEMETRY=enabled
     USER_ID=user-xxx
     SESSION_ID=sess-xxx
     ```
   - Write to `.libretto/.env`
   - Delete `.libretto/state.json`

2. **Check for `.libretto/execution/`**
   - If exists, rename to `.libretto/runs/`
   - The internal structure of run directories may also have changed; migration of individual run state is best-effort

3. **Create `.libretto/agents/` if missing**
   - This is a new directory for project-scoped persistent agents

### Migration Output

```
🔄 Migrating Libretto workspace...
  ✓ Converted .libretto/state.json → .libretto/.env
  ✓ Renamed .libretto/execution/ → .libretto/runs/
  ✓ Created .libretto/agents/
✅ Migration complete. Your workspace is up to date.
```

If no legacy files are found:

```
✅ Workspace already up to date. No migration needed.
```

### Skill File References (for maintainers)

These documentation files were renamed in the skill itself (not user workspace):

| Legacy Name       | Current Name               |
| ----------------- | -------------------------- |
| `docs.md`         | `compiler.md`              |
| `patterns.md`     | `guidance/patterns.md`     |
| `antipatterns.md` | `guidance/antipatterns.md` |

If you encounter references to the old names in user prompts or external docs, map them to the current paths.
