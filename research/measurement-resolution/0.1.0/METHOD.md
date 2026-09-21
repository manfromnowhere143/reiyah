# Complete response sets for one additional measurement

Document: reiyah.measurement-resolution.method, version 0.1.0.
Status: exploratory conditional mathematics. Physical qualification unresolved.

This is the existing scalar Lipschitz/common-clock contract with one additional
measurement channel. It addresses a specific missing guarantee: whether every
possible response to a query resolves the whole decision family. It is not a
new physical uncertainty calibration, driving monitor or control policy.

Let v be a real K-Lipschitz signal with observations li <= v(ti) <= hi.
Physical-label time is shifted by one unknown common delta in [-tau,tau].
The obligation is v(t-delta) >= d for every t in [a,b]. All quantities are exact
rationals except the continuum of admissible signals. Keep the same delta
throughout each world. Feasibility and original complete bounds use the existing
independently checked cone/LP calculations, reused by exact byte identity.

Write L(s)=max_i(li-K|s-ti|), U(s)=min_i(hi+K|s-ti|). A query at recorded time q
reports y with |y-v(q)| <= e. Its axis must be registered to the same recording
clock as the existing observations. A measurement at a physical time with an
unknown relation to that axis is not this channel. Unavailable or unregistered
queries remain blocked and are not sent to the oracle.

The feasible response set is exactly F=[L(q)-e,U(q)+e]. Necessity follows from
L<=v<=U. Sufficiency follows by taking a convex combination of feasible L and U
to obtain any desired v(q), then choosing an allowed reporting error. Conditioning
on y appends the interval [y-e,y+e] at q. It changes the complete envelopes to

```text
L_y(s) = max(L(s), y-e-K|s-q|)
U_y(s) = min(U(s), y+e+K|s-q|).
```

## Analytic producer

Let B={s in [a-tau,b+tau] : L(s)<d}. If B is empty, every feasible response
supports the obligation. Otherwise define

```text
Y_support = d + e + K * sup_{s in B} |s-q|.
```

The complete family after y is supported exactly when y>=Y_support. To see
this, the new lower cone must reach d at every time where the old lower envelope
falls below d. The supremum can be taken over the closure of B because the cone
is continuous. Enumerate threshold crossings and interval/point atoms exactly;
do not treat a point where L=d as a violating sample. The supremum value remains
necessary even when attained only at a boundary of the open bad set.

Let H=b-a and S be the closed set of window starts x in [a-tau,a+tau] such that
U(s)>=d throughout [x,x+H]. This set preserves the common clock. A sample hi<d
forbids the open interval of starts (ti-(d-hi)/K-H, ti+(d-hi)/K) when K>0.
Subtract these open intervals from the closed start domain. Equality at a
boundary is safe. For K=0, S is the whole domain if every hi>=d, otherwise empty.

If S is empty, every feasible response is contradicted. Otherwise define

```text
Y_safe_exists = d - e - K * max_{x in S} dist(q,[x,x+H]).
```

A satisfying world remains exactly when y>=Y_safe_exists. The upper envelope is
itself feasible and simultaneously maximal at every time; its new query cone
must stay at least d over one allowed window. The maximum exists on compact S.
Its piecewise-convex distance reaches a maximum at an interval endpoint. Hence
contradiction holds for y<Y_safe_exists, with a strict boundary. All other feasible
responses are unresolved. Represent endpoint inclusion explicitly. A query
guarantees resolution only when no unresolved response exists anywhere in F.
No response-width statistic is interpreted as a probability or expected value.

## Separate conventional calculation

The checker projects exact two-variable polyhedra, without importing the
producer's thresholds, forbidden-window subtraction or decisions. For a violating
world it enumerates time pieces split at observations and q, with constraints
L(s)<d and y-e-K|s-q|<d. For a satisfying world it enumerates window-start pieces
split at ti, ti-H, q and q-H, with every original upper-cone window minimum and
the added cone at least d. Bound y by the independently computed feasible
response interval. Project each feasible polygon onto y and retain open/closed
endpoints. Pairwise line intersections enumerate all vertices of these bounded
polyhedra. A centroid of feasible vertices tests strict-constraint feasibility,
including at endpoint faces; a closure alone cannot promote an unattainable
strict boundary. Singleton time/response domains remain valid.

The union of safe and violating projections classifies every feasible response:
safe only is supported, violating only is contradicted, both is unresolved.
It must cover F. Comparing canonical partitions therefore checks an infinite
response set through finite exact geometry, not a grid of sampled answers.
Actual replies are then incorporated and the inherited exact LP independently
recomputes the full attainable minimum range and verifies extremal witnesses.

## Executable reveal experiment and limits

The next authored fixtures supply explicit scalar traces, available query times,
registered clocks and reporting errors. An oracle evaluates those traces only
for requested queries; it never returns constant candidate verdicts. Both arms
receive the same observations, fixed query order and replies, with equal stops
on resolved, blocked, exhausted or inconsistent states. Every stage records the
complete response partition before acquisition and the new complete bounds after
it. Previously acquired observations at the same time are intersected, with both
the acquisition and the merge retained; an empty intersection is inconsistent.

These are authored mechanism experiments, not empirical acquisition savings,
external replication, physical evidence or a held-out benchmark. Both methods
are written in this solo session and share the strict format/custody and oracle
interface. Full file preparation is charged separately from logical queries.
The useful change is a checked universal-resolution test plus real recomputation
inside the declared model. Physical ViF-GTAD uncertainty stays unresolved, and
the closed nominal encounter is not rerun. This checkpoint does not end the
continuing mission.
