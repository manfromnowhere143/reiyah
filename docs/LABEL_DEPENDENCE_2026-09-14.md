# The benchmark verdict on this cohort rests on six of its 106 labels

Document ID: `reiyah.label-dependence.2026-09-14`

Version: `0.1.0`

Lifecycle status: `proposed`

Date: 2026-09-14. Lane: independent research.

Preregistrations fixed before any result:
`24cb90eff90f60431fd92cd25e504842eb24898e1ec40c1cc4399601e38cfe5d` (deletions),
`38af5ed9442632919b51751ee09693da2a13ca62626291624613f3978a9c8c72` (insertions).

Artifacts: [`research/label-dependence/0.1.0/deletion-family.json`](../research/label-dependence/0.1.0/deletion-family.json),
[`research/label-dependence/0.2.0/insertion-family.json`](../research/label-dependence/0.2.0/insertion-family.json),
[`research/annotation-case/0.1.0/source-reconstruction.json`](../research/annotation-case/0.1.0/source-reconstruction.json)

## The result

The Engine evaluated a fixed detector addition against the retained benchmark annotations on two
development frames. Weighted loss falls from 23.5 to 22.5, a weighted improvement of `+1` against
a tolerance of `1/10`, so the addition is `supported`. That number is correct. It is also one
label away from zero, six different ways.

| direction | family | breakdown number | what happens |
|---|---|---|---|
| a label should not have been there | 106 single deletions | **1** | six deletions each drop the weighted delta from 1 to 0, and the criterion from `supported` to `excluded` |
| a label was missed | 20 single insertions, then every pair | **none at size 1 or 2** | the weighted delta only rises, from 1 to 2. The criterion never changes |

So the verdict is fragile in exactly one direction. If the annotation contains a spurious object,
the answer "this detector helps, integrate it" can become "no measurable improvement". If the
annotation missed objects, which is the failure mode this benchmark is better known for, the answer
only gets stronger.

Nothing here says the annotation is wrong. Nobody has checked it. What is established is that six
specific labels each carry the whole conclusion, and which six they are.

## The six

| anchor | class | local index | weighted delta after deletion | criterion |
|---|---|---:|---|---|
| `window-0001` | traffic_cone | 16 | 0 | excluded |
| `window-0001` | traffic_cone | 31 | 0 | excluded |
| `window-0001` | traffic_cone | 58 | 0 | excluded |
| `window-0002` | car | 5 | 0 | excluded |
| `window-0002` | car | 16 | 0 | excluded |
| `window-0002` | car | 36 | 0 | excluded |

Each is confirmed by [`check_label_dependence.py`](../tools/measure/check_label_dependence.py),
which imports nothing from the producer, writes its own matcher, deletes the named label and
recomputes the loss. Six of six confirmed. A witness that fails to flip the criterion is refused by
name, and seven forgeries are retained as tests.

Identifiers are the benchmark's, so a witness is named by anchor, class and the label's local index
inside its anchor. No annotation token appears in any retained artifact, and a test asserts that.

## Why only six, when the gain is nine

This is the part matching competition explains and a per-object score cannot.

| anchor | labels | gain | labels that individually carry a unit of gain |
|---|---:|---:|---:|
| `window-0001` | 61 | 6 | 3 |
| `window-0002` | 45 | 3 | 3 |

At `window-0001` the added detector wins six matches, but only three labels are load bearing.
Deleting any of the other 58 leaves the gain at six, because the matching reassigns: another
detection takes the freed object and the count survives. At `window-0002` every unit of the gain
is singly supported, so all three are load bearing.

Gain in a matching problem is not evenly supported. Some of it is redundant and some of it hangs on
one object, and which is which is not visible from any per-detection score. That is why the six had
to be found by recomputing both matchings 214 times rather than inferred from the baseline.

## What is not claimed

- **No label is asserted to be wrong.** A deletion is a hypothesis this measures, not evidence.
- **Counts are not probabilities.** Six of 106 is not a 5.7 percent chance of anything. Nothing
  here says how often this annotation is spurious.
- **One insertion rule.** An insertion is placed at an unmatched retained detection's own position
  with its class, which is the hypothesis "this detection is right and the annotation missed the
  object". Other insertion geometries exist and are untested. Localization error and class error are
  different families and are untouched.
- **No deletion made the addition harmful.** The range is `[0, 1]`. Six deletions make it stop
  helping; none makes it hurt. Calling that a preference flip would overstate it.
- **This is not the physical comparison.** The same detector change under open physical references
  remains `[-8, 8]` with zero admitted human readings. That comparison is unresolved and this one
  does not narrow it.
- **Two previously exposed development frames.** Not a generalization result, not an official
  benchmark score, not a label accuracy assessment.

## What the ordinary analyst could do

All of it. The family is 107 recomputations and costs **0.108 seconds**; the insertion family is
another 0.217 seconds. An analyst holding the same bytes can run both. This is not a capability
this lane has and others lack.

What is different is that it was run at all, declared before it was run, reported with the three
outcomes kept apart, and shipped with six independently checkable witnesses. Conventional
benchmarking reports a delta. It does not report which labels the delta rests on. On this cohort
that difference is the whole finding, and it hands a validation lead a job they can actually do:
look at six labels out of 106, not at 106.

## The source reconstruction underneath

The result would be worth nothing if the case were not what it claims. The membership was rebuilt
here from the original tables rather than from the Engine's adapter or catalog: 119 annotations at
the two anchors from `sample_annotation.json`, their categories through `instance.json` and
`category.json`, the ego pose from `sample_data.json` and `ego_pose.json` by a targeted byte scan,
and the ego relative range by this lane's own quaternion transform.

All 13 exclusions are accounted for by the 50 metre range and no category is unmapped. The
suppression rule was recovered rather than assumed: same class, strictly within 2 metres, against
the retained base **and** against previously retained candidates. Base alone gives 10 additions at
`window-0001` instead of 9.

Membership matches token for token, with zero class disagreements. Both matchings, both losses and
the weighted delta match the Engine's claim exactly: 40 to 46 and 32 to 35, 29 to 26 and 18 to 19,
23.5 to 22.5, `+1`, supported. The ego translation recovered from the original table equals the
nominal ego XY the common operands carry, which a different lane produced at a different time.

One sensitivity is worth recording: the closest excluded annotation sits at **50.28 metres** against
a 50 metre boundary. The membership is 0.28 metres from changing.

## Next falsifier

A second development case. If its verdict has a breakdown number well above one, then fragility is
a property of this cohort rather than of the method, and the finding narrows. If it is also one,
the question becomes why a benchmark delta this small is being read as a decision at all.
