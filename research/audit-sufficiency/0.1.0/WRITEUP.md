# Exact robustness certificates for detection-benchmark verdicts under reference error

Document ID: `reiyah.research.audit-sufficiency.writeup`. Version: `0.1.0`.
Lifecycle status: `exploratory` (draft for internal review; no external submission).
Dated 17 September 2026. Every number below binds to `results.json`, `census-summary.json` or
`localization-summary.json` in this directory at the commit that carries this file.

## Abstract

A benchmark verdict of the form "adding detector B to detector A improves the declared loss" is
conditional on the reference labels. We give exact, adversarial certificates of how much
reference error such a verdict survives, for two error families: deletion of labels (a label
that should not exist) and displacement of labels (a label in the wrong place). For each
supported verdict the certificate yields the exact number of deletions that overturn it, a proven
lower and a certified upper bound on the audit that makes it robust to any deletion, and the
largest label position error under which it holds. On 1,125 supported verdicts over 20 ordered
pairs of five public nuScenes validation submissions and all 150 validation scenes, every verdict
is overturned by a set of deletions of median size 27 (2.4% of labels); random deletion of the
same size overturns none of them in 200 trials for 93% of verdicts; 95.7% survive any 10 cm
displacement, and 42 are overturned by exhibited displacements under 10 cm. A monotonicity
theorem shows that inserted and misclassified labels cannot overturn a supported verdict beyond
what deletion can, so the two families are the complete worst case over presence, class and
position errors. No human audit occurred; all claims are conditional on the retained labels and
the declared loss.

## 1. The object

Fix a comparison contract: detection outputs A (base) and C = A plus retained additions from a
second detector, a reference world of labelled objects, maximum same-class one-to-one matching
under a strict 2 m centre rule, unit false-negative and false-positive penalties, equal frame
weights within a scene, and a strict-improvement criterion at tolerance 1/10. The paired
difference per frame is

```text
delta = (a + b) * (TP_C - TP_A) - b * r
```

with r the number of additions, so the reference enters only through gain = TP_C - TP_A. A
verdict is `supported` when the weighted difference exceeds the tolerance. Everything here is
exact rational arithmetic on bipartite graphs; matchings are certified by Konig covers.

## 2. Questions answered

1. Deletion. What is the smallest set of labels whose removal overturns the verdict, and after
   confirming which labels can no adversarial deletion overturn it (a sufficient audit)?
2. Localization. For which epsilon does the verdict hold for every reference in which each label
   is within epsilon of its retained position, and which positions must be measured otherwise?
3. Which error families can overturn which verdicts at all?

## 3. Method

Adversary as a single mixed-integer program. Per anchor, the adversary chooses deletions (or
boundary-edge flips) to minimise gain. Maximum matching in the augmented graph equals a minimum
vertex cover (Konig), and the negative of the base maximum matching is the minimum of minus a
matching, so the bilevel problem collapses to one minimisation with binary edit variables, binary
cover variables and matching variables. HiGHS solves each anchor; the adversary's set is always
recomputed exactly, and the claim that nothing larger exists is the only thing resting on the
solver. A rational bound without a solver is reported alongside and never merged.

Sufficient audit. A confirmed set is sufficient when it intersects every adverse deletion set.
The minimum such set is computed by implicit hitting set (Moreno-Centeno and Karp): alternate a
minimum hitting set of the adverse sets found so far (each size is a proven lower bound) with a
certificate of the candidate; when the certificate holds, the candidate is optimal. A cardinality
cut from the additive pool (below) is added as an exact constraint.

Additive pool. Carriers with no base edge, each of whose deletion removes one gain unit, form a
pool whose deletions are exactly additive (alternating-path argument in README). If deleting k of
them crosses, every sufficient set contains all but k - 1 of them; and if the pool has at least
`floor` members, an exact overturning set of exactly `floor` deletions exists.

Localization. Under displacement at most epsilon, only same-class edges with centre distance in
(2 - epsilon, 2 + epsilon) can change. Flips are treated as independent in the program, a
relaxation that is sound for the robustness claim; a counterexample is reported as physical only
when an explicit displacement within epsilon realises its edge pattern object by object.

## 4. Theorem: insertion monotonicity

Adding a reference object never decreases TP_C - TP_A. Proof: the maximum matching sizes of
detection subsets form the rank function of a transversal matroid; adding an object is the
matroid union with a rank-one matroid, whose rank formula is
`r'(X) = min over Y in X of r(Y) + [Y meets N] + |X minus Y|`. If the rank of A rises while the
rank of C does not, the minimiser for C, intersected with A, certifies by submodularity that the
rank of A did not rise. Checked exhaustively on 1,236,958 small graphs. Consequences: inserted
labels and class errors (a deletion under one class plus an insertion under another) cannot
overturn a supported verdict beyond deletion; insertion is what threatens an excluded verdict.

## 5. Data

Reiyah custody only: five public nuScenes validation submissions (CenterPoint, FCOS3D,
Mapillary/MonoDIS, Megvii/CBGS, PointPillars), the v1.0-trainval tables, the devkit validation
split. Units are the research lane's frozen scale-study census: 20 ordered pairs times 150
scenes, rebuilt under the protocol semantics with an exact gate against a sealed case (2,299
objects and 2,803 edges identical). Reconciliation with the retained census index: supported or
excluded status equal on 2,998 of 3,000 units; all count differences are single annotations
within centimetres of the 50 m range boundary, and the index's generating driver was not
committed, so the residual is reported as found.

