# Exact intervals and separately controlled sampling error

Document ID: `reiyah.sequential-audit.mathematics`.
Version: `0.1.0`.
Lifecycle status: `proposed`.

All computations use rational arithmetic. Let weights w_i be nonnegative and
sum to one. The reference uncertainty is a fixed authored box
`l_i <= d_i <= u_i`, with endpoints in [-1,1]. The target is the weighted paired
difference, and strict improvement means `sum(w_i d_i) > tau`.
The current observation interface reveals the endpoints, not a point-valued
physical truth. Unqueried or unavailable members retain [-1,1]. Nonresponse
statuses remain explicit; these bounds are not zero-loss labels.

## Computational guarantee

At a queried set H, use the revealed endpoints on H and [-1,1] elsewhere.
The weighted sums give a valid enclosure. Because this test specifically allows
the whole box and weights are nonnegative, the all-lower and all-upper vertices
attain the extrema. Output supported only if the lower total exceeds tau;
excluded only if the upper total is at most tau; otherwise unresolved. The
checker establishes the same result by enumerating all box vertices.

These fixtures do not implement the Engine's more constrained geometric
common-world matching. Correlated numerical members and cluster labels do
not make their fixed population values i.i.d.; the following argument uses
only randomness from sampling. It does not authorize reinterpreting repeated
human measurements as independent reference truth.

## Statistical guarantee for endpoint totals

For the lower endpoint set `x_i = (l_i+1)/2`, with boundary `m = (tau+1)/2`.
For the other direction set `x_i = (1-u_i)/2`, with boundary `m = (1-tau)/2`.
In either case test the composite null `sum(w_i x_i) <= m`. Rejection of the
first implies a statistical claim of strict improvement; rejection of the
second implies an upper total strictly below tau, sufficient for non-improvement.
Boundary equality can still be decided by the exact rule.

Let R be the remaining positive-weight members, q a predictable positive
probability distribution on R, and S the observed weighted endpoint sum.
Without a proxy use `Z = w_I x_I / q_I`, where `I` is drawn according to q.
With fixed endpoint proxy p use

`Z = sum_{j in R}(w_j p_j) + w_I (x_I-p_I)/q_I`.

In both cases, the conditional expectation of Z is exactly the remaining
endpoint total. For the proxy case, a known lower support bound is

`a = sum_{j in R}(w_j p_j) + min_{i in R}(-w_i p_i/q_i)`.

For the unassisted case use a=0. Write `mu = m-S`. Choose
`lambda = 1/[2(mu-a)]` if mu>a, and zero otherwise. The next wealth factor is
`F = 1 + lambda (Z-mu)`. Its minimum is at least 1/2 when lambda is positive,
and one when lambda is zero. The conditional expectation under the null is
at most one. Thus the product, initially one, is a nonnegative supermartingale
under each directional null. This argument derives admissibility from the
lower support endpoint rather than relying on an unchecked betting-range formula.

The probability that wealth ever reaches 40 is at most 1/40 by Ville's
inequality. Applying the union bound to the two directional tests gives at most
1/20 for any false endpoint rejection during that registered procedure. Exact
logical decisions add no sampling error under the authored box premises.
The exhaustive checker separately verifies these probabilities for every
allocated population, using exact order probabilities rather than simulations.
The mathematical argument covers bounded fixed endpoints beyond those fixtures;
the software execution evidence covers only the frozen finite allocation.

The formulas specialize the importance-weighted betting framework reviewed in
[Shekhar et al.](https://arxiv.org/html/2305.06884v1), with a fixed stake and an
explicit residual control variate. They are not a new optimality theorem or a
reproduction of ApproxKelly and the paper's full experiments. The bound is
conditional on a valid sampling design, fixed endpoints and sound observations.
Learning or changing endpoints, targets, populations, sampling probabilities,
or loss after inspecting outcomes needs a new justification and binding.

## Registered sampling and proxies

Uniform: q_i=1/|R|. Weight: q_i=w_i/sum_R w.
Proxy and proxy_cv: q_i proportional to `w_i [1/8 + (s_i+1)/2]`, where the
authored score s_i is in [-1,1]. The 1/8 term prevents zero support.
The proxy_cv arm uses p_i=(s_i+1)/2 for the lower direction and
p_i=(1-s_i)/2 for the mirrored upper direction; other arms use no control variate.
Proxy quality is not assumed for validity, only for a possible efficiency benefit.
No score is fitted using unseen endpoint answers in the actual sampling rule.

## Identification remains a separate limit

When the fully revealed lower total is at most tau and the upper total exceeds
tau, the box contains opposing decisions. Full observation returns unresolved.
An earlier statistical decision in that situation is counted as a false
robust decision in the exact error accounting, even if it happens to agree
with an arbitrarily chosen latent point. No statistical test supplies reference
truth or eliminates this identification interval with probability one.

The 2026 [PPAT preprint](https://arxiv.org/html/2607.08347v1) supplies a relevant
residualized estimation comparator, but its asymptotic interval result does not
provide this finite-population, finite-sample optional-stopping guarantee.
We do not run PPAT or reinterpret its confidence intervals as certificates here.
