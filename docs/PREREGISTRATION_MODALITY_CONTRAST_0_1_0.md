# Preregistration: same-modality against cross-modality coincident miss dependence

Document ID: `reiyah.gate-b.prereg.modality-contrast`

Version: `0.1.0`

Lifecycle status: `proposed`, **not preregistered**

## 0. Status, stated first

This document is a **design**. It is not a preregistration until it is frozen by digest before any
analysis under it is executed, and no analysis under it has been authorized. Nothing here may be
cited as a completed preregistration, and no existing Gate B result satisfies it.

## 1. Question

Custody entry S-01 retains a stated, falsifiable mechanism from the primary safety-model text:
camera and lidar are argued to remain approximately independent for **miss** mistakes because
their shared weather causes are argued to produce **different** mistake types, camera missing
objects while lidar produces ghosts.

Primary question: **does the coincident miss-miss dependence coefficient differ between
same-modality channel pairs and cross-modality channel pairs, at matched marginals?**

This is one hypothesis. It is not a safety claim, not a vendor claim, and not a causal claim about
channel construction.

## 2. Leakage, disclosed

Prior Gate B results measured related quantities on overlapping data. This design was written
after seeing them. Specific leakage risks and mitigations:

| Risk | Mitigation |
|---|---|
| Stratification universe chosen because it produced a large prior effect | Universe is fixed to the pre-existing class x range x visibility grid used before this question was asked, and MUST NOT be tuned |
| Detector set chosen for a favourable prior contrast | Pair admission rule is stated in section 5 and enumerated before any new analysis; the prior set is not privileged |
| Operating point chosen post hoc | Full declared grid reported; no single point is primary |
| Equivalence margin chosen to make a null reachable | Margin fixed in section 8 before execution and justified on decision relevance, not on observed spread |
| The prior worst stratum treated as a hypothesis | Prohibited. Worst-group search is a separate family and cannot confirm itself |

Because leakage cannot be fully removed, the **primary contrast may not advance past
`exploratory` on this data**. Advancement requires an independent split or dataset with a
different reference process. This is a design constraint, not a caveat.

## 3. Opportunity universe

An opportunity is `(log_id, object_track_id, keyframe_t)` admitted by a relevance predicate frozen
before any channel output is read.

1. The universe MUST be the unfiltered reference universe. Any filter defined on one modality's
   returns is a **sensitivity arm**, never the primary denominator, because such a filter is a
   function of one channel and induces dependence by construction.
2. Every channel is scored on the identical opportunity set. No per-channel filtering.
3. Membership state is retained per row: `in_universe`, `excluded_by_declared_rule`, `unknown`.
4. Reference-process version and exclusion rules are digest-bound before execution.

## 4. Channel failure and matching

```
M_k(w) = 1        no channel-k output matched to w under the frozen matcher
       = 0        matched
       = unknown  channel k produced no defined output for that frame
```

The matcher and its thresholds are identical across channels and MUST NOT use channel-specific
geometry. A distance gate derived from range-sensor returns is inadmissible because it privileges
one modality.

**Operating-point comparability.** The primary contrast is computed at **matched marginal miss
rate** on a frozen calibration subset disjoint from the analysis set. A declared grid is reported
in full as secondary. No single convenience threshold is primary. CE-4 in
[`estimand_counterexamples.txt`](../evidence/measurement/estimand_counterexamples.txt) shows why:
`c` moved from 1.8186 to 1.2262 by moving one channel's operating point with the coupling
structure untouched.

## 5. Pair admission, fixed before execution

A channel is admissible only if all hold:

1. published prediction bytes with a retained digest, access terms, and redistribution state;
2. its published headline metric reproduced within a declared tolerance before use, with the
   gate recorded and a failing channel excluded and kept excluded;
3. modality declared as `camera_only`, `lidar_only`, `radar_only`, or `fused`, with `fused`
   excluded from the primary contrast because it belongs to neither arm;
4. training-corpus overlap with every other admitted channel recorded where determinable. Shared
   corpus is a **coupling mechanism** and enters as a declared covariate, never as background.

Pairs are enumerated in full before any `c` is computed. Both arms MUST contain at least two
pairs that do not share a channel, otherwise the contrast has no internal replication and the
result is `inconclusive` by construction. The prior work's cross-modality arm shared one channel
across all three pairs; that configuration is inadmissible here.

## 6. Clustering

```
person  >  log or scene  >  object track  >  detection box
```

Primary unit is the **object track**. Box-level statistics are reported only as diagnostics with
their design effect stated. Frame count is never a sample size.

## 7. Multiplicity, two separate families

| Family | Content | Method |
|---|---|---|
| F1 primary | One contrast: same-modality against cross-modality at matched marginals | Single pre-declared test, cluster-robust interval |
| F2 worst group | Search over eligible strata | Bootstrap max-t simultaneous band, critical value reported beside the naive value |

An F2 extremum MUST NOT be promoted into an F1 claim. F1 MUST NOT be re-specified after seeing F2.

Worst-group eligibility, direction, and the exact partition into `sufficient`,
`observed_insufficient`, `unknown` are fixed before ranking. Any `unknown` group makes the overall
worst-group result `unknown`. An `undefined` `c` is never coerced.

