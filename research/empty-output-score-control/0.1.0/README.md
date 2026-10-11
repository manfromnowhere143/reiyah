# Successful empty outputs must remain in the scoring population

Version 0.1.0 · 11 October 2026 · exploratory authored software control

**Dropping an annotated image because its detector output is empty can reverse
this constructed comparison.** The retained upstream scoring path prefers A;
restoring the complete reference denominator prefers B. An authored adapter
corrects this boundary in the tested COCO-format cases. It has not been applied
to the upstream repository, and no effect on published empirical scores is
established.

This follows the previously retained observation that `prepare_image_data`
omits annotated images with no detections. The new contribution is an executable
scoring-path counterexample, a tested local correction and an independent exact
arithmetic check. It is conventional correctness work, not evidence of a novel
algorithm or Reiyah performance advantage.

## The constructed decision

Both images contain one reference object. A detects the first perfectly and
returns an explicitly successful empty output for the second. B detects both
at the exact reference locations, with probability 0.8 for the correct class
and residual probability 0.2 for background. References are hard-label
endpoints of the evaluator's soft-label representation.

The metric is the upstream AUSRC calculation using TV similarity, maximum
probability sorting, IoU 0.50 and the all-size range. Larger is better.

| Arm | Native reference denominator | Native AUSRC | Complete reference denominator | Corrected AUSRC |
| --- | ---: | ---: | ---: | ---: |
| A: one perfect detection, one empty image | 1 | 1 | 2 | 51/101 ≈ 0.5049505 |
| B: both detected with class probability 0.8 | 2 | 0.8 | 2 | 0.8 |

The native preparation step iterates only image IDs present in detections.
The chunk processor therefore never counts the second reference for A. Its
one detection appears to reach full recall. With both references counted,
maximum recall is 1/2; only 51 of the 101 recall-grid levels have a qualifying
prefix. B's constant similarity remains 4/5 across all levels.

The table gives exact values for the authored arithmetic model. Native
float32 outputs, retained in [result.json](result.json), agree within 2×10⁻⁷.
This is AUSRC, not COCO AP or Reiyah's FP/FN loss.

## Correction and its boundary

The [reproducer](reproduce.py) first requires an explicit successful output
record for every fixture image. A successful empty list is distinct from a
missing file or failed inference. Missing, failed, duplicated, extra and
boolean-ID records reject before scoring. This fixture gate does not
retrospectively qualify the upstream authors' inference runs.

A wrapper around `prepare_image_data` adds annotated image IDs absent from its
output. Each receives the original reference tensors and correctly shaped empty
prediction tensors. Nonempty-image tensors and all native matching, probability,
similarity and integration functions remain unchanged. No placeholder detection
is inserted. Images with neither references nor detections contribute no metric
terms; their successful opportunity records remain explicit in the fixture gate.

The tests execute all native function bodies on the scoring path with real
PyTorch and NumPy. They compile the thirteen top-level functions unchanged from
the pinned source; progress display is replaced by a pass-through. The upstream
CLI and optional plotting/table imports are not executed. Auxiliary mean
metrics are disabled, so this is not an audit of their aggregation.

With a positive reference denominator, a completely empty prediction population
raises a native concatenation error. The adapter yields zero AUSRC. A population
with no eligible reference objects is a different case: the authored gate
rejects it as undefined rather than reporting a confident zero.

The scope is the tested COCO-format entry path. Other datasets, loaders,
class mappings, source geometry contracts and all other evaluator behavior
remain outside this correction. A production fix would need integration at the
original complete opportunity roster before empty and missing outputs become
indistinguishable.

## Verification

The [protocol](protocol.json) was written before the scoring run, after inspecting
the source and anticipating this counterexample. These are authored controls,
not blinded or preregistered empirical findings.

- Both primary arms agree across image-order reversal, chunk sizes 1 and 64,
  and worker counts 1 and 2.
- All eight detection-presence subsets of three one-object images are checked.
  The native all-empty case fails; corrected scores use all three references.
- Single-image and excluded-area controls retain their scores. Sixteen tensor
  equalities preserve two nonempty images, including a prediction-only image.
- A [separate rational checker](verify.py), importing no producer code or tensor
  library, checks 51 defined scores and their reference denominators.
- [Seven alteration controls](negative-controls.json) reject a wrong score,
  wrong denominator, boolean score, boolean worker count, missing subset,
  changed source byte and disabled correction.
- Two final producer runs yield identical result bytes. Six explicit input or
  undefined-metric rejections are retained separately in the result.

The [verification receipt](verification.json) binds the exact result. The
initial harness mishandled the native exception type; that attempt and a
premature verifier invocation are preserved in the private record. Their
correction changed neither the question nor any native scoring equation.
This is separate implementation checking, not independent scientific review.

## Reproduce

The upstream source is `regression_benchmark/evaluation/evaluate_soft.py` at
[commit f793379](https://github.com/JonathanKlees/Uncertainty-aware-Object-Detection/blob/f793379ad7a9760f71c18ba57b7ed71fa76a5e6c/regression_benchmark/evaluation/evaluate_soft.py).
Current upstream main still had those exact bytes at the recorded read.
SHA-256: `d19fab4078ffc61c594e72ad1719bd2179108187de26099c6614eb39ddeeba20`.
Its source payload is not redistributed here. Obtain it separately under the
applicable terms; the reproducer checks its hash before executing any native
function. No images, weights, inference, paid resources or network access are
needed during calculation.

Use the pinned [requirements](requirements.txt) and inspect the tested
[environment](environment.json). Python 3.14.2, PyTorch 2.10.0 and NumPy 2.4.2
were used on macOS arm64; cross-platform reproduction has not been run.

```sh
python -B reproduce.py --source /path/to/evaluate_soft.py --output result-local.json
python -B verify.py --result result-local.json --output verification-local.json
python -B negative_controls.py --source /path/to/evaluate_soft.py --result result-local.json --output controls-local.json
```

Run from this directory with output paths that do not yet exist. The recorded
runs entered a network-denying macOS sandbox before Python started. The scripts
themselves perform no network calls; the three commands above do not impose an
OS-level sandbox on their own.

## Research consequence

Any later comparison must preserve the expected image population and verify
successful empties before flattening detector records. Correct arithmetic over
a silently reduced population cannot justify the intended full-population
decision. The ordinary conventional comparator receives this correction too.

The effect's frequency and any published ranking impact remain unknown because
complete upstream prediction runs have not been qualified. Both existing public
requests remain unanswered at the latest read; no new message was sent.
The retained human response durations still omit preparation, adjudication and
integration, so they do not establish complete work savings. This control does
not admit a product-value case or reopen the completed threshold/reference pair
for tuning. See [provenance](provenance.json) and the
[next-session brief](../../../docs/NEXT_SESSION.md) for the remaining evidence gap.
