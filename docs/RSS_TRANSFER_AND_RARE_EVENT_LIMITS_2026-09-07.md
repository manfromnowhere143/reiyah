# What a measured dependence coefficient can justify

Document ID: `reiyah.rss-transfer-and-rare-event-limits.2026-09-07`

Version: `0.1.0`

Lifecycle status: `exploratory`

The proposed commercial chain needs another correction: measuring dependence on common
benchmark errors does not by itself make dependence between rare safety-critical failures
cheap to establish. This checkpoint derives a concrete limit, implements it with exact
probability tables, and distinguishes the probability laws to which RSS applies. No
historical result, study protocol or claim register is overwritten.

## 1. Three different quantities must not share one interpretation

Write \(p_{A,s},p_{B,s},j_s\) for two marginal failure probabilities and their joint
probability in stratum \(s\). With positive marginal product,

\[
c_s=\frac{j_s}{p_{A,s}p_{B,s}}.
\]

This is the minimum constant in RSS Definition 32 for those two Bernoulli variables
under that stratum's probability law. The retained source is
[arXiv:1708.06374v6](https://arxiv.org/html/1708.06374v6), revised 27 October 2018.
Its Corollary 3 concerns three subsystems, a particular majority decision, two specified
safety-critical error types, and bounds across subsystem pairs. It does not supply
Reiyah's labels, reference validity, confidence procedure or a transport theorem.

For mixture weights \(w_s\), the law of total probability instead gives

\[
c_{\mathrm{mix}}=
\frac{\sum_s w_s j_s}
{(\sum_s w_s p_{A,s})(\sum_s w_s p_{B,s})},
\qquad
c_C=\frac{\sum_s w_s j_s}{\sum_s w_s p_{A,s}p_{B,s}}.
\]

The implementation in
[`result_l_convergence.py`](../tools/measure/result_l_convergence.py), function `c_strat`,
computes the second ratio. The board already identified its product-weighted averaging.
The independently reproduced **1.151053** is that conditional aggregate on its declared
support; it is neither every \(c_s\) nor automatically \(c_{\mathrm{mix}}\).
Where all denominators are positive,

\[
c_{\mathrm{mix}}=c_C
\frac{E_w[p_{A,s}p_{B,s}]}{E_w[p_{A,s}]E_w[p_{B,s}]}.
\]

An auditable result must bind the law, unit, selection, weights and event definition,
as well as the number. A new operating distribution changes those operands.

### Correction to an older source attribution

Section 6.2(2) of the proposed
[estimand document](ESTIMAND_RSS_DEFINITION_32.md) says RSS itself requires a supremum
over pairs **and strata**. The first quantifier is in the corollary. The second is an
additional Reiyah reporting/robustness requirement, not an explicit quantifier in that
text. A theorem on one probability law need not hold conditional on every subset.
Worst-group reporting remains appropriate for the project's scientific purpose; its
authority should be our declared objective, not an overattribution to RSS.

Two exact controls expose both directions:

| Construction, with equal mixture weights | Stratum coefficients | Conditional aggregate | Mixture coefficient |
| --- | --- | --- | --- |
| Independent channels in each stratum, with common marginal rates .001 and .01 | 1, 1 | 1 | 202/121, about 1.6694 |
| Marginal rates .5/.5 in both strata; joint probabilities .4 and .1 | 1.6, .4 | 1 | 1 |

Thus even the largest conditional coefficient need not bound the mixture coefficient.
Conversely, a valid mixture coefficient of one need not bound every conditional ratio.
If a conditional fusion bound has been established, one may average the conditional
**absolute** bounds, \(\sum_s w_s\sum_{i<j}c_{ij,s}p_{i,s}p_{j,s}\), for one error type,
under that fusion rule. Replacing those terms with products of pooled marginals requires
another justified step. All earlier withdrawals of numerical safety budgets remain in force.

## 2. A finite experiment can barely distinguish the relevant worlds

For this authored example only, assume perfect reference labels, a complete opportunity
population, independent identically distributed draws, fixed channel versions and
known marginal rates \(p_A=p_B=p=10^{-5}\). There are no informative side observations.
Consider the full per-opportunity laws, in order both fail, A only, B only, neither:

\[
P_0=(p^2,p-p^2,p-p^2,1-2p+p^2),
\]

\[
P_1=(2p^2,p-2p^2,p-2p^2,1-2p+2p^2).
\]

Both laws are feasible and have exactly the same marginals. Their coefficients are
one and two. Their single-observation total variation distance is exactly

\[
\operatorname{TV}(P_0,P_1)=\tfrac12\sum_x|P_0(x)-P_1(x)|=2p^2.
\]

For \(N\) iid observations, a telescoping product argument, or a coupling on each draw,
gives \(\operatorname{TV}(P_0^N,P_1^N)\le\min(1,2Np^2)\).
For any possibly randomized test \(\phi\in[0,1]\), its expectations differ by at most
total variation. Consequently a test with false-positive probability at most \(\alpha\)
under \(P_0\) has power at most

\[
E_{P_1^N}\phi\le\min(1,\alpha+2Np^2).
\]

At \(N=100,000\) and \(\alpha=.05\), the power is at most **.05002**. This bound applies
even to a test using all four outcome categories and the known marginals. It is not
a statement about one weak estimator or a particular neural network. For 95% power
at that significance level, the same inequality requires at least **4,500,000,000**
draws. This is a coarse necessary lower bound, not a sufficient sample size or an
optimal complexity result. The exact controls and statement are in
[`limits-0.1.0.json`](../evidence/physical-reference-transfer/limits-0.1.0.json).

This example does not describe actual vehicle failure rates. Its unit is an independent
opportunity, not a camera frame, second, mile, hour or journey. Arbitrarily duplicating
frames cannot create the independent draws the derivation assumes.

## 3. The familiar zero-event calculation exposes the same scale

For a fixed-sample binomial experiment with zero observed events, the one-sided upper
confidence endpoint is \(q_U=1-\alpha^{1/N}\). The smallest \(N\) for which that endpoint
is at most a declared threshold \(q_*\) is

\[
N=\left\lceil\frac{\log\alpha}{\log(1-q_*)}\right\rceil.
\]

For the same synthetic rates and \(\alpha=.05\):

| Threshold and event being bounded | Minimum fixed sample for this zero-event rule |
| --- | ---: |
| Single-channel failure probability at most \(10^{-5}\) | 299,572 |
| Joint failure probability at most \(10^{-10}\), equivalent to \(c\le1\) if these marginals are known | 29,957,322,735 |
| Joint failure probability at most \(2\times10^{-10}\), equivalent to \(c\le2\) under the same condition | 14,978,661,367 |

These are requirements for this confidence rule **conditional on observing zero events**.
They neither ensure zero events nor design a study with specified acceptance power.
They are also not the preceding necessary lower bound for every possible test.
Uncertain marginal probabilities require joint inference: dividing a joint upper bound
by two marginal upper bounds does not provide a conservative upper bound on \(c\).
A simultaneous lower bound on the denominator, or a joint confidence set respecting
the feasible table, would be needed. None of these calculations restores Result S's
withdrawn budget percentages.

The code evaluates logarithm ratios with rational enclosures. For \(1\le x\le2\), put
\(z=(x-1)/(x+1)\). Truncating
\(\log x=2\sum_{k\ge0}z^{2k+1}/(2k+1)\) after \(m\) terms leaves a nonnegative tail
at most \(2z^{2m+1}/((2m+1)(1-z^2))\). Range reduction handles other positive arguments.
Equal ceilings of the ratio's lower and upper bounds certify each reported integer.
Small exact-integer boundaries use rational powers; unresolved boundaries fail explicitly.
This is elementary arithmetic, not a new statistical technique.

## 4. Prior art changes the novelty claim

[Butler and Finelli, IEEE TSE 1993](https://shemesh.larc.nasa.gov/paper-nonq/nonq-tse.html),
sections 5.1.2–5.1.3 of the retained NASA-hosted paper, already examine why validating
coincident failures at very low rates can return the original testing burden. Their
criticism of extrapolating from failure-free experience directly intersects this
proposed business case. Our finite-law calculation makes a bounded instance executable;
it does not discover the underlying difficulty or establish every impossibility claim
in their discussion.

[Littlewood, Popov and Strigini, Safety Science 2002](https://openaccess.city.ac.uk/id/eprint/1952/)
already distinguish system-only from four-outcome channel observations and study Bayesian
inference over the two marginals and their joint probability. Their treatment exposes
the importance and difficulty of joint priors. The repository labels its PDF version
unspecified; it is not silently treated as the final publisher text. This is material
prior art against claiming that the four-cell evidence representation or dependence
assessment is new. Bayesian information can help when justified; a convenient prior
does not create independent observations.

The binomial confidence calculation is conventional and is consistent with
[NIST's exact-binomial documentation](https://itl.nist.gov/div898/software/dataplot/refman2/auxillar/exacbino.htm).
All source-custody distinctions, dates, access limits and digests are retained in
the [source ledger](../evidence/physical-reference-transfer/source-ledger-0.1.0.json).
No paper payload enters this candidate's Git artifacts.

## 5. Consequence for Reiyah

The useful near-term claim is an independently reviewable **audit of an inference**:
what population was measured, which reference transitions change the interpretation,
what the data can distinguish, and what extra assumptions make the desired conclusion
possible. An instrument can quickly falsify some optimistic claims without being able
to certify extremely small risks. The asymmetry is part of its value proposition.

A defensible validation-cost reduction would need additional information: a valid
transport model, measured physical structure, an independently defensible prior,
or controlled/importance-sampled trials with known likelihood ratios and appropriate
support. If the sampling distribution has zero support on some operational failures,
weighting observed data cannot recover them. Every such route moves the scientific
burden into an assumption or measurement that must itself be tested.

The next discriminating research question is therefore whether a more observable,
controlled physical experiment can support a transferable **joint response law**.
The [physical-reference assessment](PHYSICAL_REFERENCE_OPTIONS_2026-09-07.md) examines
one current candidate and proposes a narrow falsification before any deployment claim.
The already frozen 240-case reference study remains the immediate empirical priority.
