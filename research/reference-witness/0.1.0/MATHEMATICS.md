# Threshold cells and optional-reference witnesses

Version `0.1.0`. The [plan](PLAN.md) fixes the empirical scope before new scores.

For fixed reference width/height and fixed orthogonal position, let u be its
translated coordinate, e its extent on that axis and h its orthogonal overlap
with a prediction. IoU at least 1/2 is equivalent to intersection area at least
(reference area + prediction area)/3. If h>0, the required axial overlap is
c = (reference area + prediction area)/(3h). When c is no greater than either
axial extent, the legal matching positions form the closed interval
[prediction_left+c-e, prediction_right-c], intersected with the legal canvas
domain. Otherwise the edge is absent. Every boundary point and every open
interval between boundaries therefore has a constant matching neighborhood.
The checker derives the same intervals from the separate piecewise-linear
overlap expression, preserving equality at the threshold.

Reference vertices with identical neighborhoods are interchangeable for the
two maximum-matching cardinalities. Keeping one geometry per neighborhood
preserves the attainable rank pairs when copies remain allowed as distinct
vertices. An isolated optional vertex can be omitted: its contribution to
both detectors' miss counts cancels in their difference. This equivalence
does not reclassify an unavailable observed object as absent.

After adding a multiset S of optional references, write the ranks rA(S),rB(S)
and D(S)=nA-nB+2(rB(S)-rA(S)). With t optional slots remaining, descendants
lie in [D(S)-2 min(t,nA-rA(S)), D(S)+2 min(t,nB-rB(S))], intersected with the
unchanged shared-prediction bound. Each added right vertex raises either rank
by at most one and never lowers it. Pruning is sound only when this entire
enclosure cannot improve either incumbent. Rank changes need not differ
after the first addition; neutral intermediate worlds cannot simply be dropped.

Image uncertainty sets remain independent Cartesian factors under the
declared contract. Summed image witnesses form an admitted case world and
their sum divided by full case size gives the case mean. Attaining a universal
endpoint proves that endpoint exact for the stated family. Failure to find it
would establish only a search gap. The primary full case retains a wider
universal enclosure than its attained interval; opposing worlds suffice to
establish its decision ambiguity without proving both full-case extrema.
