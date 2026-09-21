# Exact association constraints

Document ID: `reiyah.clock-alignment.method`. Version: `0.1.0`.

Let strictly increasing ego GPS labels be g[0..n-1] and their paired written
ROS labels be r[0..n-1]. All source decimal/calendar labels are represented
exactly in nanoseconds. For a target GPS label t with g[i] <= t < g[i+1], the
recorded association is the ordered pair of source rows (i,i+1).

A constant offset c preserves that association exactly when

    r[i] <= t+c < r[i+1], or c in [r[i]-t, r[i+1]-t).

At t=g[n-1], the terminal endpoint requirement is c=r[n-1]-t. Times outside
[g[0],g[n-1]] are input-blocked, not extrapolated or counted as positive cases.
No distance, position or physical time error is inferred from this arithmetic.

The full feasible set is the intersection of all admitted intervals. Its lower
endpoint is the maximum lower endpoint; its upper endpoint is the minimum upper
endpoint, closed only when every interval attaining it is closed. All lower
endpoints are closed. The set is empty when lower>upper or when lower=upper and
the upper endpoint is open. Otherwise the midpoint (or the shared closed point)
is a constructive feasible constant. This is standard interval feasibility,
not a new mathematical primitive.

After k logical reveals, the prefix intersection contains every constant that
could satisfy all records. An empty prefix therefore refutes the existence of
any valid constant for every possible completion of unrevealed constraints.
A nonempty prefix cannot support the full decision until all required records
are revealed. Two extremal source constraints suffice to witness emptiness in
one dimension; they exclude the complete constant family, not merely two chosen
candidate explanations. Adding constraints cannot restore feasibility.

The implementation and conventional scan calculate the same standard result
through different code paths. The complete reference uses Fraction clocks and
a monotone merge instead of the producer's Decimal clocks and binary search.
They share the existing SciPy MAT decoder and byte-identity utility. All three
were authored by the same session; their agreement is internal verification.
Clocks/rows are dependent within one scenario. Do not count rows, prefixes,
controls or the two arms as independent scientific experiments.

Preserving brackets is a deliberately narrow engineering contract. It does not
prove equal interpolated values within the bracket, a correct GNSS time scale,
physical simultaneity, bounded sensor latency or continuous physical clearance.
Rejecting every constant in this family does not reject affine/nonlinear mappings
or all alternative alignment methods. No such alternative is optimized here.
