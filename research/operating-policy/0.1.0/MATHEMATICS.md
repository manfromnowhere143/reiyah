# Threshold cells, matching and retrospective frontiers

Version `0.1.0`. The [plan](PLAN.md) fixes allocations and scope before scores.

For a retained detection with exact decimal score s, the stricter policy
retains it exactly when s>t. On each interval between successive score events,
including its left endpoint and excluding its right endpoint, the selected
multiset is constant. All equal scores leave together at their boundary.
Adding the singleton t=1 covers the entire closed domain. The common partition
uses events from both models; the individual partitions use their own events.
The export floor excludes any claim below t=1/4.

After filtering, metric identities are assigned by exact car geometry and
occurrence count within each output. Source detection IDs remain in a separate
join. This preserves duplicate multiplicity while making equal multisets share
identities regardless of which scored source occurrences survive. The shared-
prediction bound must concern those metric identities, not arbitrary source IDs.

For an output with n predictions and reference size r, maximum matching m gives
FP=n-m, FN=r-m and unit loss n+r-2m. Removing k predictions can lower matching
rank by no more than k. Hence stricter filtering cannot increase FP or decrease
FN for the fixed reference. It can change their sum in either direction; a
confidence score is not thereby a calibrated probability of a matching error.

For the original reference, retain the original graph and every one-reference
deletion. For each such base with ranks mA,mB, adding one arbitrary reference
gives the sound difference enclosure
[nA-nB+2(mB-min(nA,mA+1)), nA-nB+2(min(nB,mB+1)-mA)].
Take the minimum lower and maximum upper over deletion bases and intersect with
[-s,s], where s counts unshared metric prediction identities. This covers no
edit, insertion, deletion and replacement without assuming independent geometry
for the two detectors. It is a bound, not an assertion that every endpoint is
geometrically attainable.

Temporal optional-reference bounds use the same known ranks and fixed unknown
count as their preceding contract. Every world in the fixed inherited bank is
remeasured under the filtered predictions. An unchanged reference world does
not justify reusing a native certificate whose prediction operands changed.
The conventional and native paths receive the same finite graph.

Per-image bounds and attained worlds sum over a case. For one global edit,
start at the complete nominal total and use the greatest adverse single-image
deviation. Divide by the full allocated image count. Any blocked member retains
the complete-case input block. Opposing worlds require an attained difference
at most zero and another strictly positive; otherwise an enclosing interval
that crosses zero remains a bound gap.

A nominal point (FP,FN) is dominated when another attained point is no worse
in either count and strictly better in at least one. Retain every nondominated
point and every threshold cell attaining it. For each integer FP budget b,
minimize FN among attained cells with FP≤b. Preserve all ties, including points
with equal FN but differing feasible FP counts. If none is feasible, the result
is unavailable. The empty-output policy makes the actual nominal budget grid
feasible, but this property is not assumed by the checker.

Independent model thresholds produce a Cartesian table with each cell's
nominal difference equal to old unit loss minus new unit loss. This separable
identity permits exact reconstruction from both published individual curves.
It does not extend the independently chosen thresholds' nominal claims to
uncomputed uncertain-reference pairs. Minimum losses and matched FP budgets
are retrospective descriptions of this exposed cohort, not estimated generalization,
owner-approved operating targets or policy training.
