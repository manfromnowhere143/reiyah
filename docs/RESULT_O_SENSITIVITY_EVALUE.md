# Result O: descriptive sensitivity analysis, interpretation corrected

Document ID: `reiyah.result-o-sensitivity-evalue`

Version: `0.1.1`

Lifecycle status: `corrected`

The retained numerical sweep is historical. The original statement that **each** confounding arm
must individually exceed the E-value was wrong. Under the bounding-factor formulation, the
E-value is an equal-strength benchmark and a lower bound on the maximum strength required for
explanation, not the minimum required on each arm separately. An unequal pair can explain the
association with one arm below that benchmark.

The [research-board report](RESEARCH_BOARD_2026-09-07.md) gives an explicit counterexample.
The primary [Ding-VanderWeele paper](https://arxiv.org/abs/1507.03984) supplies the bounding-factor
framework. The sensitivity parameters and target risk ratio still require substantive justification;
this calculation does not identify a causal effect of camera failure on lidar failure.

## Retained calculation

For the original deepest-stratum support, the script computes a Mantel-Haenszel risk ratio of
lidar miss comparing camera-miss objects with camera-hit objects, and a bootstrap interval
resampling tracked instances. It then applies `E(x) = x + sqrt(x(x - 1))` to the risk ratio and
its near-null confidence bound. The formula is not a sensitivity analysis of the normalized
joint-miss coefficient itself. A new scene-cluster interval for that separate coefficient is in
[Result AO](RESULT_AO_REFERENCE_POPULATION_AUDIT.md); it does not replace the intervals below.

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

## Permitted interpretation

The table describes the original selected population and assumptions. Unmeasured object size,
truncation, occlusion or shared reference error remain possible explanations. No empirical
measurement here determines that such explanations are implausible. Conditioning on additional
variables need not monotonically lower an association statistic.

RSS permits bounded dependence under specified safety-critic events. This detector-level analysis
does not refute RSS, quantify a vendor's safety, or justify the withdrawn evidence-budget figures.

## Historical generator and custody

[The original transcript](../evidence/measurement/result_o.txt) and
[original generator](../tools/measure/result_o_sensitivity_evalue.py) remain unchanged to preserve
reproduction lineage, including their overinterpretation. Their printed prose is superseded by
this correction and the current register; a byte-identical replay does not readmit it.

No scientific support, safety finding, standards compliance, physical causal identification,
comparative vendor claim or operator acceptance is established by this correction.
