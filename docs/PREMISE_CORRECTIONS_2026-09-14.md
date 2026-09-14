# Corrections to the premises under the preparation robustness reading

Date: 2026-09-14. Lane: independent research. Lifecycle status: `corrected`.

> **Section 6 is strengthened by
> [`research/preparation-robustness/0.4.0/PREMISE_CORRECTIONS.json`](../research/preparation-robustness/0.4.0/PREMISE_CORRECTIONS.json),
> described in [`COMPARATOR_CORRECTIONS_2026-09-14.md`](COMPARATOR_CORRECTIONS_2026-09-14.md).**
> The grouping on this page reads population and kept counts only. Two different row sets can
> share those totals, so it establishes 33 aggregate signatures. Membership over exact source
> rows gives the same 33 and is what earns the claim.

Artifact: [`research/preparation-robustness/0.3.0/PREMISE_CORRECTIONS.json`](../research/preparation-robustness/0.3.0/PREMISE_CORRECTIONS.json)
Producer: [`tools/measure/premise_corrections.py`](../tools/measure/premise_corrections.py)
Tests: [`tools/measure/test_premise_corrections.py`](../tools/measure/test_premise_corrections.py), 8 tests

The grid at `research/preparation-robustness/0.2.0/preparation-grid.json` stands. Its numbers
are not recomputed here and not changed. What is corrected is what this lane said about it.
Five premises were challenged in consumer review. A sixth was found here while checking them,
and it is the one that changes the most.

Every fact below was recomputed from bytes. Nothing is carried over from the earlier prose.

## 1. Scope and cutoff

Withdrawn: "every preparation changed every cutoff".

Of the 48 grid rows, 35 are computed in the matched rate arm and 13 are not. Among the 35:

| cutoffs moved | rows |
|---|---|
| five of five | 31 |
| four of five | 2 |
| none | 2 |

So 33 rows move at least one cutoff, not 35, and 31 move all five, not 48. Both rows that move
nothing are the full population compared with itself, at population 134565. Comparing the full
scope with itself is not a scope change and must not be counted as one.

The largest single move stands: `megvii` goes from 0.272641 to 0.794052 on vehicles within
30 metres at the best visibility band, a move of 0.521411.

## 2. The residual mismatch, and why it cannot be closed

Four detectors miss 40369 of 134565 at full scope. PointPillars misses 40391. The residual is
22 objects, `22/134565`, about 0.00016349 in rate. They are not matched, and calling them
approximately matched on a rounded display did not establish anything.

Recomputing the kept counts from the original submissions settles the tie rule outright. Keeping
a prediction whose score is **strictly greater** than the cutoff reproduces every stored count
exactly, for all five detectors. Keeping at or above does not.

The interesting part is why the mismatch cannot be removed by a better cutoff:

| detector | covered objects | distinct scores | tied exactly at the cutoff | is 94196 an attainable kept count |
|---|---|---|---|---|
| centerpoint | 119627 | 118751 | 0 | yes |
| fcos3d | 103495 | 103238 | 0 | yes |
| mapillary | 101778 | 101485 | 0 | yes |
| megvii | 116474 | 116006 | 0 | yes |
| pointpillars | 115805 | **9370** | **26** | **no** |

PointPillars publishes 9370 distinct scores over 115805 covered objects, and 26 objects sit
exactly at its cutoff of 0.1492. The attainable kept counts therefore step from 94174 straight
to 94200. The matched target of 94196 lies strictly between two adjacent attainable values, so
**no cutoff at any precision produces it**. Exact marginal matching at full scope is obstructed
by the score granularity of one published submission. That is a property of the evidence, not a
tolerance this lane chose.

Inputs bound by digest, read read-only from another owner's Gate B worktree and never copied
into this repository:

| file | sha256 |
|---|---|
| `gt_val_cache.json` | `7a7fb7c3913496a64bede26468d7f4b976366ccc8a3825092e16805363ea53fd` |
| `matched_centerpoint.json` | `6a8be866b3316857f44787a3676b1557d9d8dfb6a945f16f469bb10877326275` |
| `matched_fcos3d.json` | `dd7fa5d2fe13b34a4bf6762f4c8cd512e629c88bcbbb5227dfa58cf46ae8cdf4` |
| `matched_mapillary.json` | `a8fef4a1e7dbf0fed84ae1220332fcb97196e468ebf23cb77fe835871466caca` |
| `matched_megvii.json` | `2ce14fcca8235438d2f9b2ab844f83e21413e97a2ab0cf597f445bac6e35a0c1` |
| `matched_pointpillars.json` | `46b0f70daf6e18f08a4a439c502e7026c2b5d67bcffbb2109f92b314478f484e` |

When those files are not present the producer reports `unavailable` and names the inputs it
would need. It does not fill the section in from memory.

## 3. A design limitation, not an impossibility

Zero exact matches in this fixed cutoff family is a limitation of this design on this population.
It is not a theorem about subsetting. Scope conditional statistics remain definable. A descriptive
comparison, a matched marginal comparison and a claim about a dependence mechanism stay three
different things, and the earlier text let them blur.

## 4. Sensitivity is not cause

The counterfactual cutoff calculation shows the reported ordering moving when the cutoffs move.
That is numerical sensitivity under this procedure. It does not identify a physical cause and it
does not rule out an interaction between scope and cutoff. A fixed numerical cutoff and a fixed
achieved operating rate are different fixings, and neither is the other.

## 5. Parity is a hypothesis

The parities this lane found constrain the methods and problems they were found on. Treating them
as a general property of this kind of analysis was an overreach. An integration advantage has to
be measured against an analyst equipped with ordinary source tracing, viewing and verification
tools, which is the subject of
[`ORDINARY_COMPARATOR_2026-09-14.md`](ORDINARY_COMPARATOR_2026-09-14.md).

## 6. Found here: the grid has 48 labels and 33 preparations

This one was not in the review. It was found while checking the others, and it is the correction
that costs the most.

`within_50m` is the identity on this population. The cache reaches 50 metres and no further, so
the predicate selects every row and duplicates `all_ranges`. It does so in **12** of the grid's
rows. Three further pairs coincide because the excluded static furniture all lies within
30 metres, so `exclude_static_furniture` and `all_classes` select the same rows beyond 30 metres.

| labels | distinct preparations | duplicate groups | rows inside a duplicate group |
|---|---|---|---|
| 48 | 33 | 15 | 30 |

Two rows in a duplicate group are the same preparation under two names, verified by identical
population and identical kept counts for all five detectors at fixed cutoffs. Any share computed
over the grid as though its 48 labels were 48 independent preparations is computed over 33. The
earlier "0 of 48" phrasing carried a denominator this lane had not checked.

## What this record does not do

It does not recompute the grid, does not change the preregistration whose digest remains
`8e633b95e594c8b9c13061cb0af2ce19e0049a317013f3687a3c742144ac367c`, and creates no new result
about coupling. The 0.2.0 artifact and its history are unchanged. This is a versioned successor
to the interpretation, with the lineage stated in the artifact.
