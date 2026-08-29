# Human channel: identification audit and minimum pilot

Document ID: `reiyah.gate-b.human-channel-feasibility-2026-08-29`

Version: `0.1.0`

Lifecycle status: `proposed`

Design and feasibility audit only. No dataset was downloaded, no human subject was contacted, and
no measurement was performed. Human-subjects review, consent, recruitment, and collection remain
outside all current authority.

## 1. The layering that must be preserved

```
G  gaze observation      states: observed | tracker_invalid | out_of_frame | not_recorded
H  latent awareness      NEVER directly observed
D  decision
R  response (motor action)
A  intervention
Y  outcome
```

**Gaze is not awareness.** The rejected construction is
`gaze does not intersect the object box  =>  M^H = 1`. Its negation is an unmeasured state, not a
miss. Fixating a region does not establish awareness of an object in it, and not fixating does not
establish absence of awareness: peripheral detection, prior fixation held in memory, and expectation
all break the equivalence in one direction, while looking without seeing breaks it in the other.

Identifying `H` requires an evidence channel **other than `G`**: a probe response, a verbal report,
a task-relevant action under a declared mapping, or an adjudicated awareness label whose rater
information set and inter-rater reliability are both recorded. `G` alone bounds `H` at best.

Admissible pilot-stage estimand:

```
theta_H(w) = P( H = aware | probe delivered, probe answered, w in U_P )
```

with `human_state = unknown` whenever no probe was delivered or answered, whenever gaze is invalid,
or whenever the geometric uncertainty envelope does not resolve against the object. **The default
on non-identification is `unknown`, never `miss = 1`.**

## 2. Dataset audit

Verification legend: `V` verified from primary material in this session; `S` search-level
bibliographic record only, primary body not read; `U` not established.

### 2.1 DR(eye)VE, arXiv:1705.03854 `V`

| Field | Value |
|---|---|
| Gaze source | **Real driver in a real vehicle**, SMI ETG 2w eye-tracking glasses `V` |
| Persons | **8** drivers, ages 20 to 40, 7 men and 1 woman `V` |
| Scale | 74 sequences of 5 minutes, 555,000 frames `V` |
| Temporal | eye tracker 60 Hz; ETG front camera 720p at 30 fps; roof camera 1080p at 25 fps `V` |
| Registration | manual per-sequence alignment, then frame-by-frame homography by SIFT descriptors and RANSAC `V` |
| Labels | raw fixations, fixation maps aggregated over 25-frame windows with Gaussian smoothing; about 20% of frames manually categorised `acting`, `inattentive`, `error`, `subjective` `V` |
| Object reference | **none**; semantic segmentation into 19 classes only, no boxes, no instance identities `V` |
| Individual or aggregated | individual, and separately aggregated into fixation maps `V` |
| Rights | stated publicly available; exact licence terms not established `U` |

**Verdict: NOT IDENTIFIED for `M^H`.** No object or track reference, and no awareness evidence
beyond gaze. Two further disqualifiers for inference: the outer clustering unit is the person and
`n_person = 8`, which cannot support person-level or worst-group inference at any frame count; and
the homography registration error is a geometric uncertainty source that must be propagated into
any object association rather than absorbed. **GO as a pilot instrumentation reference.**

### 2.2 MAAD, arXiv:2110.08610, ICCVW 2021 `V`

| Field | Value |
|---|---|
| Gaze source | **Laboratory**, chin-rest, subjects viewing DR(eye)VE video on a screen `V` |
| Task framing | monitor the driving scene as a safety driver might monitor an autonomous vehicle `V` |
| Persons | 23, ages 20 to 55, US licence holders with at least 2 years experience `V` |
| Scale | about 24.5 hours of gaze over 6.2 hours of road video `V` |
| Temporal | 5 Hz `V` |
| Awareness labels | **third-party raters**, asked whether they believe the subject attended a marked location, on a 1 to 5 scale, at randomly chosen point locations; 53,983 sequences of about 10 seconds, three sampling types: object, edges, non-objects `V` |
| Rater aids | green circle at 2 degrees foveal diameter, red circle at four times that `V` |
| Object reference | **none**; random point locations, no boxes, no instance identities `V` |
| Individual or aggregated | individual `V` |
| Rights | model and dataset published on a corporate GitHub; no explicit licence stated in the paper `U` |

