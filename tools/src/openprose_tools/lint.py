"""Deterministic linter for ``.prose`` files.

This is a **linter, not the compiler**: it checks the mechanically
decidable subset of ``compiler.md`` (indentation, known keywords across
all six syntax registers, balanced blocks, the root-scope flat-namespace
rule, agent/block reference resolution). Semantic validation — context
wiring, discretion, types — remains the LLM compiler's job.

Diagnostic codes:

- OP001 tab character in indentation
- OP002 dedent to a level that was never opened
- OP003 block header with no indented body
- OP004 unknown statement keyword
- OP005 duplicate root-scope declaration (flat namespace)
- OP006 reference to undefined agent
- OP007 reference to undefined block
- OP008 duplicate agent/block definition
- OP009 construct used by bundled programs but absent from compiler.md
  grammar (warning — pending a spec decision; see ROADMAP)
"""

import re
from dataclasses import dataclass
from pathlib import Path

# Canonical statement-opening keywords (compiler.md grammar).
_CANONICAL_STARTERS = {
    "use",
    "input",
    "output",
    "agent",
    "session",
    "resume",
    "let",
    "const",
    "parallel",
    "repeat",
    "for",
    "loop",
    "try",
    "catch",
    "finally",
    "choice",
    "option",
    "if",
    "elif",
    "else",
    "do",
    "block",
    "throw",
}

# Property keys valid as indented property lines.
_CANONICAL_PROPERTIES = {
    "model",
    "prompt",
    "context",
    "retry",
    "backoff",
    "persist",
    "skills",
    "permissions",
    "read",
    "write",
    "timeout",
    "max",
    "on-fail",
    "count",
    "max_concurrent",
}

# Constructs that appear in bundled examples/stdlib but are NOT in the
# compiler.md grammar. Reported as OP009 warnings until the spec either
# adopts or removes them (tracked in ROADMAP).
_UNSPECIFIED_STARTERS = {"import", "return", "break", "assert"}

# Register aliases (alias -> canonical), extracted from alts/*.md.
# A cross-check test asserts this map stays in sync with the alts tables.
REGISTER_ALIASES: dict[str, str] = {
    # arabian-nights
    "djinn": "agent",
    "tale": "session",
    "bazaar": "parallel",
    "frame": "block",
    "conjure": "use",
    "wish": "input",
    "gift": "output",
    "oath": "const",
    "scroll": "context",
    "telling": "loop",
    "crossroads": "choice",
    "path": "option",
    "should": "if",
    "otherwise": "else",
    "venture": "try",
    "curse": "throw",
    "persist": "retry",
    "command": "prompt",
    "spirit": "model",
    # borges
    "dreamer": "agent",
    "dream": "session",
    "forking": "parallel",
    "chapter": "block",
    "retrieve": "use",
    "axiom": "input",
    "theorem": "output",
    "inscribe": "let",
    "zahir": "const",
    "memory": "context",
    "labyrinth": "loop",
    "bifurcation": "choice",
    "branch": "option",
    "lest": "catch",
    "ultimately": "finally",
    "shatter": "throw",
    "recur": "retry",
    "query": "prompt",
    "author": "model",
    # folk
    "sprite": "agent",
    "scene": "session",
    "ensemble": "parallel",
    "act": "block",
    "summon": "use",
    "given": "input",
    "yield": "output",
    "name": "let",
    "seal": "const",
    "bearing": "context",
    "when": "if",
    "cry": "throw",
    "charge": "prompt",
    "voice": "model",
    # homer
    "hero": "agent",
    "trial": "session",
    "host": "parallel",
    "book": "block",
    "invoke": "use",
    "omen": "input",
    "glory": "output",
    "decree": "let",
    "fate": "const",
    "tidings": "context",
    "ordeal": "loop",
    "lament": "throw",
    "muse": "model",
    # kafka
    "clerk": "agent",
    "proceeding": "session",
    "departments": "parallel",
    "regulation": "block",
    "requisition": "use",
    "petition": "input",
    "verdict": "output",
    "file": "let",
    "statute": "const",
    "dossier": "context",
    "appeal": "loop",
    "tribunal": "choice",
    "ruling": "option",
    "submit": "try",
    "regardless": "finally",
    "reject": "throw",
    "resubmit": "retry",
    "directive": "prompt",
    "authority": "model",
}

