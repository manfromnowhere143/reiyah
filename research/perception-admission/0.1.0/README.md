# Admission of reviewed reference contents

Document ID: `reiyah.perception-admission.guide`

Version: `0.1.0`

Lifecycle status: `exploratory`

This offline boundary reads selected review contents before constructing a conditional reference
model. It freshly checks [comparison/observation binding](../../perception-binding/0.1.0/README.md),
verifies two locked [discovery records](../../perception-discovery/0.1.0/README.md), validates a
separate assisted record and consumes a complete adjudication ledger. Its output contains the
original review contents, every proposal disposition, the generated reference and compiled input.
It never authenticates a reviewer or certifies physical coverage.

The existing reference compiler remains a lower-level interface for explicitly assumed models.
This admission command is the contents-checked path for reviewed records. An arbitrary compiler
basis digest alone does not establish admission. Core matching verification still checks the
compiled mathematical graph, not physical interpretation or this upstream compilation.

## Decision and alternatives

The intended user asks whether a retained detector addition merits further integration work.
Reviewed evidence can inform that comparison only if it covers the same observations and if its
conflicts, omissions and closure assumptions survive compilation. The conventional baseline is
an explicit source join and a complete per-world accounting table. That is the mechanism used
here. A signature, digest-only attachment or majority vote would not meet those obligations.
Automatic perception or an inferred closed world would add unjustified physical premises.

This version introduces a proposed software interface, not a revision to the frozen physical
study protocol. Synthetic fixtures exercise it. No human judgment, cohort, seed, assisted-data
release, adjudication independence or study acceptance is created by running the command.

## Request and custody

Run `python -m tools.perception_admission --request FILE --request-sha256 SHA --output FRESH_FILE`.
The request has exactly `artifact_id=reiyah.perception-admission.request`, `version=0.1.0`,
`binding_request`, `discoveries`, `assisted` and `adjudication`. Every source descriptor has an
absolute `path`, nonnegative bounded `byte_size` and expected `sha256`. `discoveries` is exactly
two sealed-record descriptors. The other fields each identify one file.

The binding request is limited to 32 KiB; each discovery or assisted record to 16 MiB; the
adjudication to 32 MiB; the outer request to 32 KiB; and the complete output to 128 MiB.
The existing 64-world, 128-anchor, 128-object-per-anchor/world and 32-member-per-object limits
apply. At most 200,000 proposal/world dispositions may be evaluated. Limits fail without
clipping records, worlds or populations. Input source bytes and implementation identities are
checked again before output. JSON rejects duplicate keys, floats and nonfinite tokens.

The two discoveries must pass the existing sealed-record consumer against the freshly bound
package. Their original submitted-file hashes remain producer assertions; admission verifies
the embedded canonical records and expected sealed-file bytes. Separate handles and a local
timestamp are not independent people or attested chronology.

## Assisted proposals

The assisted record retains the discovery record's fields except its artifact is
`reiyah.perception-admission.assisted`, its phase is `proposal_assisted`, and it adds `inputs`.
Its `inputs` contains exactly `binding_request_sha256` and `discovery_sha256`, the latter an
ordered list of the two selected sealed-file hashes. Version remains `0.1.0`.

All capture occurrences, inspection states, locators, class hypotheses, reviewer handle and
reported completion/exposure states obey the discovery content rules. The shared validator
checks an explicit projection into that content contract; it does not relabel the retained
assisted record as unassisted. Assisted exposure does not satisfy discovery blinding.

The record commits to its predecessor identities. A reported completion before a predecessor's
seal is rejected. Missing times keep joint coverage unknown. Consistent local/reported times
still do not establish actual sealing before exposure. No record content authorizes phase release.

## Adjudication and full proposal accounting

The adjudication has exactly `artifact_id=reiyah.perception-admission.adjudication`, `version`,
`record_id` (neutral 32-hex), `reviewer_id`, `completed_at`, `inputs`, `joint_coverage`, `worlds`.
Its `inputs` repeats the assisted inputs and adds `assisted_sha256`. These are exact file hashes.
Its reported completion cannot precede assisted completion. Record identities cannot be reused
across stages. Handles remain unauthenticated; adjudicator independence remains unestablished.

