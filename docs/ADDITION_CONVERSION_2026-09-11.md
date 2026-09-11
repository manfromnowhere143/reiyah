# The number that decides a sensor addition, measured on a full split

Document ID: `reiyah.addition-conversion.2026-09-11`

Version: `0.1.0`

Lifecycle status: `corrected`

Lane: independent research, parallel to the Engine. Changes no released byte, no frozen protocol,
no Engine file and no owner checkout. Creates no acceptance and no scientific authority. Gate A
remains unaccepted.

## Correction of 11 September 2026, read first

External review of this lane's published code found three defects in the measurement behind this
document. They are reproduced and isolated on the real data in
[the correction](CONVERSION_CORRECTION_2026-09-11.md).

- One score floor was applied to the base and the addition **together**, so the floor sweep below
  changed the installed configuration as well as the candidate. **The claim that the required
  penalty ratio moves by about a factor of 69, and the figures `0.0284`, `34.24`, `0.6692` and
  `0.494`, are withdrawn as stated.** Holding the base fixed, the corrected span is `5.45x`.
- Keyframes with no eligible reference object were skipped. Effect here was negligible.
- The declared `50 m` limit was applied to annotations and not to predictions. Correcting it moves
  the headline conversion from `0.2960` to `0.3182` and the break-even from `2.379` to `2.143`.

The corrected numbers are in the correction document. Everything below is retained unchanged,
including the withdrawn figures, so the record shows what was published.

## The question and the result

Under an additive false-negative and false-positive loss, the decision to add a detector to an
existing configuration is governed by exactly one measured quantity and one declared one. The
measured quantity is the **conversion rate**: the fraction of the addition's retained detections
that match an object the base missed. The declared one is the **penalty ratio** `a/b`. The addition
improves the loss precisely when

```text
conversion  >  b / (a + b)      equivalently      a/b  >  1/conversion - 1
```

Measured across the whole nuScenes validation split, 5,953 keyframes and 134,565 annotated objects,
at a `0.30` score floor with strict `2 m` same-class maximum matching and `2 m` suppression:

| base | addition | retained additions | gain | conversion | break-even `a/b` |
|---|---|---:|---:|---:|---:|
| megvii lidar | mapillary camera | 33,450 | 9,900 | **0.2960** | **2.379** |
| mapillary camera | megvii lidar | 50,561 | 24,577 | **0.4861** | **1.057** |
| megvii lidar | pointpillars lidar | 22,832 | 5,995 | 0.2626 | 2.809 |

**A miss must cost more than 2.38 false detections before adding that camera to that lidar improves
the loss.** Adding the lidar to the camera pays off above about 1.06. The same two detectors, and
the direction of the addition moves the break-even by more than a factor of two.

## The operating point moves it far more than the modality does

The same pair, the same population, only the score floor changed:

| floor | retained additions | gain | conversion | break-even `a/b` |
|---|---:|---:|---:|---:|
| 0.10 | 151,671 | 4,304 | 0.0284 | **34.24** |
| 0.30 | 33,450 | 9,900 | 0.2960 | 2.379 |
| 0.50 | 16,078 | 10,760 | 0.6692 | **0.494** |

The required penalty ratio moves by a factor of about **69** across this sweep. Against that, the
cross-modality choice is minor: adding a second lidar converts at `0.2626` where adding the camera
converts at `0.2960`, a difference the threshold choice swamps.

The engineering reading is direct. **An addition decision is not separable from the operating point
at which the addition is fused**, and reporting a detector's benefit without its floor and the
penalty ratio does not determine the decision in either direction.

## Why a benchmark number cannot substitute

Three facts, verified by exhaustive enumeration over every bipartite match graph within the declared
size bound, 404 cases and zero violations:

1. adding detections to a preserved base never decreases the maximum matching, so recall is monotone
   non-decreasing in the augmentation;
2. the gain never exceeds the number of retained additions;
3. `sign(delta) = sign(conversion - b/(a+b))` at every enumerated graph.

Fact 1 is the uncomfortable one. **Any selection rule that is monotone in recall alone says add it,
every time**, including every case where the loss worsens. The two disagree exactly on
`conversion <= b/(a+b)`, and that region is never empty.

The exhaustive graph enumeration is too small to expose the penalty-ratio dependence, because at
those node counts the only worsening augmentations have zero gain and zero gain worsens the loss at
every ratio. The dependence is shown separately over the realisable `(gain, r)` pairs, every one of
which is achieved by some graph: of 90 pairs with `r <= 12`, the number that worsen the loss falls
from 48 at `a/b = 1` to 34 at `2` and 23 at `4`.

This is a statement about the declared additive loss. It is **not** a claim about mAP, which
penalises precision through ranking and is not recall-monotone. What is claimed is narrower and
still sharp: a detection benchmark publishes neither the conversion rate nor the operational penalty
ratio, so a benchmark improvement does not determine the addition decision.

## Scope and limits

One public split, released detector outputs of an earlier generation, the retained filtered
annotation cache as reference, one declared matching and suppression rule. Reference relative and
descriptive. No sampling statement is attached: these are finite-population counts, not estimates
with an error bar, and no confidence interval is claimed. Nothing here is a statement about any
deployed stack, and the identity does not transfer to F1, planner behaviour or crash risk.

The conversion rate is measured against a reference that is itself under audit. If that reference
omits objects, an addition that finds them is scored as a false detection, which biases conversion
downward. That is a real and unquantified threat here, and it is the same reference-validity gap
that the rest of this lane has repeatedly reached.

## Costs

Each full-split measurement takes 17 to 63 seconds and about 1.5 GB peak resident, dominated by
parsing the prediction files. The exhaustive enumeration takes 0.03 seconds. Everything is exact
rational arithmetic on the standard library.

## Reproduce

```sh
python3 -B tools/measure/addition_monotonicity.py
python3 -B tools/measure/conversion_rate.py CACHE_DIR PRED_DIR megvii mapillary 0.30
python3 -B -m unittest discover -s tools/measure -p test_decision_packet.py
```

The first reads no data. The second reads the retained files read only and emits aggregate counts
only: no token, coordinate, score or path.

## Non-claims

An internal research artifact, retained as `proposed`. Not independent external scientific review,
not an operator acceptance, not a safety, compliance or vendor claim, not a benchmark result and not
a statement about any deployed system. No released `1.2` byte, frozen protocol, claim-register entry
or other owner's work is modified.
