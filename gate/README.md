# Gate A Review and Release Records

This directory contains the digest-bound architecture evidence index, retained validation
reports, append-only public distribution receipts, and, only after direct human action,
append-only operator decision records.

## Frozen Gate A 1.1.0 records

The frozen indexed packet is commit
`aa5f9b9b455219536183630b0be1e801a18a575e`, with evidence-index digest
`sha256:91149ec8bfc9a3999ce95d8c18ce0d558cf974b0afb412a7ac11027c63056c7a`.
Commit `68854b474f7c4ebd95cc79ced56411c2d5935f78` adds only the append-only
[`1.1.0` public distribution receipt](public-distribution-receipts/reiyah.public-distribution-receipt-1.1.0.json).
That receipt records completed transport and verified remote readback. It does not evaluate
GA-17, accept Gate A, authorize runtime, or create scientific support.

The sequence-one receipt logically names `gate/GATE_A_EVIDENCE_INDEX.json` as it existed in the
published `1.1.0` packet. After the root path advances to `1.1.1`, offline replay resolves that
binding through the byte-exact [historical index
snapshot](../history/gate-a-1.1.0/gate/GATE_A_EVIDENCE_INDEX.json) and its [matching
sidecar](../history/gate-a-1.1.0/gate/GATE_A_EVIDENCE_INDEX.sha256). The snapshot is immutable
release history, not a second current index.

Gate A `1.1.1` is a governance-correction candidate. Its current index sidecar and canonical
validation report identify the exact review target. The mission and protocol releases remain at
`1.1.0` because this correction does not change them. The indexed candidate intentionally makes
no claim about its later Git commit or remote readback. Those transport facts exist only if a
valid append-only `1.1.1` distribution receipt is present.

The original `gate/decisions/OPERATOR_DECISION.template.json` remains the frozen historical
Gate A `1.1.0` template. It must not be rewritten or used as the current `1.1.1` procedure. The
add-only
[`OPERATOR_DECISION-1.1.1.template.json`](decisions/OPERATOR_DECISION-1.1.1.template.json) is the
current governance-correction candidate template.

## No inferred acceptance

The repository bootstrap, passing validators, assistant output, generated prose, checksums,
and a typed reviewer name do not constitute acceptance. The initial architecture intentionally
contains no completed operator decision record.

## Decision-record procedure

After canonical full-mode validation reports `architecture_complete` for the exact Gate A
`1.1.1` successor, an authorized operator may copy the non-normative template at
`gate/decisions/OPERATOR_DECISION-1.1.1.template.json` to a new append-only file named with a
stable lowercase identifier, for example:

`gate/decisions/reiyah.gate-a-decision-YYYYMMDDTHHMMSSZ.json`

The operator must replace every placeholder; use an independently verifiable lowercase
`operator.*` identifier; state a substantive authority basis and rationale; bind the exact
canonical evidence-index, mission release, protocol release, and retained validation-report
artifact IDs, paths, schema IDs, versions, and SHA-256 digests; acknowledge all four residual
risk statements; and choose `accepted`, `rejected`, or `deferred`. The bound report must be the
canonical `gate/validation-reports/gate-a-validation-1.1.1.json` bytes and must establish
architecture completeness for the same index digest.

The operator must also set `decision_sequence` and `history_policy: append_only_linear`. The
first decision uses sequence one with null predecessor ID and digest. Every later decision
names and digest-binds the immediate prior record. Repository validation rejects duplicate
record or artifact IDs, non-increasing UTC times, branches, cycles, gaps, multiple roots or
heads, and predecessor mismatch.

The record must validate against the current operator-decision schema. Structural validity is
necessary but never sufficient: identity and authority must be independently verified outside
the repository, and the repository validator never reports GA-17 as `passed`. No tool may choose
the decision or populate identity, authority, or rationale on the operator's behalf. A copied
template must remove `template_notice`, change `is_template` to `false`, and add or replace any
fields required by the current schema; the template is deliberately non-normative and invalid
until those operator-controlled steps are complete. Schema validity constrains structure but
does not authenticate identity or authority.

Changing any indexed artifact invalidates an earlier `accepted` decision for authorization
purposes but never deletes it. A new validation and later decision append a new record with a
`supersedes_record_id` reference.

The frozen public `1.1.0` packet must not be regenerated in place. A correction after public
distribution requires a newly versioned Gate A packet, index, validation report, and review
target. Independent review of the exact successor remains separate from operator acceptance.
