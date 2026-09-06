# Human channel H6b: the edge detector's blindness is genuine and size-driven

Document ID: `reiyah.human-channel.h6b-blindness-check`

Version: `0.1.0`

Lifecycle status: `proposed`

## Why

The adversarial reading of H6 called an 84.5 percent total-miss rate for a small edge detector on
objects a strong detector finds "implausible as genuine blindness and far more consistent with a
pipeline defect (resolution, class mapping, or IoU matching)". This re-executes H6's detector pass
with the same models, thresholds, alignment and matching, records each reference object's box area
and class, and tests the three named defects directly.

## The result

BDD-A validation, 120 clips, 651 frames, 9,545 reference objects. Category lists of the two models
are identical.
<!-- review-exempt: 1280=frame width, a property of the video written 720x1280 in the transcript; 320=the deployed detector's input side, from its model name -->

| condition | total-miss rate |
|---|---|
| H6 definition (deployed score at least 0.25, IoU at least 0.5) | 84.0% |
| looser matching (IoU at least 0.3) | 80.7% |
| looser deployed score (at least 0.10) | 62.7% |

| reference box area quartile (pixels squared in the 720 by 1280 frame) | n | miss | IoU 0.3 | score 0.10 |
|---|---|---|---|---|
| smallest quarter, under 607 | 2,386 | 100.0% | 99.7% | 96.9% |
| second, 607 to 1,875 | 2,386 | 99.4% | 97.4% | 83.7% |
| third, 1,875 to 7,454 | 2,386 | 94.0% | 88.7% | 54.3% |
| largest quarter, over 7,454 | 2,387 | 42.6% | 37.2% | 16.1% |

By class: traffic light 99.3 percent, stop sign 97.5, bicycle 95.5, person 93.5, car 80.9,
motorcycle 80.9, bus 64.3, truck 64.1.

## What it says

1. **Not a matching defect.** Loosening the overlap threshold from 0.5 to 0.3 recovers three
   points; a mislocalization defect would recover far more.
2. **Not a class-mapping defect.** The two models share one category list, and the miss rate is
   high on every class, including the largest and best-annotated (car, 80.9 percent).
3. **Size.** The miss rate runs from 100 percent on the smallest quarter of boxes to 42.6 on the
   largest, at every matching and score setting. A detector that downsamples the frame to 320
   pixels cannot see what occupies a few hundred pixels squared in a 720 by 1280 frame. The
   blindness is genuine and it is the blindness of a cheap detector to small and distant objects.
4. **What this does not change.** The construction's marginals (84 percent automation miss, 50
   percent human miss) still cap the coefficient near 1.18, so H6's "approximately independent"
   remains close to forced, and the human-machine cell of the law rests on H5 and H5b. The
   register requirement that the blindness be verified before the coefficient is read is met; the
   ceiling caveat stands.

## Non-claims

Same detectors, thresholds, alignment and matching as H6; a diagnostic of the automation
channel's miss rate, not a re-measurement of the coefficient. This run covered 120 clips and 651
frames against H6's 100 clips and 533 frames, so its counts differ from H6's. Research-use public
data under the Regents' licence. One detector pass; byte identity on the accelerator was shown for
H5b and is not re-tested here. No released `1.2` byte is involved.