`joint_coverage` is explicitly `{state: unknown, reason: ...}` or
`{state: assumed_complete, statement: ...}`. There is no accepted/verified physical-coverage
state. The complete adjudication file is the retained basis; the producer cannot substitute a
different opaque basis digest.

Each world has exactly `id`, `rationale` and `windows`. It contains every bound window once.
Each window has exactly `window_id`, `unlisted_objects`, `objects`, `unrepresented`.
`unlisted_objects` is unknown with a reason or `excluded_by_assumption` with a statement.
Neither complete inspection nor an empty proposal list supplies that assumption automatically.
The exclusion concerns every object capable of changing matching, including base neighbors.

A proposal member is `CANONICAL_RECORD_SHA256:proposal-NNNNN`, across both discovery records
and the assisted record. The registry binds each member to its complete proposal, phase, source
record and window. IDs are never joined by an unqualified proposal name.

Each object has `id`, `members`, `rationale`, `state`, and either `class`, `xy`, `timestamp_us`
for a point or `reason` for unresolved geometry/class/time. Point quantities obey the existing
[reference contract](../../perception-reference/0.1.0/README.md). Adjudicated points are explicit
interpretations, not automatic locator-to-coordinate conversions. Rationale must explain a
proposed resolution; it is not proof that the resolution is true.

Every proposal in that window must occur exactly once in each world: as an object member or in
`unrepresented`. An unrepresented entry has exactly `member`, `state`, `reason`; its state is
`excluded_by_assumption` or `unresolved`. An unresolved entry keeps that window open. An explicit
exclusion is retained as a conditional assumption. No omitted or repeated proposal, foreign
window member or fabricated member is accepted. Objects cannot have empty support.

The ledger preserves all supplied joint worlds and original proposal/class disagreements.
It does not prove that the author listed every physically plausible world. Assumed completeness
must remain an explicit premise; unknown completeness opens the entire comparison. Changing
the selected ledger bytes requires a new expected identity and produces a new conditional model.
The tool never selects favorable worlds, expands a Cartesian product or discards a world for
resource reasons. A world may interpret a class or grouping differently from a proposal, but
the original proposal and adjudication rationale remain in the output for challenge.

## Conservative states and output

Incomplete reported inspection by any of the three review records keeps the affected window
open. Contested/unknown discovery blinding, same discovery handle, missing completion times or
a discovery completion after its seal prevent a finite reviewed model. A contradicted recorded
time order is invalid; absent timing is unresolved. Underlying human identity, independence,
blinding and physical completeness always remain unestablished, including finite models.

Finite compilation requires explicit joint and per-window closure assumptions and no unresolved
inspection, chronology or disposition guard. These are model-relative conditions, not study
authorization. A favorable conditional result cannot be presented as physical validation.

The report retains the fresh binding, full sealed discoveries, assisted/adjudication contents,
proposal registry, guards, generated reference, compiled input and compilation receipt. Derived
world and object basis digests bind their actual adjudication contents and source links. The
reference compiler still keeps wrong-time points, unresolved objects or unavailable detector
outputs open. Missing/invalid/unviewable evidence is never converted to absence.

Output is one fresh atomic private file outside the observation package. A failed operation
writes no report. `decision_evaluated=false`: the caller can pass the embedded `compiled_input`
to the existing producer and separately structured certificate checker. Neither invokes
physical review. Shared trusted code includes parsing, source snapshots, package verification,
normalization lineage, proposal validation, nominal geometry and reference compilation.

Expected input selection, reported review facts, source coverage and local imports/runtime are
explicit premises. Digests detect substitution relative to that selection; they cannot detect
a completely fabricated but coherently selected human history. The proposed study still needs
real independent reviewers, a competent conventional comparator and adjudication arrangements.