_STARTERS = _CANONICAL_STARTERS | {
    alias for alias, canon in REGISTER_ALIASES.items() if canon in _CANONICAL_STARTERS
}
_PROPERTIES = _CANONICAL_PROPERTIES | {
    alias for alias, canon in REGISTER_ALIASES.items() if canon in _CANONICAL_PROPERTIES
}

_DECL_KEYWORDS = {"let", "const", "output"} | {
    alias
    for alias, canon in REGISTER_ALIASES.items()
    if canon in {"let", "const", "output"}
}
_AGENT_KEYWORDS = {"agent"} | {a for a, c in REGISTER_ALIASES.items() if c == "agent"}
_BLOCK_KEYWORDS = {"block"} | {a for a, c in REGISTER_ALIASES.items() if c == "block"}
_SESSION_KEYWORDS = {"session", "resume"} | {
    a for a, c in REGISTER_ALIASES.items() if c == "session"
}

_IDENT = r"[A-Za-z_][A-Za-z0-9_-]*"


@dataclass(frozen=True)
class Diagnostic:
    """One lint finding."""

    path: str
    line: int
    code: str
    message: str
    severity: str = "error"  # "error" | "warning"

    def render(self) -> str:
        """Format as ``path:line: severity CODE message``."""
        return f"{self.path}:{self.line}: {self.severity}: {self.code} {self.message}"


@dataclass
class _Line:
    number: int
    indent: int
    text: str  # code with comment stripped, rstripped
    continuation: bool = False  # inside an unclosed {, [ or ( from above


def lint_file(path: str | Path) -> list[Diagnostic]:
    """Lint one ``.prose`` file; returns diagnostics (empty = clean)."""
    source = Path(path).read_text(encoding="utf-8")
    return lint_source(source, str(path))


def lint_source(source: str, path: str = "<source>") -> list[Diagnostic]:
    """Lint ``.prose`` source text."""
    diags: list[Diagnostic] = []
    lines = _significant_lines(source, path, diags)

    _check_indentation(lines, path, diags)
    _check_block_headers(lines, path, diags)

    agents, blocks = _collect_definitions(lines, path, diags)
    _check_declarations(lines, path, diags)
    _check_references(lines, path, diags, agents, blocks)

    diags.sort(key=lambda d: (d.line, d.code))
    return diags


# ---------------------------------------------------------------------------
# Pass 0: strip comments/strings, keep significant lines
# ---------------------------------------------------------------------------


def _significant_lines(source: str, path: str, diags: list[Diagnostic]) -> list[_Line]:
    result: list[_Line] = []
    in_triple: str | None = None  # '"""' or "'''"
    in_stars = False  # multi-line *** discretion ***
    in_double_stars = False  # multi-line ** block (e.g. input defaults)
    bracket_depth = 0  # unclosed {, [ or ( carried across lines

    for number, raw in enumerate(source.splitlines(), start=1):
        if in_triple:
            if in_triple in raw:
                in_triple = None
            continue
        if in_stars:
            if raw.rstrip().endswith("***:") or raw.strip() == "***":
                in_stars = False
            continue
        if in_double_stars:
            if raw.strip() in ("**", "**:"):
                in_double_stars = False
            continue

        code = _strip_comment(raw)
        stripped = code.strip()
        if not stripped:
            continue

        # Opening of a triple-quoted string that does not close on the line.
        for quote in ('"""', "'''"):
            if code.count(quote) % 2 == 1:
                in_triple = quote
        # Multi-line discretion: `if ***` / `loop until ***` etc.
        if stripped.endswith("***") and stripped != "***":
            in_stars = True
        # Multi-line ** block: a line ENDING with a lone opening `**`
        # (e.g. `input approval: **`) — closed by a bare `**` line.
        elif stripped.endswith("**") and len(re.findall(r"\*\*", stripped)) % 2:
            in_double_stars = True

        indent = len(code) - len(code.lstrip(" \t"))
        if "\t" in code[:indent]:
            diags.append(
                Diagnostic(path, number, "OP001", "tab character in indentation")
            )
        continuation = bracket_depth > 0
        bracket_depth = max(0, bracket_depth + _net_brackets(code))
        result.append(_Line(number, indent, stripped, continuation))
    return result


