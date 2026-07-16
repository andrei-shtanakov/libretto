"""Chain-consistency verification for Libretto receipt ledgers.

Checks, per ``contracts/receipt.md``: schema validity, canonical
hashability (integers only), content-hash correctness, prev-chain
linkage, and the run.json ``ledger_head`` anchor. This is *chain
consistency* given a trusted manifest — not tamper-proofing.
"""

from dataclasses import dataclass, field

from pydantic import ValidationError

from .canonical import CanonicalizationError, receipt_content_hash
from .ledger import RawLedger
from .models import RECEIPT_SCHEMAS, Receipt, RunManifest


@dataclass
class VerificationResult:
    """Outcome of verifying one run's ledger against its manifest."""

    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        """True when no errors were found (warnings allowed)."""
        return not self.errors


def verify_ledger(raw: RawLedger) -> VerificationResult:
    """Verify chain consistency of a loaded run."""
    result = VerificationResult()

    if not raw.lines:
        result.errors.append("ledger is empty")
        return result

    prev_hash: str | None = None
    for i, line in enumerate(raw.lines, start=1):
        where = f"receipt {i}"

        version = line.get("v")
        if version not in RECEIPT_SCHEMAS:
            result.errors.append(f"{where}: unknown schema tag {version!r}")
            continue

        try:
            Receipt.model_validate(line)
        except ValidationError as exc:
            for err in exc.errors():
                loc = ".".join(str(part) for part in err["loc"])
                result.errors.append(f"{where}: {loc}: {err['msg']}")
            continue

        try:
            expected = receipt_content_hash(line)
        except CanonicalizationError as exc:
            result.errors.append(f"{where}: {exc}")
            continue

        actual = line.get("content_hash")
        if actual != expected:
            result.errors.append(
                f"{where}: content_hash mismatch (expected {expected}, found {actual})"
            )

        if line.get("prev") != prev_hash:
            result.errors.append(
                f"{where}: prev broken (expected {prev_hash!r}, "
                f"found {line.get('prev')!r})"
            )

        _check_reuse_consistency(line, where, result)

        prev_hash = actual if isinstance(actual, str) else expected

    _verify_manifest(raw, result, last_hash=prev_hash)
    return result


def _check_reuse_consistency(
    line: dict, where: str, result: VerificationResult
) -> None:
    """Skip/reuse rules from contracts/receipt.md (Skipped receipts)."""
    reused = line.get("reused_from")
    if reused is None:
        return
    if line.get("status") != "skipped":
        result.errors.append(f"{where}: reused_from is only valid on skipped receipts")
    usage = line.get("usage") or {}
    if (
        usage.get("input_tokens") != 0
        or usage.get("output_tokens") != 0
        or usage.get("basis") != "exact"
        or usage.get("model") != "none"
    ):
        result.errors.append(
            f"{where}: a skipped receipt with reused_from must carry "
            "zero usage with basis 'exact' and model 'none'"
        )
    if line.get("surprise_cause") is not None:
        result.errors.append(
            f"{where}: surprise_cause must be null on skipped receipts"
        )
    if line.get("output_fingerprint") != reused.get("output_fingerprint"):
        result.errors.append(
            f"{where}: output_fingerprint must equal reused_from.output_fingerprint"
        )


def _verify_manifest(
    raw: RawLedger, result: VerificationResult, last_hash: str | None
) -> None:
    if raw.manifest is None:
        result.warnings.append(
            "run.json missing: chain verified internally, but truncation "
            "is not detectable without the ledger_head anchor"
        )
        return

    try:
        manifest = RunManifest.model_validate(raw.manifest)
    except ValidationError as exc:
        for err in exc.errors():
            loc = ".".join(str(part) for part in err["loc"])
            result.errors.append(f"run.json: {loc}: {err['msg']}")
        return

    count = len(raw.lines)
    if manifest.ledger_head == last_hash and manifest.receipt_count == count:
        return

    # Torn write: head/count trail the ledger by exactly one receipt.
    # Covers the first receipt too (ledger has one line, manifest still
    # has ledger_head=null / receipt_count=0).
    prev_of_last = raw.lines[-1].get("prev")
    if manifest.ledger_head == prev_of_last and manifest.receipt_count == count - 1:
        result.warnings.append(
            "run.json trails the ledger by one receipt (torn write): "
            "append succeeded but the head update did not"
        )
        return

    if manifest.ledger_head != last_hash:
        result.errors.append(
            f"run.json: ledger_head {manifest.ledger_head!r} does not match "
            f"last receipt {last_hash!r} (possible truncation or rewrite)"
        )
    if manifest.receipt_count != count:
        result.errors.append(
            f"run.json: receipt_count {manifest.receipt_count} != {count} ledger lines"
        )
