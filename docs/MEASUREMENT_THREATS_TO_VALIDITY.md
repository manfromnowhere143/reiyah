# Threats to validity, stated before anyone else finds them

Document ID: `reiyah.gate-b.threats-to-validity`

Version: `0.1.0`

Lifecycle status: `proposed`

This is an adversarial self-review of the Gate B measurement (Results A through R). Each entry
names the strongest form of an attack a reviewer could make, then states what answers it and what
does not. Where a threat is only partly answered, it is left open, not talked down. A finding that
survives its own red team is worth more than one that hides it.

## 1. Shared training data could manufacture the coupling (the deepest attack)

**The attack.** Every detector was trained on the same nuScenes training split. Two detectors could
fail on the same objects not because the sensors are jointly blind, but because both learned the
same label biases, so the "hard" objects are a shared property of the annotation, not the physics.
If so, the coupling is an artifact of shared supervision.

**What answers it, partly.**
- The coupling persists **across modality**. A camera detector and a lidar detector have different
  architectures, different inputs, and different failure mechanisms, so a shared-supervision
  artifact should be far weaker for a camera-lidar pair than for two detectors of one modality. The
  cross-modality conditional coefficient still exceeds 1 for all four camera-lidar pairs.
- The coupling concentrates on the objects **least** consistent with an annotation artifact. Result
  I finds the worst group is `car, 0-20 m, visibility v80-100`: close, highly visible cars, the
  easiest objects in the dataset to annotate. A shared-label-noise mechanism predicts the opposite,
  that coupling would concentrate on distant, occluded, low-visibility objects that are hard to
  label. It does not.

**What does not answer it.** This cannot be fully controlled without detectors trained on disjoint
data or labels, which is not available here. The residual possibility that some shared-supervision
component contributes to the measured coefficient remains open and is not claimed to be zero.

## 2. The benchmark's own filter biases the estimate (and which way)

**The attack.** nuScenes deletes every ground-truth object with zero lidar and radar returns before
scoring (Result A, 9.43% of objects). A filtered denominator could distort the dependence estimate.

**What answers it.** The deleted objects are exactly the camera-favorable ones, where the camera can
succeed and the lidar cannot. Removing them removes the discordant cases that would push the
estimate toward independence, so the measured coefficient is a **lower bound**: the true coupling on
the full object set is at least as strong. Result D measured the direction directly, about 3% on the
official versus full set. This threat strengthens the finding rather than weakening it.

## 3. The matcher could be introducing the association

**The attack.** A custom per-object matcher decides which object each detection claims. A biased
matcher could create apparent coincident misses.

**What answers it.** The matcher reimplements the nuScenes devkit accumulation and is admitted only
if it reproduces the detector's **published mAP**. It does so for every detector used: Megvii,
Mapillary, PointPillars, and the two produced here, FCOS3D (0.3207 vs 0.3216) and CenterPoint (57.47
vs 57.40). nuScenes mAP and this matching are both center-distance based and use only translation,
score, and class, all of which reproduce. A matcher that reproduces published accuracy is not
inventing the miss structure.

## 4. The conditioning is incomplete

**The attack.** Five covariates cannot remove all shared difficulty; an unmeasured common cause could
produce the residual.

**What answers it, and its limit.** Result O quantifies exactly this with an E-value: an unmeasured
common cause would need to be associated with both channel failures by a risk-ratio factor of about
2 to 3, beyond the five covariates, to explain the coupling away. Weaker hidden factors cannot. This
bounds the threat; it does not prove no such factor exists. Object size and truncation are named,
untested candidates.

## 5. The coefficient is not marginal-invariant

**The attack.** `c = P(both) / (P_A P_B)` moves with the marginal miss rates, so trends in `c` can be
arithmetic rather than structural.

**What answers it.** This workstream found and reported the problem itself. Result P shows the
coefficient is smallest where the absolute joint-miss is largest, so `c` is always read alongside the
marginals. Result R shows that an inviting accuracy-coupling trend is about four fifths this
arithmetic, and only the residual that survives a matched-marginal comparison is claimed.

## 6. Effective sample size and clustering

**The attack.** Boxes are not independent; the real unit is the tracked object, so box-level counts
overstate precision.

**What answers it.** Audit 1 measured the design effect and every interval is an instance-clustered
bootstrap over the 8,976 tracked objects, not over boxes. The unit is the object throughout.

## 7. One benchmark, one split (open)

**The attack.** Everything is nuScenes validation. The result may not transfer to other datasets,
sensors, or geographies.

**Status: open.** This is a single-benchmark result and is stated as such. Transfer to KITTI, Waymo,
or an operational distribution is untested. The claim is bounded to what nuScenes val contains.

## 8. Detection is a proxy for the RSS subsystem (open)

**The attack.** RSS Definition 32 concerns subsystem errors. Two 3D detectors are not a full
perception subsystem with tracking, temporal fusion, and multi-sensor fusion; a deployed stack could
be more or less coupled than its detectors.

**Status: open and scoped.** The measurement is of two detection channels, a reasonable and
public-data-available proxy for the independence assumption, not of a fused production subsystem.
The word used throughout is detector, not system, and joint silent miss is explicitly not claimed
because this source is a benchmark, not a system under test.

## 9. Proposed, not externally audited (the meta-threat)

Every result is retained as `proposed`. It is reproducible from this repository and self-checked
against independent anchors, but no independent external scientific review has been retained. That is
the honest ceiling on current confidence, and closing it, not producing more measurements, is the
next thing that would raise it.

## Reading

Threats 2, 3, 5, and 6 are answered, and 2 strengthens the finding. Threats 1 and 4 are bounded but
not eliminated. Threats 7, 8, and 9 are open and scoped. None of them is hidden. The core claim, that
camera and lidar fail together beyond shared observable difficulty on this benchmark, rests on the
answered threats; the open ones bound how far it may be carried, and the workstream carries it no
further than they allow.
