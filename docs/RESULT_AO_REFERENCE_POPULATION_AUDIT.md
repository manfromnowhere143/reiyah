# Result AO: reference populations change the meaning of unmatched detections

Document ID: `reiyah.result-ao-reference-population-audit`

Version: `0.1.0`

Lifecycle status: `exploratory`

The independently implemented audit confirms a descriptive sensor association while exposing a
material error in interpreting the original reference. It uses existing public-data caches and
retained predictions, with no new model execution. It is reproducibility and sensitivity analysis
within this research session, not independent scientific replication or physical adjudication.

## Observation and reference

The historical ghost predicate is more than two meters from every annotation in the filtered GT
cache. The cache has already excluded classes and class-dependent ranges. Absence from that cache
is therefore different from absence in the complete annotation table, and neither is proof of
absence from the physical scene.

At score threshold 0.30:

| Channel | Predictions in evaluated samples | Historical ghost flags | Flags within two meters of excluded annotations | Fraction of historical flags |
|---|---:|---:|---:|---:|
| Mapillary camera | 103,008 | 24,432 | 3,151 | 12.90% |
| Megvii lidar | 119,670 | 23,840 | 5,728 | 24.03% |

The changed flags are an exact consequence of changing the reference population under the same
center-distance predicate. They are not independently validated correct detections. A nearby
annotation can be a different class or object, and center distance does not represent object
extent. Objects absent even from the complete table remain unresolved without another reference.

## Scene-cluster reanalysis

On the fixed original deepest-stratum support, the conditional joint-miss ratio is
**1.151053**, with scene-bootstrap percentile interval **[1.128749, 1.166206]**. The support has
131,722 rows out of 134,565, from 8,976 tracked instances and 150 scenes. The bootstrap uses
2,000 replicates, seed 20260907. Entire scenes are sampled together; strata are the original
class, range, visibility, weather and full-track motion construction.

This retains the descriptive association. It does not establish that scenes from nearby places
are independent draws, that all unmeasured difficulty has been removed, or that full-track motion
is available to an online observer. Input/matcher errors are not covered by this sampling interval.

## Temporal-null sensitivity

The primary comparison below fixes donor eligibility by temporal offset and heading availability,
including donors with no eligible lidar predictions. Empty is observed zero; a missing sample is
unavailable and the audit refuses it. Two nulls answer different questions: ego-relative
relocation preserves a donor's arrangement around its ego pose; world-fixed comparison preserves
global coordinates. Neither is privileged as ground-truth causal independence.

| Reference | Observed coincident camera candidates | Ego-relative expected count | Ego-relative ratio and scene percentile interval | World-fixed expected count | World-fixed ratio and scene percentile interval |
|---|---:|---:|---|---:|---|
| Filtered cache | 2,712 | 431.5 | 6.285052 [4.702391, 10.381009] | 543.5 | 4.989880 [3.971889, 7.197414] |
| Complete annotations | 1,689 | 245.0 | 6.893878 [4.605334, 16.129544] | 389.0 | 4.341902 [3.599600, 6.229612] |

The opportunity counts also change: 17,801 camera candidates for the filtered reference and
15,487 for complete annotations. Compare numerators and denominators, not ratios alone. Adding
reference annotations reduces both counts and can increase the ratio. A contaminated-label ratio
is not automatically an upper bound on a physical ghost parameter.

For continuity, the tool separately reconstructs the historical rule that excludes empty donors:
its filtered-reference ego-relative ratio is **6.179517**, consistent with AH's rounded 6.2.
The retained JSON contains both donor rules and all null comparisons. This is a sensitivity
analysis, not a preregistered selection of a winning null.

![Reference population and temporal-null sensitivity](figures/research-board-ao.svg)

## Replay and custody

The aggregate transcript is [result_ao.json](../evidence/measurement/result_ao.json).
The [audit tool](../tools/measure/result_ao_reference_population_audit.py) records its own digest,
Python/NumPy/SciPy versions, and the size and SHA-256 of every input before and after analysis.
It refuses changes to inputs during a run. The input hashes are identities, not proof that those
inputs are complete or physically correct.

```sh
python tools/measure/result_ao_reference_population_audit.py --data-root /path/to/local/reiyah-data
```

The required directory contains `gt_val_cache.json`, the Mapillary and Megvii matched files,
`meta.tgz`, and the corresponding JSON files under `predictions/`. The manifest records the
interpreter used for the retained bytes. Numerical bitwise reproducibility across other library
versions and platforms is not assumed.

An optional `--private-cases-output /path/to/local/cases.json` retains annotation tokens and
coordinates for follow-up adjudication. That source-derived case file stays outside public Git;
the aggregate result contains no copied annotation rows or prediction examples. The private
cases are deterministic examples, not a random or blinded adjudication sample.

## What changes

The physical interpretation of AH and related persistence/operating-point results is narrowed
to reference-relative unmatched detections. Historical transcripts remain unchanged. The new
claim register records that qualification; replaying historical stdout does not readmit its
overinterpretations.

The next experiment is blinded, scene-stratified adjudication against an independent reference,
including unresolved cases and noncoincident controls. No conclusion here establishes a vehicle
safety rate, modality-specific cause, universal independence law, human belief measurement,
operator acceptance, runtime authority or state-of-the-art performance.
