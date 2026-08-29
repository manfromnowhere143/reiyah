# Result I: redundancy is weakest on the near, clearly visible car

Document ID: `reiyah.result-i-worst-group-dependence`

Version: `0.1.0`

Lifecycle status: `proposed`

## The question nobody asked

Result E reports a pooled conditional lift of 1.156 at score `>= 0.3`. A 15.6% excess
over independence sounds like a rounding error in a redundancy argument.

Pooling is what `docs/SCIENTIFIC_CHARTER.md` section 9.7 forbids as a final answer:
every eligible group's denominator, uncertainty and validity must be reported, and no
group may be dropped so that a different group becomes the reported worst. A pooled
1.156 is equally consistent with near-independence everywhere and with severe
dependence in one operating region. For a redundancy argument only the second matters.

This is the first execution of the Reiyah worst-group contract on measured data rather
than on a fixture.

## Declared before inspection

| Item | Declaration |
|---|---|
| Direction | Larger lift is worse. Redundancy buys least where channels fail together most. |
| Estimand | Within-stratum lift `c_s = a_s n_s / ((a_s + b_s)(a_s + c_s))`, the quantity Result E pools. |
| Universe | Class x range band x annotated visibility, the identical stratification Result E uses. |
| Eligibility | `n_s >= 30`, expected joint misses `>= 5`, and a finite simultaneous interval. |
| Uncertainty | Instance-clustered multinomial bootstrap, 2,000 replicates, seed `20260828`, because Audit 1 measured a design effect of 5.02 at the box unit. |
| Multiplicity | Bootstrap max-t simultaneous band across all eligible strata. |

The eligibility criteria were fixed before any stratum was ranked. A stratum failing one
with every operand observed is `insufficient`, stays visible, and is barred from the
extremum. A stratum with a non-observed operand is `unknown` and would make the overall
result unknown.

## The partition

| Class | Strata | Boxes |
|---|---|---|
| Sufficient | 120 | 133,807 |
| Observed-insufficient | 12 | 758 |
| Unknown | 0 | 0 |
| Universe | 132 | 134,565 |

The unknown set is empty, so the overall worst-group result is identified. The
multiplicity penalty is real: the bootstrap max-t critical value across 120 eligible
strata is 5.069, making every simultaneous interval 2.59x wider than a naive 1.96.

## The result

| Quantity | Value |
|---|---|
| Pooled conditional lift, Result E | 1.156 |
| Worst eligible group | `car`, 0-20 m, visibility `v80-100` |
| Worst group lift | **6.946**, simultaneous 95% [2.221, 11.671] |
| Worst group size | 12,890 boxes |
| Ties at the extremum | 1 |
| Aggregate-to-worst gap | +5.790 |

The worst group is not an exotic corner. It is the nearby, unoccluded car: the single
most common and most safety-critical object in the split, and the case a redundancy
argument is least likely to interrogate.

The four next-worst strata are also cars at short and medium range, then barriers, then
buses. The least dependent eligible strata sit at or below independence: `truck, 0-20 m,
v80-100` at 0.635 and `trailer, 0-20 m, v80-100` at 0.838.

## The arithmetic, in the open

| Cell | Count |
|---|---|
| Both miss | 178 |
| Camera miss only | 1,032 |
| Lidar miss only | 95 |
| Neither misses | 11,585 |
| Camera miss rate | 0.0939 |
| Lidar miss rate | 0.0212 |
| Expected joint if independent | 25.6 |
| Observed joint | 178 |

Both channels are individually strong here. That is the point. When they do fail on a
near, clearly visible car, they fail **together** about seven times more often than
independence predicts.

## Four attacks, all survived

Transcript: [`audit_result_i_robustness.txt`](../evidence/measurement/audit_result_i_robustness.txt).

1. **Small-denominator instability.** Expected joint is 25.6, comfortably above the
   declared floor of 5. The ratio is not a small number over a smaller one.
2. **Absence artifact.** Only 7 of the 178 joint misses, 3.9%, are rows where both
   detectors emitted nothing. Removing every both-absent row from the denominator gives
   a lift of 6.884 and the stratum still ranks first of 132.
