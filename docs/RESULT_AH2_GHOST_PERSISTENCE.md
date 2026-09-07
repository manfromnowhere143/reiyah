# Result AH2: about half of the coincident ghosts are momentary

Document ID: `reiyah.result-ah2-ghost-persistence`

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


## The threat Result AH named

Result AH measured that camera and lidar ghosts coincide six-fold beyond a same-road,
different-instant null, and named its own biggest threat: a real object the annotation missed makes
both channels' true reports look like a coincident ghost. Such an object is static in map
coordinates, so a coincident ghost it causes recurs at the same map location in the next keyframe,
half a second later. A shared momentary hallucination does not. This measures that recurrence for
coincident ghosts and for four comparison sets, in map coordinates within the same scene, with
scene-clustered bands.

## The result

| set | items | recur within 2 m in the next keyframe | 95% band |
|---|---|---|---|
| **coincident ghosts** | 3,597 | **45.9%** | [35.9, 53.5] |
| lone camera ghosts | 20,138 | 39.1% | [35.8, 42.7] |
| lone lidar ghosts | 19,660 | 30.3% | [28.0, 32.6] |
| true camera detections | 76,796 | 76.9% | [74.9, 78.7] |
| static annotated objects, seen by the camera next keyframe | 96,068 | 60.5% | [58.1, 63.0] |

## What it says

1. **About half of the coincident ghosts are momentary.** Fifty-four percent [46, 64] of them
   have no coincident ghost within 2 m half a second later. An unannotated static object would
   recur at the rate of static annotated objects seen by the camera, about 61 percent, or of true
   detections, 77 percent. Coincident ghosts recur at 46 percent. Unannotated real objects cannot
   account for them all; the momentary share is a lower bound on shared hallucination, because a
   persistent reflective artifact both channels hallucinate at is also persistent.

2. **Coincident ghosts are more persistent than lone ghosts.** 46 percent against 39 and 30. Part
   of the coincidence is therefore persistent structure, real or artifactual, as Result AH's
   time-shift null already indicated (its null rose from 1.3 to 2.5 percent). The two results agree:
   most of the six-fold excess is instantaneous, a minority is structure.

3. **What this does to the ghost coefficient.** It bounds the reference-error threat rather than
   removing it. If every persistent coincident ghost were an unannotated real object, the
   coefficient against the time-shift null would fall by roughly the persistent share; it would not
   reach 1. The evidence-cost condition on ghosts stays measured and not identified, and the
   direction of the finding, that ghosts coincide far beyond independence, does not depend on it.

## Adversarial reading, 2026-09-06

A context-free reader (model-assisted, advisory, same model family as the author) read this document against its transcript alone. The points below are the ones that changed a sentence; the full record is `evidence/review-model-assisted-2026-09-06.json`.

1. **The reference was the wrong kind, and the right one was then measured.** The reader pointed
   out that 60.5 and 76.9 percent are single-channel recurrence rates while a coincident ghost
   recurs only if both channels re-fire within 2 m. Result AH2b measures the fair reference:
   coincident TRUE detections recur 71.7 percent [69.7, 73.4] of the time. Coincident ghosts recur
   45.9 percent [35.9, 53.5]. The gap stands against the fair reference.
2. "At least half" overstated a band that includes values below half; corrected to "about half,
   band [46, 64] percent not recurring".
3. Coincident ghosts against lone camera ghosts: the bands [35.9, 53.5] and [35.8, 42.7] largely
   overlap; "more persistent than lone ghosts" is a point-estimate ordering and is stated so.
4. The momentary share is a lower bound on momentary events, not on hallucination specifically; a
   momentary coincident ghost could also be an unannotated moving object.

## Non-claims

Released detector outputs on the public nuScenes validation split, retained as `proposed`.
Recurrence over 0.5 s in map coordinates separates persistent from momentary, not real from
artifactual. One pair, one operating point. Not a safety determination. Transcript
`evidence/measurement/result_ah2.txt` re-runs byte-identically (two runs). No detector is executed.
No released `1.2` byte is involved.
