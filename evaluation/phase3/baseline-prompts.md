# Phase 3 Baseline Prompts

Plain Claude Code prompt equivalent to the parallel `atp-workspace-fanout.prose`.
Run as a single sequential session (no OpenProse VM, no parallelism), same
model (sonnet). Key metric: sequential wall-clock vs the parallel .prose block.

## Task: 4-package workspace review (sequential)

"Review these four packages in ../atp-platform/packages/ one at a time, then
synthesize. For each of atp-core, atp-adapters, atp-dashboard, atp-sdk,
summarize purpose, key modules/patterns, code quality, and test coverage
(~200 words each). Then produce a unified workspace health report: strongest
package, weakest package, shared issues, and top 3 cross-cutting
recommendations."
