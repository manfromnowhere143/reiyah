# The contract caught an error the schema could not

Document ID: `reiyah.contract-caught-an-error`

Version: `0.1.0`

Lifecycle status: `proposed`

## Summary

A real 134,565-row joint-miss record passed JSON Schema validation with zero errors while
containing a scientific error. Reading the semantic layer's derivation rules found it. The error
was ours, it was substantive rather than clerical, and no structural check could have caught it.

This is the first evidence that Reiyah's semantic layer earns its cost.

## The error

The record declared:

```
identifiability : identified_from_common_opportunities
joint_misses    : observed, 33,711
joint_miss_risk : observed, 0.250518
```

We had measured, per object, whether a camera-only detector missed it and whether a lidar-only
detector missed it. 33,711 objects were missed by both. We recorded that number as
`joint_misses`.

**`joint_misses` in this contract does not mean that.** The contract's
`silent_joint_miss_policy` is
`both_channels_miss_and_warning_not_issued_and_fallback_not_activated`, and the derivation in the
science module makes it operational: a both-channel miss counts toward the silent-miss total only
when the warning outcome is `not_issued` and the fallback outcome is `not_activated`. If either is
unobserved, the summary is forced unknown.

Our source is an offline detection benchmark. It contains no warning-issuing subsystem and no
fallback procedure, so both operands are `unmeasured` in every row. **Silence is therefore not
establishable, and the count of silent joint misses is not derivable from this data at all.**

We had conflated two different quantities:

| Quantity | Status in this source |
|---|---|
| Both channels missed the object | **measured**, 33,711 |
| Both missed **and no warning fired and no fallback engaged** | **not establishable** |

The first is a fact about two detectors. The second is a fact about a system, and we were not
observing a system.

## Why JSON Schema could not catch it

Structural validation checks shape. `joint_misses` is an integer measurement, and 33,711 is a
valid integer measurement. Every field was correctly typed and correctly populated. The record was
well formed and wrong.

The error lived in the relationship between a declared value and the operands that are permitted
to derive it, which is precisely the class of check
`docs/MATHEMATICAL_SPECIFICATION.md` section 9 exists to require and which it states schema
validation cannot supply.

## The correction

```
identifiability : nonidentifiable_unknown
joint_misses    : unmeasured, with reason and basis
joint_miss_risk : unmeasured, with reason and basis
```

The measured both-channel count survives, in `common_opportunity_cells.both_miss`, where it belongs
and where it is not mistaken for something stronger. Cell arithmetic still reconciles exactly:
33,711 + 28,761 + 12,030 + 60,063 = 134,565, with `first_misses` 62,472 and `second_misses` 45,741.

## What this costs the earlier results

Results D, E, G and H measured joint failure between two detection channels. That is the
`both_miss` quantity and it remains correct as measured. **Wherever those results are described as
measuring joint *silent* misses, the description is wrong and the word silent must be removed.**
The RSS coefficient work is unaffected in substance: RSS Definition 32 concerns joint subsystem
error, not silence, so the quantity we estimated is the quantity that bound requires.

The distinction matters most for the mission's own framing. HARBOR names joint silent misses as a
target construct. This work does not measure them and cannot, from this source. Measuring them
requires a source that observes warning issuance and fallback activation, which means a system
under test rather than a detection benchmark.

## The general point

Fixtures cannot find this class of error either, for the same reason they could not find the
representational limits in `SCHEMA_1_3_FINDINGS.md`: a fixture author writes rows that satisfy the
derivation they already have in mind. It took real data, whose operands were genuinely absent
rather than conveniently populated, to expose a conflation that had been sitting in our own
analysis for two days.

**A contract that only ever sees data written to satisfy it cannot tell you that you have measured
the wrong thing.** This one did, on first contact with a source it was not designed around.

## Status

`proposed`. The corrected record is structurally valid under `schemas/v1.3` and remains
semantically unvalidated, because the executable contract successor specified in
[`EXECUTABLE_CONTRACT_1_3_PROPOSAL.md`](EXECUTABLE_CONTRACT_1_3_PROPOSAL.md) does not yet exist.
The correction above was derived by reading the semantic rules directly, not by executing them.
