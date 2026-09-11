# What a reader needs to verify one detector addition

Document ID: `reiyah.decision-evidence.2026-09-11`

Version: `0.2.0`

Lifecycle status: `proposed`

Lane: independent research, parallel to the Engine. Changes no released byte, no frozen protocol,
no Engine file and no owner checkout. Creates no acceptance and no scientific authority. Gate A
remains unaccepted.

## The question and the result

What is the smallest disclosure that lets another engineer verify the value of one fixed candidate
added to one fixed installed configuration, under declared reference uncertainty?

**Not a silence table.** A labelled miss table cannot express the Engine's loss, and the failure is
not a detail: two populations with identical base miss tables and identical addition counts give
opposite decisions. What is sufficient, and close to minimal, is the **neutral match graph per
reference interpretation plus a matching and a vertex cover of equal size for each configuration**.
That lets a reader recompute the loss difference and verify the matched counts **without running a
matcher**, which is otherwise the one piece of the producer they would have to trust or rewrite.

On eight real anchors built from retained detector outputs under one declared rule, the answer to
the actual decision is governed almost entirely by the penalty ratio, and the instrument makes that
explicit rather than burying it in a single number.

## Three obligations, kept apart

| obligation | what it needs | supplied here |
|---|---|---|
| calculate the claimed loss difference | `TP_base`, `TP_augmented`, `r` per anchor per world | yes, three integers |
| verify those numbers independently | the match graph and a matching plus an equal-size cover | yes |
| justify the reference assumptions | observations of the recording and human adjudication | **no, and no aggregate can** |

Conflating the third with the first two is the error this document exists to prevent. A confirmed
packet says the arithmetic of a declared comparison is right inside declared interpretations. It
says nothing about whether those interpretations are the right ones.

## Why a silence table fails, exactly

For nonnegative penalties `a` and `b`, `r` retained additions and maximum same-class one-to-one
matching, `delta = (a + b)(TP_augmented - TP_base) - b * r`. Four retained synthetic counterexamples,
all exact:

**Matching competition.** One base detection `b1`, one addition `c1`, two objects of one class. If
`c1` reaches the object `b1` cannot, `delta = +1`. If `c1` competes for the object `b1` already has,
`delta = -1`. **The base matched set and `r` are identical in both.** A maximum matching is also not
unique, so "which objects were matched" is a witness, not a canonical summary.

**False detections.** Same matched sets in both configurations, `r` of 1 against 3, and
`delta = -1` against `-3`. A miss-only table carries no `r` at all.

**Class boundaries.** The same neighbourhood with one object relabelled turns `+1` into `-1`.

**Absent is not unmatched.** An object outside a world and an object present but unreachable give
the same `delta` and are different states, and the packet keeps them different.

**One world hides the enclosure.** Reporting a single interpretation gives `[1, 1]` where the two
admitted interpretations give `[-1, 1]`. The retained base-neighbour trap is preserved in packet
form: a disputed object reachable only by the base reverses the addition's value.

## The certificate, and why the checker needs no matcher

Every matching is at most every vertex cover, because each matched edge needs its own cover vertex.
So a matching `M` and a cover `C` with `|M| = |C|` force `|M| = max matching = min cover`. That
inequality holds for any graph, so the checker needs no bipartite theorem, no search, and no trust
in the producer's matcher. It checks that the matching uses declared edges and is one to one, that
the cover covers every declared edge, and that the two sizes agree.

The checker imports nothing from the producer. The shared trusted surface is the JSON module, the
identifier and rational string conventions, and Python's `Fraction` and integer arithmetic.

## Eight real anchors

Built from retained Megvii lidar and Mapillary camera outputs and the retained annotation cache,
under one declared rule: score floor `0.30`, the ten detection classes, `50 m` range, strict `2 m`
same-class matching, an addition suppressed when a retained same-class base detection lies within
`2 m`. Anchors are keyframes selected by sorted sample order at a fixed stride, fixed before any
outcome was computed. One anchor is one keyframe. Objects with zero lidar and zero radar returns
form a declared disputed set, giving a second reference interpretation where they exist.

