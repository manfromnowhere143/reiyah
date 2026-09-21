# Encoding-aware native-grid fidelity, 0.1.0

Status: exploratory mathematical implementation. This packet is a development
regression, not a prospective empirical study or a physical uncertainty model.
Both decision implementations and this proof are authored by the same agent.

## Question and contract

Given a stored scalar signal, can its coarse affine reconstruction replace the
native affine reconstruction within a declared uniform error tolerance? An answer
can permit that recorded-data approximation, reject it, or request another native
stored value. No physical control or runtime deployment follows.

Native times t_0 < ... < t_(n-1) are exact common-clock rationals. Each native value
is q*z_i, with positive rational quantum q and integer z_i in a finite legal
encoding range [m,M]. Between native knots the declared reconstruction is affine.
Observed indices pin their integers. Availability is explicit and separate from
whether a value has been logically revealed. Coarse indices include both endpoints;
their observed values define a fixed affine baseline b(t). It is never refitted
after later replies. The rate premise is |x(t)-x(s)| <= K*|t-s|. The question is
E <= tau, where E=max_t |x(t)-b(t)|, K>=0 and tau>=0.

The baseline need not fall on the encoding lattice. Affinity on each native
interval implies E=max_i |q*z_i-b_i| exactly. It would be unsound to allow
unobserved bends within these intervals, or to replace the original rate bound
with a residual-rate bound and call the relaxation exact.

For NCOM this packet uses q=1/10000 m/s and legal signed integers
[-8388607,8388607]. -8388608 is an invalid sentinel. Encoding range and unit
resolution are not sensor error bounds or physical acceleration guarantees.
Recorded-rate consistency is checked separately against every stored native value.

## Exact integer path family

Let c_i=floor(K*(t_(i+1)-t_i)/q). The native rate constraints are exactly
|z_(i+1)-z_i|<=c_i. Let D_ij sum c over the unique path from i to j.
In general this sum differs from floor(K*|t_i-t_j|/q).

With known integers v_j, the tight coordinate bounds are

    l_i = max(m, max_known(v_j-D_ij))
    u_i = min(M, min_known(v_j+D_ij)).

The family is empty iff any l_i>u_i. Otherwise l and u are integer feasible
trajectories and each coordinate projection contains every integer between them.
More generally integer boxes [a_i,d_i] on this path are feasible iff
a_i-d_j<=D_ij for every ordered pair. Propagating all lower and upper bounds
constructs feasible integer extremes. A linearly interpolated feasible native
sequence meets the original continuous rate premise.

## Tight error range and witnesses

Maximum error is max_i(max(b_i-q*l_i,q*u_i-b_i)); one of the full l/u sequences
attains it. An empty family is inconsistent premises, never a supported claim.

For minimum error write B_i=b_i/q and epsilon=E/q. The band constraints become
ceil(B_i-epsilon)<=z_i<=floor(B_i+epsilon). Tight original l/u absorb all
domain and pin interactions. Their necessary and sufficient band conditions are

    epsilon >= l_i-B_i and epsilon >= B_i-u_i;
    ceil(B_i-epsilon)-floor(B_j+epsilon) <= D_ij for every i,j.

For A=B_i and C=B_j+D_ij, the last inequality asks for an integer in
[A-epsilon,C+epsilon]. Its least nonnegative epsilon is

    max(0, (A-C)/2 + dist((A+C)/2, integers)).

Taking the maximum of all these rational thresholds and zero gives the exact
minimum. At that error, propagate the intersected bands; their lower extreme
provides a complete attaining sequence. The i=j terms include ordinary lattice
rounding. Using only maximum observed residual would miss this restriction.

The conventional arm computes capacities independently, uses forward/backward
interval propagation, then binary searches exact feasible error bands. If L is
the least common multiple of denominators of b_i/q, every achievable error is a
multiple of q/L. Search integer multiples between an infeasible negative bound
and the error of a feasible path. This terminates at the same exact minimum
without importing the Reiyah formula. It constructs its own witnesses.

These are difference-constraint methods, not a claim of a new optimization class.
Classical temporal-constraint networks supply relevant consistency and tight-domain
background. The lattice objective and finite reply analysis above are derived here.

## Complete obtainable reply sets

For available unobserved native index h, feasible replies are precisely the
integers y in F=[l_h,u_h]. Define safe native bands

    a_i=ceil((b_i-tau)/q), d_i=floor((b_i+tau)/q).

The reply-conditioned bounds are max(l_i,y-D_ih) and min(u_i,y+D_ih).
Thus every remaining world meets the tolerance exactly when:
for each l_i<a_i, y>=a_i+D_ih; and for each u_i>d_i, y<=d_i-D_ih.
Intersect these requirements with F to obtain the universal-support interval A.

Intersect every original node box with its safe band and propagate. If feasible,
its projection S at h contains precisely replies permitting at least one
within-tolerance world; otherwise S is empty. Replies in A are supported,
in S outside A unresolved, and in F outside S contradicted. Canonical partitions
have closed integer endpoints. Adjacent encodable values have no possible real
reply between them. Guaranteed resolution means no integer reply is unresolved.

The conventional arm independently projects each possible single-node violation,
z_i<=a_i-1 or z_i>=d_i+1, using path propagation. Their union marks replies
permitting a violating world. It intersects that classification with the separately
propagated safe-world projection and partitions all transition integers.
No Reiyah envelope or partition routine is imported.

A legal encoded reply outside F contradicts the rate/observation premises.
An unencodable value is an invalid source reply. Unavailable or unregistered
queries are refused; neither is replaced by zero.

## Protocol and checks

Both arms choose the available unobserved index with largest possible absolute
native residual, with earliest index breaking ties. After one actual logical
reveal they recompute the entire family. They stop only at a resolved conclusion,
inconsistent premises, or no obtainable remaining query. This is a declared
heuristic, not a minimum-query or optimal-acquisition theorem.

Both arms share parsing, source preparation, serialization and a workflow shell.
Their solvers are distinct. A separate protocol checker does not invoke that
shell or its oracle. It checks source values, baseline, priority, reply, complete
partition, every bound/witness stage, stopping and accounting. It uses the
conventional solver, so it is not an independent check of every conventional bug.
Direct exhaustive enumeration of small integer worlds tests both solvers,
priorities, all reply classes, witnesses and endpoints without either solver
defining expected answers. Retain that scope and the common authorship.

Related interval-STL resource allocation and corrective-constraint extraction
already investigate where improved observations help. Baird et al. and Besset
et al. are context, not reproduced comparisons or a basis for novelty claims.
See the retained version/scope/rights ledger in sources.json.

