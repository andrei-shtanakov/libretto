# Vendored: upstream Reactor receipt schema (pinned copy)

Pinned, read-only copy of the upstream `openprose/prose` receipt envelope and
canonical shapes, vendored per workspace rule (cross-repo contracts are
consumed as pinned copies inside the repo, never referenced by path).

| | |
|---|---|
| **Upstream repo** | https://github.com/openprose/prose |
| **Commit** | `1542e62410fec9b0f1d937dec7e1d378ec61247b` |
| **Vendored** | 2026-07-16 |
| **Files** | `receipt.ts` ← `packages/reactor/src/receipt/index.ts`; `shapes.ts` ← `packages/reactor/src/shapes/index.ts` |
| **License** | MIT (upstream) |

These files are **reference material** for `contracts/receipt.md` — they are
not compiled, imported, or executed by anything in this repo. Do not edit
them; to update, re-copy from a newer upstream commit and bump this table.

What `openprose.receipt.v1` adopted from here:

- The envelope pattern: `schema` tag + `hash_algorithm` + `content_hash`
  computed over the canonical serialization of the envelope sans
  `content_hash`; `prev` as the chain link.
- Canonicalization rules: sorted keys, no whitespace, no non-finite numbers.
- `status: rendered | skipped | failed` render outcomes.
- The honest v1 signature posture: chain consistency with a null signer, no
  cryptographic attestation claims.

What was reshaped for OpenProse v1 (statement-scoped, not node-scoped):

- `node` / `contract_fingerprint` / `wake` / facet `fingerprints` →
  `run_id` / `statement_id` / `kind` / named `input_fingerprints` +
  single `output_fingerprint`.
- `cost` (provider/model/fresh/reused) → `usage` with a mandatory honesty
  `basis: exact | estimated | unavailable` (embodied VMs often cannot get
  exact counts from the substrate).
- Added `detail` (discretion outcomes — the deterministic-replay primitive)
  and `reused_from` (reserved for Phase 4 skip provenance).