## 8. Result states, fixed before execution

| State | Criterion |
|---|---|
| `supported` | F1 interval excludes the null on the primary unit, survives every sensitivity arm, and independently replicates |
| `contradicted` | F1 interval excludes the null in the opposite direction under the same conditions |
| `null` | F1 interval lies entirely inside the pre-declared equivalence margin. Without a declared margin this state is unavailable |
| `inconclusive` | Interval spans the null or the margin, or any sensitivity arm reverses sign, or an arm lacks internal replication |
| `invalid` | A precondition failed: reference integrity, reproduction gate, clustering, unknown contamination |
| `unknown` | Any required operand non-observed |

Equivalence margin is declared in the frozen instance of this document, justified by decision
relevance, and MUST NOT be set from observed spread.

## 9. Sensitivity ladder, all pre-declared

1. operating-point grid in full;
2. unfiltered against modality-filtered universe;
3. both-absent rows removed from the denominator;
4. alternative clustering at log and at person where available;
5. matcher tolerance perturbation;
6. covariate admissibility ladder, with any variable on the measured path excluded as a mediator
   and any mediator result recorded as a trap rather than an estimate.

## 10. Reference-error partial identification, integrated not appended

M4 is executed **inside** this preregistration. No `c` is reported without its identification
state. CE-5 shows a 0.50% reference error moves `c` from 1.0000 to 0.5512 or to 1.3673, which
exceeds most effects of interest.

### 10.1 Mechanisms, bounded separately

`omitted true opportunities`, `false opportunities`, `class error`, `attribute error`,
`localization and pose error`, `track linkage error`, `stratum assignment error`. Each carries its
own budget. A single scalar epsilon is inadmissible.

### 10.2 Assumption ladder

| Level | Assumption | Output |
|---|---|---|
| `L0` | none | Worst case. Report `unbounded` or `undefined` where the feasible set permits it. Never substitute a finite surrogate |
| `L1` | mechanism-specific budgets, no assumption on which cells absorb them | Sharp bounds by optimising the fractional-linear estimand over the feasible cell polytope |
| `L2` | `L1` plus a **bounded-differentiality** restriction, parameterised by a single `delta`, itself probed | Tighter bounds; the restriction is tested, not assumed. Two earlier encodings were refuted, see below |
| `L3` | `L2` plus error rates estimated by blinded reannotation | Tightest. **Only `L3` is eligible for a headline, and only after independent replication** |

Sharpness MUST be proved or numerically verified wherever claimed. The denominator can reach zero
inside the feasible set whenever a marginal budget covers the observed marginal count; that case
yields `undefined`, never a truncated large number.

### 10.2a Proposition M4-1 changes what reannotation must measure

`c` is scale invariant, so a strictly proportional perturbation of the four cells leaves it
exactly unchanged. Proof and numerical check in
[`M4_IDENTIFICATION_FINDINGS.md`](M4_IDENTIFICATION_FINDINGS.md) section 2.

Therefore **uniform reference error does not bias `c` at all**, and every unit of identification
exposure is differential error, error whose rate depends on the cell and so on the channel
outcomes. Two encodings of the `L2` restriction were refuted on these grounds and are retained:
tying the two single-miss cells is **vacuous**, because `c` is monotonically decreasing in both so
every extremum satisfies the tie for free; and proportional perturbation is **null**, because it is
exactly the invariance direction.

The binding formulation perturbs cell `j` at rate `r_j` in `[rbar - delta, rbar + delta]` for a
free common rate `rbar`. On the fixture stratum the set is `[1.0057, 1.1063]` at `delta = 0.02`
and `[0.9620, 1.1547]` at `delta = 0.05`, so **a five percentage point differential error rate is
already enough to leave that stratum's dependence unidentified**.

### 10.3 Blinded reannotation

Annotators see no channel output, no prior label, and no stratum assignment. Sample is stratified
random over the universe. Inter-annotator disagreement and localization uncertainty are retained
as distributions, never collapsed to a point.

**The estimation target is `delta`, not the overall error rate.** Section 10.2a establishes that
the overall rate is irrelevant to this estimand, so a design powered to estimate it would be
powered for the wrong quantity. Sample size is driven by the width of the resulting bound on
`delta`, and the reannotation must be stratified so that a per-cell error rate is estimable at all,
which requires deliberate oversampling of the both-miss cell because it is the rarest and carries
the numerator.

### 10.4 Reporting

Identification bounds and clustered sampling uncertainty are reported as an **outer interval
containing an inner interval**. They are never combined into one number and never summarized as a
single figure.

### 10.5 Known-bad cases required before any bound is trusted

1. coordinated label error that inflates `c` on a stratum while leaving marginals unchanged;
2. channel-dependent reference contamination, where the reference process was built using one
   channel's outputs;
3. a stratum where the marginal budget drives the denominator to zero;
4. a synthetic witness that must not escape into any production or evidence path.

## 11. What this design does not do

It does not measure ghost-ghost dependence, which Corollary 3 also requires. It does not measure
safety-critic mistakes, only detection misses. It does not support any evidence-budget figure. It
does not support a causal statement about channel construction, because it is observational. It
creates no operator acceptance, no scientific support, and no vendor comparison.
