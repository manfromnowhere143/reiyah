# The dependence estimand, and its exact relation to RSS Definition 32

Document ID: `reiyah.gate-b.estimand-rss-definition-32`

Version: `0.1.0`

Lifecycle status: `proposed`

Supersedes the informal estimand language used in Results D, E, G, I, J, K and L. No released
`1.2` byte is modified. Prior results are retained with their corrections attached.

## 1. The estimand

For a stratum `s` of a declared opportunity universe, with channels `A` and `B` at declared
exact versions and declared operating points,

```
c_s  =  P_s(M_A = 1 and M_B = 1)  /  [ P_s(M_A = 1) * P_s(M_B = 1) ]
```

`c_s` is an observed-to-expected coincidence ratio. It is **not** an odds ratio, **not** a
correlation coefficient, and **not** invariant to the marginal miss rates.

## 2. Exact relation to the retained primary source

`docs/PRIMARY_SOURCE_CUSTODY_2026-08-29.md` entry S-01 retains the primary text of
arXiv:1708.06374. Definition 32 of that document reads, verbatim:

> Two Bernoulli random variables `r1`, `r2` are called one side c-approximate independent if
> `P[r1 and r2] <= c P[r1] P[r2]`.

Therefore `c_s` as defined in section 1 is exactly the **smallest admissible constant** in
Definition 32 for that stratum and that channel pair, whenever the Bernoulli variables are
matched. This is a definitional identity, not an analogy, and it is bound to retained primary
bytes.

Reiyah MUST NOT call `c_s` the Eckhardt and Lee intensity function. That prohibition was
originally provisional, for want of retained text. As of 2026-08-29 the primary text is retained
via NASA Technical Memorandum 86369 and the prohibition is now **positively established** rather
than merely precautionary. See custody entry S-04 and section 3.1 below.

## 3. Heterogeneous-channel decomposition

Let `X` describe the full latent demand state of an opportunity. Define the channel-conditional
failure intensities

```
theta_A(x) = P(M_A = 1 | X = x)       theta_B(x) = P(M_B = 1 | X = x)
```

**Model CI (stated as an assumption, never as a fact):** `M_A` and `M_B` are conditionally
independent given `X`.

Under CI,

```
P_s(M_A and M_B) = E[ theta_A(X) theta_B(X) | s ]
P_s(M_A) P_s(M_B) = E[ theta_A(X) | s ] * E[ theta_B(X) | s ]
```

and therefore

```
c_s - 1  =  Cov( theta_A(X), theta_B(X) | s )  /  ( E[theta_A(X)|s] * E[theta_B(X)|s] )
```

Two readings follow, and only the first is a theorem.

1. **Homogeneous channels.** If `theta_A = theta_B = theta`, then
   `c_s - 1 = Var(theta(X)|s) / E[theta(X)|s]^2 >= 0` by Jensen, with equality only when
   `theta` is constant on `s`. Identical construction cannot fall below independence.
2. **Heterogeneous channels.** With distinct `theta_A` and `theta_B` the covariance may be
   negative, so `c_s < 1` is possible in principle. This is a possibility statement about the
   model, not a claim that any observed `c_s < 1` was produced that way.

`c_s` is therefore, under CI, a normalised covariance of the two channels' conditional failure
intensities over **residual unmodelled demand heterogeneity within `s`**. It is a property of the
stratification as much as of the channels.

### 3.1 What the retained coincident-error text does and does not license

Custody entry S-04 retains NASA Technical Memorandum 86369, the NASA variant of Eckhardt and Lee
1985. Two of its statements bear directly on section 3, and one forbids a tempting shortcut.

**Theorem 2, verbatim:** "a necessary and sufficient condition for (unconditional) independent
failure of the component versions is that `theta(x)` be constant except on a subset `A` of
`Omega` for which `Q(A) = 0`." And, verbatim: "the variance `sigma^2` of the intensity
distribution gives a measure of departure from the independence model."

That is the same boundary case the homogeneous reading of section 3 reaches: `c_s = 1` exactly
when the conditional failure intensity is constant almost everywhere on the stratum, and the
departure is governed by its variance. Reiyah's `c_s - 1` is the **normalised** form of that
departure measure, dividing by the squared mean so the quantity is dimensionless. The agreement
is a useful check on section 3, arrived at independently and forty-one years later.

**Three reasons the identification still fails, all from the retained text.**

1. `theta` is a **function on the input space**, not a scalar. The departure measure is the
   variance of its induced distribution, not a ratio.
