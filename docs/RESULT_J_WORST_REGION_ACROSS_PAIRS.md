# Result J: the worst region generalises, the worst stratum does not

Document ID: `reiyah.result-j-worst-region-across-pairs`

Version: `0.1.0`

Lifecycle status: `proposed`

## The question

Result I found that for `mapillary x megvii` the most dependent eligible stratum is
`car, 0-20 m, v80-100` at lift 6.946 against a pooled 1.156. One pair cannot distinguish
a fact about two detectors from a fact about a region of the driving problem.

The falsifier was declared before running: if each pair's worst group is a different
stratum, Result I is about a detector pair and must be stated that way.

## Detectors, and one deliberate exclusion

| Detector | Modality | Published mAP | Reproduced |
|---|---|---|---|
| Mapillary MonoDIS | camera | 29.80 | 29.58 |
| Megvii CBGS | lidar | 51.90 | 51.97 |
| PointPillars | lidar | 29.50 | **29.54** |

The PointPillars match file was rebuilt for this result and gated on the devkit's own AP
definition before use: reconstructed 29.54 against published 29.50, delta 0.04, PASS. A
match set that does not reproduce published mAP is not admitted.

**CenterPoint is excluded.** Its predictions come from a third-party mirror that
`GATE_B_MEASUREMENT_CONTRACT.md` marks "explicitly weaker provenance", and its accuracy
figure is reconstructed and unconfirmed. Audit 2 withdrew a claim that leaned on it. It is
not readmitted here, even though including it would have produced three same-modality
pairs instead of one.

Nothing was re-tuned per pair. Direction, universe, eligibility, uncertainty and
multiplicity are identical to Result I.

## Results

| Pair | Kind | Pooled lift | Worst group | Worst lift | Simultaneous 95% |
|---|---|---|---|---|---|
| mapillary x megvii | cross | 1.156 | `car`, 0-20 m, `v80-100` | 6.946 | [2.221, 11.671] |
| mapillary x pointpillars | cross | 1.101 | `car`, 0-20 m, `v60-80` | 2.350 | **[0.992, 3.709]** |
| megvii x pointpillars | SAME | 1.313 | `car`, 0-20 m, `v80-100` | 6.427 | [1.429, 11.424] |

Every partition is exact with zero unknown groups, so every worst-group result is
identified.

## What generalises

**The region does.** In all three pairs the worst eligible stratum is a close-range car,
and in all three the entire top three are close-range cars. This holds for two
camera-lidar pairs and for a lidar-lidar pair, which share no common modality structure.

**The exact stratum does not.** Two pairs put `v80-100` worst and one puts `v60-80` worst.
Result I's single-stratum reading is therefore narrowed: it is one pair's extremum inside
a region that is consistently worst, not a universally worst cell.

**One pair's extremum is not established.** For `mapillary x pointpillars` the
simultaneous lower bound is **0.992**, which does not exceed 1.0. After honest multiplicity
correction across 112 eligible strata, that pair's worst group is not distinguishable from
independence. It is reported, not hidden, and it is not counted as support.

## Two observations worth keeping

The same-modality lidar pair carries the **highest pooled lift**, 1.313 against 1.156 and
1.101 for the cross-modality pairs. That is consistent in direction with Result H's
modality separation, obtained here from an independent estimator and a different
stratification.

`mapillary x pointpillars` is the accuracy-matched cross-modality pair, 29.8 against 29.5
mAP. It shows both the lowest pooled lift and the lowest worst-group lift. This is a
single observation and is recorded as such. It is **not** offered as evidence for the
accuracy claim withdrawn in Audit 2, which would need a design, not another data point.

## Consequence

| Pair | Evidence cost, pooled | Evidence cost, worst group |
|---|---|---|
| mapillary x megvii | 7.5% | 163.5% |
| mapillary x pointpillars | 4.9% | 53.3% |
| megvii x pointpillars | 14.6% | 153.5% |

Under `N` proportional to `sqrt(c)`, a redundancy argument provisioned from a pooled lift
under-provisions the close-range car for every pair tested, including a same-modality
pair. The size of the shortfall varies by an order of magnitude between pairs; the
direction does not vary at all.

## Required amendment to Result I

[`RESULT_I_WORST_GROUP_DEPENDENCE.md`](RESULT_I_WORST_GROUP_DEPENDENCE.md) must be read as
one pair's extremum within a consistently worst region. Its worst-stratum identity is
pair-specific. Its regional finding is supported by all three pairs. The amendment is
recorded there.

## Non-claims

No scientific support, safety finding, compliance determination, comparative claim about
any detector or vendor, and no operator acceptance. Three published detection outputs on
one public split, retained as `proposed`. No released `1.2` byte is modified.
