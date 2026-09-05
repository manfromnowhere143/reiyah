# Result R: does the coupling rise with detector accuracy? Mostly it is Result P

Document ID: `reiyah.result-r-accuracy-coupling`

Version: `0.1.0`

Lifecycle status: `proposed`

## The tempting headline, and why it is wrong as stated

Adding a third, stronger lidar (CenterPoint, produced and validated here at mAP 0.574) makes a
clean-looking trend appear. With the camera fixed and each lidar at its own default `score >= 0.3`,
the conditional coefficient rises monotonically with lidar accuracy:

| lidar | accuracy | miss rate P_B | conditional c |
|---|---|---|---|
| PointPillars | 29.5 | 0.479 | 1.096 |
| Megvii | 51.9 | 0.340 | 1.151 |
| CenterPoint | 57.4 | 0.213 | 1.216 |

The tempting claim writes itself: *the better your detector, the more it fails together with the
camera, so redundancy buys the least for state-of-the-art systems.* It would be a striking,
safety-critical result. **It is also confounded, and must not be claimed as stated.**

## The confound is our own Result P

Result P established that `c = P(both) / (P_A·P_B)` is deflated by the marginal miss rates. A
stronger detector has a **lower** miss rate — CenterPoint misses 21% of objects at 0.3, Megvii
34%, PointPillars 48% — and a lower marginal **inflates `c` for arithmetic reasons alone**. So the
monotonic rise above is partly, perhaps mostly, the marginal artifact, not coincident failure. A
finding this session already proved predicts exactly this trap.

## The honest test: match the miss rate

Threshold each lidar to the **same** global miss rate `P_B`, hold the camera fixed, and recompute
the conditional coefficient. If `c` still rises with accuracy at equal miss rates, the effect is
real; if it flattens, the raw trend was the artifact.

| matched P_B | PointPillars (29.5) | Megvii (51.9) | CenterPoint (57.4) | spread |
|---|---|---|---|---|
| 0.40 | 1.116 [1.106, 1.124] | 1.128 [1.117, 1.136] | 1.141 [1.129, 1.149] | 0.025 |
| 0.45 | 1.103 [1.093, 1.110] | 1.114 [1.104, 1.121] | 1.124 [1.114, 1.131] | 0.021 |
| 0.50 | 1.091 [1.083, 1.098] | 1.098 [1.089, 1.104] | 1.108 [1.098, 1.114] | 0.017 |
| 0.55 | 1.081 [1.073, 1.087] | 1.083 [1.075, 1.089] | 1.093 [1.084, 1.098] | 0.012 |

The raw spread across the accuracy range was **0.120**. At a matched miss rate it collapses to
about **0.02**.

## What is actually true

1. **About four fifths of the apparent accuracy-coupling trend is the Result P marginal
   artifact.** Match the miss rates and most of it disappears. Anyone who reports a raw
   accuracy-versus-`c` trend without matching marginals is largely reporting the arithmetic of the
   ratio, not coincident failure.

2. **A small, robust residual survives.** At every one of the four matched miss-rate levels the
   ordering is perfectly monotonic in accuracy, and at the extremes the intervals separate
   (P_B = 0.40: PointPillars 1.116 [1.106, 1.124] vs CenterPoint 1.141 [1.129, 1.149], no
   overlap). So there is a genuine effect — the strongest detector does fail together with the
   camera slightly more than the weakest, even at equal miss rates — but it is an order of
   magnitude smaller than the naive comparison implied.

3. **The safety reading is the careful one.** "Better sensors couple more" is directionally
   supported and quantitatively tiny once the artifact is removed. It is not the dramatic result
   the raw numbers advertised, and this result exists to stop that dramatic result from being
   claimed.

This is the point of the whole workstream in miniature: the interesting-looking number was checked
against its most likely artifact, the artifact explained most of it, and only the residue that
survived the check is claimed.

## Non-claims

Three published or workstream-produced detection outputs on one public split, retained as
`proposed`. CenterPoint was produced here and validated to published mAP. This is a property of the
estimand on public data, not a causal effect, not a safety determination, and not a comparative
claim about any vendor's detector. No released `1.2` byte is modified.