2. `theta` is an expectation over a **random draw from a population of versions** developed to a
   common specification. Reiyah's channels are two fixed, named, published, heterogeneous
   detectors. There is no version population and no random draw, so there is no `theta` to be the
   intensity of.
3. The model is **homogeneous**: one intensity function shared by all versions. Reiyah's case is
   heterogeneous by construction, which is why section 3 needs two functions and a covariance.

**A warning the retained text states explicitly**, verbatim: "Our results show it is incorrect to
interpret a low intensity as implying statistical independence and a high intensity as implying
statistical dependence." And, on the scope of the word independence in that model: "We emphasize
that statistical independence in the current context refers only to the selection process and
does not imply statistically independent failures among software components."

So the admissible statement is that section 3's homogeneous case **agrees in form** with a
retained theorem, and nothing stronger. `c_s` is not that theorem's intensity, is not its
variance, and inherits none of its conclusions.

## 4. Non-identification, with checkable counterexamples

Transcript: [`estimand_counterexamples.txt`](../evidence/measurement/estimand_counterexamples.txt).
Generator: `tools/measure/estimand_counterexamples.py`. Exact rational arithmetic, no sampling,
no seed, no data. Re-running reproduces the transcript byte for byte.

| Case | Construction | Result |
|---|---|---|
| CE-1 | Two difficulty regimes, channels **exactly** conditionally independent within each, no coupling of any kind | `c = 1.8186` |
| CE-2 | Same, regimes hard for opposite channels, still exactly conditionally independent | `c = 0.1814` |
| CE-3 | 99% independent bulk, 1% subgroup at `c = 5`, identical marginals everywhere | pooled `c = 1.0400` |
| CE-4 | One channel's operating point moved, coupling structure untouched | `c` moves `1.8186 -> 1.2262` |
| CE-5 | Exactly independent truth, then 0.50% reference error | `c` moves `1.0000 -> 0.5512` (omission) or `-> 1.3673` (phantom) |
| CE-6 | A stratum where one channel never misses | `c` **undefined** |

Consequences, all normative:

1. `c > 1` is consistent with genuine coupling, with incomplete stratification, and with
   correlated reference error. It is **not** causal proof of a common cause.
2. `c < 1` is consistent with a diversity benefit, with anti-correlated difficulty, with
   reference error, and with sampling noise under multiplicity. It is **not** causal proof that
   diversity protected the system.
3. A pooled `c` arbitrarily close to 1 is compatible with an arbitrarily coupled subgroup, and
   CE-3 shows the marginals cannot reveal it. Worst-group partition is mandatory, not optional.
4. `c` is not comparable across operating points. Any contrast must match or condition on
   marginals.
5. A sub-percent reference error moves `c` further than most effects of interest. Reference-error
   partial identification is P0 and belongs in the same contract as the estimate.
6. A zero denominator yields the explicit `undefined` state. Coercion to 0, 1, or "independent"
   is prohibited.

The only design that supports a causal statement is an intervention on channel construction. No
observational contrast in this program supports one.

## 5. Required reporting vector

A bare `c` is not a reportable result. Every reported `c_s` MUST be accompanied by, in the same
table row:

| Operand | Requirement |
|---|---|
| `p_A`, `p_B` | Both marginal miss probabilities on `s` |
| `p_AB` | The joint miss probability on `s` |
| cell counts | `both_miss`, `A_only`, `B_only`, `neither`, summing to the denominator |
| denominator | Eligible opportunity count on `s`, and the universe definition that produced it |
| operating point | Exact declared `tau_A`, `tau_B`, and the matching rule used |
| clustering unit | The unit at which uncertainty was computed |
| uncertainty | Interval with method, replicate count, and seed |
| identification | The reference-error bound state from the M4 ladder |
| definedness | `defined` or `undefined`, never coerced |

## 6. Corrections to the evidence-cost chain

### 6.1 What the primary text supports

Corollary 3 of arXiv:1708.06374 is retained verbatim in custody entry S-01:

> Assume that for any pair `i != j`, the random variables `e_i^m`, `e_j^m` are one sided
> c-approximate independent, and the same holds for `e_i^g`, `e_j^g`. Assume also that for every
> `i`, `P[e_i^m] <= p` and `P[e_i^g] <= p`. Then, `P[e^m or e^g] <= 6 c p^2`.

The attribution carried in `tools/measure/result_k_evidence_cost_interval.py` was therefore
**correct**, and is confirmed rather than withdrawn.

### 6.2 Five scope mismatches, all disqualifying as currently used

