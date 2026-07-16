"""Canonical JSON serialization and content addressing.

Implements the canonical form of ``contracts/receipt.md``: sorted keys,
no whitespace, UTF-8 strings unescaped, integers only (floats are a
contract violation), ``sha256:`` content addresses.
"""

import hashlib
import json
import re
from typing import Any

CONTENT_ADDRESS_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")

_JSON_SCALARS = (str, bool, int)


class CanonicalizationError(ValueError):
    """Raised when a value cannot be rendered in canonical form."""


def canonical_json(value: Any) -> str:
    """Render *value* in the contract's canonical JSON form.

    Rejects floats, non-finite numbers, and any non-JSON type.
    """
    _validate(value, path="$")
    return json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )


def content_address(canonical: str) -> str:
    """Return the ``sha256:<hex>`` content address of a canonical string."""
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def receipt_content_hash(receipt: dict[str, Any]) -> str:
    """Compute a receipt's ``content_hash`` (over all fields except itself)."""
    payload = {k: v for k, v in receipt.items() if k != "content_hash"}
    return content_address(canonical_json(payload))


def _validate(value: Any, path: str) -> None:
    if value is None or isinstance(value, _JSON_SCALARS):
        return
    if isinstance(value, float):
        raise CanonicalizationError(
            f"{path}: floats are forbidden in canonical form (integers only)"
        )
    if isinstance(value, list):
        for i, item in enumerate(value):
            _validate(item, f"{path}[{i}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise CanonicalizationError(f"{path}: object keys must be strings")
            _validate(item, f"{path}.{key}")
        return
    raise CanonicalizationError(
        f"{path}: cannot canonicalize value of type {type(value).__name__}"
    )
