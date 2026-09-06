# Result S: the corrected safety calculus, RSS Corollary 3 with the coefficient measured

Document ID: `reiyah.result-s-corrected-safety-calculus`

Version: `0.1.0`

Lifecycle status: `corrected` (figures withdrawn as stated on 2026-09-06; direction retained as conditional)

## Correction of 2026-09-06, read first

The reconciliation check `tools/measure/check_claim_reconciliation.py` caught this document
asserting figures the claim register withdrew on 2026-08-29 under
`reiyah.gate-b.claim.evidence-cost-pooled`: the evidence counts and the "at least 26 percent"
percentage. That register entry lists five conditions that must hold before any evidence-budget
figure returns, set out in [`ESTIMAND_RSS_DEFINITION_32.md`](ESTIMAND_RSS_DEFINITION_32.md)
section 6.4. This document meets none of them:

1. the bridge `N proportional to 1/p` is used with no stated estimator or confidence level;
2. `c` is measured on detection misses over all annotated objects, not on safety-critic mistakes;
3. ghost-ghost dependence is unmeasured;
4. the corollary bounds a three-subsystem majority vote and this is a two-channel pair; and
5. the pooled marginal `c` is used where the corollary requires a uniform bound over every pair.

Disposition: every evidence count, percentage, and multiplier below is **withdrawn as stated** and
retained with this correction attached, per the register's deletion-prohibited policy. What
survives is qualitative and conditional: from `P <= 6 c p^2` the admissible per-channel rate
shrinks as `1/sqrt(c)`, so a campaign sized under independence is undersized wherever `c > 1`, by
an amount that grows with `c`. The direction is retained. The number is not. The illustrative
effective-channel reading (`n_eff`) is not an evidence budget and is retained as illustrative. The
original text follows unchanged except for the withdrawal markers the check requires.

## Original text, retained historically

This turns the measurement into the number a safety argument actually consumes. Every prior
result asked whether the independence assumption holds. This asks the next question: given that
it does not, by how much is the published evidence-reduction wrong. The answer is computed from
RSS's own formula, with the coefficient we measured substituted for the one RSS assumed.

## The formula, reconstructed from the primary text

RSS (arXiv:1708.06374) argues direct statistical validation of a vehicle needs evidence on the
order of `1/P_e` examples, which is infeasible for a target dangerous-error rate `P_e` near
`1e-9`. Corollary 3 escapes this with redundancy: if a dangerous outcome requires **both**
subsystems to fail and they are `c`-approximately independent (Definition 32), then
`P(both) <= 6 c p^2`, so validating each subsystem to single-channel error
`p = sqrt(P_e / (6 c))` suffices, and the required evidence is

```
N(c, P_e) = 1 / p = sqrt( 6 c / P_e ).
```

**Self-check against RSS's own worked example.** For `c = 1`, `P_e = 1e-9`:
`N = sqrt(6 / 1e-9)`, about `7.7 x 10^4`, consistent with the text's "on the order of `10^5`."
The specific count is a Reiyah derivation, not a figure RSS publishes (register: narrowed). This
consistency was taken to license substituting a measured `c` into the same formula; the correction
above records why that licence does not hold as stated.

The consequence is the whole point: **required evidence scales as `sqrt(c)`.** RSS assumes
`c ~ 1` and never estimates it. We estimated it.

## Which `c` the safety argument consumes

The coefficient that enters the deployed joint-failure rate is the **marginal** coefficient, not
the conditional one (Result G). A deployed system integrates over the operating distribution and
cannot condition on class, range, or visibility, so its joint-failure rate is
`P(both) = c_marginal * P_A * P_B`. The conditional coefficient of Results L to R answers the
mechanism question (is the coupling real beyond shared difficulty); the marginal coefficient
answers the safety-evidence question. Result S uses the marginal.

## The corrected requirement

Marginal camera-lidar coefficient measured on nuScenes val (Mapillary x Megvii), and the
corrected evidence at `P_e = 1e-9`:

| operating point (score >=) | marginal c | inflation `sqrt(c)` | corrected `N` | extra evidence vs RSS | status |
|---|---|---|---|---|---|
| 0.10 | 2.271 | 1.507 | 116,724 | +39,265 | withdrawn as stated |
| 0.20 | 1.878 | 1.370 | 106,146 | +28,686 | withdrawn as stated |
| 0.30 | 1.587 | **1.260** | 97,596 | +20,136 | withdrawn as stated |
| 0.40 | 1.363 | 1.168 | 90,447 | +12,987 | withdrawn as stated |
| 0.50 | 1.239 | 1.113 | 86,216 | +8,757 | withdrawn as stated |

The marginal `c` column is measured and stands (Results K and P). The `sqrt(c)` column is the
conditional derivation. The `N` and extra-evidence columns are withdrawn as stated.

**The former headline, withdrawn as stated.** It read: at a `0.30` operating point, RSS's
independence-based evidence figure is understated by a factor of `sqrt(1.587) = 1.260` (withdrawn as stated), at least
26% more validation evidence than Corollary 3 claims, for this pair (withdrawn as stated). Withdrawn
on the five grounds above. The range it described, `1.11x` to `1.51x`, is likewise withdrawn as stated,
because the marginal coefficient depends on the operating threshold (Result P). And it is a
**lower bound**, because the benchmark deletes the camera-only-visible objects before scoring
(Result A), which biases the coefficient toward independence.

## The redundancy RSS does not model at all

RSS's redundancy is automation-automation. A real Level 2 or Level 3 safety case additionally
credits the **human** as a redundant channel. That redundancy carries its own measured
dependence, `c = 1.46` (Result H3), a further `sqrt(1.46) = 1.208x` correction that RSS applies
by **zero**, because the human is outside its model. Two credited redundancy layers compound: the
automation `sqrt(1.587)` and the human `sqrt(1.46)` give **`1.522x`** (withdrawn as stated) the RSS evidence figure, a
52% understatement, before the lower-bound caveat. These multipliers are withdrawn as stated on the
same five grounds; the compounding structure is retained as the shape of the open question.

## An interpretation: effective independent channels

A cleaner way to feel the loss. Two channels with dependence `c` at miss rates `p_A, p_B` provide
the joint-failure protection of `n_eff = 2 + ln(c) / ln(sqrt(p_A p_B))` truly-independent
channels. For the measured pair at `0.30` (`c = 1.587`, miss rates `0.46` and `0.34`),
`n_eff = 1.50`. **You provisioned two sensors and received the redundancy of one and a half.**
This quantity depends on the operating miss rate and is stated as illustrative, not as the
headline; the `sqrt(c)` evidence scaling is the load-bearing result.

## What this is, and is not

It is the honest correction to a published formula, computed from coefficients measured on public
data and verified against RSS's own example. It is **not** a certification, not a required-evidence
figure for any real deployed system, and not a safety determination. The constant `6` and the
`sqrt(c)` scaling are taken from the retained primary text; the coefficient is a lower bound; and
no adjustment here is claimed sufficient for a real safety case, which would need the operating
distribution and error rates of the specific system, not a public benchmark.

What it does establish is the shape of the answer the field has left open: the loop from a measured
dependence back into the evidence requirement. Closing that loop is the contribution. The number
for any particular system is that system owner's to compute with this method and their own data.

## Non-claims

A correction to a published formula using coefficients measured on two public detection outputs,
retained as `proposed`. Not a certification, not a safety determination, not a comparative claim
about any vendor. RSS's formula is reproduced from retained primary text under fair use for
analysis. No released `1.2` byte is modified.
