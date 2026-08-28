# Gate A Review and Distribution Records

This directory separates four record classes that must never confer authority on one another:

1. a current candidate evidence index and sidecar when generated, with released predecessors
   frozen under `history/`;
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

## Current public correction packet

Gate A `1.2.0` is the current public scientific and validation-integrity correction. It keeps
mission `reiyah.mission@1.1.0` and proposes protocol
`reiyah.protocol.harbor-gate-a@1.2.0`. The index deliberately remains
`candidate_pending_canonical_report` because the report is outside its acyclic projection. The
exact canonical report binds that index, records `architecture_complete`, closes `CR-001` through
`CR-016`, passes GA-01 through GA-16, and contains zero diagnostics.

| Item | Exact identity or state |
|---|---|
| `C_packet` | `86409473c8fd1571236c849a6cc730db896465fb` |
| `C_receipt` | `d42d4d298d515b59e9df15f2ba45572a91b9fab8`, a direct child of `C_packet` |
| Index digest | `sha256:b39a9bd02b3d86e32b95b988115243918d39b8fa7dea15012d90a0cb0f7c811a` |
| Report digest | `sha256:79d6f3578630994c54cbe341e2c62b79fe4606b4645b85499bcb76f018ad1961` |
| Sequence-four receipt digest | `sha256:74817d54ec3085ef0f6ceb45f54db4c24e353aa48e20a44b5ab36c97bd9d9a99` |
| Transport | publisher `asserted_unverified`; independent verification `not_evaluated` |
| Authority | operator `unaccepted`; GA-17 `not_evaluated`; runtime `false`; Gate B `false` |

The sequence-four receipt exists and binds the exact public packet, index, report, rights record,
and publisher readback assertion. No real operator decision or independent transport record
exists. The `1.2.0` decision template remains deliberately invalid and non-accepting:

[`OPERATOR_DECISION-1.2.0.template.json`](decisions/OPERATOR_DECISION-1.2.0.template.json)

Historical decision templates remain frozen for their own packets and cannot be retargeted.

A `1.2.1` continuity successor is tracked in
[GitHub issue #1](https://github.com/manfromnowhere143/reiyah/issues/1). This prose cannot validate
or publish it. Resolve those states only from an exact `1.2.1` report and append-only event
receipt; absent those records, treat the successor as proposed.

## No inferred acceptance

Repository bootstrap, passing validators, public visibility, generated prose, assistant output,
checksums, signatures, consensus, a typed reviewer name, a publisher receipt, and an independent
transport observation do not constitute operator acceptance.

The offline validator may check a decision record's schema, exact artifact bindings, and linear
history. It cannot select a decision, create a record, authenticate a person, establish their
authority, or mark GA-17 as passed.

## Decision-record procedure

The canonical release report classifies the exact `1.2.0` index bytes as
`architecture_complete`. An authorized human may use the current template as a starting point,
but no such action or acceptance is inferred. The human must create a new append-only record named
with a stable lowercase identity, for example:

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

Publication is a separate event. For `1.2.0`, it used fresh event-specific operator distribution
authority, a current rights observation, exact index and report bindings, the distinct
`C_packet`, and the append-only sequence-four receipt at `C_receipt`. The receipt records
`transport_verification_state: asserted_unverified`; its remote readback object is explicitly a
publisher assertion.

The packet commit had to exist before the rights record because the rights schema binds that exact
commit, index, and report. The validation plan therefore permitted exactly one event-specific
future-rights path as a cycle-breaking projection exclusion and forbade a broad rights prefix.
After two clean packet replays, the event created the fresh rights record, pushed the exact packet,
and committed that record and the receipt together as a direct child. Release replay at the
receipt-bearing child reproduced the same packet index and report bytes.

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
