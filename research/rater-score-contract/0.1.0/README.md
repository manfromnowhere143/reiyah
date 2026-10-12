# A maximum rater score and its evidence boundary

Study ID: `reiyah.rater-score-contract`. Version: `0.1.0`.
12 October 2026. Exploratory source qualification using six authored cases.

**The released WOD-E2E scorer can return 10/10 while its own
`is_fully_within_trust_region` flag is false.** A separate case retains both
10/10 and a true flag while moving six metres away from its matching reference
between the evaluated times. These are reproducible consequences of what the
metric measures. They do not establish a defect, unsafe driving, or an effect
on a published empirical ranking.

This investigation began by qualifying the remaining WOD-E2E lead for Reiyah's
next complete-work comparison. That case is **not admitted**. The inspected
release supplies a scoring interface, but not the identified complete paired
runs, observation histories and work records that comparison requires.
The small software probe below qualifies the interface's interpretation;
it does not substitute for the missing value experiment.

## What the scalar retains

We inspected the [official scorer at commit
99a4cb3](https://github.com/waymo-research/waymo-open-dataset/blob/99a4cb3ff07e2fe06c2ce73da001f850f628e45a/src/waymo_open_dataset/metrics/python/rater_feedback_utils.py),
its tests, tutorial and schemas. The [WOD-E2E paper, v3, §3.5](https://arxiv.org/html/2510.26125v3#S3.SS5)
describes reference matching at three and five seconds, followed by a maximum
over references and an average over those times. Our witnesses exercise that
definition, rather than contradicting it.

For one prediction, write `a(p,t)` for the rated score after distance decay
relative to reference `p` at time `t`. Before the outside-region floor, the
scalar is:

`S = [max_p a(p,3) + max_p a(p,5)] / 2`.

The maximizing reference can differ between the two times. The separate native
flag requires **one reference** whose regions contain the prediction at **both**
times. Consequently, the two outputs answer different questions. Neither
checks the prediction's intermediate waypoints. The native outside-region rule
raises scores below four to four; it does not cap a high score at four.

This gives a concrete requirement for any later Reiyah adapter: retain scalar,
support flag, evaluated times, input validity and any separately justified
trajectory checks as distinct fields. A scalar cannot reconstruct information
its calculation never used. No runtime adapter or alternative safety metric is
implemented here.

## Frozen witnesses and controls

The [protocol](protocol.json) froze before implementation and execution. Source
code, paper and upstream test examples had already been read; anticipated
results are explicit. This was not a blinded experiment. A
[post-execution clarification](protocol-clarification.json) records that the
protocol omitted the predictions’ longitudinal coordinate. The separately frozen
implementation already specified `x=10t`; no input, code or result changed.
All paths below are
authored mathematical inputs, without qualification of vehicle dynamics,
road geometry or physical plausibility.

Twenty waypoints cover five seconds at 4 Hz. All references use `x=10t`.
Their lateral coordinates are zero and ±`6 min(t/2.5,1)` metres. One prediction
has probability one; initial speed is 10 m/s. The scorer and its defaults are
unchanged. The main reference scores are `[10,10,2]`.

| Authored case | Native score | Native same-reference flag | What it checks |
| --- | ---: | --- | --- |
| Follow reference zero | 10 | true | Positive control. |
| Match reference zero at 3 s and reference one at 5 s | 10 | false | A maximum scalar does not imply the flag. |
| Same switch, reference scores `[10,6,2]` | 8 | false | Contributions can come from differently scored references. |
| Return to reference zero at both evaluated times, six-metre excursion at 4 s | 10 | true | Both outputs leave intermediate motion unresolved. |
| Far from every reference at both times | 4 | false | Outside-region floor control. |
| Same switch, reference scores `[8,8,2]` | 8 | false | The effect is not specific to a score of ten. |

All six declared outcomes match. Singleton evaluation, reversed batch order and
all six paired reference/score permutations preserve each outcome: 14 native
calls and 54 case evaluations per execution. Two executions produce identical
result bytes. A deliberately changed source file is rejected before import.
These controls check the named cases, not universal numerical robustness.
The producer records the intermediate deviations; a separate
[result inspection](verification.json) checks the zero-versus-six comparison
and equal sampled positions/outputs. That comparison is not a mutation-tested
assertion inside the producer.

The [result](result.json) retains every call and flag. The
[execution record](execution.json) distinguishes expected source rejection from
successful numerical runs. Native execution and direct arithmetic inspection
belong to one assisted investigation, not independent scientific replication.
No full upstream test suite, dataset benchmark or evaluation server was run.

## Reproduce

Use Python with NumPy. Obtain the source file linked above separately under its
Apache-2.0 terms. Its exact digest is in the protocol and is checked before use.
From the repository root:

```sh
python3 -B research/rater-score-contract/0.1.0/reproduce.py \
  --native /path/to/rater_feedback_utils.py \
  --output /tmp/reiyah-rater-score.json
cmp /tmp/reiyah-rater-score.json research/rater-score-contract/0.1.0/result.json
```

The script makes no network calls or model runs. Retained executions additionally
denied network access before Python started. Source files and dataset payloads
are not redistributed here. [Provenance](provenance.json) binds authored files,
versions and retained source descriptors.

## Admission decision and next action

The [admission record](../../../evidence/wod-case-admission-2026-10-12.json)
separates what is available from what remains missing. The official tutorial
contains a placeholder prediction; upstream tests contain selected sample
trajectories and outcomes. These are exposed development examples, not complete
identified submissions or measured workflow histories. We did not acquire a
dataset split or authenticate to a download service.

The data schema exposes trajectory-level scores, including invalid or absent
states; it does not supply individual review histories or work durations.
Dataset access and the complete applicable agreement remain unresolved in our
retained evidence. Code licensing does not resolve dataset rights. None of
these statements asserts that the missing records do not exist elsewhere.

The scorer is a geometric maximum-and-decay function, not fixed-rank binary
AUGRC. The previously qualified exact-choice formula therefore cannot be
imported as a drop-in comparator. Any later comparison must give both arms the
same native scoring semantics, shared reference uncertainty and validity rules.

Stop this qualification here. Reopening requires a concrete new packet or
source change: complete paired outputs and roster, justified metric and decision,
applicable rights, separate development records for observation qualification,
and a full-work collection plan frozen before held-out responses. The
[existing submission guide](../../../docs/SHARE_A_COMPARISON.md) remains the
entry point. No further synthetic sweep or acquisition of the same unchanged
lead is scheduled. No product advantage, physical validity, scientific novelty,
or Gate A acceptance is established.
