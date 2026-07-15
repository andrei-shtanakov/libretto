# Phase 4 Baseline Prompts

Plain-prompt equivalents of the two custom Phase 4 programs. Run as single
sequential sessions (no OpenProse VM, no explicit control-flow structure),
same model (sonnet). Key question: does formal control flow in .prose add
reliability over the same logic expressed in natural language?

## Task 1: Iterative refactor (NL control flow)

"Find the single worst code smell in ../atp-platform/packages/atp-core/ (code
is under packages/atp-core/atp/). Propose a minimal fix as a diff (do NOT edit
files — atp-platform is read-only). Then verify your own fix: would it preserve
behavior and pass related tests? If your fix has problems, try a different
approach and verify again — do this up to 2 times. Report the final verified
fix, or explain why none worked."

## Task 2: Conditional pipeline (NL branching)

"Analyze test coverage of ../atp-platform/packages/atp-core/ (code under
packages/atp-core/atp/, tests under the repo-root tests/unit/). Estimate the
overall coverage percentage. Then: if coverage is below 60%, write 3 new test
cases for the least-covered module; if it's 60-80%, hunt for edge-case bugs
that existing tests might miss; if it's above 80%, identify the top 3
code-quality improvement opportunities beyond testing. Do the branch that
matches the actual coverage."
