# Result AH: the camera and the lidar report phantom objects at the same places, at the same instants

Document ID: `reiyah.result-ah-ghost-coincidence`

Version: `0.1.0`

Lifecycle status: `proposed`

## The mistake type the program had never measured

RSS Corollary 3 assumes c-approximate independence for both mistake types, misses and ghosts, and
the register's evidence-cost claim lists "measure ghost-ghost dependence" as its third unmet
condition. Every coefficient in this program so far is a miss coefficient. This is the first ghost
coefficient, on Mapillary (camera) and Megvii (lidar) at the 0.30 operating point.

A ghost is a detection with no annotated object of any class within 2 m of its center, counting
every annotation, including those the benchmark deletes for having no lidar or radar return; the
definition is deliberately lenient, so a duplicate or misclassified report of a real object is not
a ghost. Coincidence is a camera ghost with a lidar ghost within 2 m. Three nulls, stated in
advance: the lidar ghosts rotated about the ego by a random angle (keeps count and range), rotated
by 180 degrees, and, geometry-preserving, the lidar ghosts of the same scene about five seconds
earlier or later carried into the current ego frame with the heading recovered from the ego track
(same road, same sensor, a different instant). Bands are scene-clustered bootstraps.

## The result

Camera detections 103,008, of which 24,432 are ghosts (23.7 percent); lidar detections 119,670, of
which 23,840 are ghosts (19.9 percent).

| quantity | value | 95% band |
|---|---|---|
| P(lidar ghost within 2 m of a camera ghost), observed | 15.25% | [12.13, 18.33] |
| same, rotation null | 1.30% | [0.97, 1.66] |
| same, 180-degree null | 0.67% | [0.48, 0.92] |
| P(lidar ghost within 2 m of a camera ghost), on the 3,756 keyframes with a time-shift partner | 15.58% | [12.41, 18.85] |
| same, within-scene time-shift null | 2.52% | [1.33, 3.92] |
| P(camera ghost within 2 m of a lidar ghost), observed | 15.14% | [11.71, 18.87] |
| sanity: P(lidar true detection within 2 m of a camera true detection), observed / rotation null | 86.91% / 10.68% | |

| coefficient | value | 95% band |
|---|---|---|
| `c_ghost`, camera to lidar, against the rotation null | 11.73 | [10.46, 13.30] |
| `c_ghost`, lidar to camera, against the rotation null | 11.82 | [10.59, 13.44] |
| **`c_ghost`, against the within-scene time-shift null** | **6.18** | **[4.60, 10.31]** |
| `c_real` (sanity), true detections against the rotation null | 8.14 | [7.43, 9.00] |

By camera-ghost class against the rotation null: car 8.8, pedestrian 9.1, truck 9.4, bus 11.0,
barrier 15.3, traffic cone 16.5.

## What it says, with its red team attached

1. **Ghosts coincide far beyond independence, and mostly at the same instant.** One camera ghost
   in seven has a lidar ghost within 2 m; independent placement with the same ranges predicts one
   in seventy-seven. Against the strong null, which keeps the road, the sensor and the persistent
   structure and changes only the instant, the excess is still six-fold with a lower bound of 4.6.
   Persistent shared structure explains part of the coincidence (the null rises from 1.3 to 2.5
   percent) and not most of it.

2. **The rotation null is weak, and the sanity row says so.** True detections co-locate 8 times
   above it, because rotating detections about the ego scatters them off the road. The rotation
   coefficients are therefore inflated by shared road geometry, exactly as the marginal miss
   coefficient includes shared difficulty. The time-shift coefficient is the load-bearing one.

3. **Reference error can manufacture coincident ghosts.** A real object the annotation missed makes
   both channels' true reports look like coincident ghosts. The class table points at this: barrier
   and traffic-cone ghosts coincide at 40 and 26 percent, and those are the classes whose small,
   repeated instances are most plausibly under-annotated. The register's reference-error
   identification is `unknown`, so `c_ghost` is an upper bound in that direction. The car,
   pedestrian and truck rows, where annotation is most complete, still sit near 9 against the
   rotation null. Result AH2 bounds this threat: 54 percent [46, 64] of coincident ghosts do not
   recur half a second later, where an unannotated static object would recur about 61 to 77
   percent of the time, so unannotated objects cannot account for them all.

4. **What this does to the evidence-cost claim.** Condition three, ghost-ghost dependence, is now
   measured and is not small. It is not identified as a bound, because of point 3, and conditions
   one, two, four and five are untouched. The withdrawn figures stay withdrawn. What the measurement
   adds is direction: a redundancy argument that assumed independent ghosts assumed something
   further from the data than the miss assumption was.

Replicated the same day on a second camera, a second lidar and a second operating point, with
time-shift coefficients of 4.6 to 9.8 and no band reaching 1
([AH3](RESULT_AH3_GHOST_REPLICATION.md)).

## Adversarial reading, 2026-09-06

A context-free reader (model-assisted, advisory, same model family as the author) read this document against its transcript alone. The points below are the ones that changed a sentence; the full record is `evidence/review-model-assisted-2026-09-06.json`.

1. **The table mixed two keyframe sets.** The time-shift null (2.52 percent) is computed on the
   3,756 keyframes with a heading and a partner, where the observed rate is 15.58 percent, and the
   coefficient 6.18 is their ratio; the 15.25 percent row is the all-keyframe rate. The table now
   carries both rows. 2,197 keyframes are excluded from that null, of which 1,173 lack a heading and
   the rest lack a partner ten keyframes away.
2. The 180-degree null was announced and its outcome was not reported: 0.67 percent [0.48, 0.92],
   coefficient 22.73 [17.09, 30.80]. It is the weakest of the three nulls for the same geometric
   reason as the rotation null.
3. "Where annotation is most complete" and "most plausibly under-annotated" are conjectures about
   the annotation set, stated as such now.
4. **Operating-point dependence (Preregistration AK, run after this reading).** At 0.10 the
   time-shift coefficient is 2.65 [2.47, 2.88] and ghosts co-locate less than true detections
   relative to the rotation null; the finding as stated here holds at 0.30 and 0.50 and not at
   0.10. See Result AK.

## Non-claims

Released detector outputs on the public nuScenes validation split, retained as `proposed`. One pair,
one operating point in this document, four in AH3, one ghost definition stated in advance; the annotation set is a reference
process with unknown error, and the class-agnostic 2 m rule is lenient by design. The time-shift
null excludes the 1,173 keyframes whose ego moved under 0.5 m. Not a safety determination, not a
certificate about any deployed system. Transcript `evidence/measurement/result_ah.txt` re-runs
byte-identically (two runs of the final tool). No detector is executed. No released `1.2` byte is
involved.
