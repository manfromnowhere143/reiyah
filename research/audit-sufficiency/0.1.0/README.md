# Audit sufficiency for a paired detector comparison

Artifact ID: `reiyah.research.audit-sufficiency`. Version: `0.1.0`. Lifecycle status: `exploratory`.
Dated 16 September 2026. Lane: independent research and comparator. Engine core, shared
interfaces, main integration and Gate A history are untouched.

## The question

A comparison packet reports a paired loss difference under one finite reference world and a
strict-improvement criterion. A minimum deletion witness tells the smallest set of reference
objects whose removal overturns the criterion. That is not an audit list: two disjoint minimum
witnesses exist on the retained forty-frame case, so confirming one leaves the other available.

The object that answers the audit question is a sufficient confirmed set: after these objects are
confirmed present, no admissible deletion of the others can overturn the criterion. Finding one
is a hitting-set problem over every admissible adverse deletion, not a search for one adverse set.

This package makes that question computable for the deletion family, then measures how many
audit queries each of several selection policies needs before a certificate exists.

## What is computed

`sufficiency.py` is self-contained: its own Hopcroft-Karp matcher, exact rationals, and a
single-level mixed-integer program for the adversary. Within one anchor the paired difference
depends on the reference only through `gain = TP_augmented - TP_base`. The adversary deleting a
set `S` of unconfirmed objects seeks the minimum of `gain(S)`. By Konig's theorem the maximum
augmented matching equals a minimum vertex cover, and the negative of the maximum base matching
is the minimum of the negative of a matching, so both terms are minimisations and the problem is
one program with binary deletion variables, binary cover variables and matching variables.

Every certificate carries three tiers that are never merged:

| Tier | Meaning | Trust |
|---|---|---|
| `sound` | The adversary removes at most one gain unit per deleted object that has an edge, and never more than the anchor's gain | Exact rational proof, loose |
| `solver` | Per-anchor MILP optimum (HiGHS through scipy); the adversary's set is recomputed exactly | Only the claim that nothing larger exists rests on the solver |
| `achieved` | A concrete deletion set recomputed exactly | Proof of insufficiency when it crosses |

A budgeted variant restricts the adversary to at most `k` deletions in total, combining
per-anchor deletion curves by a small dynamic program.

Scope: one finite world, whole-object deletion, fixed detections, fixed loss. Insertion, class,
geometry and time errors are outside the family. A certificate is conditional on the family and on
the confirmed observations being correct. It says nothing about physical truth.

## Controls

| Control | Expected | Observed |
|---|---|---|
| Joint-deletion trap: one base at 0, one addition at 3, objects at 1.1, 1.5, 1.9; floor 1, minimum 2 | budget 1 sufficient; budget 2 insufficient | as expected |
| Two-carrier control: base sees `o1,o2`; additions see one each; loss (1,0) | each label alone is a witness; confirming one is insufficient; both sufficient | as expected |
| Forty-frame case, original 49 witness confirmed, budget 49 | another crossing 49-set exists (Codex review, 15 September) | reproduced by the MILP without using that probe |

## Results on the retained cases

All numbers are exact rationals or label counts. Query counts are label queries against the
retained benchmark labels taken as the audit oracle, in batches of 10 (forty-frame) or 5 (first,
second), until the solver-tier certificate reports sufficiency under the unbounded deletion
family. The sound tier never certified before every edge-bearing label was confirmed; every
certificate below is solver-tier, with the counterexample tier verified exactly at each step.

### Structure of the three cases

| Case | Labels | Delta | Margin | Carriers | Carriers with a base edge | Additive pool | Floor | Disjoint floor witnesses built | Proven lower bound on a sufficient audit |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| First (2 anchors, lidar base + camera additions) | 106 | 1 | 9/10 | 6 | 0 | 6 | 1 | 6 | 6 |
| Second (14 frames, same two scenes) | 737 | 2/7 | 13/70 | 53 | 11 | 42 | 2 | 26 | 41 |
| Forty-frame (scene-0101, camera base + lidar additions) | 2,299 | 51/20 | 49/20 | 361 | 7 | 354 | 49 | 7 | 306 |

The additive pool is the set of carriers with no base edge. Deleting any subset of it lowers the
augmented matching by exactly the subset size and leaves the base matching unchanged (alternating
path argument), so any `floor` of them cross and every sufficient set contains all but `floor - 1`
of them. That cut is exact; it is what lifts the forty-frame bound from 7 (disjoint witnesses) to 306.