| anchor | `r` | enclosure | coarse bound | TP base to augmented |
|---|---:|---|---|---|
| 00 | 12 | `[-6, -6]` | `[-12, 12]` | 18 to 21, 17 to 20 |
| 01 | 9 | `[-7, -7]` | `[-9, 9]` | 18 to 19, 17 to 18 |
| 02 | 4 | `[-2, -2]` | `[-4, 4]` | 16 to 17 |
| 03 | 1 | `[-1, -1]` | `[-1, 1]` | 5 to 5 |
| 04 | 4 | `[-2, -2]` | `[-4, 4]` | 14 to 15 |
| 05 | 6 | `[0, 0]` | `[-6, 6]` | 24 to 27 |
| 06 | 5 | `[1, 1]` | `[-5, 5]` | 22 to 25 |
| 07 | 4 | `[-4, -4]` | `[-4, 4]` | 6 to 6 |

Under unit penalties the improvement criterion at tolerance `1/10` is supported on 1 anchor and
excluded on 7. Every enclosure lies inside its coarse count bound. The declared disputed objects
changed no `TP` gain here, which is itself worth recording: the alternative axis was admitted and
did not bind.

## The number the decision actually turns on

`delta > 0` exactly when `a/b > r/(TP gain) - 1`. Per anchor:

| anchor | `r` | TP gain | break-even `a/b` |
|---|---:|---:|---:|
| 00 | 12 | 3 | 3 |
| 01 | 9 | 1 | 8 |
| 02 | 4 | 1 | 3 |
| 03 | 1 | 0 | never |
| 04 | 4 | 1 | 3 |
| 05 | 6 | 3 | 1 |
| 06 | 5 | 3 | 2/3 |
| 07 | 4 | 0 | never |

Sweeping the ratio: the addition improves the loss on 1 anchor at `a/b = 1`, 2 at `2`, 5 at `4` and
6 at `10`. **The decision is a question about the penalty ratio, not about the detector**, and unit
penalties are a research tolerance rather than a safety weighting. Nothing here establishes the
right ratio; that is the engineering team's to declare, and the packet makes the consequence of
their declaration immediate.

## What the retained open comparison actually needs

The Engine's own comparison returns `[-8, 8]`. Applying the arithmetic above to its declared
structure shows that interval **is exactly the coarse count bound** `[-b*R, a*R]` for a weighted
retained-addition total of `R = 8` under unit penalties. It is the arithmetic of ignorance rather
than a measurement, and the cause is specific: the reference is in the `open` state with no admitted
interpretation, so the true-positive gain is bounded only by `0` and `r`.

That turns the blocking dependency into a counted task. Under the declared additive loss,

```text
delta > 0   exactly when   (TP gain) / r  >  b / (a + b)
```

so with unit penalties the addition pays off exactly when **more than half** the added detections
match objects the base missed. Resolving one addition's status narrows its anchor's interval by
`(a + b) * weight`, which here is exactly `1`.

| adjudications completed | worst-case enclosure width |
|---:|---:|
| 0 | 16 |
| 4 | 12 |
| 8 | 8 |
| 12 | 4 |
| 16 | 0 |

**Sixteen adjudications close the comparison completely**, and the count is fixed in advance even
though the outcome is not. The schedule above is the worst case, in which no adjudication so far has
confirmed a new object; a real review narrows faster whenever an addition converts.

### A falsifiable prior

On this lane's eight real anchors, under the declared rule, the added camera detections converted to
new true positives at `12` of `45`, a rate of `4/15`, about `0.267`. That is well below the `1/2`
threshold. It is a **prior and not a prediction** about the retained comparison: a different
population, a different reference and a different anchor selection. It is falsifiable by exactly the
sixteen adjudications above, which is the point of stating it.

If those sixteen judgments put the conversion above one half, this prior is wrong and the addition
pays off under unit penalties. If they land near `4/15`, the comparison resolves against the
addition and the question is closed at a cost of sixteen human decisions rather than a sixty-scene
study. Either outcome is worth more than the interval that stands today.

## Compared with the conventional alternatives, on the same evidence

