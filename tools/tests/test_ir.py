"""IR validation: schema, hashes, freshness, internal consistency."""

import json
from pathlib import Path
from typing import Any

from libretto_tools.canonical import canonical_json, content_address
from libretto_tools.cli import main
from libretto_tools.ir import check_ir, default_ir_path, file_content_hash

SOURCE_TEXT = """# Tiny program
agent worker:
  model: haiku
  prompt: "You do the work"

let findings = session: worker
  prompt: "Do the thing"

output result = findings
"""


def make_ir(source: Path, **overrides: Any) -> dict[str, Any]:
    """A valid IR for SOURCE_TEXT (content_hash computed last)."""
    # prompt_hash: sha256 over the exact prompt text bytes (no quotes)
    prompt_hash = content_address("Do the thing")
    ir: dict[str, Any] = {
        "v": "libretto.compile-ir.v1",
        "program": str(source),
        "source": {"path": str(source), "content_hash": file_content_hash(source)},
        "state_backend": "filesystem",
        "inputs": {},
        "agents": {
            "worker": {
                "model": "haiku",
                "prompt_hash": prompt_hash,
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
                "binding": "findings",
                "prompt_hash": prompt_hash,
                "context": [],
                "is_output": False,
            },
            {
                "id": "s003",
                "line": 9,
                "kind": "output",
                "binding": "result",
                "is_output": True,
            },
        ],
        "outputs": {"result": "s003"},
        "diagnostics": [],
        "hash_algorithm": "sha256",
    }
    ir.update(overrides)
    payload = {k: v for k, v in ir.items() if k != "content_hash"}
    ir["content_hash"] = content_address(canonical_json(payload))
    return ir


def write_case(tmp_path: Path, **overrides: Any) -> Path:
    source = tmp_path / "program.libretto"
    source.write_text(SOURCE_TEXT, encoding="utf-8")
    ir = make_ir(source, **overrides)
    ir_path = default_ir_path(source)
    ir_path.parent.mkdir()
    ir_path.write_text(json.dumps(ir, indent=2), encoding="utf-8")
    return source


def test_valid_ir_passes(tmp_path: Path) -> None:
    source = write_case(tmp_path)
    result = check_ir(source)
    assert result.ok, result.errors


def test_missing_ir_fails(tmp_path: Path) -> None:
    source = tmp_path / "program.libretto"
    source.write_text(SOURCE_TEXT, encoding="utf-8")
    result = check_ir(source)
    assert not result.ok
    assert any("IR missing" in error for error in result.errors)


def test_stale_ir_detected(tmp_path: Path) -> None:
    source = write_case(tmp_path)
    source.write_text(SOURCE_TEXT + '\nsession "One more"\n', encoding="utf-8")
    result = check_ir(source)
    assert not result.ok
    assert any("stale" in error for error in result.errors)


def test_tampered_ir_detected(tmp_path: Path) -> None:
    source = write_case(tmp_path)
    ir_path = default_ir_path(source)
    raw = json.loads(ir_path.read_text())
    raw["state_backend"] = "postgres"  # edit after hashing
    ir_path.write_text(json.dumps(raw))
    result = check_ir(source)
    assert not result.ok
    assert any("content_hash mismatch" in error for error in result.errors)


def test_dynamic_suffix_rejected(tmp_path: Path) -> None:
    source = write_case(tmp_path)
    ir_path = default_ir_path(source)
    ir = make_ir(source)
    ir["statements"][2]["id"] = "s003.i1"
    payload = {k: v for k, v in ir.items() if k != "content_hash"}
    ir["content_hash"] = content_address(canonical_json(payload))
    # outputs still points at s003, now missing
    ir_path.write_text(json.dumps(ir))
    result = check_ir(source)
    assert not result.ok
    assert any("not a static base ID" in error for error in result.errors)


def test_non_dense_ids_rejected(tmp_path: Path) -> None:
    source = write_case(tmp_path)
    ir = make_ir(source)
    ir["statements"][1]["id"] = "s005"
    ir["statements"][1]["agent"] = "worker"
    payload = {k: v for k, v in ir.items() if k != "content_hash"}
    ir["content_hash"] = content_address(canonical_json(payload))
    default_ir_path(source).write_text(json.dumps(ir))
    result = check_ir(source)
    assert not result.ok
    assert any("dense and ascending" in error for error in result.errors)


def test_unknown_agent_reference_rejected(tmp_path: Path) -> None:
    source = write_case(tmp_path)
    ir = make_ir(source)
    ir["statements"][1]["agent"] = "ghost"
    payload = {k: v for k, v in ir.items() if k != "content_hash"}
    ir["content_hash"] = content_address(canonical_json(payload))
    default_ir_path(source).write_text(json.dumps(ir))
    result = check_ir(source)
    assert not result.ok
    assert any("unknown agent 'ghost'" in error for error in result.errors)


def test_compile_error_diagnostics_fail_gate(tmp_path: Path) -> None:
    source = write_case(
        tmp_path,
        diagnostics=[{"severity": "error", "line": 6, "message": "undefined variable"}],
    )
    result = check_ir(source)
    assert not result.ok
    assert any("does not compile" in error for error in result.errors)


def test_cli_ir_check(tmp_path: Path, capsys) -> None:
    source = write_case(tmp_path)
    assert main(["ir-check", str(source)]) == 0
    assert "ir-check: OK" in capsys.readouterr().out
    assert main(["ir-check", str(tmp_path / "nope.libretto")]) == 2


def test_unreadable_files_do_not_crash(tmp_path: Path, monkeypatch) -> None:
    source = write_case(tmp_path)

    # Unreadable IR: check_ir degrades to a clean error, no exception.
    real_read_text = Path.read_text

    def failing_read_text(self: Path, *args: Any, **kwargs: Any) -> str:
        if self.suffix == ".json":
            raise OSError("permission denied")
        return real_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", failing_read_text)
    result = check_ir(source)
    monkeypatch.undo()
    assert not result.ok
    assert any("IR unreadable" in error for error in result.errors)

    # Unreadable source: freshness check degrades; CLI exits 2.
    def failing_read_bytes(self: Path) -> bytes:
        raise OSError("permission denied")

    monkeypatch.setattr(Path, "read_bytes", failing_read_bytes)
    result = check_ir(source)
    assert not result.ok
    assert any("source unreadable" in error for error in result.errors)
    assert main(["ir-check", str(source)]) == 2
