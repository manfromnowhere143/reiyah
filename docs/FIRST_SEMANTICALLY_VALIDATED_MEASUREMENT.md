# The first semantically validated measurement

Document ID: `reiyah.first-semantically-validated-measurement`

Version: `0.1.0`

Lifecycle status: `proposed`

## Result

8,976 joint-performance records, one per tracked object in the nuScenes validation split,
134,565 opportunity rows in total, pass the executed joint-silent-miss semantic checks with
**zero violations**.

This is the first Reiyah record derived from measured data that satisfies the semantic layer
rather than only the schema. Transcript at
[`evidence/measurement/semantic_validation_1_3.txt`](../evidence/measurement/semantic_validation_1_3.txt).

## What had to change, and why the contract was right each time

### The unit was wrong, not the contract

The first attempt was a single record holding 134,565 rows spanning every object. The contract
refused it, and correctly. Two rules make the intended unit explicit: every row must bind the same
`object_ref`, and `occurred_at` must be strictly increasing. That is not a limitation. It states
that an opportunity set is **one common object observed over a time series**, exactly as
`docs/MATHEMATICAL_SPECIFICATION.md` section 5.11 says when it requires that every row binds *the
common object*.

nuScenes objects are tracked, so the data already had the right shape: 8,976 instances, mean 15
observations each, and not one instance carrying two observations at the same timestamp.

**The contract's structure also encodes the correct statistical unit.** Treating roughly fifteen
near-identical boxes of one tracked object as independent observations is precisely the clustering
error listed in our own traps table two days earlier. The contract demanded the right unit before
we thought to apply it.

### Error one: silent joint miss is not both-channel miss

Caught by reading the derivation, recorded in
[`CONTRACT_CAUGHT_AN_ERROR.md`](CONTRACT_CAUGHT_AN_ERROR.md). We had recorded both-channel misses
as `joint_misses`. That field means *silent* joint misses, which additionally require that no
warning was issued and no fallback activated. Our source observes neither, so silence is not
establishable.

### Error two: unknown propagation is conditional on the operand being reached

Caught by **executing** the rules rather than reading them, which is the difference this step was
for. Having learned error one, we declared every record `nonidentifiable_unknown`. The validator
rejected 2,451 of 8,976 with *all operands observed but identifiability is not identified*.

It was right. Warning and fallback are consulted only for a both-miss row. For a tracked object
that was never missed by both channels there is nothing whose silence needs establishing: every
operand actually consulted is observed, and the silent count is knowably **zero**.

Unknown does not propagate from an operand that is never reached. Blanket pessimism is as wrong as
blanket optimism, and it is wrong in the direction that looks responsible, which is why it survives
review unless something executes the rule.

## The measurement, at the correct unit

| Quantity | Value |
|---|---|
| Records, one per tracked object | 8,976 |
| Opportunity rows | 134,565 |
| Semantic violations | **0** |
| Objects where silence is establishable | 2,451 (27.3%) |
| Objects where it is not | 6,525 (72.7%) |

Aggregated cells: both miss 33,711, first only 28,761, second only 12,030, neither 60,063,
summing exactly to 134,565.

Object kinds now representable, which `1.2` could not express because it pinned every opportunity
object to a vehicle: 4,596 vehicles, 2,386 static obstacles, **1,994 vulnerable road users**.

## What this does not establish

Structural and semantic conformance of a record is not scientific support. Nothing here is
accepted, independently reviewed, or admitted as evidence. The `1.3` schema and executable contract
are proposed successors; no released `1.2` byte was modified.

The semantic validator executed here is a faithful port of the `1.2` derivation with the
substitution guard split into policy and subject, per
[`EXECUTABLE_CONTRACT_1_3_PROPOSAL.md`](EXECUTABLE_CONTRACT_1_3_PROPOSAL.md). It is not the shipped
science module. Running these records through the real module requires the contract successor to be
released into the definition registry, which has not happened.

## The pattern worth keeping

Three limits were found by pointing the schema at real data. Two errors were found by pointing the
semantic layer at it, and the second of those only surrendered to execution. In every case the
contract was right and the usage was wrong.

That is the strongest available argument for the architecture, and it is worth stating precisely:
**a specification earns its cost the first time it refuses something you believed.** This one
refused four things in two days, and each refusal was correct.
