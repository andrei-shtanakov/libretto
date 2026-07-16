# Phase 2 Baseline Prompts

Plain Claude Code prompts equivalent to the two custom .libretto programs.
Each baseline runs as a single plain session (no Libretto VM, no state files),
same model (sonnet) as the .libretto agents.

## Task 1: Evaluator Refactoring

"Read the evaluator implementations in ../atp-platform/packages/atp-core/. List
all evaluator classes and their interfaces. Then extract the common interface.
Finally, propose a refactoring plan with an ideal base class."

## Task 2: Module Review (x3)

"Review code quality in ../atp-platform/packages/atp-core/: organization,
naming, test coverage, error handling, docs. Rate 1-10 each. Then do the same
for ../atp-platform/packages/atp-adapters/ and ../atp-platform/packages/atp-sdk/.
Finally, compare all three."