1. **Arity.** Corollary 3 analyses **three** sub-systems under a majority-vote fusion. The
   constant 6 is three sub-systems times two mistake types under a union bound. The Gate B
   measurements are of a **two-channel pair** with no fusion rule. The constant does not carry
   over.
2. **Uniformity.** Corollary 3 assumes the pairwise property "for any pair `i != j`". Its `c` is
   a single constant bounding **every** pair simultaneously. The corresponding empirical quantity
   is therefore a supremum over pairs and strata, not a pooled point estimate. This is an
   argument from the primary source itself for worst-group reporting.
3. **Mistake type.** The corollary requires the property separately for miss-miss pairs and for
   ghost-ghost pairs. Gate B measures **miss-miss only**. The ghost side is entirely unmeasured,
   so no Corollary 3 conclusion can be formed from Gate B data.
4. **Population.** The Bernoulli variables are **safety-critic** mistakes, defined in the primary
   text against the safety model, and the text explicitly argues that ordinary measurement error
   is unlikely to be safety-critic. Gate B measures detection misses over all annotated objects.
   The populations differ and the direction of the difference is unknown.
5. **Confidence.** The primary text says "order of `10^5` examples". It attaches no confidence
   level. Reporting a 95% sampling interval on a derived example count assigns a precision the
   source quantity does not carry.

### 6.3 Disposition

| Prior statement | New status |
|---|---|
| `P <= 6 c p^2` attributed to RSS Corollary 3 | **confirmed**, primary text retained |
| Evidence requirement scales as `sqrt(c)` | **conditionally supported**, see 6.4 |
| `RSS_BASELINE_N = 77460` as "RSS's own worked example" | **narrowed**: a Reiyah derivation, not an RSS figure |
| "about 26% more evidence", "+26.0%, 95% CI [25.0, 26.9]", "97,596 examples, CI [96,860, 98,332]" | **withdrawn as stated**, on scope mismatches 1, 3, 4 and 5 |
| "163.5% more evidence" for the worst group | **withdrawn as stated**, same grounds |

Withdrawal is of the **reported figures and their intervals**, not of the direction. The retained
statement is qualitative and conditional: if the measured dependence transfers to safety-critic
mistakes, a validation campaign sized under independence is undersized, and the shortfall is
larger in the worst group than in the pooled estimate. That statement carries no number.

### 6.4 The bridge that must be declared before any `sqrt(c)` figure returns

From `P <= 6 c p^2`, holding the target `P*` fixed, the admissible per-channel rate is
`p <= sqrt(P* / (6c))`, so `p` shrinks as `1/sqrt(c)`. Converting a rate into an evidence count
requires a second, separate relation

```
N  proportional to  1 / p
```

which the primary text uses only as an order-of-magnitude statement, with no confidence level and
no estimator. Under that bridge `N` grows as `sqrt(c)`, and at `P* = 10^-9`, `c = 1` the value
`1/sqrt(10^-9/6) = 77459.7` reproduces the text's "order of `10^5`".

Before any evidence-budget figure is reported again, all of the following must hold and be
retained:

1. the bridge `N proportional to 1/p` is replaced by a stated estimator with a stated confidence
   level, or is explicitly declared as an order-of-magnitude device carrying no interval;
2. the measured `c` is defined on **safety-critic** mistakes, or the transfer from detection
   misses to safety-critic mistakes is bounded rather than assumed;
3. the ghost-ghost dependence is measured, since Corollary 3 needs both;
4. the arity and fusion rule of the system under analysis matches the corollary, or a two-channel
   corollary is derived and retained;
5. the `c` used is the uniform bound the corollary requires, not a pooled estimate.

Until then, Reiyah reports `c` with its absolute-risk vector and reports **no** evidence-budget
percentage.

## 7. The falsifiable mechanism the primary source states

Custody entry S-01 proposition 6 retains the primary rationale for assuming approximate
independence between camera and lidar: their common weather causes are argued to produce
**different mistake types**, camera missing objects while lidar produces ghosts, so that
miss-miss coupling stays low.

This is a stated, falsifiable mechanism, and it is exactly the quantity a camera-against-lidar
miss-miss measurement addresses. A preregistered test of it is specified in
`docs/PREREGISTRATION_MODALITY_CONTRAST_0_1_0.md`. No result in the current repository is
admissible as such a test, because none was preregistered against this mechanism and none
satisfies section 6.2.

## 8. Non-claims

No scientific support, safety finding, compliance determination, comparative claim about any
vendor or detector, and no operator acceptance. This document defines an estimand and corrects
prior language. It reports no new measurement.
