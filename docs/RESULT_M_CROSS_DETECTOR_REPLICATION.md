# Result M: the convergence-above-independence result replicates on a second lidar detector

Document ID: `reiyah.result-m-cross-detector-replication`

Version: `0.1.0`

Lifecycle status: `proposed`

## The question Result L leaves open

Result L closed the second open item from `GATE_B_SESSION_HANDOFF.md`: on the
`mapillary x megvii` pair the conditional coefficient converges to `1.151`,
`[1.138, 1.160]`, above independence, after five admissible confounders on a fixed
population. Its own non-claims are explicit that this is two published detection outputs
on one split.

That leaves a single-pair reviewer's objection standing: **is the residual dependence a
property of the two sensing channels, or an artifact of the Megvii lidar model in
particular?** One pair cannot separate the two. Result J answered the parallel question
for the *worst group* by running the worst-group contract across all three pairs. This
result answers it for the *headline coefficient* by running Result L's exact convergence
contract on a second, architecturally distinct lidar detector.

## The second pair

Result L crosses the camera detector with Megvii (CBGS, lidar, 51.9 mAP published). This
result crosses the identical camera detector with PointPillars:

| Detector | Family | Modality | mAP published | mAP reproduced |
|---|---|---|---|---|
| mapillary | MonoDIS | camera | 29.8 | 29.58 |
| pointpillars | PointPillars | lidar | 29.5 | 29.54 |

PointPillars is a different lidar architecture from CBGS and roughly half its accuracy. If
the coefficient stayed above 1.0 only for Megvii, that would point at the model; a repeat
above 1.0 on a weaker, unrelated lidar backbone points at the sensing channels.

Nothing is re-tuned. Same admissible-covariate set, same `num_lidar_pts` exclusion on
stated mediator grounds, same common-support construction, same instance-clustered
bootstrap, same seed `20260828`, same `score >= 0.3`.

## The sequence, on a fixed population

| Level | Strata | c | 95% CI | Step |
|---|---|---|---|---|
| L0 none, marginal | 1 | 1.401 | [1.383, 1.419] | |
| L1 + class | 10 | 1.341 | [1.325, 1.357] | -0.060 |
| L2 + range band | 33 | 1.209 | [1.197, 1.221] | -0.132 |
| L3 + visibility | 132 | 1.104 | [1.094, 1.112] | -0.105 |
| L4 + weather and lighting | 334 | 1.101 | [1.092, 1.109] | **-0.002** |
| L5 + motion state | 623 | **1.096** | **[1.087, 1.103]** | **-0.005** |

All estimates use an instance-clustered bootstrap over the tracked objects on the fixed
131,722-row common support, 1,500 replicates, seed `20260828`.

## Answer

**The convergence signature repeats, and again it is not to independence.**

The same three covariates carry the association down hard — class, range and visibility
account for steps of -0.060, -0.132 and -0.105 — and the next two admissible covariates
move it by -0.002 and -0.005, an order of magnitude smaller. The terminal value is 1.096
with a cluster-robust 95% interval of `[1.087, 1.103]` that excludes 1.0.

| Pair | Terminal c | 95% CI | Excludes 1.0 |
|---|---|---|---|
| mapillary x megvii (Result L) | 1.151 | [1.138, 1.160] | yes |
| mapillary x pointpillars (Result M) | 1.096 | [1.087, 1.103] | yes |

Two lidar detectors that share no architecture, one at half the accuracy of the other,
both fail together with the same camera beyond what class, range, visibility, weather and
motion explain. The excess over independence is **smaller** on the weaker lidar — 1.096
against 1.151 — and this result does not speculate on why; it records the sign as
unchanged and the interval as still excluding 1.0.

### The mediator error, in the second pair too

| | c | 95% CI | Step from L5 |
|---|---|---|---|
| L5, admissible covariates only | 1.096 | [1.087, 1.103] | |
| L6 + `num_lidar_pts` bucket | 1.067 | [1.060, 1.073] | **-0.029** |

Conditioning on the lidar point count again moves the coefficient several times more than
either legitimate covariate, and again it is not an estimate: `num_lidar_pts` is the lidar
return itself, on the path being measured. The trap is the same size and the same
direction as in the Megvii pair. It is recorded so nobody reaches for it as convergence.

## What this adds, and what it does not

It removes the single-model objection to Result L's headline: the residual dependence is
not an artifact of the Megvii detector, because it survives replacing that detector
entirely. Together with Result J's worst-group replication across the same three pairs,
the dependence is a property of the operating region and the two sensing channels, not of
one model pair.

It does not widen identification. The same bound holds: this is association after declared
conditioning, not a causal effect; it is limited to the covariates nuScenes annotates
(object size and truncation were not available in this cache and were not tested);
unmeasured common causes remain possible; and no adjustment set is claimed sufficient for
identification. Two pairs excluding independence is stronger evidence than one, not a proof
of the underlying mechanism.

## Consequence

Result L's conclusion — that RSS Definition 32's channel-independence assumption fails on
this evidence — is now shown for two lidar detectors rather than one. The RSS critique in
Results D, E, I, J, K and L rests on a coefficient that has been reproduced on an
independent detector, not on a single measurement.

## Provenance

`evidence/measurement/result_m.txt` records the exact command and the raw tool output. The
tool `result_l_convergence.py` prints a fixed title line reading `mapillary x megvii`
regardless of its arguments; the pair measured is fixed by the third argument
(`matched_pointpillars.json`), and every number in this result differs from Result L,
confirming the second detector's matched file was consumed.

## Non-claims

No scientific support, safety finding, compliance determination, comparative claim about
any detector or vendor, and no operator acceptance. Two published detection outputs on one
public split, retained as `proposed`. No released `1.2` byte is modified.