def _net_brackets(code: str) -> int:
    """Net open-minus-close brackets outside string literals."""
    net = 0
    quote: str | None = None
    for ch in code:
        if quote:
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
        elif ch in "{[(":
            net += 1
        elif ch in ")]}":
            net -= 1
    return net


def _strip_comment(line: str) -> str:
    quote: str | None = None
    for i, ch in enumerate(line):
        if quote:
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
        elif ch == "#":
            return line[:i]
    return line


# ---------------------------------------------------------------------------
# Pass 1: indentation discipline
# ---------------------------------------------------------------------------


def _check_indentation(lines: list[_Line], path: str, diags: list[Diagnostic]) -> None:
    stack = [0]
    for line in lines:
        if line.indent > stack[-1]:
            stack.append(line.indent)
        else:
            while stack and stack[-1] > line.indent:
                stack.pop()
            if not stack or stack[-1] != line.indent:
                diags.append(
                    Diagnostic(
                        path,
                        line.number,
                        "OP002",
                        f"dedent to column {line.indent}, which does not "
                        "match any open block",
                    )
                )
                stack.append(line.indent)


# ---------------------------------------------------------------------------
# Pass 2: block headers must have bodies; statement keywords must be known
# ---------------------------------------------------------------------------


def _check_block_headers(
    lines: list[_Line], path: str, diags: list[Diagnostic]
) -> None:
    for i, line in enumerate(lines):
        if line.continuation:
            continue  # inside a multi-line literal — not a statement
        if line.text.endswith(":") and not _is_property_line(line.text):
            nxt = lines[i + 1] if i + 1 < len(lines) else None
            if nxt is None or nxt.indent <= line.indent:
                diags.append(
                    Diagnostic(
                        path,
                        line.number,
                        "OP003",
                        "block header has no indented body",
                    )
                )
        _check_statement_keyword(line, path, diags)


def _is_property_line(text: str) -> bool:
    """`key: value` lines — known properties or nested config keys.

    Statement starters (`parallel:`, `try:`, …) are never properties,
    even though they share the `word:` shape.
    """
    m = re.match(rf"({_IDENT}):(\s|$)", text)
    return bool(m and m.group(1) not in _STARTERS)


def _check_statement_keyword(line: _Line, path: str, diags: list[Diagnostic]) -> None:
    text = line.text
    first = re.match(rf"({_IDENT})", text)
    if not first:
        return  # punctuation-led lines (e.g. bare `***:`) are not checked
    word = first.group(1)

    if word in _STARTERS:
        return
    if word in _UNSPECIFIED_STARTERS:
        diags.append(
            Diagnostic(
                path,
                line.number,
                "OP009",
                f"'{word}' is used by bundled programs but is not in the "
                "compiler.md grammar (pending spec decision)",
                severity="warning",
            )
        )
        return
    # Property-like line: `key: value` (session/agent properties, nested
    # config such as permission entries). Statement keywords that take an
    # identifier (`agent name:`) don't match this shape.
    if re.match(rf"{_IDENT}:(\s|$)", text):
        return
    # Bare assignment / parallel branch binding: `name = ...`
    if re.match(rf"{_IDENT}\s*=", text):
        return
    # Program invocation: `research(topic: ...)` or destructuring let
    if re.match(rf"{_IDENT}\s*\(", text):
        return
    diags.append(
        Diagnostic(
            path,
            line.number,
            "OP004",
            f"unknown statement keyword '{word}' (not a canonical keyword, "
            "register alias, property-like line, assignment, or invocation)",
        )
    )