### Named confirmed sets on the forty-frame case

| Confirmed set | Size | Unbounded family | Budget of 49 deletions |
|---|---:|---|---|
| None | 0 | insufficient: 538 deletions remove all 21 units of gain | insufficient: a 49-set crosses (8 frames) |
| Original 49 witness | 49 | insufficient: 493 deletions remove 373/20 | insufficient: a disjoint 49-set crosses (reproduces the 15 September review) |
| Additive pool | 354 | insufficient: 181 individually inert labels jointly remove 33/10, more than the 49/20 margin | sufficient: at most 27/20 removable |

The third row is the fact that a carrier count cannot see: 66 units of gain are removable only
through joint deletion of labels whose single deletion changes nothing.

### Exact minimum sufficient audits by implicit hitting set

| Case | Minimum sufficient set | Iterations | Adverse sets enumerated | Seconds |
|---|---:|---:|---:|---:|
| First | **9 of 106** | 9 | 10 | 0.7 |
| Second | **53 of 737** | 249 | 1,344 | 112 |
| Forty-frame | interval **[306, 373]** | 150 and more | over 4,500 | see note |

For the forty-frame case the lower bound comes from the pool cut and did not move over the first 150
iterations of the hitting-set loop; the upper bound is an inclusion-minimal sufficient set shrunk
from the best policy result. The exact minimum lies in the interval; closing it needs a better
adverse-set generator than random shrinking of the maximal counterexample.

### Queries to a certificate, forty-frame case, unbounded family

| Policy | Queries | Share of 2,299 | Rounds | Seconds |
|---|---:|---:|---:|---:|
| Random (seeds 0, 1, 2) | 2,020 / 1,960 / 2,000 | 85 to 88% | 196 to 202 | 75 to 82 |
| Most augmented edges first | 1,660 | 72% | 166 | 36 |
| Single-deletion influence first (AMIP-style first order) | 1,170 | 51% | 117 | 59 |
| Counterexample-guided (first 10 of the adversary set each round) | 530 | 23% | 53 | 59 |
| Objects adjacent to an addition first (one-line heuristic) | **480** | 21% | 48 | 25 |
| Inclusion-minimal shrink of the heuristic set (107 labels dropped, 480 certificate checks) | **373** | 16.2% | | 287 |
| Proven lower bound | 306 | 13.3% | | |

Pre-declared comparison, reported as it came out: the one-line heuristic beat the naive
counterexample-guided policy on this case. On the first and second cases the order reverses
(first: 13 versus 45 versus 85 for guided, influence, random; second: 65 versus 75 versus 700),
and guided lands within 4 and 12 labels of the exact optimum. Selection quality is case-dependent;
the certificate and its stopping rule are what make any of these counts meaningful, because no
policy knows when to stop without it.

### Injected-error control, forty-frame case

About 5% of labels were planted absent at random (124 and 106 of 2,299). A queried absent label
is removed from the world and the decision is recomputed before continuing.

| Policy, seed | Queries | Absent found | Final delta | Certificate on the corrected world |
|---|---:|---:|---:|---|
| Influence, 0 | 1,790 | 96 of 124 | 27/20 | sufficient |
| Influence, 1 | 1,490 | 68 of 106 | 19/10 | sufficient |
| Counterexample-guided, 0 | 560 | 29 of 124 | 8/5 | sufficient |
| Counterexample-guided, 1 | 540 | 22 of 106 | 39/20 | sufficient |

The procedure updates its world when an audit answer contradicts a label and still terminates
with a certificate for the corrected world. Planted absences are random; no error process was
observed.

### Reuse of confirmed observations under a changed decision rule

| Variant | Delta | Fresh queries | Extra queries starting from the 530 confirmed labels |
|---|---:|---:|---:|
| FN 1, FP 4, tolerance 1/10 | -213/10, criterion excluded | not modeled | not modeled |
| FN 4, FP 1, tolerance 1/10 | 681/20 | 180 | **0** |
| FN 1, FP 1, tolerance 1/2 | 51/20 | 550 | **20** |

Same world, same observations, only the rule changed, so confirmed presence stays applicable. This
shows the certificate is reuse-aware; it is not a measured saving on a changed system.

### Cost check requested by the shared contract

