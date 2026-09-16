# Detector replacement and conditional reference audits

Artifact family: `reiyah.perception-revision`. Version: `0.1.0`. Status: `exploratory`.

This offline interface compares independently declared detector outputs A and B on a common
weighted cohort and complete joint reference worlds. It also checks whether supplied reference
observations suffice to support strict improvement under a bounded deletion-error family.
The [implementation report](../../../docs/PERCEPTION_REVISION_AUDIT_2026-09-16.md) records the
real case, corrections and costs. The legacy `tools.perception_decision` interface is unchanged.

## Comparison contract

The [input schema](input.schema.json) replaces legacy `base` and `additions` with `output_a`
and `output_b`. Observed empty outputs remain distinct from missing, unmeasured, sensor-invalid,
abstained, outside-support and unknown outputs. Unavailable outputs block the comparison.
Open references yield conservative bounds; they never become an empty reference population.

Both configurations use the same reference world, target objects, nonnegative penalties, fixed
weights and tolerance. Let a and b be miss and false-positive penalties, D the output count,
and TP the maximum one-to-one matching cardinality:

```text
delta = loss_A - loss_B = (a+b)*(TP_B-TP_A) - b*(D_B-D_A)
```

A common detection ID must have the same record digest and the same matching eligibility in
the shared graph. With p A-only detections and q B-only detections, each graph differs from its
common subgraph by p or q vertices. Therefore:

```text
-p <= TP_B-TP_A <= q
-a*p-b*q <= delta <= a*q+b*p
```

Identical outputs give zero, including under open references. A preserved-base addition has
p=0 and recovers the legacy bound. Without justified common identity, use separate IDs. Source
identity and geometric eligibility are preparation premises; the checker verifies the submitted
graph. These identities are established matching mathematics, not a novelty claim.

The replacement nuScenes adapter qualifies each output independently at score >=0.30 and
global-XY range <=50m. It adds no within-output or cross-output suppression. It composes the
existing base-qualification code twice and retains every row's disposition. A missing A does
not make an observed B missing. The adapter supplies open references until the caller provides
a qualified graph; it does not reproduce upstream inference or validate physical annotations.

## Sufficient observations and counterexamples

An [audit request](audit-request.schema.json) declares a total reference-deletion budget k and
supplied `present`/`absent` answers. A qualified object is identified by anchor and object ID.
The admitted family contains every original joint world and every deletion set of size at most
k compatible with those answers. An absent object already absent in a joint world consumes no
deletion. An observed present object must remain present. Conflicting premises produce an
inconsistent model, never vacuous support.

An audit is **sufficient** only if every remaining admitted interpretation has delta greater
than the declared tolerance. A checked adverse interpretation proves **insufficient**.
A conservative interval crossing the threshold is **unresolved**. Exhausted computation does
not prove that no counterexample exists. A smallest adverse set and a sufficient confirmed set
solve different problems; witness overlap is not a measure of saved audit work.

The caller proposes observations or an adverse candidate. This package supplies a bounded
checker and simple proof producer, not a minimum-audit-set optimizer or a learned query planner.
There are three proof routes:

1. Complete enumeration of every compatible joint world and deletion set, within resource limits.
2. A conservative universal bound checked in every compatible joint world. Deleting one object
   changes the weighted loss difference by at most `(a+b)*anchor_weight`. The k largest remaining
   object weights bound the total change. A surviving protected matching and a valid original
   cover further bound each output's cardinality. Intersect these bounds with the common-output
   count bound. A sufficient decision need not reproduce an exact numerical interval.
3. One explicit adverse world with matching/cover certificates. The checker verifies observation
   compatibility, the deletion budget and failure of strict improvement. This proves insufficiency
   without pretending to enclose the entire error family.

The audit checker reconstructs admissible domains and verifies cardinality certificates without
calling a matching solver. Its `conclude` function is the normative conclusion calculation;
the audit producer also calls it when serializing a proposal. Shared trusted code includes input
parsing, rational arithmetic, domain semantics and the existing matching/cover checker. The
replacement comparison separately computes producer and checker classifications.

The family deletes declared reference objects only. Missing-object insertion, changed class,
geometry, identity, reviewer error and population shift need explicit additional models.
`hypothetical`, `benchmark_reference` and `supplied_external_records` describe supplied premises;
none authenticates an independent reviewer. No probability distribution over worlds is invented.

