# What the moment-cone diagnostic decides, and what it cannot

Document ID: `reiyah.moment-cone.decision-value.2026-09-10`

Version: `0.2.0`

Lifecycle status: `proposed`

Lane: independent research, parallel to the Engine. Changes no released byte, no frozen protocol
and no owner checkout. Creates no acceptance and no scientific authority. Gate A remains unaccepted.

## The question and the answer

The question a perception-validation lead is actually asking is whether an added observer earns
further integration work. The question this lane's certificate procedure answers is whether a
population's subset-averaged silence moments are representable by a scalar iid mixture.

**Those are different questions, and the second does not help with the first.** This document
establishes that with exact controls and one measurement, and states where the diagnostic does
belong. For the evidence that does support the decision, see
[what a reader needs to verify one addition](DECISION_EVIDENCE_2026-09-11.md).

## Control one: heterogeneity alone rejects, with no dependence present

For `K` mutually independent Bernoulli channels with fixed rates `p_i`, write `m_1` for the average
rate and `m_2` for the average pairwise joint silence. Then

```text
m_2 - m_1^2 = - Var(p) / (K - 1)
```

with the variance taken uniformly over the named channels. The derivation is elementary: with
`S = sum p_i` and `Q = sum p_i^2`, `m_2 = (S^2 - Q) / (K(K-1))` and `m_1^2 = S^2 / K^2`, whose
difference is `(S^2 - K Q) / (K^2 (K-1))`, and `Var(p) = (K Q - S^2) / K^2`.

Any spread in the rates therefore puts the vector strictly outside the cone, because a mixture
representation requires `m_2 >= m_1^2`. There is no coupling anywhere in that construction.

**Correction of 11 September 2026.** Version `0.1.0` of this document generalised that sentence too
far, saying heterogeneity alone rejects. The independence premise is load bearing. In general, for
any joint law,

```text
m_2 - m_1^2 = meanCov - Var(p) / (K - 1)
```

where `meanCov` is the mean covariance over distinct channel pairs. Positive dependence can offset
the heterogeneity penalty: the law placing mass `1/2` on all-observing, `1/4` on all-silent, `1/8`
on `100` and `1/8` on `110` has rates `1/2, 3/8, 1/4`, variance `1/96`, mean pair covariance `5/32`,
and `m_2 - m_1^2 = 29/192 > 0`. It is heterogeneous, dependent, and inside the condition.

The conclusion is stronger than the one it replaces: **cone membership isolates neither coupling nor
heterogeneity.** The identity is checked on 500 random joint laws in the retained tests.

The control is not hypothetical for this program. Taking the five retained channels at their own
exact measured silent rates and making them **mutually independent**:

| channel | exact silent rate |
|---|---|
| mapillary | `2814/8971` |
| fcos3d | `13628/44855` |
| megvii | `18091/134565` |
| pointpillars | `7797/44855` |
| centerpoint | `14938/134565` |

the resulting subset-averaged moment vector is **rejected by the same procedure that rejects the
observed data**, with `Var(p) = 3289970134/452693480625`. No dependence is present to explain it.

## Control two: perfect coupling is accepted

For identical, perfectly coupled channels `X_i = Z` with `P(Z) = p`, every `m_k` equals `p`, and the
mixture `(1 - p) delta_0 + p delta_1` reproduces the vector exactly. The procedure returns feasible
at every `p` tested. Meanwhile a further identical channel adds exactly zero protection.

So on the axis this program cares about, the diagnostic runs **backwards**: the worst possible
redundancy passes, and mere heterogeneity fails.

## What this changes about the eight certificates

The eight exact certificates stand as computations. Four are infeasible and four are feasible, and
the arithmetic in each is unaffected. What changes is the reading.

An infeasible verdict says the declared summary vector is incompatible with a scalar iid mixture
representation. Given deliberately heterogeneous named detectors, that was largely determined in
advance by the spread of their rates, and the estimand contract said as much before any of this was
computed. It is **not** evidence of coupling, not a rejection of a physical population, and not a
refutation of any classical theorem.

