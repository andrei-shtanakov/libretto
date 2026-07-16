"""Run the committed fixture corpus (tests/fixtures/) end to end.

Skipped outside a full repo checkout (the corpus is not shipped with the
package). In the repo, these tests pin the linter and verifier to the
documented diagnostics.
"""

import json
import re
from pathlib import Path

import pytest

from openprose_tools.ir import check_ir
from openprose_tools.ledger import load_run
from openprose_tools.lint import REGISTER_ALIASES, lint_file
from openprose_tools.verify import verify_ledger

REPO = Path(__file__).resolve().parents[2]
LINT_FIXTURES = REPO / "tests" / "fixtures" / "lint"
RUN_FIXTURES = REPO / "tests" / "fixtures" / "runs"
IR_FIXTURES = REPO / "tests" / "fixtures" / "ir"
ALTS = REPO / "skills" / "prose" / "alts"

in_repo = pytest.mark.skipif(
    not LINT_FIXTURES.is_dir(), reason="fixture corpus requires repo checkout"
)


def _lint_cases() -> list[Path]:
    if not LINT_FIXTURES.is_dir():
        return []
    return sorted(LINT_FIXTURES.glob("*.prose"))


def _run_cases() -> list[Path]:
    if not RUN_FIXTURES.is_dir():
        return []
    return sorted(p for p in RUN_FIXTURES.iterdir() if p.is_dir())


def _ir_cases() -> list[Path]:
    if not IR_FIXTURES.is_dir():
        return []
    return sorted(p for p in IR_FIXTURES.iterdir() if p.is_dir())


@in_repo
def test_fixture_corpus_is_present() -> None:
    """All fixture families exist and are non-empty in a repo checkout.

    Guards against parametrized tests silently collecting zero cases
    when a corpus directory is deleted or moved.
    """
    assert _lint_cases(), "tests/fixtures/lint is empty"
    assert _run_cases(), "tests/fixtures/runs is empty"
    assert _ir_cases(), "tests/fixtures/ir is empty"


@in_repo
@pytest.mark.parametrize("case", _ir_cases(), ids=lambda p: p.name)
def test_ir_fixture(case: Path) -> None:
    expected = json.loads((case / "expected.json").read_text())
    result = check_ir(case / "program.prose")

    assert result.ok == expected["ok"]
    if "error_contains" in expected:
        assert any(expected["error_contains"] in error for error in result.errors), (
            result.errors
        )


@in_repo
def test_committed_example_irs_are_fresh() -> None:
    """Every committed IR in examples/dist/ validates against its source."""
    dist = REPO / "skills" / "prose" / "examples" / "dist"
    irs = sorted(dist.glob("*.ir.json"))
    assert irs, "examples/dist is empty"
    for ir_path in irs:
        source = dist.parent / f"{ir_path.name.removesuffix('.ir.json')}.prose"
        result = check_ir(source, ir_path)
        assert result.ok, (ir_path.name, result.errors)


@in_repo
@pytest.mark.parametrize("case", _lint_cases(), ids=lambda p: p.stem)
def test_lint_fixture(case: Path) -> None:
    expected = json.loads(
        case.with_suffix("").with_suffix(".expected.json").read_text()
    )
    actual = [
        {"code": d.code, "line": d.line, "severity": d.severity}
        for d in lint_file(case)
    ]
    assert actual == expected


@in_repo
@pytest.mark.parametrize("case", _run_cases(), ids=lambda p: p.name)
def test_run_fixture(case: Path) -> None:
    expected = json.loads((case / "expected.json").read_text())
    result = verify_ledger(load_run(case))

    assert result.ok == expected["ok"]
    if "error_contains" in expected:
        assert any(expected["error_contains"] in error for error in result.errors), (
            result.errors
        )
    if "warning_contains" in expected:
        assert any(
            expected["warning_contains"] in warning for warning in result.warnings
        ), result.warnings


@in_repo
def test_register_aliases_in_sync_with_alts() -> None:
    """Every alias documented in alts/*.md must be known to the linter."""
    row = re.compile(r"\|\s*`([a-z_]+)`\s*\|\s*`([a-z_]+)`\s*\|")
    documented: dict[str, str] = {}
    for path in sorted(ALTS.glob("*.md")):
        for line in path.read_text(encoding="utf-8").splitlines():
            m = row.match(line)
            if m and m.group(1) != m.group(2):
                documented[m.group(2)] = m.group(1)

    assert documented, "no alias tables parsed from alts/*.md"
    missing = {
        alias: canon
        for alias, canon in documented.items()
        if REGISTER_ALIASES.get(alias) != canon
    }
    assert not missing, f"aliases missing or wrong in lint.py: {missing}"


@in_repo
def test_all_bundled_programs_lint_clean() -> None:
    """Every bundled example and stdlib program is error-free."""
    programs = sorted((REPO / "skills" / "prose" / "examples").glob("*.prose"))
    programs += sorted((REPO / "skills" / "prose" / "lib").glob("*.prose"))
    assert programs
    errors = [
        diag.render()
        for path in programs
        for diag in lint_file(path)
        if diag.severity == "error"
    ]
    assert errors == []
