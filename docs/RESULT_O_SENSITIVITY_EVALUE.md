# Result O: how strong an unmeasured common cause would have to be to explain the coupling

Document ID: `reiyah.result-o-sensitivity-evalue`

Version: `0.1.0`

Lifecycle status: `proposed`

## The caveat every result declares, now quantified

Results L, M and N each end on the same honest sentence: the residual camera-lidar
dependence is measured after the covariates nuScenes annotates, and an **unmeasured** common
cause of both failures could in principle produce it. Object size and truncation are the
named candidates; occlusion finer than the coarse visibility bin is another. Until now that
caveat was only declared. This result measures it.

The standard instrument is the **E-value** (VanderWeele and Ding, *Annals of Internal
Medicine*, 2017): the minimum strength of association, on the risk-ratio scale, that an
unmeasured confounder would need with **both** the exposure and the outcome, beyond the
measured covariates, to move an observed conditional association all the way to the null. A
large E-value means only an implausibly strong hidden factor could account for the finding; a
small one means a weak factor could.

The framing fits this problem exactly. Take camera failure as the exposure and lidar failure
as the outcome; the unmeasured confounder the E-value bounds is a **common cause of both** -
precisely the latent shared difficulty a critic invokes. So the E-value answers the skeptic's
real objection in the skeptic's own terms: *how much* unmeasured shared difficulty would it
take.

## Method

For each score threshold and each detector pair, on the same L5 common support as Results L,
M and N (five admissible confounders; the ground-truth-fixed 131,722-row population), compute
the Mantel-Haenszel conditional risk ratio of lidar-miss comparing camera-miss objects to
camera-hit objects, directly from the same 2x2 cells the coefficient uses:

```
a = camera miss AND lidar miss     b = camera miss AND lidar hit
c = camera hit  AND lidar miss     d = camera hit  AND lidar hit
RR_MH = sum_i a_i (c_i + d_i)/n_i  /  sum_i c_i (a_i + b_i)/n_i      (Greenland-Robins)
```

The risk ratio is taken directly from the counts, so no odds-ratio-to-risk-ratio
approximation is involved and the common-outcome caveat of the OR-based E-value does not
apply. Uncertainty is the identical instance-clustered bootstrap. The E-value
`E(x) = x + sqrt(x(x-1))` is reported for the point estimate and, as the method requires for a
finding, for the confidence bound nearest the null.

**Self-check.** The Mantel-Haenszel odds ratio at `score >= 0.30` is `2.776` for the Megvii
pair, against Result E's independently derived conditional MH OR of `2.810` on the shallower
class x range x visibility stratification. Adding weather and motion lowers it slightly, as it
should, which confirms the machinery reproduces the established conditional association before
any E-value is computed on it.

## The sweep

**Mapillary (camera) x Megvii (lidar)**

| score >= | conditional RR (lidar \| cam) | MH OR | E-value | E-value (CI) |
|---|---|---|---|---|
| 0.10 | 2.643 [2.471, 2.804] | 3.583 | 4.726 | 4.378 |
| 0.20 | 2.261 [2.134, 2.376] | 3.291 | 3.949 | 3.691 |
| 0.30 | 1.816 [1.744, 1.888] | 2.776 | **3.034** | 2.883 |
| 0.40 | 1.526 [1.481, 1.571] | 2.612 | 2.422 | 2.326 |
| 0.50 | 1.458 [1.414, 1.500] | 2.947 | 2.275 | 2.179 |

**Mapillary (camera) x PointPillars (lidar)**

| score >= | conditional RR (lidar \| cam) | MH OR | E-value | E-value (CI) |
|---|---|---|---|---|
| 0.10 | 1.876 [1.771, 1.983] | 2.656 | 3.158 | 2.940 |
| 0.20 | 1.503 [1.455, 1.551] | 2.288 | 2.373 | 2.269 |
| 0.30 | 1.394 [1.357, 1.432] | 2.153 | **2.134** | 2.053 |
| 0.40 | 1.355 [1.321, 1.391] | 2.094 | 2.048 | 1.972 |
| 0.50 | 1.355 [1.315, 1.398] | 2.071 | 2.048 | 1.958 |

## Answer

At the `score >= 0.30` reference point, an unmeasured common cause of camera failure and
lidar failure would have to be associated with **each**, on the risk-ratio scale and beyond
class, range, visibility, weather and motion, by a factor of at least:

- **3.03** for Mapillary x Megvii (2.88 for the near-null 95% bound),
- **2.13** for Mapillary x PointPillars (2.05 for the near-null 95% bound),

to explain the coupling away. A hidden factor weaker than that on either arm cannot account
for it; one at least that strong on both could. For scale, that is an unmeasured shared
difficulty comparable to the strongest **measured** covariate effects in this data, not a
slight residual imbalance the conditioning happened to miss.

Two things stated as measured, neither softened nor oversold:

1. **The E-value falls as the threshold tightens** (Megvii 4.73 to 2.28; PointPillars 3.16 to
   2.05), tracking the coupling's own attenuation in Result N. The strictest operating points
   ask the least of a confounder; the loosest ask the most.

2. **The E-value bounds plausibility; it does not test existence.** Object size and truncation
   are named unmeasured candidates. This result says how strong such a factor would have to
   be, not that one is present or absent.

## The three robustness axes

With this result the finding stands on three independent axes, each answering a distinct
cheap objection on evidence rather than assertion:

| Axis | Result | Objection answered |
|---|---|---|
| the detector | M | "it is one model pair" - survives a second, architecturally distinct lidar backbone |
| the score threshold | N | "0.3 is cherry-picked" - conditional coefficient excludes 1.0 across the whole 0.1-0.5 range |
| unmeasured confounding | O | "you did not measure everything" - a hidden common cause must reach RR >= ~2-3 on both arms to nullify |

The one axis still open is the camera detector: every pair shares the single Mapillary camera
model, so robustness to the *camera* choice is untested and needs a second camera-only
detector.

## Consequence

RSS Definition 32's channel-independence assumption fails on this evidence not only across
detectors and operating points but robustly to unmeasured shared difficulty: the residual
coupling cannot be an artifact of one omitted covariate unless that covariate is strong. The
safety-argument premise in Result G is correspondingly harder to dismiss.

## Provenance

`evidence/measurement/result_o.txt` records both commands, both full sweeps, and the
odds-ratio self-check against Result E.

## Non-claims

No scientific support, safety finding, compliance determination, comparative claim about any
detector or vendor, and no operator acceptance. The E-value bounds unmeasured confounding; it
neither rules it in nor out. Two published detection outputs on one public split, retained as
`proposed`. No released `1.2` byte is modified.