A feasible verdict says the summaries are representable. It does not say the generating model is
exchangeable, and it certainly does not say the channels are independent.

The legitimate use is the one Audit AV made: deciding whether a mixture-based bound has an
identified set to report. That use is unaffected and the exact certificates strengthen it.

## The measurement that does answer the decision

For an installed set `C` and a candidate `j`, on one shared reference and opportunity population,
the restricted miss-only benefit is

```text
benefit(C, j) = P(every channel in C silent AND j observes)
              = P(every channel in C silent) - P(every channel in C and j silent)
```

Read directly off the labelled joint cells of all 134,565 annotation rows at the `0.10` floor, with
each channel in turn treated as the candidate added to the other four:

| candidate | observed benefit | independent prediction | prediction over observed |
|---|---:|---:|---:|
| mapillary | 0.005365 | 0.036233 | **6.75x** |
| fcos3d | 0.004496 | 0.036147 | **8.04x** |
| megvii | 0.006963 | 0.047078 | **6.76x** |
| pointpillars | 0.012819 | 0.049774 | **3.88x** |
| centerpoint | 0.010991 | 0.051933 | **4.73x** |

The independent prediction is the serious conventional baseline, not an equal-rate straw man: it
uses each candidate's own measured marginal rate and assumes only that the candidate is independent
of the installed set. **It overstates the benefit of every candidate by between 3.9 and 8.0 times.**

That is the number the decision needs, and none of it comes from the cone.

## The three methods on the same question

| method | what it returns for this decision | cost |
|---|---|---|
| moment cone | nothing about it | 1 ms |
| independent heterogeneous Bernoulli | a prediction wrong by 3.9x to 8.0x here | under 1 ms |
| labelled joint cells | the answer | 2.3 s over the caches |

The silence histogram cannot supply it either. The retained counterexample makes that concrete: on
`{100, 011}` the benefit of adding channel 3 to channel 1 is `1/2`, and on `{010, 101}` it is `0`,
with identical marginals, identical histogram and identical subset-averaged moments.

## Scope, stated because these numbers invite over-reading

This is a miss-only query under one declared reference, matching rule and score floor. It carries no
false-positive term, no unmatched predictions and no matching competition, so it must not be used to
infer false-detection cost, planner behaviour or crash risk, and it is not the Engine's detector
loss. It is a descriptive quantity on one benchmark split with released detectors of an earlier
generation. It is reference relative throughout, and no sampling statement is attached: these are
finite-population counts, not estimates with an error bar.

## Recommendation

Keep the certificate procedure as an assumption check for mixture-based bounds, where it is exact
and useful, and stop short of any reading that treats a rejection as a dependence result. For the
next-channel decision, publish and use the labelled joint cells for the installed set and each
candidate. That is a handful of integers per stratum and it answers the question the cone cannot.

The open problem is unchanged and is not a computation: none of this identifies what an **unmeasured**
candidate would contribute. Existing-channel summaries cannot, without further evidence or a
justified and stated transfer assumption.

## Reproduce

```sh
python3 -B tools/measure/moment_cone_discrimination.py
python3 -B tools/measure/next_channel_decision.py /path/to/local/cache
python3 -B -m unittest discover -s tools/measure -p test_moment_cone_certificate.py
```

The first reads no data. The second reads the retained caches read only and emits aggregate counts
only. Retained outputs are [the controls](../evidence/moment-cone/discrimination.json) and
[the decision table](../evidence/moment-cone/next-channel-decision.json).

## Non-claims

An internal research artifact, retained as `proposed`. Not independent external scientific review,
not an operator acceptance, not a safety, compliance or vendor claim, and not a statement about any
deployed system. No released `1.2` byte, frozen protocol, claim-register entry or other owner's work
is modified.
