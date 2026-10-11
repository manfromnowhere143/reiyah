# A mean error must not depend on the processing batch

Version 0.1.0 · 11 October 2026 · exploratory authored software control

**Changing only the processing batch reverses this constructed mean-error
comparison in the retained evaluator.** Its chunk processor returns auxiliary
metric arrays from the final image of each chunk; the outer evaluator averages
those arrays. Collecting every image's arrays restores the detection-weighted
means across all tested image orders, batch sizes and worker counts.

This completes the specific aggregation check omitted from the
[earlier empty-output control](../../empty-output-score-control/0.1.0/README.md).
Both arms retain that control's unchanged empty-image correction. The new
correction addresses auxiliary means; it leaves AUSRC and reference counts
unchanged in all 90 paired checks. Neither correction has been applied upstream.

## An execution setting changes the winner

Two images each contain one object and one geometrically correct detection.
A assigns correct-class probabilities 1 and 1/2; B assigns 5/8 to both.
Remaining probability belongs to background. For the hard reference labels in
this example, per-detection total variation distance is one minus the
correct-class probability. Lower mean TV distance is better.

| Processing configuration, image order 1 then 2 | Native A | Native B | Corrected A | Corrected B |
| --- | ---: | ---: | ---: | ---: |
| One image per chunk | 0.25 | 0.375 | 0.25 | 0.375 |
| Both images in one chunk | 0.50 | 0.375 | 0.25 | 0.375 |

The two-image chunk retains only the second image's auxiliary metric arrays.
Reversing the image order makes native A report zero mean TV distance instead.
Its correct mean is always `(0 + 1/2) / 2 = 1/4`. The predictions, references,
matching and metric definition are otherwise unchanged. Worker counts 1 and 2
give the same respective results.

The example concerns mean TV distance. Different error metrics have different
preferences; it is not a claim that A is uniformly better under all six metrics.
All MAE, MSE, KL, Jensen–Shannon distance, TV distance and cosine-distance results
are retained in [result.json](result.json).

## Correct the population before averaging

The [authored wrapper](reproduce.py) calls the exact native chunk processor for
each image, collects its arrays and concatenates every image's auxiliary
results before the unchanged outer mean. It preserves the score, similarity
and true-positive arrays and reference count used by AUSRC. The underlying
per-detection metric and matching functions are unchanged.

This is a conventional aggregation correction, not a new estimator. Images
with unequal numbers of detections must contribute different amounts of data.
In the unequal-count fixture, image 1 has two detections with TV distances 0
and 1/4; image 2 has one with distance 1/2. The correct mean is 1/4. Averaging
the two image means gives 5/16, which the checker rejects.

All eligible detections and matched detections are separate populations.
An unmatched prediction is compared with the native background target and
belongs only to the all-detection population. Area-ignored detections belong
to neither population. The fixtures use exact or disjoint boxes, so their
geometry has no ambiguous assignment.

If a population has no eligible detections, its mean is undefined. The native
function returns NaN for such an empty mean; the authored report represents
that observation as `count: 0`, `state: undefined_no_samples`, and null means.
It never substitutes zero error. Conversely, a final empty or area-filtered
image must not erase metric values from earlier nonempty images in its chunk.

## What was checked

The [protocol](protocol.json) and all eight [fixtures](fixtures.json) were frozen
before scoring, after source inspection identified the suspected mechanism.
This is an anticipated authored counterexample, not a blinded empirical study.
Every image-order permutation is combined with chunk sizes 1, 2 and 64 and
worker counts 1 and 2: 90 configurations and 180 native/corrected evaluations
per complete run.

The controls cover the two comparison arms, unequal detection counts, mixed
matched and unmatched detections, a trailing empty image, a completely empty
output, a population with no matches and a final area-filtered image.

The [separate checker](verify.py) imports neither the producer nor PyTorch nor
the upstream source. It derives the detection populations and metric values
from the authored distributions and unambiguous geometry:

- 1,656 numeric means agree. MAE, MSE and TVD expectations use rational
  arithmetic; KL, Jensen–Shannon and cosine expectations use scalar logarithms
  and square roots. Native float32 values use an absolute tolerance of 5×10⁻⁶.
- 504 undefined mean fields preserve null values, zero counts and explicit
  undefined states.
- All 90 paired AUSRC values and reference denominators are unchanged by the
  new aggregation wrapper.
- Native and corrected metric populations differ in 44 configurations.
  Twelve configurations restore an all-detection population that native
  aggregation incorrectly presents as empty. These are dependent authored
  configurations, not estimated real-world failure frequencies.
- [Ten alteration controls](negative-controls.json) reject wrong means,
  wrong counts, image-weighted averaging, zero or defined states for empty
  populations, boolean counts, missing configurations, changed source or
  fixture bytes, and a disabled correction.
- Two complete producer runs have identical result bytes.

The [verification receipt](verification.json) binds the exact result. The
checks establish this aggregation behavior under these controls, not independent
scientific replication or correctness of the full evaluator.

## Reproduce

Use the unchanged source file `regression_benchmark/evaluation/evaluate_soft.py`
at [upstream commit f793379](https://github.com/JonathanKlees/Uncertainty-aware-Object-Detection/blob/f793379ad7a9760f71c18ba57b7ed71fa76a5e6c/regression_benchmark/evaluation/evaluate_soft.py).
Its SHA-256 is
`d19fab4078ffc61c594e72ad1719bd2179108187de26099c6614eb39ddeeba20`.
The source payload is not redistributed here; obtain it separately under its
applicable terms. The inherited control loader checks its exact bytes, compiles
the thirteen function bodies unchanged and uses real CPU tensor operations.
Optional plotting imports and the upstream CLI are not executed.

The [environment](environment.json) uses Python 3.14.2, PyTorch 2.10.0 and NumPy
2.4.2 on macOS arm64. [Requirements](requirements.txt) are pinned. Run from this
directory in the Reiyah checkout, keeping the linked prior control in place:

```sh
python -B reproduce.py --source /path/to/evaluate_soft.py --output result-local.json
python -B verify.py --result result-local.json --output verification-local.json
python -B negative_controls.py --source /path/to/evaluate_soft.py --result result-local.json --output controls-local.json
```

Output paths must not exist. Source, fixture and inherited control identities
are checked before native scoring. The recorded runs entered a macOS
network-denying sandbox before Python started; these example commands alone
do not impose that sandbox. No image access, weights, inference or paid compute
are required. Cross-platform reproduction has not been run.

## Consequence and stopping point

A later conventional comparison should pass both population-completeness and
aggregation checks before its values inform a decision. Reiyah receives no
advantage from withholding these ordinary corrections from its comparator.

This closes the planned local audit increment of this evaluator. Effects on
published datasets or rankings remain unknown. The two existing public requests
still have no new reply at the recorded read; no new outreach was sent. Further
product-value work needs a fresh consequential comparison, a qualified review
action and complete costs. This control does not supply those missing records
or justify another exposed selector sweep. See [provenance](provenance.json)
and the [next-session brief](../../../docs/NEXT_SESSION.md).
