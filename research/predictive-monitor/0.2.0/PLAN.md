# Does preserving spatial continuity recover discarded predictive information?

Document ID: `reiyah.predictive-monitor-spatial-plan.0.2.0`

Version: `0.2.0`

Lifecycle status: `exploratory`

This follow-up is designed after inspecting the completed 0.1.0 collection-log
holdout. Cross-channel summaries improved equal-scene deviance by 2.7%, with a
band including zero. The current-label oracle reduced it much more. This is an
adaptive exploratory investigation, not part of the original pre-fit plan.

The question is whether the earlier summary representation discarded useful
spatial continuity. Before adding sensor payloads or a foundation model, test
the retained output sets themselves. No new dataset, detector or human label is
introduced. The 240-case blinded study remains untouched.

For each anchor, use the current and preceding two metadata keyframes only.
Construct sites supported by both channels by same-class, strict 2 m greedy
pairing; the site's position is the midpoint and its score the lesser score.
These are hypotheses from detector outputs, not confirmed physical objects.

Measure how many previous paired sites have nearby support in neither, one or
both current channels at 2 m and 4 m. Separately count the loss of same-channel
spatial support. Compare a stationary-position projection with a constant-velocity
projection estimated from the preceding two sets of paired sites. For the latter,
use mutual-nearest same-class associations strictly within 10 m; record rejected
or unmatched sites. A 10 m association gate is a chosen diagnostic parameter,
not a physical speed limit or a validated tracking rule. No claim of identity
correctness follows. Empty sets are valid; unavailable history and unavailable
summary statistics remain NaN, accompanied by availability/count fields.

The candidate concatenates these current spatial-continuity summaries with the
0.1.0 `joint_history` matrix. It uses the same three Poisson tree configurations,
five collection-log outer folds, three inner log folds, seed, loss and .80
training prediction alert quantile. Compare with the retained, verified
`joint_history` predictions on the **exact same 5,693 anchor/target pairs**.
No baseline refit or parameter change is allowed. Verify the reused baseline's
specification, dataset identity, source closure and fold assignments.

The primary metric remains equal-scene Poisson deviance, with paired scene
bootstrap and an additional log-resampled interval preserving equal-scene
weighting. The latter resamples whole logs and divides summed scene losses by
the sampled scene count; it must not be confused with an equal-log estimand.
Report alert coverage, unflagged misses, proper count loss and unavailable
operational lead time. A five-percent improvement with a descriptive interval
above zero is the same minimum numerical screen; it is not proof of a physical
or operational benefit. A smaller or unresolved result ends this particular
feature-expansion attempt without tuning gates or adding variants post hoc.

Test that no feature reads a future output or annotation, that moving sites
behave differently under the two projections on authored examples, and that
ambiguous/non-mutual associations do not become accepted tracks. Successful
software checks validate these calculations only. A positive result would
justify a new-domain frozen-rule test, while a null result favors obtaining
independent physical observations over enlarging this output-summary monitor.