Full recomputation of all 40 anchors: 3.8 ms. Recomputing only the 8 touched anchors after the
49-record deletion, reusing the other 32: 12 ms, because the copy costs more than the matching.
Matching is not the expensive operation in this workflow; nothing here should be optimized further.

## Reading the numbers

1. A witness is not an audit. Confirming the 49 leaves a disjoint 49 available; confirming all
   354 individually influential no-base-edge labels still leaves 66 units removable by joint
   deletion of labels that are individually inert.
2. The exact minimum audit is small on the small cases (9 of 106; 53 of 737) and provably large
   on the forty-frame case (at least 306 of 2,299, at most 373). Robustness of that verdict to
   reference deletion costs at least 13% of the labels, whatever policy is used.
3. Selection heuristics are competitive with the exact adversary as selectors; the exact machinery
   earns its place as the stopping rule and as the certificate, not as the picker.
4. Under a budget of 49 deletions the pool is sufficient; under unbounded deletion it is not. The
   family and budget must be declared with every audit claim.

## Certified robustness census: 20 detector pairs, 150 scenes, 3,000 verdicts

Dated 17 September 2026. `census_units.py` rebuilds every decision unit of the research lane's
scale study from Reiyah custody (five retained nuScenes validation submissions, the v1.0-trainval
tables, the devkit validation split) under the frozen protocol semantics; `census_run.py`
computes, per unit, the exact decision, the arithmetic floor, the carrier structure and pool cut,
a certified sufficient set (addition-adjacent policy, batch 20, solver-tier stopping rule), and a
Monte Carlo comparator; `census_summary.py` aggregates and reconciles. Aggregates are in
`census-summary.json`. Per-unit inputs and identity-bearing outputs stay private.

Consistency gate: the rebuilt scene-0101 Mapillary-to-Megvii unit equals the sealed forty-frame
case object for object (2,299) and edge for edge (2,803).

### Reconciliation with the retained census index (research lane, 0.2.0 and 0.4.0)

| Quantity | Equal | Differ |
|---|---:|---:|
| Supported versus excluded status | 2,998 | 2 |
| Exact decision value | 2,830 | 170 |
| Arithmetic floor | 2,941 | 59 |
| Annotation, base and addition counts | 2,340 | 660 |

Every count difference is one or two annotations within centimetres of the 50 m range boundary.
Detections reconcile everywhere once the range is taken as planar distance in the global frame
(the module docstring describes an ego-rotated rule; the retained index matches the global rule).
For annotations no single ego-pose channel or file-order rule reproduces the retained counts, and
the census driver that produced the index was not committed, so the exact reference point cannot
be recovered from retained code. The residual is reported as found. Supported and excluded status
agree on 2,998 of 3,000 units, so no conclusion below depends on it.

### What every supported verdict carries

| Quantity over the 1,125 supported verdicts | p10 | median | p90 | max |
|---|---:|---:|---:|---:|
| Floor: deletions that can overturn the verdict | 3 | 27 | 106 | 575 |
| Floor as a share of the unit's labels | 0.4% | 2.4% | 7.5% | 21.7% |
| Proven lower bound on a sufficient audit, share of labels | 3.5% | 11.5% | 23.1% | 49.0% |
| Certified upper bound on a sufficient audit, share of labels | 6.8% | 17.7% | 29.5% | 79.8% |
| Interval width, labels | 11 | 40 | 188 | 2,080 |
| Carrier pool, share of labels | 4.8% | 14.8% | 28.4% | 54.6% |

In all 1,125 supported units the additive pool is at least as large as the floor, so an exact
crossing set of exactly `floor` deletions exists by construction. This proves per unit what the
research lane's census reported empirically (minimum equals floor everywhere) and explains it:
the sufficient condition holds in every unit. A minimum above the floor remains possible in
principle (the joint-deletion trap) and occurs in none of these units.

All 1,125 certified upper bounds reached solver-tier sufficiency; none returned unresolved.

### The comparator: random label noise versus the exact adversary

For each supported unit, 200 random deletion sets of size `floor` and 200 of size `2 x floor`
were applied and the criterion recomputed exactly.

| | Random never overturned the verdict in 200 trials | Mean overturn rate | Exact adverse set exists |
|---|---:|---:|---|
| Deletions = floor | **1,048 of 1,125 (93.2%)** | 0.35% | all 1,125 |
| Deletions = 2 x floor | **930 of 1,125 (82.7%)** | 1.45% | all 1,125 |

