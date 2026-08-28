# Three representational limits found by measuring

Document ID: `reiyah.schema-1-3-findings`

Version: `0.1.0`

Lifecycle status: `proposed`

## What happened

The Gate A `1.2` scientific contracts were validated against 611 deterministic synthetic fixtures.
That is the correct construction order: the contract is written before the data exists, so the
data cannot quietly reshape it.

On 2026-08-28 the joint-performance contract was pointed at measured data for the first time: a
real camera-versus-lidar joint-miss record over the nuScenes validation split, 134,565 opportunity
rows, one per annotated object surviving the official class-range filter. The synthetic fixture
that the contract was built against carries four rows.

**The first validation returned 134,657 errors.** Three of them were representational limits in
the contract rather than defects in the record. All three were invisible against fixtures, because
a fixture author naturally writes data the schema accepts.

## Limit one: channel roles were encoded in property names

`opportunityRow` named its two channels `human_channel` and `automation_channel`. A comparison
between two machine perception channels was therefore unrepresentable without misusing a field
name to mean something it does not say.

**Remedy.** `1.3` replaces the two named properties with `channels`, an ordered pair in which each
element carries an explicit `role` drawn from a closed set: `human`, `automation`,
`machine_perception`, `reference_process`, `fallback_procedure`. `jointSilentMiss` gains a
`channel_contract` binding array position to channel identity and role, and the contingency cells
and marginals are renamed from role to position: `first_only_miss`, `second_only_miss`,
`first_misses`, `second_misses`.

The mathematics is untouched. Cell reconciliation, unknown propagation and the identifiability
disposition are all indifferent to what a channel is.

**Deliberately not done.** The pair stays a pair. Generalising to n channels turns a 2x2
contingency contract into a 2^n partition and requires its own reconciliation rules. That is a
separate successor, and half-doing it here would be worse than naming it.

## Limit two: the opportunity object was pinned to a vehicle

`object_ref.record_kind` carried `const: "reiyah.kind.vehicle_object"`.

**A joint miss on a pedestrian, a cyclist, or a traffic cone was not expressible.** For a program
whose mission names vulnerable road users and worst-group validation, this is the most serious of
the three. It survived 611 fixtures because the fixture that exercised this path used a vehicle,
and the `const` was written to match the fixture rather than the domain.

**Remedy.** `1.3` replaces the constant with a `roadObjectKind` enumeration covering vehicle,
vulnerable road user, static obstacle, and a general annotated road object.

## Limit three: a partial measurement was unrepresentable

The record requires `selective_evaluation`, `ood_evaluation`, `conformal_evaluation`,
`transfer_evaluation`, `worst_group_evaluation`, `study_ref`, `odd_ref` and `evidence_binding`.
Every one of them rejected an explicit non-observed state and demanded a complete populated
evaluation of its own kind.

A record could therefore not say *I measured joint misses and nothing else*. Satisfying the
contract required either fabricating five evaluations that were never performed, or abandoning the
schema.

**This inverts Reiyah's own principle.** `docs/STATUS_MODEL.md` insists that a value which was not
measured must say so explicitly rather than be coerced to a default. The same discipline was not
applied one level up, to sections. A real measurement is partial almost by definition; a synthetic
fixture never is, because its author fills in every field.

**Remedy.** `1.3` admits an explicit `nonObservedMeasurement`, carrying a reason and at least one
basis identifier, at each of those eight positions. Partial measurement becomes a stated fact about
the world rather than a defect in the record.

## Result

After the three remedies, the same 134,565-row record validates with **zero errors**, and the
derived quantities reconcile exactly:

| Check | Value |
|---|---|
| Opportunity rows | 134,565 |
| Cells sum to opportunities | 33,711 + 28,761 + 12,030 + 60,063 = 134,565 |
| `first_misses` equals both + first-only | 62,472 |
| `second_misses` equals both + second-only | 45,741 |
| Joint miss risk | 0.250518 |
| Schema errors | **0** |

Transcript at [`evidence/measurement/v13_validation.txt`](../evidence/measurement/v13_validation.txt).

## The record's true state

The record is **structurally valid and semantically unvalidated**, and that distinction matters.

`docs/MATHEMATICAL_SPECIFICATION.md` section 9 states that JSON Schema validation is necessary and
not sufficient, and lists 31 deterministic semantic checks the offline validator must additionally
perform. Those live in the science module, and they will refuse this record: before any arithmetic
runs, the executable contract is compared by exact equality against a fixed expectation that pins
the object reference, both channel references, the clock, the window and the opportunity set
identifiers to synthetic values.

That refusal is correct behaviour. It is a substitution guard preventing the contract being
weakened by editing the profile, and `AGENTS.md` requires exactly that instinct. The consequence is
that **a schema successor alone is not enough**: reaching a semantically validated real record
requires a matching executable contract release. That is specified in
[`EXECUTABLE_CONTRACT_1_3_PROPOSAL.md`](EXECUTABLE_CONTRACT_1_3_PROPOSAL.md) and does not yet
exist.

Claiming this record is validated would therefore be false. It passes the structural half of a
two-part contract.

## What this says about the method

Writing contracts before data is right, and it is not sufficient. Fixtures test whether a schema
rejects what its author expected to reject. They cannot test whether the schema can express what
the world contains, because the author writes the fixture to fit.

Three limits, one attempt, and the most serious of them would have excluded pedestrians from the
one analysis the mission cares most about. The correct conclusion is not that the Gate A work was
wrong. It is that **a contract is not finished until real data has refused to fit into it**, and
that refusal should be sought deliberately rather than waited for.

## Non-claims

No released `1.2` byte was modified. `1.3` is a proposed successor and is not accepted. The record
validating against a schema establishes structural conformance only: no scientific support, no
operator acceptance, and no claim about any detector or vendor.
