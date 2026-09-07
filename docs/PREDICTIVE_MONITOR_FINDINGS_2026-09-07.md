# Output-only prediction: recovered results and a stopped feature expansion

Document ID: `reiyah.predictive-monitor-findings.2026-09-07`

Version: `0.1.0`

Lifecycle status: `exploratory`

The interrupted engine session completed its measurements but did not retain them
in Git. This checkpoint preserves its original sources, plans and aggregate
results. It closes the proposed output-summary experiment without selecting
another feature variant after seeing its negative follow-up.

## What was measured

The [original plan](../research/predictive-monitor/0.1.0/PLAN.md) asks whether
relations between retained camera and lidar outputs predict future
reference-relative joint misses beyond each channel's summaries and history.
The [collection-log extension](../research/predictive-monitor/0.1.0/TRANSFER_EXTENSION.md)
was retained before fitting. The [spatial follow-up](../research/predictive-monitor/0.2.0/PLAN.md)
was designed after inspecting the first results and is explicitly adaptive.

The complete official validation census contains 6,019 frames in 150 scenes
from 18 collection logs. Approximately one-second joins produce 5,693
anchor/target pairs; 326 anchors lack an eligible future target. The census
includes 66 frames without selected cache annotations. Their zero reference
counts do not establish physically empty scenes. Matching agrees with the
retained historical matcher on the declared annotation population.

All comparisons below predict the original cache's future joint-miss count.
Each uses nested selection over the same three tree configurations. Positive
improvement means lower equal-scene mean Poisson deviance. The displayed bands
resample scenes while keeping predictions fixed; they exclude fitting and
benchmark-selection uncertainty.

| Comparison and split | Baseline loss | Candidate loss | Relative improvement | Paired 95% descriptive band |
| --- | ---: | ---: | ---: | --- |
| Cross-channel history versus marginal history; scene holdouts | 2.721791 | 2.599354 | 4.4984% | [1.7494%, 7.4775%] |
| Same comparison; whole collection-log holdouts | 2.852402 | 2.775330 | 2.7020% | [-0.0264%, 5.5982%] |
| Spatial continuity versus frozen cross-channel history; log holdouts | 2.775330 | 2.783030 | -0.2774% | [-1.5236%, 1.0214%] |

The original engineering screen required at least five percent improvement and
a descriptive band above zero. Neither the primary comparison nor the spatial
follow-up meets it. The scene split shares 11 to 15 collection logs between
training and test in each fold; the log split shares none. These splits change
the training task, so the difference is not a randomized estimate of leakage.

The spatial result also retains a whole-log bootstrap that preserves the
equal-scene estimand: relative band [-1.7848%, 1.4911%]. Equal-log weighting is
a separate estimand: the history increment is 0.4057% with band
[-3.5503%, 4.2989%]. These numbers are not interchangeable error bars.

Under log holdouts, cross-channel history flags 22.0095% of eligible anchors
and covers 42.4420% of reference-relative misses, leaving 18,479 of 32,105
misses outside alerts. These are paired with the marginal-history baseline's
21.6055% alert fraction and 41.1182% coverage. Alert frequency was measured
using a training-only threshold, not forced to match on test data. This is
not a causal benefit or a measured false-alarm cost.

The unavailable current-label oracle reaches loss 1.190160 on log holdouts.
It uses information forbidden to the deployable comparisons. Its stronger
prediction is a diagnostic of missing information, not evidence that the
information is observable from current outputs or independent sensor data.

## Dependence and training-data census

The [collection-log sensitivity](../evidence/predictive-monitor/collection-log-sensitivity-0.1.0.json)
retains conditional coefficient 1.151053 on the fixed selected reference and
support. Its whole-log band is [1.121796, 1.170522], compared with the
whole-scene band [1.128749, 1.166206]. These resamples do not establish that
the logs are independent deployments or identify the underlying mechanism.

The [training preflight](../evidence/predictive-monitor/training-overlap-2-result.json)
finds 700 training scenes in 50 logs and 150 validation scenes in 18 logs,
with zero common logs. It proposes three seeded divisions of training logs.
Their sample budgets are unequal and their raw sensor coverage is unchecked.
This does not test overlap between the two detectors' training sets. No
new detector has been trained and the effect of shared training remains null
as an unmeasured field, rather than a finding of no effect.

## The result checker was itself incomplete

The original separately written checker recomputed reported metrics but did
not require the planned experiments to be present. It returned success after
all experiment reports were removed. It also accepted a forged [0.5, 0.6]
relative band in the spatial log-resampled equal-scene field because that
field was not recomputed. The exact original checker and run outputs remain
unchanged for historical replay.

The [completion auditor](../tools/measure/audit_predictive_monitor_completion.py)
requires the frozen experiment, model, comparison, private-output and fold
populations; validates the seeded outer assignment and denominators; invokes
the original numerical audit; and separately recomputes the log-resampled
equal-scene result. Both reproduced attacks now exit nonzero without writing
a success artifact. All three complete original runs pass. The
[regressions](../tests/test_predictive_monitor_completion.py) include a
three-scene example proving that equal-log and equal-scene weighting differ.

## Interpretation and next experiment

These are exploratory predictions of annotation-relative counts on an already
used benchmark. Physical failure rate, actual online warning lead time,
readiness, recoverability and safety benefit remain unmeasured. The independent
240-case reference study still has no human judgments. This result does not
justify a breakthrough, frontier ranking or public safety claim.

The [next experiment](TRAINING_OVERLAP_NEXT_EXPERIMENT_2026-09-07.md) separates
shared training from dataset transfer. That experiment can distinguish a
training mechanism from an observational association; another tuned summary
feature on this same validation split cannot make that distinction. The
[engine checkpoint](ENGINE_RECOVERY_CLOSEOUT_2026-09-07.md) gives exact custody,
replay limits and continuation commands.
