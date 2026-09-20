# Exact conditional clearance range, version 0.1.0

This is a scalar mathematical observation model, not a vehicle dynamics model.
Times and clearances are exact rational seconds and metres. The signed quantity
is road-projected lead rear minus ego front. Supplied intervals must already
account for reference points, geometry and position errors. They do not do so
merely because a caller labels them clearance. All study inputs are authored.
Physical qualification remains unresolved in every result.

Let ordered observations be `(t_i, l_i, h_i)`. A world is `(f, delta)` with one
common offset `delta` in `[-tau,tau]`, intervals
`l_i <= f(t_i + delta) <= h_i`, and `|f(u)-f(v)| <= K |u-v|` on the real line.
The supplied global bound licenses extrapolation beyond observations. It bounds
relative clearance rate, not the ego speed alone. Per-sample jitter, drift,
acceleration, collision physics, actor association changes and probabilistic
coverage are outside this model. The obligation is `f(t) >= d` for every
`t in [a,b]`, including endpoints and equality.

Write `v(s)=f(s+delta)`. Define

```
L(s) = max_i (l_i - K |s-t_i|)
U(s) = min_i (h_i + K |s-t_i|).
```

Feasibility is equivalent to `l_i <= h_j + K |t_i-t_j|` for every ordered pair.
Necessity follows from the Lipschitz inequality. For sufficiency, this condition
makes both L and U satisfy every observation interval. Finite maxima/minima of
K-Lipschitz functions are K-Lipschitz; each envelope is therefore a feasible
global signal, and `L <= v <= U` for every feasible v. Inconsistent inputs are
not vacuously supported. No observations or absent assumptions remain blocked.

Let `H=b-a`. The attainable extreme minimum clearances are

```
m_low  = min_{s in [a-tau,b+tau]} L(s)
m_high = max_{x in [a-tau,a+tau]} min_i [h_i + K dist(t_i,[x,x+H])].
```

For m_low, the union of shifted horizons is exactly the expanded interval.
Choose a minimizer s and any admissible delta with `s+delta in [a,b]`;
`f(t)=L(t-delta)` attains it. For m_high, U is simultaneously maximal over
all times. Minima commute over time and sample index, yielding distance to
the shifted interval. A maximizing x gives `delta=a-x` and
`f(t)=U(t-delta)`. This preserves a single clock offset throughout a world.
Expanding the horizon is correct for the lower extremum but not the upper;
using it for both can falsely report contradiction.

The producer enumerates cone corners and affine-line intersections, then
evaluates the actual envelopes (extra candidates cannot change the extrema).
The separate reference partitions at absolute-value/interval-distance corners
and solves each two-variable linear program by enumerating feasible vertices.
It imports neither producer arithmetic nor its candidate enumeration. Exact
rational arithmetic avoids tolerance changes at the decision boundary.

`supported` means `m_low >= d`; `contradicted` means `m_high < d`; otherwise
`unresolved`. Extremal trajectories are actual model witnesses, not just bounds.
For an unresolved result, one horizon time has different values in the two
opposing witnesses. A same-time clearance measurement with absolute error
strictly less than half that separation distinguishes these two explanations.
It is not claimed to resolve every other feasible world or to be feasible to
acquire. Clock registration for that new measurement is an additional premise.

Uniform extra interval error epsilon expands every interval by epsilon without
changing K or tau. Then L decreases and U increases by epsilon, so the extrema
become `m_low-epsilon` and `m_high+epsilon`. For an already supported case,
`m_low-d` is the exact nonnegative additional allowance, equality included.
For a contradicted case, contradiction persists only for
`epsilon < d-m_high`, a strict boundary. These are conditional error allowances,
not estimates of sensor error or disturbance tolerance of a dynamical system.

The arithmetic and evidence binding do not calibrate their premises. Before a
physical study, obtain provenance-bearing projected bumper error bounds,
common-clock offset bounds and a relative-motion envelope covering the horizon.
For example, two observations of six metres two seconds apart do not rule out
a dip to four metres halfway between when the supplied rate bound is two metres
per second. This is a permitted authored signal, not an observed vehicle event.