| disclosure | bytes for eight anchors | computes `delta` | reader can verify `TP` |
|---|---:|---|---|
| counts only, `TP` and `r` | 1,434 | yes | no, taken on trust |
| silence table, matched sets | 5,109 | no, `r` is absent | no, and the matched set is one witness of many |
| decision packet, case and report | 122,242 | yes | yes, from the certificates, with no matcher |

Stated plainly because it cuts against the proposal: **the packet is about 85 times larger than the
counts, and it is not faster.** Verifying all eight from certificates takes `1.1 ms`; reproducing
them by running the matcher takes `1.2 ms`. At this scale the certificate route buys no speed at
all. What it buys is that a reader needs no matcher implementation, and that a forged count is
caught. On a real report, inflating one `TP_augmented` by one is rejected; a counts-only disclosure
would have accepted exactly that change.

## Costs

Building the eight real cases from the retained sources took `6.1 s` wall and `1,391 MB` peak
resident, dominated by parsing two prediction files totalling about `569 MB`. Producing and checking
all eight packets took `5 ms`. Source preparation, the correspondence analysis and this write-up are
not separately instrumented and are recorded as unmeasured.

## Disclosure limits

The packet emits neutral identifiers, class labels, edge structure and counts. No annotation,
instance or sample token, no coordinate, no score and no path. That is a real reduction and it is
not anonymity. Edge structure still describes scene density through degree patterns and object
counts, a small anchor is a small cell, and anyone holding the source could attempt linkage. This is
stated as a limit. No suppression or noise is applied, because either would change the decision the
packet exists to support, and that trade would need its own accounting.

## Correspondence with the Engine's comparison, and why these must not be combined

These anchors are **not** the Engine's. The gaps were computed, not assumed:

- population: keyframes selected here by a stated stride, against the Engine's two anchors inside
  two previously exposed development windows;
- reference: the retained filtered annotation cache here, against unfiltered source annotations
  admitted by the Engine, so the object sets differ;
- disputed set: zero lidar and zero radar returns here, which is not the Engine's joint reference
  alternative construction;
- clock and geometry: positions taken as recorded, with no timing or calibration reconciliation.

A matching detector name does not establish matching rows, thresholds, clocks or reference rules.
The exact missing information needed to run this on the Engine's comparison is its two anchors'
neutral row-to-detection mapping and its admitted interpretations, which are the Engine owner's to
supply.

## The exact missing information

For this lane to run the same producer and checker on the Engine's real comparison rather than on
its own anchors, two things are needed and nothing else:

1. the two anchors' neutral detection-to-object candidate edges per admitted interpretation, which
   is what `reference.state = open` currently withholds; and
2. the admitted interpretations themselves, that is which objects are declared present in each.

Both are the Engine owner's to supply, and the second is the one that requires people. No format,
no aggregate and no further mathematics substitutes for it.

## What is established, and what is not

Computationally valid: the arithmetic of each declared comparison inside its declared
interpretations, independently checkable. Physically valid: nothing. Demonstrated decision value:
one workflow that converts a detector-addition question into an explicit penalty-ratio question,
on real outputs, with an independent verification path. Whether that changes a real team's decision
is untested, because no external engineer has used it.

## Reproduce

```sh
python3 -B -m unittest discover -s tools/measure -p test_decision_packet.py
python3 -B tools/measure/reference_resolution.py
python3 -B tools/measure/decision_packet.py research/decision-packet/0.1.0/cases/real.megvii-plus-mapillary.00.json
python3 -B tools/measure/check_decision_packet.py \
    research/decision-packet/0.1.0/cases/real.megvii-plus-mapillary.00.json \
    evidence/decision-packet/real.megvii-plus-mapillary.00-report.json
python3 -B tools/measure/build_decision_cases.py CACHE_DIR PRED_DIR 8 OUT_DIR
```

The first three read no dataset. The last reads the retained sources read only and emits neutral
structure only.

## Non-claims

An internal research artifact, retained as `proposed`. Not independent external scientific review,
not an operator acceptance, not a safety, compliance or vendor claim, not a statement about any
deployed system, and not a study result. The synthetic counterexamples are labelled synthetic. The
real results are descriptive under their declared reference and rule. No released `1.2` byte, frozen
protocol, claim-register entry or other owner's work is modified.