A robustness estimate based on random label perturbation at the exact flipping size reports
"stable" for 93% of these verdicts. Each of them is overturned by a specific set of the same size.
The two estimates answer different questions (typical noise versus worst-case error), and the
census quantifies how far apart the answers are on real detector outputs.

### By ordered pair (base -> +addition)

| Pair | Supported of 150 | Median floor | Median lower bound | Median upper bound | Random never crossed at floor |
|---|---:|---:|---:|---:|---:|
| centerpoint -> +fcos3d | 3 | 1 | 7.6% | 8.9% | 1 |
| centerpoint -> +mapillary | 4 | 5 | 6.2% | 9.8% | 3 |
| centerpoint -> +megvii | 11 | 13 | 5.9% | 7.8% | 11 |
| centerpoint -> +pointpillars | 11 | 10 | 3.5% | 5.9% | 10 |
| fcos3d -> +centerpoint | 86 | 69 | 24.2% | 31.6% | 83 |
| fcos3d -> +mapillary | 86 | 21 | 11.4% | 17.2% | 80 |
| fcos3d -> +megvii | 114 | 65 | 19.7% | 24.8% | 111 |
| fcos3d -> +pointpillars | 99 | 46 | 12.4% | 18.6% | 94 |
| mapillary -> +centerpoint | 61 | 31 | 17.5% | 24.0% | 58 |
| mapillary -> +fcos3d | 63 | 6 | 2.8% | 5.0% | 55 |
| mapillary -> +megvii | 92 | 37 | 14.1% | 18.9% | 87 |
| mapillary -> +pointpillars | 77 | 23 | 9.1% | 13.9% | 71 |
| megvii -> +centerpoint | 16 | 22 | 9.4% | 15.5% | 15 |
| megvii -> +fcos3d | 27 | 5 | 3.3% | 5.6% | 23 |
| megvii -> +mapillary | 15 | 16 | 7.3% | 13.2% | 14 |
| megvii -> +pointpillars | 20 | 18 | 5.0% | 8.2% | 18 |
| pointpillars -> +centerpoint | 69 | 34 | 17.5% | 21.2% | 65 |
| pointpillars -> +fcos3d | 108 | 14 | 6.0% | 8.6% | 97 |
| pointpillars -> +mapillary | 59 | 20 | 10.3% | 16.4% | 53 |
| pointpillars -> +megvii | 104 | 31 | 13.6% | 16.8% | 99 |

Camera-base pairs (FCOS3D, Mapillary) are supported most often and need the largest audits;
lidar-base pairs (CenterPoint, Megvii) are rarely improved by an addition. The three earlier
development cases sit inside these distributions.

### Limits of the census

Units share scenes, objects and detectors; 3,000 is not 3,000 independent experiments. The
detectors are 2019 to 2020 public submissions. The error family is whole-object deletion under
one finite reference world; localization, class and insertion errors are not modeled. Verdicts
are conditional on the retained labels. Upper bounds come from one policy with batch 20 and are
local, not minimal. Nothing here involves a human audit or a physical claim.

## Localization-error census: the same 1,125 verdicts under label position error

Dated 17 September 2026. `localization.py` and `localization_census.py`; aggregates in
`localization-summary.json`. For every supported verdict and every epsilon, the certificate asks
whether any reference in which each label position is within epsilon of the retained one can
overturn the verdict. `robust` is proven under the independent-flip relaxation, so it holds for
real displacements. `insufficient_realized` means an explicit displacement of specific objects,
each within epsilon, has been exhibited that overturns the verdict: a physical counterexample.
`insufficient_relaxed` means the relaxed adversary crosses but no realizing displacement was
found for at least one object: unresolved between geometry and relaxation. `solver_failed`
means an anchor MILP hit its 30 s limit and the unit is reported unresolved, never robust.
When a verdict is not robust, the counterexample-guided audit confirms positions (batch 20, at
most 40 rounds) until it is; the count is the audit cost.

| Position error allowed | Robust, no audit | Physically realized counterexample | Relaxed only | Solver limit | Median positions to measure | Median share of labels | p90 share |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0.1 m | 1077 (95.7%) | 42 | 6 | 0 | 8 | 0.9% | 2.3% |
| 0.25 m | 986 (87.6%) | 97 | 42 | 0 | 20 | 1.8% | 3.8% |
| 0.5 m | 813 (72.3%) | 129 | 183 | 0 | 20 | 2.9% | 6.6% |
| 1.0 m | 491 (43.6%) | 112 | 472 | 50 | 53 | 5.6% | 11.9% |

