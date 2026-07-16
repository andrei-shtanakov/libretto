"""Canonical form: sorted keys, no whitespace, integers only."""

import pytest

from libretto_tools.canonical import (
    CanonicalizationError,
    canonical_json,
    content_address,
    receipt_content_hash,
)


def test_sorted_keys_no_whitespace() -> None:
    assert canonical_json({"b": 1, "a": [1, 2]}) == '{"a":[1,2],"b":1}'


def test_nested_objects_sorted() -> None:
    value = {"z": {"y": 1, "x": 2}, "a": None}
    assert canonical_json(value) == '{"a":null,"z":{"x":2,"y":1}}'


def test_non_ascii_not_escaped() -> None:
    assert canonical_json({"k": "тест"}) == '{"k":"тест"}'


def test_floats_rejected() -> None:
    with pytest.raises(CanonicalizationError):
        canonical_json({"tokens": 1.5})


def test_non_json_types_rejected() -> None:
    with pytest.raises(CanonicalizationError):
        canonical_json({"when": object()})


def test_content_address_shape() -> None:
    address = content_address("{}")
    assert address.startswith("sha256:") and len(address) == 71


def test_receipt_content_hash_excludes_itself() -> None:
    body = {"v": "libretto.receipt.v1", "prev": None}
    hashed = receipt_content_hash({**body, "content_hash": "sha256:" + "0" * 64})
    assert hashed == receipt_content_hash(body)
