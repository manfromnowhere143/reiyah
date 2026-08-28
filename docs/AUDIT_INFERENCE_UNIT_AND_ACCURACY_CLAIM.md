# Two audits: the inference unit, and a claim no computation produced

Document ID: `reiyah.audit-inference-unit-and-accuracy-claim`

Version: `0.1.0`

Lifecycle status: `proposed`

Both audits were run against the measurements already in this workstream, with the
intent of refuting them. One result survived and was narrowed. One claim did not
survive and is withdrawn.

## Audit 1: Result E survives, its evidence was overstated about fivefold

Transcript: [`audit_result_e_clustering.txt`](../evidence/measurement/audit_result_e_clustering.txt).
Tool: [`audit_result_e_clustering.py`](../tools/measure/audit_result_e_clustering.py).

### The attack

`tools/measure/result_e.py` iterates one row per ground-truth box. nuScenes ground
truth is tracked, so those 134,565 boxes come from 8,976 instances, a mean of 14.99
boxes each. Boxes of one tracked instance are the same object seen by the same
detector at adjacent timestamps. They are not independent draws. A Mantel-Haenszel
chi-square computed as if they were overstates the evidence by the design effect.

This workstream had already named this exact error for itself. From
[`FIRST_SEMANTICALLY_VALIDATED_MEASUREMENT.md`](FIRST_SEMANTICALLY_VALIDATED_MEASUREMENT.md):
"Treating roughly fifteen near-identical boxes of one tracked object as independent
observations is precisely the clustering error listed in our own traps table." The
correction was applied to the record-building unit. It was never applied to the
statistics in Results D, E, G and H.

### What the audit did

The audit first reproduces Result E exactly at score `>= 0.3`, stratified by class,
range band and visibility: 132 strata, 134,477 used, 88 thin, 33,665 observed joint
misses, conditional lift `1.156`. Byte-anchored against the published transcript
before anything is changed.

It then runs two matched multinomial bootstraps at 2,000 replicates, seed
`20260828`: one resampling rows, as the published analysis implicitly assumes, and
one resampling whole tracked instances.

### Result

| Quantity | Row unit, as published | Instance unit |
|---|---|---|
| Conditional lift `c` | 1.156 | 1.156 |
| Bootstrap standard error | 0.00249 | 0.00558 |
| 95% interval | [1.151, 1.161] | [1.144, 1.166] |
| Design effect | 1.00 by construction | 5.02 |
| Effective sample size | 134,565 | 26,832 |
| CMH, 1 df | 4,924 | about 982 |

**Result E's conclusion stands.** The point estimate is identical, because clustering
affects variance and not the estimator. The cluster-robust interval [1.144, 1.166]
excludes 1.0. Camera and lidar detectors do fail together beyond what class, range
and visibility explain, and a chi-square near 982 on 1 df is still far past any
conventional threshold.

**Result E's stated evidence does not stand.** The published CMH of 4,924 is
computed at the box unit and overstates the evidence by a factor of about five. The
correct denominator for any RSS-style evidence-count argument is roughly 8,976
independent tracked objects, not 134,565 boxes.

Results D, G and H share the box-level unit. No point estimate changes. Every
interval and test statistic derived from them must be restated at the instance unit
before use.

### A second observation, recorded not corrected

`cam.get(i, -1.0) < thr` cannot distinguish a detector that emitted nothing from a
detector that emitted a low score. Both become a confident miss. The counts:

| Detector | Rows with no entry | Share of rows | Share of that detector's misses |
|---|---|---|---|
| Mapillary | 32,787 | 24.4% | 52.5% |
| Megvii | 18,091 | 13.4% | 39.6% |
| Both absent | 10,715 | 8.0% | not applicable |

For a detection task an unmatched ground-truth object is a genuine false negative, so
the coercion is defensible and no result changes. It is recorded because
`docs/SCIENTIFIC_CHARTER.md` section 7 forbids silent coercion, and more than half of
Mapillary's measured misses arrive through this path.

## Audit 2: the accuracy claim is withdrawn

Transcript: [`audit_result_h_accuracy_claim.txt`](../evidence/measurement/audit_result_h_accuracy_claim.txt).
Tool: [`audit_result_h_accuracy_claim.py`](../tools/measure/audit_result_h_accuracy_claim.py).

### The claim

[`GATE_B_MEASUREMENT_CONTRACT.md`](GATE_B_MEASUREMENT_CONTRACT.md) row H, labelled
`measured`, and [`GATE_B_SESSION_HANDOFF.md`](GATE_B_SESSION_HANDOFF.md) section 4:
"Joint-failure odds rise with the accuracy of both models: 7.01, 15.86, 31.99."

### No computation produced it

`tools/measure/result_h.py` binds

```python
MAP = {"mapillary": 29.8, "megvii": 51.9, "pointpillars": 29.5, "centerpoint": 61.6}
```

and never references it again. No script in `tools/measure/` regresses, ranks,
correlates or tests an odds ratio against accuracy. The three figures are the three
same-modality Mantel-Haenszel odds ratios from
[`result_h.txt`](../evidence/measurement/result_h.txt), read in ascending order.

### Five independent objections, any one of which is sufficient

1. **The covariate does not order the data.** `centerpoint x pointpillars` and
   `megvii x pointpillars` share an identical weaker-model accuracy of 29.5 mAP, yet
   their odds ratios differ by 2.26x, 15.863 against 7.010. "The accuracy of both
   models" orders these three points only if "both" silently means the sum, which is
   a different and unstated claim.
2. **A monotone trend on three points carries almost no evidence.** Of the six
   permutations, one is monotone increasing. The permutation p for the stated
   direction is 0.167, and 0.333 for either direction. No threshold is met, and no
   test statistic was reported because no test was run.
3. **The three points are not independent.** Each of CenterPoint, Megvii and
   PointPillars appears in two of the three pairs. The odds ratios share detectors
   pairwise.
4. **Two of the three points rest on an unvalidated accuracy figure.** CenterPoint's
   61.6 mAP is reconstructed and not confirmed against a published number, from a
   source this contract itself marks "explicitly weaker provenance". It appears in two
   of the three pairs.
5. **The headline uses the metric with the widest spread.** Result G states that the
   lift `c`, not the odds ratio, "is the number that belongs against Corollary 3". In
   that metric the same three pairs are 1.313, 1.386 and 1.725, a spread of 1.31x
   against 4.56x for the odds ratio.

### Disposition

The accuracy sentence is **withdrawn**. It must not carry the label `measured`.

Result H's supported finding is untouched. Same-modality and cross-modality pairs do
separate on these six measurements, and that separation is what the script actually
computes. The accuracy sentence was a separate assertion sitting beside it.

Answering the question properly would need more detectors, a validated accuracy for
every one, a metric declared before inspection, and intervals that respect both the
pair-sharing in objection 3 and the instance clustering in Audit 1. That is a design,
not a result, and it is recorded as a proposed question.

## What these audits do not establish

Neither audit creates scientific support, safety finding, compliance determination,
comparative claim about any detector or vendor, or operator acceptance. Audit 1
narrows a retained measurement. Audit 2 withdraws a claim. Both leave every released
`1.2` byte unmodified. Advancing anything here beyond `proposed` still requires the
evidence admission process, an authorized operator decision, and independent review,
none of which this document supplies.
