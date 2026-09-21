# Exact predicates for a declared nominal reconstruction

Document: reiyah.nominal-separation.method, version 0.1.0. Status: exploratory.

For input latitude and longitude, the reporting sphere has R = 6,371,008.8 m.
The binary64 operation order is `phi = radians(latitude)`,
`lam = radians(longitude)`, `h = R*cos(phi)`, then
`XYZ = (h*cos(lam), h*sin(lam), R*sin(phi))`. Interpret the resulting finite
binary64 components as exact rationals for subsequent arithmetic. Do not round
coordinates to CSV decimal precision. The reference also checks a colatitude
parameterization to 1 micrometre numerically; this is not a physical error bound.
The pinned runtime and package versions define the tested compilation environment.

This spherical chord model omits altitude, datum residuals and body geometry.
Affine intersample paths can leave the sphere. Neither omission is asserted to
approximate physical separation within a specified error. Changing projection,
reference point, time convention or interpolation defines a different experiment.

On each union interval [l,r], normalized time u belongs to [0,1]. Subtract ego
from target to get d(u) = a + uv. Squared separation is

```text
q(u) = A*u^2 + 2*B*u + C
A = v dot v >= 0; B = a dot v; C = a dot a.
```

Separation is nondecreasing on the interval exactly when B >= 0, with A = 0
giving constant distance. If B < 0, the minimum occurs at
u* = min(1, -B/A). All tests and minimum times use rational arithmetic. Endpoint
agreement or increasing endpoint distance alone is insufficient. The conventional
implementation instead constructs relative per-nanosecond slopes, solves for
the absolute-time minimum and walks overlapping source segments without union
knots or producer geometry imports.

Let D = max over s <= t of [distance(s) - distance(t)]. On any affine segment,
the norm is convex, so its maximum is at an endpoint and it has at most one
minimum. Maintain the maximum of all endpoints through the current left boundary.
Subtract the current segment minimum from that prefix maximum. The largest such
difference is D: within the current segment the only possible earlier peak is
its left endpoint, already included. This proves completeness over the entire
continuous nominal reconstruction, not only sampled endpoints.

For rational q >= 0, integer arithmetic encloses sqrt(q) at scale 10^12 per m.
Set k = floor(sqrt(floor(q*10^24))). The lower endpoint is k/10^12; the upper
is equal if its square equals q, otherwise (k+1)/10^12. The checker verifies
the squared inequalities. Each decrease has a conservative enclosure of width
at most 2 picometres; taking maxima preserves that bound. These tiny widths
describe arithmetic enclosure of the declared model, never sensor accuracy.
Public prose rounds to meaningful metre precision. A witness attaining the
largest lower endpoint is retained; it is within the reported enclosure of D,
without an unsupported assertion about exact ordering of nearly tied radicals.

The minimum uniform scalar adjustment that permits some nondecreasing function
is delta = D/2. Necessity: if |h-d| <= delta and h(s) <= h(t), then
d(s)-d(t) <= 2*delta. Sufficiency: h(t) = max(0, prefix_max(d)(t)-delta) is
nondecreasing and within delta whenever 2*delta >= D. This is a standard
unweighted L-infinity isotonic feasibility principle, with the continuous
trajectory extrema handled explicitly here. It is not a new regression theorem,
an estimate of real measurement noise, or proof that repaired scalar distances
can be realized by admissible physical vehicle trajectories.

All per-interval states and maximum-reversal witnesses remain. One interval with
B < 0 is a complete counterexample to the universal nominal premise. A pass
requires every interval. Physical clearance and physical maneuver interpretation
remain unresolved without applicable joint pose, reference, clock and motion
evidence, regardless of either arithmetic verdict.
