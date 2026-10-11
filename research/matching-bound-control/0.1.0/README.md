# Overlap bounds and greedy matching

Document ID: `reiyah.matching-bound-control`

Version: `0.1.0`

Lifecycle status: `exploratory`

Date: 11 October 2026. Authored finite control, checked with exact arithmetic
and the pinned COCO evaluator. No detector inference or sensor data are used.

## Finding

Elementwise bounds on intersection over union (IoU) do not automatically bound
the average precision (AP) obtained by running a greedy matcher at those
endpoints. Matching can change when competing overlaps change.

The [plan](PAIRWISE_BOUND_SCREEN_PLAN.json) was frozen before execution, after
constructing the example mathematically. This is a deliberately chosen
counterexample, not a blinded empirical discovery. The
[result](PAIRWISE_BOUND_SCREEN_RESULT.json) and
[source](screen_pairwise_bounds.py) preserve their original bytes.

## Construction and result

One image, one category, no ignored or crowd objects. Coordinates are
`[x, y, width, height]`; prediction confidence determines matching order.

| Item | Box | Confidence or reference IoU-distance radius |
| --- | --- | --- |
| Reference 1 | [20, 5, 10, 10] | radius 1/10 |
| Reference 2 | [23, 5, 11, 10] | radius 1/20 |
| Prediction 1 | [21.71, 5, 10, 10] | confidence 0.9 |
| Prediction 2 | [18, 5, 10, 10] | confidence 0.8 |

The nominal IoU matrix, with predictions as rows and references as columns, is:

```text
829/1171   871/1229
2/3        5/16
```

Subtract or add the corresponding reference radius to each column and clip to
[0,1]. The nominal matrix lies within these elementwise bounds. The unchanged
reference is an admissible zero-perturbation world under the declared radii.

At IoU threshold 1/2:

| Overlap matrix | First prediction | Second prediction | Exact AP50 | Maximum matching cardinality |
| --- | --- | --- | ---: | ---: |
| Nominal | Reference 2 | Reference 1 | 1 | 2 |
| Lower endpoint | Reference 2 | Reference 1 | 1 | 2 |
| Upper endpoint | Reference 1 | Unmatched | 51/101 | 2 |

The upper endpoint changes which reference the first prediction claims.
The second prediction loses its only eligible reference. Nominal AP50 is 1,
which exceeds the upper-endpoint score of approximately 0.504950495.
Thus the claimed implication fails even though every nominal overlap is
enclosed. Sorting the two endpoint scores would remove this particular
inversion but would not supply a universal proof.

The script checks exact rational geometry against native IoU computation,
then checks the native matching trace and 101-point AP against separate
calculations. For the endpoint evaluations, it explicitly substitutes the
overlap matrix through `computeIoU`; COCO matching and accumulation are
unchanged. The endpoint matrices are not claimed to be jointly realizable
geometric references. The nominal admissible world is the counterexample.

## What this establishes

An AP enclosure must account for the matching procedure and the score being
bounded. Per-pair overlap enclosures alone are insufficient for the shortcut
tested here. This is a deterministic statement about the constructed case;
it is not an estimated effect size or confidence interval.

Reiyah's existing conditional FP/FN engine uses maximum-cardinality matching.
The cardinality remains two in every row above. This control does not add an
AP capability or demonstrate that Reiyah makes better decisions.

No empirical frequency, saved reviewer effort, commercial advantage or novelty
is established. Greedy-assignment concerns were already discussed in
[COCO issue 564, opened in 2021](https://github.com/cocodataset/cocoapi/issues/564).
That discussion is not an accepted declaration that the benchmark is defective.

The investigation was motivated by
[Noise-Aware Evaluation of Object Detectors, WACV 2025](https://openaccess.thecvf.com/content/WACV2025/papers/Llerena_Noise-Aware_Evaluation_of_Object_Detectors_WACV_2025_paper.pdf).
The radii here are authored deterministic values, not that paper's fitted
expected-noise parameters. Its adjusted evaluator was not reproduced.
No defect in the authors' implementation or published results is established.
[Provenance](provenance.json) records the private source captures; no paper
body or upstream implementation is redistributed.

## Reproduce

Use Python 3.13 with the versions in [requirements.txt](requirements.txt).
The retained run used Python 3.13.5, NumPy 2.2.6 and pycocotools 2.0.11.
The script also checks the exact `cocoeval.py` digest. A different evaluator
is rejected rather than treated as the same experiment.

From the repository root, with that environment active:

```sh
reiyah_control_run=$(mktemp -d)
cp research/matching-bound-control/0.1.0/PAIRWISE_BOUND_SCREEN_PLAN.json \
   research/matching-bound-control/0.1.0/screen_pairwise_bounds.py \
   "$reiyah_control_run/"
python -B "$reiyah_control_run/screen_pairwise_bounds.py"
python - "$reiyah_control_run" <<'PY'
import json
import pathlib
import sys

name = "PAIRWISE_BOUND_SCREEN_RESULT.json"
expected = json.loads((pathlib.Path("research/matching-bound-control/0.1.0") / name).read_text())
actual = json.loads((pathlib.Path(sys.argv[1]) / name).read_text())
for record in (expected, actual):
    del record["wall_seconds"]
if actual != expected:
    raise SystemExit("Result mismatch")
print("All non-timing result fields match.")
PY
```

The fresh directory preserves the retained result. Running beside an existing
result fails because output files are created exclusively. The calculation
requires CPU only and performs no network requests. Internal timing excludes
imports and preparation; it is not a measurement of complete workflow cost.
Repeating this calculation is not independent scientific review.
