# Recorded reconstruction, complete families and a stronger conventional arm

Document: reiyah.navigation-measurement.method, version 0.1.0.
Status: exploratory. The question and selector were frozen before sample capture.
This method is specified before decoding the sample's numeric outcomes.

Write v(t) for the declared affine reconstruction of original encoded north
velocity and b(t) for the 10 Hz candidate. The conditional premise is that v is
K=5 Lipschitz in m/s per second; the full reference will test this on every
selected native interval. It is not a physical acceleration guarantee. Observed
integer values have exact stored-value semantics, not zero physical error.

The Reiyah arm uses r=v-b with Q=K+max|b'|. Its uncertainty family contains all
Q-Lipschitz residuals agreeing with acquired samples. This is a conservative
relaxation of the original K-Lipschitz velocity family, since it discards known
baseline shape. The result is complete for that declared residual family, not
necessarily tight for original velocities or their fixed native-grid interpolant.
An unresolved residual witness need not be admissible under the stronger original
velocity premise. Do not promote that witness to physical or stronger ambiguity.

For error tolerance e=1/20 m/s, the two scalar margins are e-r and e+r. Their
observations and replies are exact complements, and the same recorded clock
has zero offset within this comparison. Both must stay nonnegative. Every
observation and query lies in the horizon. All observations are exact values.
If an observed residual is outside [-e,e], every remaining world violates the
obligation. Otherwise a satisfying world exists: clip any feasible Lipschitz
signal into [-e,e]. Clipping preserves the Lipschitz constant and every observed
value. Thus joint support means both one-sided checks support; joint contradiction
means either contradicts; otherwise uncertainty remains. This argument does not
apply unchanged to arbitrary shared clock uncertainty or coupled vector signals.

Combining full one-sided response partitions uses the same response r in both
transforms. It does not independently choose favorable responses for the signs.
The partition covers every feasible real reply, with explicit endpoint inclusion.
The original exact LP/polyhedron calculation checks both transformed margins.
The minimum attainable uniform error is the largest absolute observed residual;
clipping proves attainability. The maximum comes from the two envelope extremes.

## Conventional method retains more of the same information

A competent conventional method can use K directly and retain b(t). It receives
exactly the same source prefix, coarse samples, measurement opportunities and
original rate premise. It is not restricted to Reiyah's residual relaxation.
Its envelopes are L=max_i(v_i-K|t-t_i|), U=min_i(v_i+K|t-t_i|). Enumerating their
affine pieces together with baseline knots gives exact maximum possible error
max_t(max(b-L,U-b)). The minimum attainable error is the maximum observed
|v_i-b(t_i)| when b is K-Lipschitz: min(max(b,L),U) is K-Lipschitz, interpolates
the observations and attains that minimum. If coarse b violates K, retain the
inconsistent original premise rather than applying this lemma.

For a candidate query, the conventional response range is [L(q),U(q)]. Unsafe
responses are projections of two-variable strict polyhedra expressing the
existence of a time where either the lower envelope falls below b-e or the upper
envelope exceeds b+e. Split at observations, q and baseline knots. Safe worlds
exist exactly for replies within [b(q)-e,b(q)+e], if earlier observations admit
one, by clipping between the K-Lipschitz functions b-e and b+e. Canonical response
cells combine safe/unsafe membership. This is a continuum calculation, not a
finite reply grid. It uses original velocity coordinates, separate arithmetic
and a stronger retained family than the Reiyah residual arm.

Each method queries the available native instant with greatest current possible
absolute residual, breaking ties by earliest index. The same rule may select
different instants because one method keeps sharper information. Retain these
differences and all costs. Agreement means sound conclusions against the full
recorded reference; it does not require artificially equal bounds or query counts.
If the conventional method needs fewer observations, that is a useful negative
finding about the current Reiyah representation. This demanding comparator choice
is fixed before numeric outcome inspection, not substituted after results.

## Input and reference scope

The narrow Python decoder retains invalid, status-only, unsupported, asynchronous
and unregistered-clock records. It uses only a preceding valid minute anchor,
matching the manufacturer's streaming interface, and never backfills earlier
records from future status information. A separate wrapper of the pinned,
unchanged manufacturer C decoder checks selected synchronous values, validity,
source-byte positions and registered times. C floating output is checked against
exact encoded integer units and millisecond ticks, with stated floating-rounding
bounds; it does not turn floats into exact rationals silently.

The baseline decision calculations and wrappers are authored in this solo session;
only the manufacturer decoder has separate authorship. No external replication
or independent scientific acceptance is claimed. All source decoding/preparation
is charged even when fewer logical reveals are used. The full-data reference
checks every selected native interval, original rate premise and both-sided
interpolation error. The five adjacent segments are dependent parts of one
supplied example. Physical provenance, calibration and economic value remain
unresolved. No held-out samples or reserved images are opened.
