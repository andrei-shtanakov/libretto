"""Regenerate the malformed-IR fixtures (deterministic).

Run from this directory:
    uv run --project ../../../tools python generate.py

Each fixture is a program + dist IR pair that must FAIL ir-check in a
specific way (expected.json). Asserted by tools/tests/test_fixtures.py.
"""

import json
import sys
from pathlib import Path
from typing import Any

from openprose_tools.canonical import canonical_json, content_address
from openprose_tools.ir import file_content_hash

HERE = Path(__file__).resolve().parent

PROGRAM = """# Fixture program
agent worker:
  model: haiku
  prompt: "You do the work"

session: worker
  prompt: "Do the thing"
"""


def base_ir(source: Path) -> dict[str, Any]:
    return {
        "v": "openprose.compile-ir.v1",
        "program": "program.prose",
        "source": {
            "path": "program.prose",
            "content_hash": file_content_hash(source),
        },
        "state_backend": "filesystem",
        "inputs": {},
        "agents": {
            "worker": {
                "model": "haiku",
                "prompt_hash": content_address("You do the work"),
                "persist": None,
                "skills": [],
                "retry": None,
                "backoff": None,
            }
        },
        "blocks": {},
        "statements": [
            {"id": "s001", "line": 2, "kind": "agent_def", "name": "worker"},
            {
                "id": "s002",
                "line": 6,
                "kind": "session",
                "agent": "worker",
                "binding": None,
                "prompt_hash": content_address("Do the thing"),
                "context": [],
                "is_output": False,
            },
        ],
        "outputs": {},
        "diagnostics": [],
        "hash_algorithm": "sha256",
    }


def seal(ir: dict[str, Any]) -> dict[str, Any]:
    payload = {k: v for k, v in ir.items() if k != "content_hash"}
    ir["content_hash"] = content_address(canonical_json(payload))
    return ir


def write(name: str, mutate, expected: dict[str, Any]) -> None:
    case = HERE / name
    (case / "dist").mkdir(parents=True, exist_ok=True)
    source = case / "program.prose"
    source.write_text(PROGRAM, encoding="utf-8")
    ir = base_ir(source)
    ir = mutate(ir)
    (case / "dist" / "program.ir.json").write_text(
        json.dumps(ir, indent=2, sort_keys=True) + "\n"
    )
    (case / "expected.json").write_text(json.dumps(expected, indent=2) + "\n")


def stale(ir: dict[str, Any]) -> dict[str, Any]:
    ir["source"]["content_hash"] = "sha256:" + "0" * 64
    return seal(ir)


def tampered(ir: dict[str, Any]) -> dict[str, Any]:
    ir = seal(ir)
    ir["state_backend"] = "postgres"  # edited after sealing
    return ir


def ghost_agent(ir: dict[str, Any]) -> dict[str, Any]:
    ir["statements"][1]["agent"] = "ghost"
    return seal(ir)


def main() -> None:
    write("stale-source", stale, {"ok": False, "error_contains": "stale"})
    write(
        "tampered-ir",
        tampered,
        {"ok": False, "error_contains": "content_hash mismatch"},
    )
    write(
        "unknown-agent",
        ghost_agent,
        {"ok": False, "error_contains": "unknown agent"},
    )
    print("ir fixtures regenerated")


if __name__ == "__main__":
    sys.exit(main())
