"""Keyless health check for a Libretto workspace.

Checks what is mechanically checkable without a model or API key: spec
and contract files present, state directory writable, committed compile
IRs fresh, run ledgers verifiable. Host-primitive availability (Task
tool etc.) is the embodied `libretto doctor`'s half — see SKILL.md.
"""

import tempfile
from dataclasses import dataclass
from pathlib import Path

from .ir import check_ir
from .ledger import LedgerLoadError, load_run
from .verify import verify_ledger

SPEC_FILES = ("SKILL.md", "libretto.md", "compiler.md")
CONTRACT_FILES = ("receipt.md", "ir.md", "adapters.md")


@dataclass(frozen=True)
class Check:
    """One doctor finding."""

    name: str
    status: str  # "ok" | "warn" | "fail"
    detail: str


def _spec_root(root: Path) -> Path | None:
    for candidate in (
        root / "skills" / "libretto",
        root / "skills" / "prose",
        root,
    ):
        if all((candidate / name).is_file() for name in SPEC_FILES):
            return candidate
    return None


def _check_specs(root: Path, checks: list[Check]) -> None:
    spec_root = _spec_root(root)
    if spec_root is None:
        checks.append(
            Check(
                "specs",
                "fail",
                f"spec files {SPEC_FILES} not found under {root} "
                "(neither repo nor installed-skill layout)",
            )
        )
    else:
        checks.append(Check("specs", "ok", f"VM/compiler specs at {spec_root}"))

    # Always emitted, so the check order is stable across workspace states.
    contracts = root / "contracts"
    missing = [n for n in CONTRACT_FILES if not (contracts / n).is_file()]
    if not missing:
        checks.append(Check("contracts", "ok", f"contracts at {contracts}"))
    else:
        checks.append(
            Check(
                "contracts",
                "warn",
                f"missing under {contracts}: {', '.join(missing)} "
                "(installed skills may ship without contracts)",
            )
        )


def _check_writable(root: Path, checks: list[Check]) -> None:
    if (root / ".libretto").is_dir():
        target = root / ".libretto"
    elif (root / ".prose").is_dir():
        target = root / ".prose"
    else:
        target = root
    try:
        with tempfile.NamedTemporaryFile(dir=target, prefix=".doctor-"):
            pass
    except OSError as exc:
        checks.append(Check("state-writable", "fail", f"{target}: {exc}"))
        return
    checks.append(Check("state-writable", "ok", f"{target} is writable"))


def _check_irs(root: Path, checks: list[Check]) -> None:
    irs = sorted(root.glob("**/dist/*.ir.json"))
    irs = [p for p in irs if ".venv" not in p.parts and "fixtures" not in p.parts]
    if not irs:
        checks.append(Check("compile-ir", "warn", "no compiled IRs found"))
        return
    stale: list[str] = []
    for ir_path in irs:
        source = ir_path.parent.parent / (
            ir_path.name.removesuffix(".ir.json") + ".libretto"
        )
        if not source.is_file():
            legacy_source = ir_path.parent.parent / (
                ir_path.name.removesuffix(".ir.json") + ".prose"
            )
            if legacy_source.is_file():
                source = legacy_source
        result = check_ir(source, ir_path)
        if not result.ok:
            stale.append(ir_path.name)
    if stale:
        checks.append(
            Check(
                "compile-ir",
                "fail",
                f"{len(stale)}/{len(irs)} IRs stale or invalid: "
                + ", ".join(sorted(stale)),
            )
        )
    else:
        checks.append(Check("compile-ir", "ok", f"{len(irs)} IRs fresh"))


def _check_runs(root: Path, checks: list[Check]) -> None:
    run_dirs = [
        p
        for pattern in (".libretto/runs/*", ".prose/runs/*", "**/examples/runs/*")
        for p in root.glob(pattern)
        if p.is_dir() and ".venv" not in p.parts and "fixtures" not in p.parts
    ]
    if not run_dirs:
        checks.append(Check("run-ledgers", "warn", "no runs found"))
        return
    broken: list[str] = []
    legacy = verified = 0
    for run_dir in sorted(run_dirs):
        if not (run_dir / "receipts.jsonl").is_file():
            legacy += 1  # pre-receipt run (before libretto.receipt.v1)
            continue
        label = str(run_dir.relative_to(root))
        try:
            if verify_ledger(load_run(run_dir)).ok:
                verified += 1
            else:
                broken.append(label)
        except LedgerLoadError:
            broken.append(label)
    if broken:
        checks.append(
            Check(
                "run-ledgers",
                "fail",
                f"{len(broken)} ledgers broken ({verified} verify, "
                f"{legacy} legacy pre-receipt): " + ", ".join(sorted(broken)),
            )
        )
    elif verified == 0:
        checks.append(
            Check(
                "run-ledgers",
                "warn",
                f"no receipt-era runs ({legacy} legacy pre-receipt runs only)",
            )
        )
    else:
        checks.append(
            Check(
                "run-ledgers",
                "ok",
                f"{verified} ledgers verify"
                + (f" ({legacy} legacy pre-receipt runs skipped)" if legacy else ""),
            )
        )


def run_doctor(root: str | Path = ".") -> list[Check]:
    """Run all workspace checks; order is stable."""
    base = Path(root).resolve()
    checks: list[Check] = []
    _check_specs(base, checks)
    _check_writable(base, checks)
    _check_irs(base, checks)
    _check_runs(base, checks)
    return checks
