# Result AH2b: the fair reference for Result AH2, coincident true detections

Document ID: `reiyah.result-ah2b-coincident-true-recurrence`

Version: `0.1.1`

Lifecycle status: `proposed`

> Reference correction, 2026-09-07: the historical ghost label in this analysis means absence
> from a class/range-filtered annotation cache. [Result AO](RESULT_AO_REFERENCE_POPULATION_AUDIT.md)
> demonstrates material differences from the complete annotation reference. Neither reference
> certifies physical nonexistence. Physical ghost interpretations and any automatic upper-bound
> reading of the coincidence ratio are withdrawn as stated. Numerical results below remain
> historical, reference-relative observations; they have not been physically adjudicated or all
> recomputed under the corrected reference. True-detection controls use that same selected
> reference and do not independently resolve the missing-reference issue.


## Why

An adversarial reading of Result AH2 pointed out that its reference rates (static annotated
objects 60.5 percent, true camera detections 76.9 percent) are single-channel recurrences, while a
coincident ghost recurs only if both channels re-fire within 2 m half a second later. The gap
could have been the conjunction penalty of a stricter event. The fair reference is the recurrence
of coincident true detections, measured here with Result AH2's definitions imported unchanged.

## The result, primary pair at 0.30

| set | items | recur within 2 m in the next keyframe | 95% band |
|---|---|---|---|
| coincident ghosts (AH2) | 3,597 | 45.9% | [35.9, 53.5] |
| **coincident true detections** | 66,723 | **71.7%** | [69.7, 73.4] |
| true camera detections, single channel | 76,796 | 74.2% | [71.8, 76.0] |
| true lidar detections, single channel | 93,648 | 76.9% | [75.2, 78.5] |

## What it says

The conjunction penalty is small: coincident true pairs recur 71.7 percent of the time against 74
to 77 for single channels. Coincident ghosts recur 45.9 percent. The AH2 reading stands against the
fair reference: about half of the coincident ghosts are momentary, and unannotated static objects,
which would recur like coincident true pairs, cannot account for them all.

## Non-claims

Released detector outputs on the public nuScenes validation split, retained as `proposed`.
Recurrence separates persistent from momentary, not real from artifactual. One pair, one operating
point. Transcript `evidence/measurement/result_ah2b.txt` re-runs byte-identically (two runs). No
detector is executed. No released `1.2` byte is involved.
