# Bounded endpoint audits
Document ID: reiyah.adaptive-audit.mathematics. Version 0.1.0.

Let L_i <= D_i <= U_i be the declared reference-family endpoints, each within the
known symmetric bound [-B_i,B_i]. The target is the mean over all original units.
Zero-bound units contribute exactly zero and remain listed. Let n be the number
with positive B_i and M=max B_i. The n active units are uniformly permuted.
If n=0 the exact result is exclusion at zero with no query.

For support use x_i=(L_i+M)/(2M); for exclusion use x_i=(M-U_i)/(2M).
Both scores belong to [0,1]. In each direction test the null mean(x)<=1/2.
Rejecting the first supports mean(L)>0; rejecting the second implies mean(U)<0.
The full logical interval includes queried L_i/U_i and unqueried -B_i/+B_i.
Its sign check precedes statistics and uses tighter unit bounds than the common
statistical range. This deliberately supplies a competent exact comparator.

Before draw t+1, set S=sum of that direction's previously observed scores and
m=(n/2-S)/(n-t). For 0<m<1 multiply wealth by 1+lambda*(x-m).
The fixed arm uses lambda=1/(2m).
For ALPHA, let eta0=3/4, c=1/8, d=10 or 100 and
epsilon=c*floor(2^24/sqrt(d+t))/2^24. The floor is computed exactly by integer
square root of floor(2^48/(d+t)). Set
eta=min(1,max((d*eta0+S)/(d+t),m+epsilon))
and lambda=(eta-m)/(m*(1-m)).
Only past observations enter the stake. The publication's sum is interpreted
as the previous observations, as explicitly stated in its pseudo-algorithm.

Because 0<=lambda<=1/m, the factor is nonnegative for every allowed x in [0,1].
Under the fixed finite-population null, E[x_next | past] <= m, so conditional
expected factor is <=1. Nonnegative wealth begins at one. Ville's inequality
gives <=1/40 chance of ever reaching 40 under each null. A union bound yields
<=1/20 for the two endpoint claims for one chosen procedure on one population.
No belief about independence of image values or correctness of a proxy is used.
A declaration about an interval is conditional on the validity of its endpoints.

Boundary handling avoids division by zero. For m>=1, bet zero. For m=0,
use factor 1 if x=0 and enter an absorbing null-impossible state if x>0.
For m<0, past observations already make that null impossible. A null-impossible
state is represented explicitly, not as a numeric infinity or missing value;
under the null it has zero probability. It may trigger the statistical direction
only after the exact check. Wealth zero is absorbing until such an impossible
event. Full census still returns the exact endpoint result. Boundary behavior
is checked on authored controls.

At every prefix apply: exact support/exclusion first; full-census unresolved
second; statistical conflict third; single directional crossing last.
If nothing applies, continue. The stored endpoint interval at full census
can remain unresolved even when every unit has been queried. No missing state
is converted to a known outcome. Six-unit probabilities use 1/n!; large-path
averages are descriptive across frozen seeds, not expectations or coverage proofs.

Source: Stark, ALPHA, arXiv 2201.02707v9, sections 2.2, 2.2.1, 2.3, 2.5.2 and 3.
The finite-population endpoint application, exact comparator and rational
epsilon convention here are explicit Reiyah choices. This does not establish
a new statistical theorem or independent scientific verification.
