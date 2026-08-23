# Gate A Decisions

This directory contains the digest-bound architecture evidence index and, only after direct
human action, append-only operator decision records.

## No inferred acceptance

The repository bootstrap, passing validators, assistant output, generated prose, checksums,
and a typed reviewer name do not constitute acceptance. The initial architecture intentionally
contains no completed operator decision record.

## Decision-record procedure

After canonical full-mode validation reports `architecture_complete`, an authorized operator may copy the
non-normative template at `gate/decisions/OPERATOR_DECISION.template.json` to a new append-only
file named with a stable lowercase identifier, for example:

`gate/decisions/reiyah.gate-a-decision-YYYYMMDDTHHMMSSZ.json`

The operator must replace every placeholder; use an independently verifiable lowercase
`operator.*` identifier; state a substantive authority basis and rationale; bind the exact
canonical evidence-index, mission release, protocol release, and retained validation-report
artifact IDs, paths, schema IDs, versions, and SHA-256 digests; acknowledge all four residual
risk statements; and choose `accepted`, `rejected`, or `deferred`. The bound report must be the
canonical `gate/validation-reports/gate-a-validation-1.1.0.json` bytes and must establish
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
