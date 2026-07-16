"""Doctor: workspace health checks against synthetic and real layouts."""

from pathlib import Path

from conftest import build_chain, write_run
from libretto_tools.cli import main
from libretto_tools.doctor import run_doctor

REPO = Path(__file__).resolve().parents[2]


def _status(checks, name: str) -> str:
    for check in checks:
        if check.name == name:
            return check.status
    raise AssertionError(f"check {name!r} not emitted; got: {[c.name for c in checks]}")


def test_doctor_on_this_repo_is_green() -> None:
    checks = run_doctor(REPO)
    assert _status(checks, "specs") == "ok"
    assert _status(checks, "contracts") == "ok"
    assert _status(checks, "state-writable") == "ok"
    assert _status(checks, "compile-ir") == "ok"
    assert _status(checks, "run-ledgers") == "ok"


def test_doctor_missing_specs_fails(tmp_path: Path) -> None:
    checks = run_doctor(tmp_path)
    assert _status(checks, "specs") == "fail"
    # Check order is stable: contracts is emitted even when specs fail.
    assert _status(checks, "contracts") == "warn"
    assert _status(checks, "compile-ir") == "warn"
    assert _status(checks, "run-ledgers") == "warn"


def test_doctor_flags_broken_ledger(tmp_path: Path) -> None:
    receipts = build_chain([{"statement_id": "s001"}])
    run = write_run(tmp_path / ".libretto" / "runs" / "r1", receipts)
    ledger = run / "receipts.jsonl"
    ledger.write_text(ledger.read_text().replace("s001", "s999"))

    checks = run_doctor(tmp_path)
    assert _status(checks, "run-ledgers") == "fail"


def test_doctor_cli(tmp_path: Path, capsys) -> None:
    assert main(["doctor", str(REPO)]) == 0
    assert "doctor: OK" in capsys.readouterr().out
    assert main(["doctor", str(tmp_path)]) == 1
