# Interpretation-specific matching, 12 September 2026

The existing geometric compiler and common projection preserve this constructed
four-world case. No Engine interface change is needed. Matching competition and
world assignments must remain part of the checked input: two corruptions change
individual decisions while preserving the entire aggregate result, and the existing
inverse structural check rejects both.

This is a software conformance result, not a reference admission or a planner result.
The [case](case.json), [regression](../../../tests/test_perception_varying_match.py)
and [verification](verification.json) are the complete public reproduction inputs.
The case is copied byte-for-byte from the research lane's selected immutable
`resolution-plan-0.3.0` exchange at commit
`2ad46bb4d34e88d6586609eab00069a807d53ae7`, path
`research/cohort-packet/0.1.0/adaptive-beats-fixed-varying-edges-case.json`.
Its SHA-256 is `655b0afaecc89bd6544ae59c6f842705713e17e6924447d5c09742276a324194`;
the selected manifest SHA-256 is
`b36a06dc02ca92752a8fc767cf19d8ad1dd1c02f0657f7dc1f9ed9680c5f70ca`.
Only this constructed case is consumed. No planner, checker repair or theorem is
accepted here, and no Fable source, ref or outbox is changed.

## Exact realization and comparison

Keep the base detection `b0=(0,0)` and added detection `c0=(3,0)` fixed, both class
`car`, score 0.8. The existing normalization retains both under strict 2 m suppression.
Ego position is `(0,0)`. Every constructed reference object is a car at the same
declared time, within the 50 m range. Matching uses squared distance strictly below
4 and one-to-one assignments. There is one anchor of weight 1, unit false-negative
and false-positive penalties, and tolerance 1/10. Finite coverage is an explicit
test assumption, never an established property of a capture.

| World | Reference coordinates | Base loss | Augmented loss | Difference |
|---|---|---:|---:|---:|
| none | k=(3/2,0) | 0 | 1 | -1 |
| c_only | k=(0,0), dC=(3,0) | 1 | 0 | +1 |
| b_only | k=(0,0), dB=(3,0) | 1 | 0 | +1 |
| a_and_c | k=(0,0), dA=(0,1), dC=(0,-1) | 2 | 3 | -1 |

The direct baseline enumerates partial injections from these positions and computes
both full losses. It uses neither compiler graphs nor the Engine producer's matcher.
The test also compares every declared world graph with its compiled and neutral
counterparts, then verifies every world's matching counts with the separate
matching/vertex-cover checker. A patched producer matcher raises if that checker
tries to invoke it. All four per-world differences agree; their enclosure is [-1,1].

The object name `dC` persists between two alternatives, but its coordinate changes.
The larger named-object set therefore does not preserve the matching edge set.
In `c_only`, the addition can match dC. In `a_and_c`, only the base can match any
reference object, so the addition is a false detection. These are alternative
interpretations, not a measured motion or a temporal sequence. Settling either
of those worlds would give opposite integration preferences under the declared loss.

The compiler represents each world's object occurrences separately, retaining
world conditions and the mapping to original interpretation/object identities.
Renaming anchors and detections preserves that structure. Matching edges need not
carry nonempty guards themselves when their object occurrence has the world guard.

## Discriminating controls

1. In `a_and_c` only, redirect the edge to dC from the base to the addition. Its
   difference becomes +1, while the other three worlds keep their values.
2. Swap the object-occurrence conditions for `c_only` and `a_and_c`. Their
   differences swap, while `none` and `b_only` remain unchanged.

Each modified input is a valid mathematical model with a valid fresh certificate.
Each still reports [-1,1], unresolved preference and the same other aggregate fields.
Neither is the selected input: `check_projection` rejects both with
`REVIEWED_SEMANTICS`. These are rejection controls for source-preserving projection,
not failures of the matching certificate checker and not discovered Engine defects.

## Replay and cost

From the repository root with the documented research dependencies available:

```sh
python -B -m unittest -v tests.test_perception_varying_match
python -B -m unittest -v tests.test_perception_varying_match tests.test_perception_reference tests.test_perception_reviewed_operands
```

The three new tests pass in a captured process span of 0.233137 s, with macOS peak
child RSS 39,714,816 bytes. The relevant geometric and reviewed-common suites plus
these tests pass: 33 tests, 12.285678 s, peak child RSS 63,258,624 bytes. These spans
include interpreter startup. The compiler budgets 16 geometric comparisons for
the case. Baseline and Engine timings are not separately benchmarked, and no human
review effort or performance advantage follows. Unchanged broad suites and the
research lane's algorithms are not rerun to accumulate test counts.

The shared parser, rational representation, upstream normalization and semantic
contracts remain trusted premises. The new case exercises compilation/projection
directly; it supplies no complete admission packet, independent discovery, reviewer,
exposure record or physical observation. Existing admission tests remain separate.
The real two-anchor comparison remains [-8,8]. Gate A remains unaccepted.

The useful next observation remains the prepared participant viewing/selection
exercise described by the [desktop prerequisite checkpoint](../../../docs/PERCEPTION_DESKTOP_RECOVERY_2026-09-12.md).
Its diagnosed service/runtime incompatibility is unchanged. This regression does
not establish interactive usability or reduce the missing human-reference work.