Every audit that ran restored robustness (573 of 584 at 1 m; 11 hit the time cap). Reading:

1. **42 verdicts on this benchmark split (3.7%) are overturned by moving specific labels less
   than 10 cm**, with the displacement exhibited; 97 (8.6%) by less than 25 cm. nuScenes annotation
   accuracy is not stated to that precision, so these verdicts are not established by the labels.
2. Where a verdict is not robust, robustness is restored by measuring a median of 8 positions
   (10 cm) or 20 positions (25 cm): under 2% of the labels. The certificate names them.
3. At 1 m about half of all supported verdicts depend on label positions; the deletion and
   localization families together give each verdict a two-parameter robustness margin
   (deletions, metres) that the scalar it summarizes does not carry.

Limits: independent-flip relaxation (sound for robust, exhibited for realized, open for relaxed);
planar displacement only; class-preserving; the same 2019 to 2020 submissions and correlated units
as the deletion census; no human measurement occurred.

## Which error family threatens which verdict: insertion monotonicity

Claim. Adding a reference object never decreases `TP_augmented - TP_base`. Hence an inserted
label (a missing object in the reference) cannot overturn a supported verdict, a class error
(delete under one class, insert under another) is at most a deletion, and the deletion family
is the worst case over all presence and class errors for supported verdicts. For excluded
verdicts the mirror holds: deletion cannot rescue them, insertion can.

Proof. Fix the reference graph `G` with detection sets `A` (base) and `C = A + additions`. The
maximum matching size of any detection subset `X` is the rank `r(X)` of the transversal
matroid of `G` on detections. Adding an object `o*` with neighbour set `N` gives the matroid
union of that matroid with the rank-one matroid on `N`, whose rank is

```text
r'(X) = min over Y contained in X of  r(Y) + [Y meets N] + |X minus Y|
```

so `r'(X) - r(X)` is 0 or 1 for every `X`. Suppose `r'(A) = r(A) + 1` and `r'(C) = r(C)`. Take
`Y` attaining the minimum for `C`; then `Y` misses `N` and `r(Y) + |C minus Y| = r(C)`. From
submodularity `r(Y union A) = r(Y) + |A minus Y|` and then
`r(Y intersect A) + |A minus Y| <= r(A)`, while subadditivity gives the reverse inequality, so
`r(Y intersect A) + |A minus Y| = r(A)`. Since `Y intersect A` also misses `N`, the formula
gives `r'(A) <= r(A)`, a contradiction. Therefore `r'(C) - r'(A) >= r(C) - r(A)`.

Check. Exhaustive over every graph with up to 3 base, 2 addition and 3 object vertices and every
neighbourhood of one inserted object: 1,236,958 cases, no decrease. Randomized check in
`test_controls.py`.

## Reproduce

```sh
python -B experiment.py INPUT_DIR PRIVATE_OUT_DIR results.json
```

```sh
python -B census_units.py META_DIR PREDICTIONS_DIR UNIT_DIR --splits nuscenes_splits_devkit.py --range-rule global_xy --gate BEFORE_INPUT.json
python -B census_run.py UNIT_DIR census-results.json --workers 6
python -B census_summary.py census-results.json fable-census-index-0.2.0.json fable-unresolved-closed-0.4.0.json census-summary.json
```

Inputs are the sealed comparison files from the Engine common exchange (`BEFORE_INPUT.json`,
`AFTER_INPUT.json`, `SOURCE_CASE.json`), the first and second case comparison inputs, and for the
census the retained prediction files and nuScenes tables in Reiyah custody. They
contain nuScenes annotation tokens and stay private; their SHA-256 identities are recorded in
`results.json`. Requires `numpy` and `scipy` (`scipy.optimize.milp`). The committed
`results.json` holds aggregate counts and timings only.

## What this does not establish

No human audit occurred. The benchmark labels served as the query oracle, so "confirmed" means
"declared present by the retained labels", and the injected-error control plants absences at
random rather than from any observed error process. Query counts are label counts, not hours.
The public checkpoints are development data with exposed outcomes. Nothing here shows that a
capable team reaches the same decision with less total work; it shows how many declared labels
each policy needs before the deletion-family certificate exists, and which certificate tier
delivers it.
