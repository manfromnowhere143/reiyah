# The group the average hides, and why it has to be found jointly

Document ID: `reiyah.worst-group.2026-09-12`

Version: `0.1.0`

Lifecycle status: `proposed`

Lane: independent research and conventional comparator, parallel to the Engine. Changes no Engine
file, no shared handoff, no frozen protocol and no owner checkout. Creates no reference admission,
no reviewer and no human judgement. Gate A remains unaccepted.

## A defect in this lane's own instrument

The cohort comparison this lane built reports a weighted average over anchors:

```
D(w) = sum_i weight_i * delta_i(w)
```

An average is the wrong summary for the question that actually gets asked, which is whether an
addition is safe to ship. A cohort can be `supported` while a named group inside it is harmed in
every admitted reading, and the cohort report as written would not say so. Not because it is wrong,
but because it is an average, and it was never asked about groups.

`worst-group-masking-case.json`, three anchors in two declared groups, one admitted reading:

| | enclosure | criterion |
|---|---|---|
| cohort | `[3/5, 3/5]` | **supported** |
| group `clear_daylight`, weight share `4/5` | `[1, 1]` | supported |
| group `low_light`, weight share `1/5` | `[-1, -1]` | **excluded** |

The cohort number is correct. A reader of it would ship an addition that harms the low light group
at the worst value the loss permits, in the only reading anyone admitted. A test asserts that the
cohort report does not contain the string `low_light` anywhere, because the defect is that the
information is absent, not that it is wrong.

Anchors now carry an optional `group`, and the value inside a group is renormalised by the group's
weight share so it is comparable against the same tolerance.

## The worst group has to be found inside each reading

The quantity that matters is

```
worst(w) = min over groups g of value_g(w)
```

and its enclosure over the admitted readings is `[min_w worst(w), max_w worst(w)]`. Computing each
group's enclosure separately and combining them afterwards is a different and weaker thing, and the
difference has a direction.

The lower ends agree: a minimum over groups of a minimum over readings is a minimum over pairs
either way. The upper ends do not. `max_w min_g` is at most `min_g max_w`, and that inequality is
frequently strict, so **the separate view is too wide at the top and can only lose decisiveness.**

`worst-group-flip-case.json` is the demonstration. Two groups, two admitted readings, and the groups
trade places between them:

| | enclosure | criterion |
|---|---|---|
| group `group_a` alone | `[-1, 1]` | unresolved |
| group `group_b` alone | `[-1, 1]` | unresolved |
| separate relaxation | `[-1, 1]` | unresolved |
| **worst group, jointly** | **`[-1, -1]`** | **excluded** |

Taken one at a time, neither group can be told anything about. Taken jointly, **some group is harmed
at the worst value the loss permits, in every admitted reading**, and which group it is depends on
the reading. The separate treatment does not merely lose precision here; it loses the entire
negative result, and the negative result is the one that would stop a release.

This is the same error this lane found once before, when summing per anchor extrema gave `[-1, 1]`
where the joint cohort gave `[0, 0]`. It is worth naming as a pattern rather than as two incidents:
**a bound computed one part at a time is a relaxation of the bound computed over one shared world,
and a relaxation is never a result.** The separate figures are still reported, labelled as a
relaxation, and the checker refuses them as an answer.

The inequality is asserted on 200 random grouped cohorts, where the lower ends agreed every time,
the separate upper end was never below the joint one, and it was strictly above it often enough for
the test to require it.

## What this does not do

A group is a partition **the case asserts**. This program does not discover groups, and it cannot.
An unexamined split can still hide a harm, so a cohort that reports no masking has been checked
against the groups someone thought to declare and against no others. That is a real limit and it is
not softened by the machinery: the instrument will confirm the absence of a harm only in the
dimensions it was handed.

Nor does any of this establish that a group is a meaningful population, that the weights represent
exposure, or that a harmed group in a synthetic case corresponds to a harmed population anywhere. The
cases are synthetic and labelled synthetic. The live two-anchor comparison has no admitted reference
and no declared groups, so it has no worst group either, and none is invented for it.

## Reproduce

```sh
python3 -B tools/measure/worst_group.py research/cohort-packet/0.1.0/worst-group-masking-case.json
python3 -B tools/measure/worst_group.py research/cohort-packet/0.1.0/worst-group-flip-case.json
python3 -B -m unittest discover -s tools/measure -p 'test_worst_group.py'
```

Thirteen tests, about 0.05 seconds. Exact rational arithmetic, standard library only, no data read.
An ungrouped cohort reduces exactly to the existing cohort enclosure, which is asserted on three
retained cases so the extension cannot silently change an existing result.

## Non-claims

An internal research artifact, retained as `proposed`. Not independent external scientific review,
not an operator acceptance, not a safety, compliance, fairness or vendor claim, and not a statement
about any real population or protected group. No released `1.2` byte, frozen protocol, claim-register
entry, Engine file or other owner's work is modified.
