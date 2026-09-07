# Output-only joint-miss prediction: a bounded falsification experiment

Document ID: `reiyah.predictive-monitor-plan.0.1.0`

Version: `0.1.0`

Lifecycle status: `exploratory`

This plan is retained before the new fits. The nuScenes validation split has already
been used throughout Reiyah's exploratory program. This is neither a fresh external
test set nor a confirmatory preregistration. Existing detector outputs are read; no
perception model, service or vehicle is executed.

## Question and discriminating comparison

Do cross-channel output relations predict future reference-relative joint misses
beyond the same channels' counts, scores, classes, ranges and recent history?
The primary comparison is `joint_history` against `marginal_history` for the
approximately one-second target and the original cache population. Both receive
the same model search, scene splits and loss. Lower held-out Poisson deviance is
better. Current-frame prediction, individual feature increments and the subset
with positive lidar/radar point counts are declared secondary comparisons.

The null interpretation is no resolved useful increment with these features,
models and scenes. It does not say that future failures are fundamentally
unpredictable. A positive increment would demonstrate only reference-relative
prediction. It would not establish a causal role for dependence, physical object
existence, hazard recovery, calibrated safety probability or novel monitoring.

## Population, clocks and reference

Reconstruct all official validation scenes and their complete sample chains from
the retained split source and metadata, independently of annotations. Both
prediction inputs must have exactly that frame set. Empty prediction lists are
observed empties; omitted frames invalidate the computation. No frame is dropped
because it has no selected annotation. Every zero target means zero misses in
the supplied reference population, never a known physically empty scene.

Label matching is score-ordered, same-class, one-to-one, strict distance less
than 2 m, with score at least .30 and prediction class-range filtering. Original
cache order breaks equal-distance ties; original prediction order breaks score
ties. Compare every selected annotation's matched flag with the separately
retained historical matcher. The primary target counts annotations missed by
both channels. The point-positive sensitivity restricts that same match result
to rows with `nl + nr > 0`; it does not claim complete SDK evaluation conformance.

Feature extraction receives only released predictions and metadata ego pose.
It cannot read annotations, visibility, full-track motion, future labels, scene
description or identity. Metadata LIDAR_TOP poses are joined independently of
the cache, then checked against cached poses as a consistency test. Historical
detector preprocessing, internal sweep use and wall-clock output availability
are not established by prediction JSON: all deployment/latency claims remain
unknown even when the feature calculation obeys a metadata-time prefix.

For horizon zero, predict the current sample's count. For horizon one second,
choose the nearest later sample to `anchor + 1,000,000 us` within 150,000 us;
break a tie toward the earlier timestamp. Record actual offsets and every
excluded boundary/gap. History consists only of the two immediately preceding
samples in the same scene, their actual ages and the current feature vector.
Missing history/statistics remain NaN with availability/count information;
the selected tree implementation handles them explicitly. No mean, score or
missing reference is silently replaced with a measured zero.

## Features and comparisons

`density_current` receives the two raw above-threshold detection counts.
`marginal_current` also receives each channel's score summaries, class counts
and ego-range bins. `joint_current` adds same-class greedy correspondence,
unpaired counts, paired/unpaired score summaries and agreement. The two history
variants receive the corresponding present and past vectors with past ages.
This identifies the value of these particular relations, not all information
in the complete output point sets. Counts include above-threshold boxes outside
the evaluation range, as in the older monitor; ranges expose that composition.

All five feature variants select from the same three histogram gradient-boosted
Poisson mean estimators: 200 iterations, learning rate .05, no internal random
early-stopping split, 7/15/31 leaves, minimum leaf sizes 40/40/80 and L2 penalties
1/1/10. There is no tuning after the outcomes. A constant training mean and the
older proportional union-count rule are controls, not the sole comparisons.
The proportional rule uses a documented 1e-6 positive prediction floor.

A shuffled-training-label control uses the full history and the middle tree
configuration; only training labels are shuffled separately inside each outer
fold. This checks gross leakage without claiming a valid randomization test.
A current-reference-count oracle at horizon zero, and current joint-miss-count
oracle at horizon one second, expose the effect of normally unavailable
information. Oracle values are explicitly excluded from deployable comparisons.

## Separation and fitting

Five outer scene folds use a seeded permutation of sorted scene identities,
assigned round-robin. Hyperparameters are selected on three inner scene folds
inside the outer training partition. No frame, label, fit transform or threshold
from an outer test scene enters its fit or selection. The same outer mapping
serves both horizons, targets and feature variants. These scenes do not provide
independent cities, sensors or collection logs; retain those grouping counts.

Inner selection minimizes the equal-scene mean Poisson deviance. This is a
proper loss for a conditional count mean, without assuming that the observed
counts themselves follow a Poisson law. The selected model is refit on all
outer training scenes. Its inner out-of-fold predictions set an alert threshold
at the .80 quantile (higher order statistic). Alerts use strict `>`; achieved
test alert frequency is measured, never fixed by test ranking. A training-only
75th-percentile count defines the secondary high-count ROC endpoint.

## Outcomes and limits of inference

Report frame and equal-scene deviance, MAE, calibration (predicted/observed
counts), high-count ROC AUC, actual alert fraction, fraction of target misses
inside alerts, misses left outside alerts, and high-count false-alarm rate.
Undefined ratios/correlations are null. No rejected frame disappears from a
denominator. Also report the worst observed scene losses and location groups,
with their sample counts; they are descriptive, not uniform guarantees.

For declared paired differences, resample the 150 outer test scene summaries
3,000 times with a fixed seed and report a 95% percentile band. Predictions stay
fixed. This does not capture model-training uncertainty, shared collection-log
dependence or exploration across this already-used benchmark. Fold spread is
not a confidence interval. Secondary comparisons receive no confirmatory
significance label.

**Failure criterion:** the primary mean improvement is nonpositive, its band
includes zero, or an apparent benefit requires reference/oracle or future input.
**Minimum useful numerical result:** at least 5% lower equal-scene deviance and
a paired descriptive band wholly above zero, with no hidden frame rejection.
Five percent is a declared engineering screen, not a scientific constant or a
safety threshold. A result passing that screen still needs new detector pairs,
collection-domain holdouts, independent references and an intervention study.

If history helps but cross-channel relations do not, investigate persistent
scene difficulty before adding a larger model. If only the oracle helps,
investigate what missing observation it supplies. If neither helps, stop
optimizing this output-summary formulation. If cross-channel relations help,
freeze the learned rule before a genuinely new domain test. In every case the
independent 240-case reference study remains unchanged and unjudged.

## Required computational controls

Before real fitting, reject missing prediction frames, malformed numeric inputs,
broken scene chains, source digest changes, illegal temporal joins, overlapping
scene partitions and metric undefinedness disguised as zero. Prove on small
authored fixtures that future-output changes cannot alter past feature rows,
reference changes cannot alter output-only features, matching ties/range and
distance boundaries have the stated meaning, and scene metrics preserve all
frames. Retain the complete input/source closure, fold assignments, private
per-frame outcomes, aggregate results, process exit/status and source checks.
Tests and matching agreement are computation evidence, not physical validation.
