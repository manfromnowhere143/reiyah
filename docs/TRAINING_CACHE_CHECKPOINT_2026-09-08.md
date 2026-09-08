# Unavailable velocity and training-cache checkpoint

Document ID: `reiyah.training-cache-checkpoint.2026-09-08`

Version: `0.1.0`

Lifecycle status: `exploratory`

This checkpoint completes actual regression-loss and annotation-consumer probes and a full
validation-cache recount. The two training-group caches are still running at the recorded
handoff time. It does not complete the entire preparation plan or establish detector performance.
The [aggregate record](../evidence/training-cache/results-0.1.0.json) binds the original outputs,
correction, source comparisons and remaining work.

## The concrete failure and tested correction

The pinned historical dataset parsers replace unavailable velocity with zero. Preserving NaN
labels is necessary to distinguish unavailable motion from observed stationary motion, but NaN
labels alone are insufficient: the actual configured CenterPoint L1 and FCOS3D SmoothL1 losses
become nonfinite. FCOS3D also produces nonfinite gradients. Multiplying an already evaluated NaN
loss by zero does not correct that arithmetic.

The [observed-target adapter](../tools/measure/observed_velocity.py) masks unavailable prediction
and target operands before the original loss is evaluated. Unknown targets have zero weight
and zero gradient. The loss contribution is zero; the estimated error on an entirely unavailable
velocity population remains null. The original normalization denominator is preserved.

[Actual CPU and CUDA probes](../evidence/training-cache/observed-velocity-probe-0.1.1.json)
exercise configured losses and the real heads' target/loss paths using synthetic prediction
tensors. All 16 head cases are retained. The corrected cases preserve the tested observed-label
losses and gradients and the geometry gradients. Nine invalid-input controls reject malformed
velocity, nonfinite predictions or targets, invalid weights and shape mismatches. These are
bounded synthetic checks, not a completed training run.

## Annotation and augmentation checks

The [annotation bridge](../tools/measure/annotation_velocity_bridge.py) preserves source velocity
through the actual camera parser's selection policy. It traces retained row indices on a private
copy and restores real attributes before returning. The lidar adapter restores the original
paired velocity after the actual dataset filter. Availability must be derived again from the
boxes after sampling and augmentation, so a stale side array cannot silently change row meaning.

The [parser probe](../evidence/training-cache/annotation-velocity-probe-0.1.1.json) checks the
fixed 204-sample, 1,224-image smoke population. It retains 5,289 lidar annotations and 7,388
camera annotations after native parser filtering, including 32 unavailable lidar velocities
and 40 unavailable camera velocities. Geometry, classes, attributes and observed velocity
agree with the original parser. Separate singleton parser invocations check the batched camera
row mapping. This uses the same upstream selection policy; it is not an independent evaluation
of that policy's physical validity.

Synthetic actual transforms check flips, lidar rotation/scaling, object sampling and range
filtering. Observed zero velocity stays observed; unavailable velocity stays a paired unknown.
Four malformed-geometry or velocity cases are rejected. Full training pipeline integration,
including all data augmentations and model optimization, remains outstanding.

## Full validation cache and separate recount

The completed cache contains all 6,019 validation samples and 36,114 camera images. Its lidar
reference contains 192,041 annotations, with 519 unavailable velocities; the camera export
contains 227,623 annotations, with 610 unavailable velocities. These populations follow their
respective upstream filters and must not be treated as interchangeable physical reference sets.

The [separate recount](../evidence/training-cache/validation-cache-recount-0.1.1.json) verifies
retrieved output hashes, every sample and camera opportunity, source point-count filtering,
annotation counts, valid geometry and paired missingness. It retains 29,778 lidar reference
annotations with zero lidar/radar points. It does not independently recompute every projection
or velocity value. Upstream camera JSON omits original annotation tokens, so complete per-row
camera source identity remains a further adapter task.

The [original producer record](../evidence/training-cache/original-validation-cache-0.1.0.json)
incorrectly says `payload_decoding: not_run_here`. The pinned upstream camera exporter calls
`mmcv.imread` to obtain image dimensions. The aggregate therefore explicitly corrects the scope
to upstream camera decoding for dimensions; lidar point decoding is not performed by this
builder. This correction also applies to its two running training-group jobs. Original producer
and result bytes remain retained. A future corrected producer needs a new version and output
identity.

## Execution and continuation

The [source ledger](../evidence/training-cache/source-ledger-0.1.0.json) binds the historical
framework, SDK, loss wheel and actual loaded source comparisons. The
[execution record](../evidence/training-cache/execution-0.1.0.json) distinguishes passing runs,
failed fixtures, development checks and running jobs.

The first loss probe failed because its synthetic predictions were leaf tensors passed to an
upstream in-place operation; a nonleaf fixture was then tested under a new run identity. The
first annotation probe omitted a required dataset-root argument. The first separate cache
recount omitted boolean dtype for an empty source-reference array. All failed receipts and
original checker/probe sources are retained privately; none is counted as a passing result.

The next session should follow the [engine handoff](ENGINE_BUILD_HANDOFF_2026-09-08.md): resolve
the two running builds, retrieve and recount their original results, then construct distinct
training object databases. Freeze initialization exposure, calibration, common optimization
steps and the effect/uncertainty protocol before fitting the four detectors. No shared-training
effect has been measured, no independent physical-reference judgments have arrived, and Gate A
remains operator-unaccepted.
