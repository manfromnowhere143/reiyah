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
| Forty-frame | **372** (Engine: 372-label construction plus matching necessary bound, main `0d6f116`; this lane had bounded it to [306, 373]) | superseded | superseded | see note |

For the forty-frame case this lane's interval [306, 373] (pool cut below, shrunk certified set above)
is superseded by the Engine's exact result of 372 for the unrestricted-deletion, confirmed-present
count problem. That is a count of labels to confirm, not a minimum adaptive query policy and not a
measured human effort.

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
   on the forty-frame case (exactly 372 of 2,299 by the Engine's certificate). Robustness of that
   verdict to reference deletion costs 16% of the labels, whatever policy is used.
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
| fcos3d -> +megvii (interval [8,458, 8,481]) | 114 | 65 | 19.7% | 24.8% | 111 |
| fcos3d -> +pointpillars (interval [4,879, 4,902]) | 99 | 46 | 12.4% | 18.6% | 94 |
| mapillary -> +centerpoint | 61 | 31 | 17.5% | 24.0% | 58 |
| mapillary -> +fcos3d | 63 | 6 | 2.8% | 5.0% | 55 |
| mapillary -> +megvii | 92 | 37 | 14.1% | 18.9% | 87 |
| mapillary -> +pointpillars | 77 | 23 | 9.1% | 13.9% | 71 |
| megvii -> +centerpoint | 16 | 22 | 9.4% | 15.5% | 15 |
| megvii -> +fcos3d | 27 | 5 | 3.3% | 5.6% | 23 |
| megvii -> +mapillary | 15 | 16 | 7.3% | 13.2% | 14 |
| megvii -> +pointpillars | 20 | 18 | 5.0% | 8.2% | 18 |
| pointpillars -> +centerpoint | 69 | 34 | 17.5% | 21.2% | 65 |
| pointpillars -> +fcos3d (interval [1,728, 1,733]) | 108 | 14 | 6.0% | 8.6% | 97 |
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

## Localization-error census: the same 1,125 verdicts under label position error (contract 0.2.0)

Dated 17 September 2026, recomputed under `localization.py` 0.2.0 after the Engine's review
found two defects in 0.1.0 (both reproduced on the Engine's retained controls before the repair,
see `private/controls/`): a present edge at exactly the inner boundary was treated as fixed, and a
confirmed position froze all edges regardless of measurement error. 0.2.0 uses exact rationals
from the source decimals, closed balls with `guaranteed iff e < R and s < (R - e)^2` and
`possible iff s < (R + e)^2`, and carries a returned centre and residual radius for every
confirmed position. The residual-case witness this lane produces, shift (13/250, -21/250), is
verified by the Engine's `localization` command as `refuted_by_displacement`.

`robust` is proven under the independent-flip relaxation and therefore holds for real
displacements. `insufficient_realized` means a displacement of specific objects, each within
epsilon, has been exhibited (vectors retained privately; Engine verification in
`engine-localization-exchange.json`: 375 of 376 exhibited counterexamples are accepted by the Engine's
`localization` command as `refuted_by_displacement`; the one exception hit the Engine's work limit). `insufficient_relaxed` means the relaxed adversary crosses
but the grid search found no realizing displacement for at least one object: unresolved, never
infeasible. `solver_failed` means an anchor MILP hit its 30 s limit: unresolved, never robust.

| Position error allowed | Robust, no audit | Exhibited geometric counterexample | Relaxed only | Solver limit | Median positions to certify (exact-adjacency oracle) | Median share of labels | p90 share |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0.1 m | 1077 (95.7%) | 44 | 4 | 0 | 8 | 0.9% | 2.3% |
| 0.25 m | 986 (87.6%) | 97 | 42 | 0 | 20 | 1.8% | 3.8% |
| 0.5 m | 813 (72.3%) | 128 | 184 | 0 | 20 | 2.9% | 6.3% |
| 1.0 m | 495 (44.0%) | 107 | 480 | 43 | 48 | 5.6% | 11.8% |

The audit column uses the declared exact-adjacency oracle (returned centre = retained centre,
residual radius 0). With a residual radius of half the perturbation (a 5 cm measurement against a
10 cm question), the same guided audit certifies only 22 of 48 cases at 10 cm, 83 of 139 at 25 cm,
173 of 312 at 50 cm and 273 of 566 at 1 m within its 40-round budget: a label measured to within
its residual of the 2 m boundary stays uncertain however many other labels are measured.
Certification depends on measurement precision at the boundary, not on the number of queries.

Reading: 44 verdicts on this split are overturned by exhibited displacements of specific labels
under 10 cm; 97 under 25 cm. Where a verdict is not robust and answers are exact, a median of 8
(10 cm) or 20 (25 cm) measured positions restores it. Limits: independent-flip relaxation (sound
for robust, exhibited for realized, open for relaxed); planar, class-preserving displacement; the
same submissions and correlated units as the deletion census; no physical measurement occurred.

## Split-level verdicts: the leaderboard margin

Dated 17 September 2026. `split_level.py`; aggregates in `split-level.json`. The pair verdict on
the whole validation split is the equal-weight mean of the 150 scene decisions under the same
criterion. The deletion adversary spends deletions anywhere on the split. Two bounds are computed and kept
apart: a universal lower bound (any deletion removes at most one gain unit, and a scene cannot lose
more units than its gain, so take the largest possible weighted steps first), and an attained upper
bound (a witness built from the additive pools, which is a convenient subset of the possible
steps). The minimum is exact when the two coincide. The Engine's independent weighted composition
(main `b41963e`) gives the same nine results: six exact minima and three intervals. The position adversary's per-scene maxima add across all 150 scenes,
excluded scenes included (their gain can still be lowered). A split-level position result is
proven when the summed maxima stay below the margin; when they cross it is reported as not proven,
because realization was checked per scene, not for the summed pattern.

| Pair (base -> +addition) | Split delta | Scenes supported | Deletions to overturn: attained witness (share of 148,441 labels); exact unless an interval is given | Robust at 10 cm / 25 cm / 50 cm / 1 m | Largest proven epsilon |
|---|---:|---:|---:|---|---|
| centerpoint -> +fcos3d | -0.731 | 3 | excluded | | |
| centerpoint -> +mapillary | -2.082 | 4 | excluded | | |
| centerpoint -> +megvii | -1.209 | 11 | excluded | | |
| centerpoint -> +pointpillars | -1.332 | 11 | excluded | | |
| fcos3d -> +centerpoint | 1.800 | 86 | **4,972** (3.35%) | yes / yes / yes / no | 0.50 m |
| fcos3d -> +mapillary | 0.927 | 86 | **2,420** (1.63%) | yes / yes / no / no | 0.25 m |
| fcos3d -> +megvii (interval [8,458, 8,481]) | 2.970 | 114 | **8,481** (5.71%) | yes / yes / yes / yes | 1.00 m |
| fcos3d -> +pointpillars (interval [4,879, 4,902]) | 1.764 | 99 | **4,902** (3.30%) | yes / yes / yes / yes | 1.00 m |
| mapillary -> +centerpoint | -0.471 | 61 | excluded | | |
| mapillary -> +fcos3d | 0.056 | 63 | excluded | | |
| mapillary -> +megvii | 0.981 | 92 | **2,577** (1.74%) | yes / yes / no / no | 0.25 m |
| mapillary -> +pointpillars | 0.431 | 77 | **968** (0.65%) | yes / yes / no / no | 0.25 m |
| megvii -> +centerpoint | -2.058 | 16 | excluded | | |
| megvii -> +fcos3d | -0.377 | 27 | excluded | | |
| megvii -> +mapillary | -1.476 | 15 | excluded | | |
| megvii -> +pointpillars | -1.081 | 20 | excluded | | |
| pointpillars -> +centerpoint | 0.068 | 69 | excluded | | |
| pointpillars -> +fcos3d (interval [1,728, 1,733]) | 0.690 | 108 | **1,733** (1.17%) | yes / yes / yes / no | 0.50 m |
| pointpillars -> +mapillary | 0.189 | 59 | **260** (0.18%) | no / no / no / no | none proven |
| pointpillars -> +megvii | 1.167 | 104 | **3,120** (2.10%) | yes / yes / yes / no | 0.50 m |

Nine of twenty ordered pairs are supported on the split. Their attained margins differ by a factor
of 30 in labels (260 to 8,481) and from none proven to 1 m in position. This is a conditional loss
aggregate under the declared contract, not an official nuScenes leaderboard metric. "Adding Mapillary to
PointPillars helps" holds on 59 scenes and on the split, and is overturned by 260 deletions
(0.18% of labels); its position robustness is not proven even at 10 cm. "Adding Megvii to FCOS3D
helps" survives 8,481 deletions and 1 m of position error. A leaderboard that printed these two
verdicts as two metric differences would show no such distinction.

## Cross-implementation agreement with the Engine

Dated 17 September 2026. `engine_agreement.py`; result in `engine-agreement.json`. Every rebuilt
unit was converted to a strict-schema Engine input (coordinates and classes stripped; detection
record digests are row-canonical, not the Engine's byte-span digests) and run through the
Engine's producer and its separate certificate checker as exported from main at
`e23bfe49f2a42433f7aad4170578db504427508c`.

| Outcome | Units |
|---|---:|
| Engine exact enclosure equals this package's decision, criterion equal | 2,981 |
| Engine resource limit (2,000,000 estimated work units) reached; sound count bound returned as unresolved | 19 |
| Of those 19, this package's exact value lies inside the Engine's bound | 19 of 19 |
| Disagreements | 0 |

The split-level witness for the most fragile pair was also applied through the Engine: deleting
the 260 named labels across the split moves "PointPillars + Mapillary" from 180911/959400
(0.1886) to 31877/319800 (0.0997), at or below the tolerance, as computed by the Engine kernel
and accepted by its checker. The Engine's matcher, this package's Hopcroft-Karp and the MILP
adversary are three separate implementations that share only the parsed graph.

## Cost to a checked decision: the frozen experiment

Dated 17 September 2026. Plan frozen before any outcome in `PLAN_COST_EXPERIMENT.json`
(SHA-256 `262128744a50e5fea0b5f089ef4cb76070f31fa0069aae6b8afdecfda6be83b9`); results in `cost-experiment.json`. Fifteen cases: the three
development cases and twelve census units chosen by digest order (exposed development data,
correlated units, not held out). Every selector uses the same checker (solver-tier certificate),
the same batch of 10, the same declared oracle (retained labels; localization answers carry a
residual radius of 0 or 0.25 m), a cheap sound proof tried and charged before every solver call,
and a cap of 200 rounds. Queries are counted until the first checked decision; a run that does not
certify within budget is `not certified`, never a win.

### Deletion family: queries to a sufficiency certificate

| Case | random | degree | addition-adjacent | influence | counterexample-guided | hitting set online | strongest conventional |
|---|---:|---:|---:|---:|---:|---:|---:|
| first | 100 | 90 | 20 | 50 | 15 | 10 | 20 |
| second | 730 | 560 | 330 | 80 | 66 | 55 | 80 |
| forty | 2000 | 1660 | 480 | 1170 | 530 | 200 (budget exhausted) | 480 |
| fcos3d__centerpoint__scene-0638 | 690 | 530 | 290 | 290 | 290 | 200 (budget exhausted) | 290 |
| fcos3d__centerpoint__scene-0782 | 770 | 550 | 230 | 230 | 230 | 200 (budget exhausted) | 230 |
| fcos3d__mapillary__scene-0636 | 460 | 280 | 130 | 120 | 120 | 116 | 120 |
| fcos3d__megvii__scene-0269 | 450 | 460 | 240 | 160 | 340 | 90 | 160 |
| fcos3d__megvii__scene-0554 | 650 | 450 | 230 | 190 | 280 | 183 | 190 |
| fcos3d__megvii__scene-0802 | 320 | 160 | 80 | 80 | 80 | 71 | 80 |
| fcos3d__pointpillars__scene-0557 | 500 | 250 | 120 | 100 | 110 | 99 | 100 |
| fcos3d__pointpillars__scene-0636 | 450 | 290 | 140 | 130 | 130 | 128 | 130 |
| fcos3d__pointpillars__scene-0910 | 930 | 480 | 200 | 170 | 190 | 167 | 170 |
| mapillary__megvii__scene-0915 | 930 | 710 | 190 | 180 | 190 | 178 | 180 |
| pointpillars__mapillary__scene-0928 | 1176 | 750 | 160 | 1030 | 271 | 118 | 160 |
| pointpillars__mapillary__scene-0963 | 500 | 420 | 230 | 280 | 280 | 178 | 230 |

Against the strongest conventional selector on each case: **hitting set online wins 12 of 12
certified cases and fails to certify 3 within 200 rounds** (it adds about one label per round
and needs more rounds on the largest cases); counterexample-guided wins 2, draws 5, loses 8.
Computation is the price: hitting set online spent 395.4 s in the solver and 46.6 s in selection over
the 15 cases against 65.9 s and 0.2 s for the addition-adjacent heuristic. Fewer queries, three to
six times the computation; the plan asked for the tradeoff and this is it.

### Localization family, 0.5 m: queries to a robustness certificate

Ten of the thirteen cases with coordinates are robust at 0.5 m with no query under every
selector (draws). The two that need queries:

| Case | residual radius (m) | random | boundary-first | counterexample-guided | hitting set online |
|---|---|---:|---:|---:|---:|
| fcos3d__mapillary__scene-0636 | 0 | 190 | 20 | 20 | 9 |
| fcos3d__mapillary__scene-0636 | 1/4 | 360 | 50 | 20 | 17 |
| pointpillars__mapillary__scene-0928 | 0 | 1160 | 290 | 109 | 69 |
| pointpillars__mapillary__scene-0928 | 1/4 | 1176 (budget exhausted) | 317 (no candidates) | 112 (no candidates) | 100 (no candidates) |

With a 0.25 m residual against a 0.5 m question, no selector can certify the fragile case: the
measured labels near the 2 m boundary remain uncertain. That is the precision limit, not a
selection failure, and it is reported as `not certified`.

### What this establishes and what it does not

The exact machinery pays for itself as a **stopping rule** everywhere (no selector can stop
without it) and as a **selector** only in the hitting-set form, at a computation cost. On the
localization side most verdicts need no audit at 0.5 m; where they do, the guided and hitting-set
selectors beat boundary-first by 3 to 4 times on the fragile case. Nothing here is a human-time or
money saving, and the fifteen cases are not independent.

## Reuse of obtained observations on a distinct comparison

Dated 17 September 2026. `reuse_experiment.py`; results in `reuse-experiment.json`. Twenty pairs
of supported units sharing the base detector and the scene, with a different addition detector
(chosen deterministically by digest order). The first comparison is audited with the
counterexample-guided selector (batch 10, exact-adjacency oracle for deletion; 0.25 m residual for
localization at 0.5 m). Every observation actually obtained is checked for applicability to the
second comparison record by record (same reference object present in the second unit), then the
second comparison is audited fresh and again starting from the applicable observations.

| First comparison (base / addition, scene) | Second addition | First-run queries | Applicable to second | Second fresh | Second warm |
|---|---|---:|---:|---:|---:|
| mapillary / megvii / scene-0635 | centerpoint | 530 | 530 | 510 | 120 |
| fcos3d / pointpillars / scene-0910 | mapillary | 190 | 190 | 220 | 100 |
| mapillary / megvii / scene-0915 | centerpoint | 190 | 190 | 250 | 70 |
| fcos3d / megvii / scene-0554 | mapillary | 280 | 280 | 300 | 160 |
| mapillary / pointpillars / scene-0969 | centerpoint | 300 | 300 | 450 | 210 |
| fcos3d / megvii / scene-0269 | mapillary | 340 | 340 | 270 | 50 |
| fcos3d / pointpillars / scene-0557 | megvii | 110 | 110 | 150 | 70 |
| pointpillars / mapillary / scene-0963 | centerpoint | 280 | 280 | 200 | 90 |
| fcos3d / mapillary / scene-0636 | pointpillars | 120 | 120 | 130 | 70 |
| fcos3d / centerpoint / scene-0344 | pointpillars | 760 | 760 | 540 | 70 |
| fcos3d / centerpoint / scene-0782 | megvii | 230 | 230 | 220 | 40 |
| pointpillars / mapillary / scene-0928 | centerpoint | 271 | 271 | 400 | 160 |
| fcos3d / mapillary / scene-0522 | centerpoint | 370 | 370 | 600 | 280 |
| fcos3d / centerpoint / scene-0638 | pointpillars | 290 | 290 | 150 | 0 |
| fcos3d / megvii / scene-0802 | centerpoint | 80 | 80 | 150 | 80 |
| pointpillars / fcos3d / scene-0966 | centerpoint | 240 | 240 | 640 | 440 |
| pointpillars / centerpoint / scene-0782 | megvii | 190 | 190 | 190 | 40 |
| mapillary / fcos3d / scene-1062 | pointpillars | 39 | 39 | 50 | 30 |
| mapillary / fcos3d / scene-0104 | centerpoint | 100 | 100 | 329 | 239 |
| pointpillars / centerpoint / scene-0273 | megvii | 220 | 220 | 190 | 10 |

Totals over the twenty pairs, deletion family: first plus second fresh 11069 queries; first plus
second warm 7459; the second comparison needed 2329 queries with reuse against 5939 without
(**39% of fresh**). Confirmed presence is a fact about the reference, so it carries across the
change of the added detector; what changes is which of those facts the new verdict depends on.
Localization at 0.5 m: fourteen of twenty second comparisons needed no query either way; reuse
saved 35 of 265 second-run queries overall, and three second comparisons could not be certified
under the 0.25 m residual (precision limit, as in the cost experiment).

Scope: the comparison contract is preserved-base additions, so this measures reuse when the
added detector changes with the base held fixed. It is not a measurement under A-to-B replacement
of the base, and it is not witness overlap or a changed loss coefficient; it counts actual queries
under the same checked stopping rule.

## Solver-free certificates: robustness anyone can check

Dated 17 September 2026. `dual_certificate.py`, `verify_dual_certificate.py`. Every `robust`
and `sufficient` above rests on a mixed-integer solver having found the true optimum of the
adversary program (the "solver tier"). A fourth tier removes that trust. Both adversaries are
programs `minimise c^T x` subject to `lo <= A x <= hi`, `0 <= x <= 1`, some `x` integer. For any
rational multipliers `y_lo >= 0`, `y_hi >= 0`, every feasible `x`, integer or not, satisfies

```text
c^T x >= y_lo^T lo - y_hi^T hi + sum_j min(0, r_j),    r = c - A^T (y_lo - y_hi)
```

(Neumaier and Shcherbina, 2004). The multipliers are taken from the LP relaxation's dual,
converted to rationals, and the bound is evaluated exactly; since the objective is an integer
gain it rounds up. A certificate is the multiplier vector per anchor. The checker
`verify_dual_certificate.py` rebuilds the program from the unit geometry and the declared rules,
evaluates the inequality with exact arithmetic, and never runs a solver. What it shares with the
producer is the program construction; the rest is arithmetic.

| Case and claim | Sound tier | Dual tier (certificate) | Solver tier |
|---|---:|---:|---:|
| Forty-frame verdict, position error 0.1 m (margin 49/20) | 39/4 unresolved | **3/20 robust** | 3/20 robust |
| Forty-frame verdict, 0.25 m | 73/4 unresolved | **9/20 robust** | 9/20 robust |
| Forty-frame verdict, 0.5 m | 99/5 unresolved | **21/10 robust** | 37/20 robust |
| Forty-frame verdict, 1 m | 417/20 unresolved | 33/4 unresolved | 101/20 crosses |

The 0.5 m robustness of the forty-frame verdict, which the Engine's conventional bound leaves
unresolved and which was solver-tier only until now, is certified by
`forty-frame-dual-certificate-0.5m.json` (40 anchor certificates, no annotation identities):

```sh
python -B verify_dual_certificate.py UNIT_JSON forty-frame-dual-certificate-0.5m.json
# delta 51/20 margin 49/20 certified max drop 21/10
# robust certified
```

For the deletion program the LP relaxation is half-integral (a vertex-cover relaxation) and the
dual bound is far too loose to certify anything: 14 against a margin of 9/10 on the first case.
Deletion sufficiency therefore stays solver-tier; the honest route to a checkable deletion
certificate is the Engine's combinatorial construction (its 372-label proof), not LP duality.

Tests: the dual bound never exceeds the exact optimum on random geometries, and a forged
multiplier can only weaken a bound, never strengthen it; negative multipliers are refused.

### The certificate tier across the census

`dual_census.py`; aggregates in `dual-summary.json`. For every supported verdict and epsilon, the
solver-free bound was evaluated alongside the solver tier.

| Position error | Solver-tier robust | Certified solver-free (share) | Solver-robust but not certified | Certified where the solver tier was unresolved |
|---|---:|---:|---:|---:|
| 0.1 m | 1077 | **1077** (100.0%) | 0 | 0 |
| 0.25 m | 986 | **980** (99.4%) | 6 | 0 |
| 0.5 m | 813 | **784** (96.4%) | 29 | 0 |
| 1.0 m | 495 | **415** (83.8%) | 80 | 17 |

At 1 m the LP dual certifies 17 verdicts whose mixed-integer solve hit its 30 s limit: the
relaxation is polynomial, terminates, and its multipliers are a proof. Where the dual tier does
not certify, the verdict keeps its solver-tier status and the gap is the integrality gap of the
flip program on that unit.

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