**Verdict: NOT IDENTIFIED as truth for `M^H`.** The awareness label is a third-party rater's
inference from a scan path, not the subject's report and not an observed state. The subjects had
**no vehicle control and no consequence**, so awareness under monitoring is not awareness under
driving; the paper itself asks raters a separate "expected awareness if driving" question, which is
an inference rather than an observation. **GO as the probe-protocol template**: the randomized
probe location plus rated-awareness structure is the closest existing design to what the pilot
needs, and it should be adapted to live delivery with the subject answering rather than a rater.

### 2.3 Look Both Ways, ECCV 2022, DOI 10.1007/978-3-031-19778-9_8 `S`

Synchronized driver-face and forward-road video with eye-tracking-glasses ground truth; 28
subjects, 5 held out as a test set. Temporal resolution, registration method, licence, and any
object reference **not established** `U`.

**Verdict: NOT IDENTIFIED.** No awareness evidence and no object reference reported. Candidate
second instrumentation reference; requires a primary audit before any use.

### 2.4 BDD-A, arXiv:1711.06406 `S`

Reported as in-laboratory observers viewing driving video, with clips selected around braking
events, trimmed to 6.5 seconds before and 3.5 seconds after. Persons, temporal resolution, and
licence **not established** `U`.

**Verdict: NOT IDENTIFIED, and additionally selection-conditioned.** Observer gaze without control
authority, plus event-conditioned sampling that changes the opportunity universe.

### 2.5 DADA-2000, arXiv:1904.12634 `S`

2,000 clips, about 658,476 frames, 54 accident categories, crowd-sourced source video across road
types, weather, and lighting. Provides fixation maps, saccade scan paths, focusing time, accident
categories and windows, and crash-object spatial locations. Persons and protocol **not
established** `U`.

**Verdict: NOT IDENTIFIED.** Gaze is from laboratory viewers of crowd-sourced accident video, not
from the driver who had control. Accident-conditioned selection is severe. Crash-object locations
are not a tracked-instance reference.

### 2.6 LOOK, arXiv:2112.04212 `V`

Eye contact detection for **pedestrians** looking toward the vehicle.

**Verdict: EXCLUDE, wrong construct.** This measures a vulnerable road user's attention to the ego
vehicle, not the driver's awareness of an object. It must not enter `M^H` under any adaptation. It
may be retained as a candidate source for a different, separately specified estimand.

## 3. Overall feasibility verdict

The required intersection is

```
(real driver gaze with control authority)
    AND (independent object or track reference)
    AND (awareness or response evidence beyond gaze)
```

**That intersection is empty across every dataset audited.** `M^H` is therefore not identified from
public data, and the M3 NO-GO rests on evidence rather than caution. Any human-automation
dependence coefficient computed from these sources today would be an artifact of a gaze-intersection
rule, which section 1 rejects.

## 4. Minimum synchronized pilot

Design only. Execution requires authority that does not exist.

1. **Independent object and track reference.** Annotation produced blind to every channel output
   and blind to gaze, with instance identities stable across time.
2. **Individual gaze with an explicit uncertainty envelope.** Per-person point of regard plus a
   calibrated angular error term, propagated to a probability of object intersection. Never a hard
   hit test. Calibration drift measured within session and retained.
3. **Awareness or response evidence.** Either sparse randomized probes delivered live and answered
   by the subject, or a declared task-relevant response under a preregistered mapping. Probe rate,
   timing distribution, and non-response handling frozen before data.
4. **Exact temporal windows.** Onset, window length, and deadline declared per opportunity before
   data.
5. **Identical opportunities.** The human channel and every machine channel scored on the same
   opportunity set, same matcher, same operating-point discipline, so the resulting `c` is defined.
6. **Unknown propagation.** Any unresolved operand yields `human_state = unknown` and propagates to
   the record disposition. Unknown counts reported beside every rate.
7. **Person as the outer cluster**, with a target `n_person` derived from the width of the
   person-clustered interval. Eight persons is not a study.
8. **Control authority declared.** Whether the subject was driving, supervising, or observing is a
   first-class field, because the audit above shows it is the dimension on which every public
   source fails.

## 5. Prerequisites outside current authority

Human-subjects review and approval; informed consent; recruitment; private-data handling and
retention terms; vehicle or simulator operation. None is authorized. This document requests none of
them; it records what would be required.

## 6. Non-claims

No scientific support, no operator acceptance, no dataset criticism, and no comparative claim. The
verdicts are about fitness for one specific estimand, not about dataset quality for the purposes
their authors designed them for.
