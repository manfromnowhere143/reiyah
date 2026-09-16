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

## Reproduce

```sh
python -B experiment.py INPUT_DIR PRIVATE_OUT_DIR results.json
```

Inputs are the sealed comparison files from the Engine common exchange (`BEFORE_INPUT.json`,
`AFTER_INPUT.json`, `SOURCE_CASE.json`) and the first and second case comparison inputs. They
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