# ---------------------------------------------------------------------------
# Pass 3: definitions, flat namespace, references
# ---------------------------------------------------------------------------


def _block_body_ranges(lines: list[_Line]) -> list[tuple[int, int, int]]:
    """(start_idx, end_idx, header_indent) for each block definition body."""
    ranges: list[tuple[int, int, int]] = []
    for i, line in enumerate(lines):
        word = line.text.split("(")[0].split(":")[0].strip().split(" ")[0]
        if word in _BLOCK_KEYWORDS and line.text.endswith(":"):
            end = i + 1
            while end < len(lines) and lines[end].indent > line.indent:
                end += 1
            ranges.append((i + 1, end, line.indent))
    return ranges


def _in_block_body(idx: int, ranges: list[tuple[int, int, int]]) -> bool:
    return any(start <= idx < end for start, end, _ in ranges)


def _collect_definitions(
    lines: list[_Line], path: str, diags: list[Diagnostic]
) -> tuple[set[str], set[str]]:
    agents: set[str] = set()
    blocks: set[str] = set()
    for line in lines:
        m = re.match(rf"({_IDENT})\s+({_IDENT})\s*(\(.*\))?\s*:$", line.text)
        if not m:
            continue
        keyword, ident = m.group(1), m.group(2)
        if keyword in _AGENT_KEYWORDS:
            target, label = agents, "agent"
        elif keyword in _BLOCK_KEYWORDS:
            target, label = blocks, "block"
        else:
            continue
        if ident in target:
            diags.append(
                Diagnostic(
                    path,
                    line.number,
                    "OP008",
                    f"duplicate {label} definition '{ident}'",
                )
            )
        target.add(ident)
    return agents, blocks


def _check_declarations(lines: list[_Line], path: str, diags: list[Diagnostic]) -> None:
    ranges = _block_body_ranges(lines)
    seen: dict[str, int] = {}
    for i, line in enumerate(lines):
        if _in_block_body(i, ranges):
            continue  # block-frame locals are per-invocation (prose.md)
        m = re.match(rf"({_IDENT})\s+({_IDENT})\s*=", line.text)
        if not m or m.group(1) not in _DECL_KEYWORDS:
            continue
        ident = m.group(2)
        if ident in seen:
            diags.append(
                Diagnostic(
                    path,
                    line.number,
                    "OP005",
                    f"duplicate root-scope declaration of '{ident}' "
                    f"(first declared on line {seen[ident]}; flat "
                    "namespace — declare once, reassign with "
                    f"'{ident} = ...')",
                )
            )
        else:
            seen[ident] = line.number
    return


def _check_references(
    lines: list[_Line],
    path: str,
    diags: list[Diagnostic],
    agents: set[str],
    blocks: set[str],
) -> None:
    session_kw = "|".join(sorted(_SESSION_KEYWORDS))
    agent_ref = re.compile(rf"\b(?:{session_kw})\s*:\s*({_IDENT})\s*$")
    do_ref = re.compile(rf"\bdo\s+({_IDENT})\s*(?:\(|$)")
    for line in lines:
        m = agent_ref.search(line.text)
        if m and m.group(1) not in agents:
            diags.append(
                Diagnostic(
                    path,
                    line.number,
                    "OP006",
                    f"reference to undefined agent '{m.group(1)}'",
                )
            )
        m = do_ref.search(line.text)
        if m and m.group(1) not in blocks:
            diags.append(
                Diagnostic(
                    path,
                    line.number,
                    "OP007",
                    f"reference to undefined block '{m.group(1)}'",
                )
            )
