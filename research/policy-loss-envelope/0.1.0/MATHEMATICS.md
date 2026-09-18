# Exact penalty envelopes and complete ties

Version `0.1.0`. Let a retained threshold cell have false positives F and
misses M. Its loss at nonnegative penalty share p is

`L(p) = F + (M-F)p`, for `0 <= p <= 1`.

Dividing the totals by the same 64-image allocation changes neither its
optimizer nor the comparison sign. For p<1, multiplication by 1/(1-p)
gives the equivalent loss F + lambda M, where lambda=p/(1-p). The p=1
endpoint represents miss-only loss and is retained directly.

For a candidate line i to minimize loss, it must satisfy, for every j,

`(F_i-F_j) + ((M_i-F_i)-(M_j-F_j))p <= 0`.

Each constraint is a closed half interval, the entire domain or an
impossibility. Their exact rational intersection with [0,1] is the complete
minimizing domain of i. An empty intersection means never minimal. A singleton
is retained as a point-only optimizer, even if another policy dominates it
away from that endpoint. Identical cost lines retain every cell identity.
No Pareto-frontier shortcut is allowed to discard zero-weight endpoint ties.

The source loss is constant within each already verified strict-confidence
threshold cell. Those cells cover [1/4,1], including the singleton threshold
one; they are not assumed to provide comparable calibrated probabilities.
The finite set of attained FP/FN pairs is the whole available policy class.
No unobserved below-floor output or arbitrary score recalibration is added.

Take the union of both envelopes' domain boundaries. On any resulting open
penalty interval, each optimal loss is affine, so their difference is affine.
Add its exact zero if that zero is internal. Also add the original shared-
cutoff difference's zero. The final partition contains every singleton
boundary and every intervening open interval. All optimizer sets, affine
coefficients, ties, signs and changed original-cutoff conclusions are retained.
This is a continuum calculation, not interpolation from a numerical grid.

The separate checker sorts loss lines by decreasing slope. For equal slopes
it retains the smallest intercept in the hull construction; it then restores
all identities by evaluating every original line at each boundary and probe.
Successive exact line intersections locate the lower hull, with superseded
segments removed. The checker recovers every original line's equality domain
against this hull and compares it with the inequality-based construction.

For every reported open cell, the chosen optimizer is no greater than every
original line at both closed endpoints. The difference between any two lines
is affine, so these endpoint inequalities prove dominance throughout the
cell. An interior optimizer tie must agree at both endpoints as well. The
same affine argument checks both comparison signs. Direct singleton checks
retain all boundary ties and prevent a strict claim at a zero.

The independently optimized nominal envelopes here are equal at p=0 and
p=1/17. New is lower only on (0,1/17); old is lower on (1/17,1]. In the
equivalent miss/FP parameter, the nonzero tie is lambda=1/16. At p=1/2,
the weighted totals are 207/2 and 210/2, or the previously reported unit
totals 207 and 210 after multiplying both by two.

These are retrospective minima against one exposed reference convention.
They are not measured performance of a threshold-selection algorithm on new
data. Earlier uncertain-reference results involve their stated policy pairs;
they are neither erased nor silently transferred to independent thresholds.
