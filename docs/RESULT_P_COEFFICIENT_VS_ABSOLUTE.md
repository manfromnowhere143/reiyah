# Result P: the RSS coefficient is smallest where the sensors jointly miss the most

Document ID: `reiyah.result-p-coefficient-vs-absolute`

Version: `0.1.0`

Lifecycle status: `proposed`

## The claim in one line

The RSS Definition 32 coincidence constant `c` and the absolute rate at which both sensors miss
the same object move in **opposite directions** across the detector operating range. `c` is
smallest exactly where the joint failure is largest, so `c` alone cannot certify redundancy.

## Why this matters, and why it is not obvious

RSS Corollary 3 reduces the required validation evidence from about `10^9` to about `10^5` by
assuming `c`-approximate independence between subsystem errors. The whole reduction turns on `c`
being near 1. A reader naturally treats a small `c` as good news: the channels are close to
independent, the redundancy is doing its job.

The estimand doc (`docs/ESTIMAND_RSS_DEFINITION_32.md`, section 1) already warns that `c` is
`P(both) / (P_A · P_B)` and is **not invariant to the marginal miss rates**. This result makes
that warning concrete and shows it has a safety edge: as a detector's score threshold tightens,
the marginal miss rates `P_A` and `P_B` rise, the denominator `P_A·P_B` rises, and `c` is dragged
toward 1 for arithmetic reasons — while the thing a redundancy argument actually needs to bound,
the absolute joint-miss rate `P(both)`, rises at the same time.

## The measurement

Full nuScenes validation population, both detector pairs, instance-clustered bootstrap
(1,500 reps, seed `20260828`). At each threshold, the coefficient is reported beside the two
absolute quantities.

**Mapillary (camera) x Megvii (lidar)**

| score >= | P_A | P_B | c (coefficient) | P(both) — absolute | excess = P(both) − P_A·P_B |
|---|---|---|---|---|---|
| 0.10 | 0.314 | 0.134 | **2.271** [2.216, 2.322] | **0.096** [0.091, 0.101] | 0.054 [0.051, 0.056] |
| 0.20 | 0.395 | 0.220 | 1.878 [1.843, 1.913] | 0.163 [0.157, 0.169] | 0.076 [0.073, 0.079] |
| 0.30 | 0.464 | 0.340 | 1.587 [1.564, 1.611] | 0.250 [0.243, 0.258] | 0.093 [0.090, 0.096] |
| 0.40 | 0.559 | 0.489 | 1.363 [1.347, 1.380] | 0.372 [0.364, 0.381] | 0.099 [0.096, 0.102] |
| 0.50 | 0.686 | 0.598 | **1.239** [1.226, 1.252] | **0.509** [0.499, 0.518] | 0.098 [0.095, 0.102] |

**Mapillary (camera) x PointPillars (lidar)**

| score >= | P_A | P_B | c (coefficient) | P(both) — absolute | excess |
|---|---|---|---|---|---|
| 0.10 | 0.314 | 0.174 | **1.909** [1.860, 1.957] | **0.104** [0.099, 0.110] | 0.050 [0.047, 0.052] |
| 0.20 | 0.395 | 0.378 | 1.557 [1.532, 1.581] | 0.232 [0.225, 0.240] | 0.083 [0.080, 0.086] |
| 0.30 | 0.464 | 0.479 | 1.393 [1.375, 1.411] | 0.310 [0.302, 0.318] | 0.087 [0.084, 0.090] |
| 0.40 | 0.559 | 0.555 | 1.284 [1.270, 1.298] | 0.398 [0.390, 0.407] | 0.088 [0.085, 0.091] |
| 0.50 | 0.686 | 0.617 | **1.193** [1.183, 1.203] | **0.505** [0.496, 0.514] | 0.082 [0.078, 0.085] |

Every interval is non-overlapping between adjacent thresholds, so the two trends are not noise.

## What the numbers say

- **The coefficient falls.** `c` drops by 1.03 (Megvii) and 0.72 (PointPillars) from 0.1 to 0.5.
- **The absolute joint-miss rate rises the opposite way**, and hard: from about 10% of objects to
  about 51%. At `score >= 0.5`, both sensors miss the same object roughly **half the time**, and
  that is the operating point at which `c` looks most independent.
- **The absolute excess over independence rises and plateaus** in the 0.3–0.4 band (Megvii 0.054
  to 0.099; PointPillars 0.050 to 0.088). It never follows `c` down. At every operating point at
  or above 0.2 the absolute excess is far above its loose-threshold value while `c` is below its
  loose-threshold value.

## Reading, stated as a property of the estimand and not a safety determination

1. `c` is a ratio deflated by the rising marginal miss rates. As `P_A` and `P_B` climb toward 1,
   `P_A·P_B` climbs, and any two frequent events look independent by this ratio. The fall of `c`
   with the threshold, first reported in Result N, is in large part this arithmetic, not the
   channels becoming more independent.

2. The safety-relevant quantity is not the ratio. A real object missed by both sensors is missed
   whatever `c` says. `P(both)` and its absolute excess are what a redundancy argument must bound,
   and they are largest where `c` is smallest.

3. Therefore a redundancy argument that certifies safety by exhibiting a small `c` — the shape of
   Corollary 3's premise — can hold at exactly the operating point where the two sensors jointly
   miss the most objects. **`c` must be read together with the marginal miss rates, never alone.**

This does not overturn Results L, M, N or O: after conditioning on the five admissible confounders
the coefficient still exceeds 1 across detectors, thresholds and plausible unmeasured confounding.
It adds the orthogonal point that even where the marginal coefficient is closest to 1, the
absolute joint failure is at its worst, so the coefficient is necessary but not sufficient to read
the redundancy.

## Non-claims

Two published detection outputs on one public split, retained as `proposed`. Rates after declared
matching, not a causal effect or a safety determination. No claim is made that any specific
operating point is used by any deployed system, nor that any vendor's safety case is invalid. No
released `1.2` byte is modified.