## Three distinct reuse operations

**Matching calculation.** `run` can consume a prior input and checked packet. For each current
world and anchor, restrict the old cover to current vertices and retain surviving matching edges.
Reuse the candidate only if it is a valid current matching and cover of equal cardinality.
Otherwise recompute. New edges, removed vertices, changed worlds and altered penalties still
require current checks. All current joint worlds are considered. A changed cohort or anchor set
is rejected as a revalidation input; run a fresh explicitly defined comparison instead.

**Observation premise.** `rebind-audit` carries supplied answers only when the declared reference
context digest and cohort agree and each endpoint exists. `reference_context_sha256` names an
upstream source/interpretation context. Equality of opaque digests does not establish physical
applicability: the caller must qualify the underlying source, identity and interpretation.
The forty-frame example separately checks the same source reference population before rebinding.
An altered context requires a fresh applicability assessment. Rebinding issues no decision.

**Conclusion.** Every new conclusion requires checking the current input and current request.
No prior verdict, witness overlap or unchanged file count certifies a new decision. Report the
additional valid observations and complete computation needed by the same procedure with and
without prior observations before claiming saved effort.

## Resource and binding rules

- Strict JSON, exact rationals, known properties only; expected SHA-256 required before parsing.
- Input/request limit: 4 MiB. Output packet limit: 16 MiB. Atomic writes refuse an existing path.
- At most 128 anchors, 128 reference objects per anchor, 1024 detections per output, and 2048
  shared graph edges per anchor. Boolean variables and clauses retain the legacy schema limits.
- Complete enumeration: at most 4096 raw joint assignments and 2,000,000 screening work units.
  The versioned work estimate counts each output's own vertices and all its potential guarded
  edges: `2*(D+1)*(T+E+1)`, plus clause and guard work, across all raw worlds. It is a deterministic
  screening policy, not a CPU-time or memory guarantee. It does not prune worlds using outcomes.
- Audit enumeration additionally admits at most 4096 world/deletion variants within that work
  budget. Larger finite deletion families can receive conservative certificates. Open reference
  audits are explicitly outside this version's scope.
- Packets bind input, request where applicable, and producer source digest. An alternative
  producer may supply a valid proof; verification separately reports whether its source digest
  matches the installed code. Execution, model consistency, enclosure and authority stay distinct.

## Run a small example

Use the repository's Python environment with `jsonschema` installed. From the repository root,
choose a fresh output directory, then run:

```sh
python3 -B -m tools.perception_revision run \
  --input research/perception-revision/0.1.0/replacement-example.json \
  --input-sha256 df5b8715898a4e6c7a3cdcbe7eaea9b993547a3c2ea535d189a9d43eec25ab0b \
  --output /tmp/reiyah-replacement-packet.json

python3 -B -m tools.perception_revision audit \
  --input research/perception-revision/0.1.0/replacement-example.json \
  --input-sha256 df5b8715898a4e6c7a3cdcbe7eaea9b993547a3c2ea535d189a9d43eec25ab0b \
  --request research/perception-revision/0.1.0/audit-confirmed-example.json \
  --request-sha256 e4417abee41a8b2378a82fab42fe63707fa3f6cabec68c466ee8193412f90965 \
  --output /tmp/reiyah-audit-packet.json
```

The synthetic replacement gives delta=2 at strict tolerance 1. Confirming both objects is
sufficient for k=1. The [one-confirmation request](audit-insufficient-example.json), digest
`35c8c0edf4d2e7b24a0a5613a0538f78eb99d9469306928328652c077557f33d`, is insufficient: deleting
the other object gives delta=1. No actual audit occurred.

Use `verify` or `verify-audit` with the input, request where applicable, output packet and their
expected digests. `run --help` lists the four required prior-input/prior-packet bindings for
revalidation. `from-addition` explicitly converts fully observed legacy A and augmented A+C;
its B still denotes that augmentation, not standalone C.

Tests: `python3 -B -m unittest discover -s tests -p 'test_perception_revision*.py'`.
All certificates remain conditional research results, without physical safety, sampling
confidence, deployment acceptance, minimal audit cost or commercial superiority claims.
