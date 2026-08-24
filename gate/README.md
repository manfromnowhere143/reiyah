# Gate A Review and Distribution Records

This directory separates four record classes that must never confer authority on one another:

1. the current candidate evidence index and its digest sidecar;
2. immutable versioned validation reports;
3. append-only publisher distribution receipts; and
4. append-only operator decisions created only through direct authorized human action.

Independent transport observations use a separate schema and are never inferred from a publisher
receipt.

## Immutable public predecessors

Gate A `1.1.0`, `1.1.1`, and `1.1.2` are frozen public history. Their current-path indexes would
collide, so exact copies are retained under `history/`; their version-qualified reports and
publisher receipts remain at their canonical paths.

| Packet | Packet commit | Index digest | Report digest | Publisher receipt |
|---|---|---|---|---|
| `1.1.0` | `aa5f9b9b455219536183630b0be1e801a18a575e` | `sha256:91149ec8bfc9a3999ce95d8c18ce0d558cf974b0afb412a7ac11027c63056c7a` | versioned report retained | sequence 1 |
| `1.1.1` | `90072fb64f3c16cb5d0af0f1a3bcad56554707fa` | `sha256:308f65ba2693c13fa71d081dad3f74f56ec80617e97497a2606c0d88a07b2ceb` | `sha256:76c0dcce583beb02b121776e14bc9df41833a26c5c49488270d96861b3e33806` | sequence 2 |
| `1.1.2` | `ad1a8cae6ad17f26f5a07f43fb60b6c9f55b4b1b` | `sha256:17f3a2e601e9cb4e1c0cd0f97561b1da9ffdc7d5893ed4af4eaccbaf8a67989f` | `sha256:06fc3114522c16625da337fe25c71b1fd53abeeaf9c31a11748afc06eb5d66d8` | sequence 3 |

The `1.1.2` receipt-bearing commit is
`656d826cfe6938fd628c0ede7ea15929fe11d90e`. Exact recovery identity and replay limits are
recorded in [`history/gate-a-1.1.2/RECOVERY.json`](../history/gate-a-1.1.2/RECOVERY.json).

Historical receipts retain publisher assertions about publication and remote readback. They are
not independent transport observations. No historical receipt evaluates GA-17, accepts Gate A,
creates scientific evidence, supports a safety or compliance claim, or authorizes runtime.

## Current correction candidate

Gate A `1.2.0` is a candidate intended to correct the retained `1.1.2` scientific and
validation-integrity defects. It keeps
mission `reiyah.mission@1.1.0` and proposes protocol
`reiyah.protocol.harbor-gate-a@1.2.0`. Its current index remains
`candidate_pending_canonical_report` until a clean immutable release replay emits a
byte-identical, zero-diagnostic `gate-a-validation-1.2.0.json` report.

No sequence-four publisher receipt, real operator decision, or independent transport record
exists during candidate construction. The `1.2.0` template is deliberately invalid and
non-accepting:

[`OPERATOR_DECISION-1.2.0.template.json`](decisions/OPERATOR_DECISION-1.2.0.template.json)

Historical decision templates remain frozen for their own packets and cannot be retargeted.

## No inferred acceptance

Repository bootstrap, passing validators, public visibility, generated prose, assistant output,
checksums, signatures, consensus, a typed reviewer name, a publisher receipt, and an independent
transport observation do not constitute operator acceptance.

The offline validator may check a decision record's schema, exact artifact bindings, and linear
history. It cannot select a decision, create a record, authenticate a person, establish their
authority, or mark GA-17 as passed.

## Decision-record procedure

Only after the canonical release report classifies the exact `1.2.0` index bytes as
`architecture_complete` may an authorized human use the current template as a starting point.
The human must create a new append-only record named with a stable lowercase identity, for
example:

`gate/decisions/reiyah.gate-a-decision-YYYYMMDDTHHMMSSZ.json`

The operator must replace every placeholder and bind the exact index, canonical report, mission,
protocol, artifact IDs, paths, schema IDs, versions, and SHA-256 digests. The record must identify
the operator and authority basis, retain a UTC decision time and substantive rationale,
acknowledge residual risks and the no-runtime boundary, and choose `accepted`, `rejected`, or
`deferred`.

Decision records form one append-only linear chain. Sequence one has null predecessor fields.
Every successor binds the immediate prior record's identity and digest and has a strictly later
UTC decision time. Duplicate identities, branches, cycles, gaps, multiple roots, multiple heads,
or predecessor mismatch are invalid.

Structural validity is necessary but insufficient. An independently authorized external process
must verify the named human's identity and authority. A change to any bound byte makes the
decision stale for authorization purposes but never deletes it.

## Publication and transport procedure

Publication is a separate event. It requires fresh event-specific operator distribution
authority, a current rights observation, exact index and report bindings, a distinct packet
commit, and an append-only sequence-four receipt. The receipt schema permits only
`transport_verification_state: asserted_unverified`; its remote readback object is explicitly a
publisher assertion.

The packet commit must exist before the rights record because the rights schema binds that exact
commit, index, and report. The validation plan therefore permits exactly one event-specific future
rights path as a cycle-breaking projection exclusion and forbids a broad rights prefix. After two
clean packet replays, create the fresh rights record, push the exact packet, then commit that
record and the receipt together as a direct child of the packet commit. Release replay at the
receipt-bearing child must reproduce the same packet index and report bytes.

The two official-page capture manifests are created before the packet and indexed normally. They
retain predeclared method-specific observation metadata, bounded paraphrases, and an explicit
no-body/no-redistribution limitation. Direct HTTP mode records the unretained response digest and
size; a closed adapter mode records a blocked direct attempt and leaves transport values the
adapter did not expose unasserted. The post-packet rights record exact-binds those manifest bytes.
Publication freshness is checked against both capture completion times and ordered event
timestamps; an aged capture requires a new packet rather than an in-place refresh.

Independent transport verification requires a separate authorized observer and retained
observation bytes bound to the exact repository URL, ref, commit, index, report, and publisher
receipt. The observer must not treat publisher assertions as independent evidence. A transport
record can report verified, contradicted, inconclusive, or failed observation as its schema
allows, but none of those states accepts Gate A or changes GA-17.

Never regenerate, relabel, or overwrite a released index, report, decision, or receipt. A changed
review target always receives a newly versioned append-only successor.
