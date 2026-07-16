"""Typed models mirroring ``contracts/receipt.md`` (openprose.receipt.v1).

Models ignore unknown fields (the contract requires consumers to), so
hashing must always be computed over the raw parsed JSON, never over a
model dump. Use these for typed inspection only.
"""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

RECEIPT_SCHEMA = "openprose.receipt.v1"
RUN_SCHEMA = "openprose.run.v1"

Fingerprint = str  # "sha256:<64 hex>", validated by pattern where it matters

ReceiptKind = Literal[
    "session", "parallel_branch", "block_call", "discretion", "control"
]
ReceiptStatus = Literal["rendered", "skipped", "failed"]
SurpriseCause = Literal["input", "self", "external"]
UsageBasis = Literal["exact", "estimated", "unavailable"]

_FP = Field(pattern=r"^sha256:[0-9a-f]{64}$")


class Usage(BaseModel):
    """Token/cost attribution with a mandatory honesty basis."""

    model_config = ConfigDict(extra="ignore")

    basis: UsageBasis
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    model: str


class ErrorInfo(BaseModel):
    """Failure payload for ``status: failed`` receipts."""

    model_config = ConfigDict(extra="ignore")

    type: str
    message: str
    retry_count: int = Field(default=0, ge=0)


class ReusedFrom(BaseModel):
    """Skip-provenance record (reserved for Phase 4; always null in v1)."""

    model_config = ConfigDict(extra="ignore")

    run_id: str
    statement_id: str
    output_fingerprint: Fingerprint = _FP


class Receipt(BaseModel):
    """One ledger line. See ``contracts/receipt.md`` for field semantics."""

    model_config = ConfigDict(extra="ignore")

    v: Literal["openprose.receipt.v1"]
    run_id: str
    statement_id: str
    kind: ReceiptKind
    agent: str | None
    input_fingerprints: dict[str, Fingerprint]
    output_fingerprint: Fingerprint | None = None
    status: ReceiptStatus
    surprise_cause: SurpriseCause | None
    usage: Usage
    error: ErrorInfo | None
    detail: dict[str, Any] | None
    reused_from: ReusedFrom | None
    prev: Fingerprint | None
    hash_algorithm: Literal["sha256"]
    content_hash: Fingerprint = _FP


class RunManifest(BaseModel):
    """``run.json`` — anchors the ledger head."""

    model_config = ConfigDict(extra="ignore")

    v: Literal["openprose.run.v1"]
    run_id: str
    program: str
    state_backend: str
    status: str
    receipt_count: int = Field(ge=0)
    ledger_head: Fingerprint | None
