# What a portable redundancy report must carry, decision by decision

Document ID: `reiyah.redundancy-disclosure-sufficiency.2026-09-10`

Version: `0.1.0`

Lifecycle status: `proposed`

Lane: independent research, parallel to the Engine's population-binding work. This document
corrects a proposal made earlier in this session by the same author. It changes no released byte,
no frozen protocol and no owner checkout, and creates no acceptance or scientific authority.

## The correction, stated first

An earlier verdict in this session proposed that the distribution of `S`, the number of channels
silent on an opportunity, is a sufficient portable summary for a redundancy audit, and drew a
product conclusion from that. **The sufficiency claim fails for the query that decision actually
asks, and the product conclusion does not follow.** The identity it rested on,

```text
mean over subsets C of size k of P(all of C silent) = E[C(S,k)] / C(K,k),
```

is exact and assumes nothing. It concerns the uniform average over subsets. A decision about a
named channel is not an average over subsets, and the histogram does not determine it.

A first draft of this document said the histogram determines "no labelled query at all". That is
too broad and is corrected here. Some labelled events are determined:

| labelled event | determined by | why |
|---|---|---|
| channel `j` silent, any single `j` | the marginals | supplied alongside the histogram |
| all `K` channels silent | `P(S = K)` | the top histogram bin is that event |
| at least one channel silent | `1 - P(S = 0)` | the bottom bin is its complement |

What is not determined is a general proper subset of size between 2 and `K - 1`, and with it the
addition query. That is the class the counterexample below inhabits, and it is the class the
decision needs.

## The separation, exhibited exactly

Three channels, `1` meaning silent, two populations of two equally weighted rows.

| population | rows | marginals | silence histogram | subset-averaged `m_1, m_2, m_3` |
|---|---|---|---|---|
| A | `100`, `011` | `1/2, 1/2, 1/2` | `P(S=1)=1/2, P(S=2)=1/2` | `1/2, 1/6, 0` |
| B | `010`, `101` | `1/2, 1/2, 1/2` | `P(S=1)=1/2, P(S=2)=1/2` | `1/2, 1/6, 0` |

Every published summary is identical. The labelled quantity is not:

| population | `P(channel 1 silent)` | `P(channels 1 and 3 both silent)` | what adding channel 3 to channel 1 buys |
|---|---|---|---|
| A | `1/2` | `0` | removes all of channel 1's silence |
| B | `1/2` | `1/2` | removes none of it |

The construction is due to the Engine-side review of the earlier verdict. It is reproduced here
independently and is retained as an acceptance criterion for any future disclosure contract.

## How much the histogram actually adds, quantified

The counterexample shows the histogram is not sufficient. The stronger statement is that for this
query it is not even partially informative. Over every population consistent with those marginals
and that histogram, the attainable range of `P(channels 1 and 3 both silent)` is

```text
[0, 1/2]
```

which is exactly the Frechet interval `[max(0, p_1 + p_3 - 1), min(p_1, p_3)]` implied by the
marginals alone. Both endpoints are attained by populations A and B, and the Frechet bound caps the
interval, so the range is exact and does not depend on the search lattice used to find it. **The
histogram removes none of the ambiguity that the marginals had already left.**

## What to carry instead

| decision | what must be published | verdict |
|---|---|---|
| average all-silent rate over `k`-subsets | silence histogram | sufficient |
| all-silent rate for one named subset | silence histogram | not sufficient |
| value of adding named channel `j` to installed set `C` | the two rates for `C` and `C + {j}` | sufficient |
| value of every candidate addition to `C` | one rate per candidate, plus the rate for `C` | sufficient |
| every labelled subset query | all `2^K` cell counts | sufficient, and minimal |
| value of a channel never measured | a model, and a certificate that the model is admissible | no summary suffices |

Two consequences worth stating plainly.

First, **compactness was never the binding constraint, though the earlier verdict got the
arithmetic backwards and that error is corrected here.** For five channels the full labelled table
is 32 counts per stratum, carrying 31 free parameters after normalisation. The histogram plus
marginals is 11 entries carrying 9 independent parameters, since the histogram sums to one and the
marginals sum to `E[S]`. **The labelled table is larger, not smaller.** The earlier claim that it
was smaller is withdrawn.

The case for it is sufficiency, not size. The labelled table answers every query about binary
silence patterns; the coarse summary answers a strictly smaller family that excludes the addition
query. Thirty-two integers per stratum is small in absolute terms, which is the only sense in which
compactness matters here. Any minimality claim must name its representation and its query family:
the labelled table is minimal for the family of all binary-pattern queries, and says nothing about
minimality under a different encoding or a narrower family.

Second, the decision an engineering team actually faces, which candidate to add to an installed
configuration, needs only one number per candidate plus one for the installed set. That is a very
small labelled disclosure, and it is the one worth specifying.

## Compactness is not privacy

A cell table is not anonymous, and the earlier verdict's claim that a compact summary is
inherently safe to publish is withdrawn. A stratum holding `n` opportunities discloses the exact
multiset of per-object silence patterns across every channel; at `n = 1` it discloses one object's
complete pattern. Releasing one population under two different stratifications permits linkage
between them. A minimum cell occupancy and a release ledger therefore belong in the disclosure
contract itself, not in operational guidance around it. What a producer may safely publish is a
separate question from what a consumer needs, and this document settles only the second.

## What this does not resolve

The table above concerns one fully observed binary indicator per channel on one shared opportunity
population. It does not address channels that are missing, invalid, abstained or outside support,
which must travel as their own states and never as a successful observation. It does not address
false detections or unmatched predictions, so it does not supply the operands of the Engine's
paired false-negative and false-positive loss. That loss is
`a * (T(w) - TP_pi(w)) + b * (D_pi - TP_pi(w))`, so its false-positive term is the count of emitted
detections left unmatched under the declared reference and matching rule, `D_pi - TP_pi`. It needs
no enumerated true-negative universe, and an earlier draft of this document wrongly said it did.
What a per-object binary silence indicator loses is different and more specific: it discards the
competing-match structure, so it cannot represent the case where an added detection captures one
object only by releasing another to the base detector. It does not preserve scene
or log clustering, so it supports no uncertainty statement. It does not permit discovering a worst
group that was not among the declared strata, because the labels needed to form a new partition are
gone once the table is built. Each of those is a separate obligation and none of them is closed
here.

## Reproduce

```sh
python3 -B tools/measure/disclosure_sufficiency.py
python3 -B -m unittest discover -s tools/measure -p test_moment_cone_certificate.py -v
```

Exact rational arithmetic, standard library only, no data read, about `0.2` seconds.

## Non-claims

An internal research artifact, retained as `proposed`. It corrects an earlier proposal by the same
author and establishes an exact impossibility for one class of query. It is not independent
scientific review, not an operator acceptance, not a product decision, and not a claim that any
particular disclosure format should be adopted. No released `1.2` byte, frozen protocol or other
owner's work is modified.