## 6. Results

### 6.1 Deletion (1,125 supported verdicts)

| Quantity | p10 | median | p90 |
|---|---:|---:|---:|
| Deletions that overturn the verdict (exact set exists in all 1,125) | 3 | 27 | 106 |
| Share of labels | 0.4% | 2.4% | 7.5% |
| Proven lower bound on a sufficient audit, share of labels | 3.5% | 11.5% | 23.1% |
| Certified upper bound on a sufficient audit, share of labels | 6.8% | 17.7% | 29.5% |

In every supported unit the additive pool meets the floor, so the minimum equals the floor by
construction; the research lane's empirical census result is thereby proven per unit.

Exact minimum sufficient audits on the three development cases: 9 of 106 labels, 53 of 737, and
an interval of 306 to 373 of 2,299 (lower bound from the pool cut, upper bound an
inclusion-minimal certified set; the implicit hitting set did not close it in 400 iterations).

### 6.2 Exact adversary versus random label noise

| Random deletions of size | Verdicts never overturned in 200 random trials | Mean random overturn rate | Exact overturning set exists |
|---|---:|---:|---|
| floor | 1,048 of 1,125 (93.2%) | 0.35% | all 1,125 |
| 2 x floor | 930 of 1,125 (82.7%) | 1.45% | all 1,125 |

A robustness estimate from random label perturbation reports "stable" at the exact overturning
size for 93% of verdicts. The two estimates answer different questions (typical versus worst
case); the census measures their distance on real outputs.

### 6.3 Localization (the same 1,125 verdicts)

| Position error allowed | Robust, no audit | Physically realised counterexample | Relaxed only | Solver limit | Median positions to measure to restore robustness |
|---|---:|---:|---:|---:|---:|
| 10 cm | 1,077 (95.7%) | 42 | 6 | 0 | 8 (0.9% of labels) |
| 25 cm | 986 (87.6%) | 97 | 42 | 0 | 20 (1.8%) |
| 50 cm | 813 (72.3%) | 129 | 183 | 0 | 20 (2.9%) |
| 1 m | 491 (43.6%) | 112 | 472 | 50 | 53 (5.6%) |

Every audit that ran restored robustness. Solver limit hits are reported unresolved.

### 6.4 The two families agree on which verdicts are fragile

Verdicts with an exhibited counterexample under 10 cm have median deletion floor 2 and median
margin 0.175; robust verdicts have median floor 28 and margin 1.51. 851 of 1,125 verdicts (75.6%)
are robust to both 25 cm of position error and any 9 deletions. Fragility is a property of the
verdict's margin, not of the family; what the certificate adds is which labels carry it.

### 6.5 Selection policies and what the certificate is for

On the 2,299-label case, queries to a deletion-sufficiency certificate: random 1,960 to 2,020;
degree first 1,660; single-deletion influence first 1,170; naive counterexample-guided 530;
"objects adjacent to an addition first" 480; inclusion-minimal shrink 373; proven lower bound
306. On the smaller cases the guided policy is best and within 4 and 12 labels of the exact
optimum. Selection quality is case-dependent; the certificate and its stopping rule are what make
any of these counts meaningful. For localization the guided policy needed 190 positions against
890 for the boundary-first heuristic on the same case.

## 7. Relation to prior work

Label errors destabilise benchmark rankings (Northcutt et al., 2021) was shown by simulation;
this work gives the exact adversarial counterpart with certificates and measures the gap between
the two on a benchmark split. Data-dropping sensitivity (AMIP, Broderick et al.) and its known
approximation failures are the statistical analogue of the deletion witness; here the object is
combinatorial and exact, and the audit question (a hitting set, dual to the witness) is answered
rather than approximated. Formal explanations and adversarial examples are related by hitting-set
duality (Ignatiev et al., 2019); the implicit hitting set method is theirs and Moreno-Centeno and
Karp's. Noise-aware detector evaluation (Llerena et al., WACV 2025) adjusts metrics for expected
box noise; this work certifies verdicts against worst-case noise instead. None of these validate
the present results; they locate them.

## 8. Limits

Units share scenes, objects and detectors and are not independent experiments. The submissions
are 2019 to 2020 public entries. Verdicts are conditional on retained labels and the declared
loss; nothing here is a physical claim or a human audit. Solver optimality rests on HiGHS; the
sound tier is reported separately and is loose. The localization family uses planar,
class-preserving displacement and an independent-flip relaxation; the `relaxed only` rows are
open. Upper bounds on audits are from one policy and are local. The comparison contract is
addition of retained detections, not replacement of one detector by another; extension to
replacement keeps the identity but needs its own contract.

## 9. Reproduce

`README.md` gives the commands. Inputs carry nuScenes annotation tokens and stay private; their
SHA-256 identities are recorded. Everything runs offline on one machine: the deletion census in
46 minutes on six cores, the localization census in about 40 minutes with a 30 s solver limit per
anchor.
