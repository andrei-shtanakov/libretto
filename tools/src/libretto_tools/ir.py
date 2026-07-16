"""Compile-IR validation (``contracts/ir.md``, libretto.compile-ir.v1).

The LLM compiler produces the IR; this module mechanically validates it:
schema, content hash, source freshness, and internal consistency.
"""

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .canonical import CanonicalizationError, canonical_json, content_address

IR_SCHEMA = "libretto.compile-ir.v1"
LEGACY_IR_SCHEMA = "openprose.compile-ir.v1"
IR_SCHEMAS = frozenset({IR_SCHEMA, LEGACY_IR_SCHEMA})

_BASE_ID = re.compile(r"^s(\d{3,})$")
_FP = Field(pattern=r"^sha256:[0-9a-f]{64}$")


class IrSource(BaseModel):
    """Source identity + freshness anchor."""

    model_config = ConfigDict(extra="ignore")

    path: str
    content_hash: str = _FP


class IrAgent(BaseModel):
    """One agent-table entry."""

    model_config = ConfigDict(extra="ignore")

    model: str | None = None
    prompt_hash: str | None = Field(default=None, pattern=r"^sha256:[0-9a-f]{64}$")
    persist: str | bool | None = None
    skills: list[str] = Field(default_factory=list)
    retry: int | None = None
    backoff: str | None = None


class IrBlock(BaseModel):
    """One block-table entry."""

    model_config = ConfigDict(extra="ignore")

    params: list[str] = Field(default_factory=list)
    statements: list[str] = Field(default_factory=list)


class IrStatement(BaseModel):
    """One statement-inventory entry (structural, not semantic)."""

    model_config = ConfigDict(extra="ignore")

    id: str
    line: int = Field(ge=1)
    kind: str
    name: str | None = None
    binding: str | None = None
    agent: str | None = None
    prompt_hash: str | None = Field(default=None, pattern=r"^sha256:[0-9a-f]{64}$")
    context: list[str] | None = None
    is_output: bool | None = None
    branches: list[str] | None = None
    body: list[str] | None = None
    modifiers: dict[str, Any] | None = None
    condition_count: int | None = None


class IrDiagnostic(BaseModel):
    """Compiler finding recorded in the IR."""

    model_config = ConfigDict(extra="ignore")

    severity: Literal["error", "warning", "info"]
    line: int | None = None
    code: str | None = None
    message: str


class CompileIr(BaseModel):
    """The full IR artifact."""

    model_config = ConfigDict(extra="ignore")

    v: Literal["libretto.compile-ir.v1", "openprose.compile-ir.v1"]
    program: str
    source: IrSource
    state_backend: str
    inputs: dict[str, str] = Field(default_factory=dict)
    agents: dict[str, IrAgent] = Field(default_factory=dict)
    blocks: dict[str, IrBlock] = Field(default_factory=dict)
    statements: list[IrStatement]
    outputs: dict[str, str] = Field(default_factory=dict)
    diagnostics: list[IrDiagnostic] = Field(default_factory=list)
    hash_algorithm: Literal["sha256"]
    content_hash: str = _FP


@dataclass
class IrCheckResult:
    """Outcome of validating one IR against its source."""

    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        """True when no errors were found."""
        return not self.errors


def default_ir_path(source: Path) -> Path:
    """Conventional IR location for a source file: ``<dir>/dist/<stem>.ir.json``."""
    return source.parent / "dist" / f"{source.stem}.ir.json"


def file_content_hash(path: Path) -> str:
    """``sha256:`` content address of a file's exact bytes."""
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def check_ir(
    source_path: str | Path, ir_path: str | Path | None = None
) -> IrCheckResult:
    """Validate the IR for *source_path* per contracts/ir.md."""
    result = IrCheckResult()
    source = Path(source_path)
    ir_file = Path(ir_path) if ir_path is not None else default_ir_path(source)

    if not ir_file.is_file():
        result.errors.append(f"IR missing: {ir_file}")
        return result

    try:
        raw = json.loads(ir_file.read_text(encoding="utf-8"))
    except OSError as exc:
        result.errors.append(f"IR unreadable: {exc}")
        return result
    except json.JSONDecodeError as exc:
        result.errors.append(f"IR is not valid JSON: {exc.msg}")
        return result
    if not isinstance(raw, dict):
        result.errors.append("IR must be a JSON object")
        return result

    if raw.get("v") not in IR_SCHEMAS:
        result.errors.append(f"unknown IR schema tag {raw.get('v')!r}")
        return result

    try:
        ir = CompileIr.model_validate(raw)
    except ValidationError as exc:
        for err in exc.errors():
            loc = ".".join(str(part) for part in err["loc"])
            result.errors.append(f"schema: {loc}: {err['msg']}")
        return result

    _check_content_hash(raw, result)
    _check_freshness(ir, source, result)
    _check_statements(ir, result)
    _check_references(ir, result)

    if any(diag.severity == "error" for diag in ir.diagnostics):
        result.errors.append(
            "IR records compile errors in diagnostics — the program does not compile"
        )
    return result


def _check_content_hash(raw: dict[str, Any], result: IrCheckResult) -> None:
    payload = {k: v for k, v in raw.items() if k != "content_hash"}
    try:
        expected = content_address(canonical_json(payload))
    except CanonicalizationError as exc:
        result.errors.append(f"canonical form: {exc}")
        return
    if raw.get("content_hash") != expected:
        result.errors.append(
            f"content_hash mismatch (expected {expected}, "
            f"found {raw.get('content_hash')})"
        )


def _check_freshness(ir: CompileIr, source: Path, result: IrCheckResult) -> None:
    if not source.is_file():
        result.errors.append(f"source not found: {source}")
        return
    try:
        actual = file_content_hash(source)
    except OSError as exc:
        result.errors.append(f"source unreadable: {exc}")
        return
    if ir.source.content_hash != actual:
        result.errors.append(
            "stale: source content changed since compile "
            f"(IR has {ir.source.content_hash}, file is {actual})"
        )


def _check_statements(ir: CompileIr, result: IrCheckResult) -> None:
    prev = 0
    seen: set[str] = set()
    for stmt in ir.statements:
        m = _BASE_ID.match(stmt.id)
        if not m:
            result.errors.append(
                f"statement id {stmt.id!r} is not a static base ID "
                "(dynamic suffixes belong in receipts, not IR)"
            )
            continue
        if stmt.id in seen:
            result.errors.append(f"duplicate statement id {stmt.id!r}")
        seen.add(stmt.id)
        number = int(m.group(1))
        if number != prev + 1:
            result.errors.append(
                f"statement ids must be dense and ascending: found "
                f"{stmt.id!r} after s{prev:03d}"
            )
        prev = number


def _check_references(ir: CompileIr, result: IrCheckResult) -> None:
    ids = {stmt.id for stmt in ir.statements}
    agent_names = set(ir.agents)

    def check_id(owner: str, ref: str) -> None:
        if ref not in ids:
            result.errors.append(f"{owner} references unknown statement {ref!r}")

    for stmt in ir.statements:
        if stmt.agent is not None and stmt.agent not in agent_names:
            result.errors.append(
                f"statement {stmt.id} references unknown agent {stmt.agent!r}"
            )
        for ref in stmt.branches or []:
            check_id(f"statement {stmt.id} branches", ref)
        for ref in stmt.body or []:
            check_id(f"statement {stmt.id} body", ref)

    for name, block in ir.blocks.items():
        for ref in block.statements:
            check_id(f"block {name!r}", ref)

    for name, ref in ir.outputs.items():
        check_id(f"output {name!r}", ref)