3. **Concentration in a few keyframes.** The joint misses span 177 distinct samples; the
   largest single sample carries 1.12%. Re-bootstrapping clustered on sample instead of
   instance gives a pointwise 95% of [6.338, 7.585].
4. **Operating-point coincidence.** The stratum ranks first at every threshold where it
   is eligible: 0.2, 0.3, 0.4 and 0.5. At 0.1 its expected joint count falls to 1.8 and
   it is ineligible under the pre-declared floor, so it has no rank there.

### A defect found in this audit's own first version

The first version of the robustness script assigned an ineligible stratum a numeric rank
of 110 by sorting it against `-inf`, and reported check 4 as FAILED. That is the exact
error the charter forbids: an ineligible group coerced into a confident value. The fix
removed the coercion and reports ineligible points as ineligible. The criterion was not
loosened. This is recorded because a robustness audit that quietly repairs itself is
worth less than one that says where it was wrong.

## Amendment from Result J

[`RESULT_J_WORST_REGION_ACROSS_PAIRS.md`](RESULT_J_WORST_REGION_ACROSS_PAIRS.md) ran this
identical contract over three detector pairs. The result below is **narrowed**.

The worst-stratum identity is pair-specific. Two pairs put `car, 0-20 m, v80-100` worst
and one puts `car, 0-20 m, v60-80` worst. The claim that this exact cell is universally
worst is not supported.

The regional finding is supported and strengthened. In all three pairs, including a
lidar-lidar pair sharing no modality structure with the other two, the worst eligible
stratum and the entire top three are close-range cars.

Read this document as one pair's extremum inside a consistently worst region.

## The limit of this finding, stated plainly

The 178 joint misses come from **34 distinct tracked instances**. That is the real
evidence base, and it is small. The instance-clustered simultaneous band [2.221, 11.671]
already carries that cost, which is why it is so much wider than the sample-clustered
[6.338, 7.585]. The conservative lower bound of 2.221 still excludes independence, so
the direction holds, but the magnitude is not tightly determined and must not be quoted
as 6.946 without its band.

This is one camera detector against one lidar detector on one split. It is not a claim
about camera and lidar as modalities, about any vendor, or about any deployed system.

## Why it matters

**This section is WITHDRAWN as stated and retained as historical.** It formerly converted
the pooled and worst-group coefficients into extra-validation-evidence percentages through
Result G. Those percentages are withdrawn from current scientific use. The exact superseded
values are retained in
[`result_i.txt`](../evidence/measurement/result_i.txt) and in
[`claim-status-register-2026-08-29.json`](../evidence/claim-status-register-2026-08-29.json)
under `reiyah.gate-b.claim.evidence-cost-worst-group`.

Two independent grounds, both recorded in
[`ESTIMAND_RSS_DEFINITION_32.md`](ESTIMAND_RSS_DEFINITION_32.md) section 6. Result G itself
has no data path: its coefficients are hand-transcribed rounded literals. And RSS
Corollary 3 is a three-subsystem majority-vote bound over safety-critic miss **and** ghost
mistakes, so it is not a validated conversion from a two-channel detection-miss `c` into a
validation-evidence multiplier.

What survives the withdrawal carries no number and is unchanged in substance. A pooled
coefficient and a worst-group coefficient are different quantities, they differ here by
more than a factor of four, and a redundancy argument that reports only the pooled value
cannot see the worst group at all. Counterexample CE-3 in
[`estimand_counterexamples.txt`](../evidence/measurement/estimand_counterexamples.txt) shows
this is not an artifact of these data: a pooled coefficient of 1.0400 is compatible with a
subgroup at 5.0000 while every marginal is identical. That is the entire argument for
worst-group reporting, and it needs no evidence-budget conversion to stand.

## Non-claims

This creates no scientific support, safety finding, compliance determination,
comparative claim about any detector or vendor, and no operator acceptance. It is one
measured stratification of two published detection outputs on one public split, retained
as `proposed`. Advancing it requires the evidence admission process, an authorized
operator decision, and independent review, none of which this document supplies. No
released `1.2` byte is modified.
