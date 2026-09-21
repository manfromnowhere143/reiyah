# Nominal two-vehicle separation decision

Document: reiyah.nominal-separation.plan, version 0.1.0. Status: exploratory.
Freeze this plan, code and input identities before computing new joint geometry.

## Decision and consequence

May an offline evaluator assume that navigation-reference separation is
nondecreasing throughout the complete common time support of ViF-GTAD v2,
scenario 3, ego and BME Honda, under the model below? A counterexample rejects
that premise for this reconstruction. A supported result admits it only for this
exact scope. Do not silently force a monotone trace or choose a favorable window.

The scenario description motivates this question, but does not define a precise
Euclidean reference-point quantity. This is our explicit recorded-data
interpretation, not an adjudication of the authors' physical maneuver, vehicle
safety, bumper clearance or road-longitudinal separation. No five-metre threshold.

All 7,761 ego and 4,437 target rows were exposed in earlier serialization and
clock work. New relational geometry has not been computed before this freeze.
This is development evidence on one dependent encounter, not a held-out trial.
The already selected stream pair is fixed; no additional actor/window search.

## Inputs and model

Use the retained ego GPS_ROS CSV and target MAT numeric coordinates. The lossy
target CSV is not admitted. Bind exact bytes and preserve zero-based source rows.
Parse all records, reject invalid coordinates, clock order, missing fields and
source changes. Unused height, heading and standard deviations do not become
zeros or calibrated bounds. Ego is the documented rear-axle reference; target
is its recorded navigation output reference. No nominal antenna-to-plate offset
is applied and no uncertainty-qualified common body reference is asserted.

Interpret ego GPS week/seconds and target literal calendar labels under the
previous frozen GPS-label convention. No timezone, UTC/leap-second, fitted clock
or physical synchronization correction. Independently reproduce all 2,504 prior
target-to-ego source brackets and written-ROS constraints. Never replace that
mapping with a constant offset. Direct joint geometry uses the GPS-label axis.

Project latitude/longitude onto the explicit nominal sphere in METHOD.md.
Interpolate each actor affinely in its own projected XYZ coordinates between
consecutive source timestamps. This is an authored reconstruction, not a measured
motion law or qualified physical datum. Restrict to the intersection of supports.
Every timestamp is classified before/within/after it. A timestamp outside the
intersection can still provide a boundary interpolation bracket; report used
source rows separately. No extrapolation, smoothing, imputation or selective gap
removal. Reject absent positive-length overlap.

## Frozen outputs and comparison

Compute every merged interval, exact monotonicity disposition, first reversal,
maximum earlier-to-later separation decrease and its witness. Report start/end
distances and the minimum scalar uniform repair compatible with a nondecreasing
distance function. Retain complete interval coefficients, source indices,
extremum times and arithmetic enclosures privately. Public aggregates bind them.

The Reiyah arm uses union knots and normalized quadratic coefficients. A
competent conventional arm uses overlapping source segments and per-nanosecond
velocity vectors. It independently parses clocks, compiles coordinates and
computes every extremum. Both use identical evidence, geometry and mathematical
opportunities, in source order. A separate implementation is not independent
authorship: both are written in this solo session and share the MAT decoder,
custody helpers, Python libraries and explicit model. Conventional parity is a
valid negative result. Do not present the conventional arm as an empirical oracle.

Compare complete traces and results, not just verdict labels. Distinguish the
logical interval prefix sufficient to reject the premise from all intervals
actually evaluated and all source records loaded. The full data were already
acquired; no acquisition saving can be inferred from logical early rejection.
No separate measurement acquisition or experimental physical intervention runs.

Directed controls cover interior minima hidden by increasing endpoints, zero
and stationary distance, global reversal, clipped/staggered support, exact tiny
derivatives, coordinate/clock rejection, source tampering and result mutations.
No repeated authored random sweep or closed-study rerun. Retain every failure;
frozen method corrections require an explicit successor freeze.

## Resources and claims

Use the existing pinned Python/NumPy/SciPy runtime offline, network denied before
execution/checking. Limits remain 128 MiB new owned artifacts and temporary
bytes, 8 MiB newly captured/derived sources, 5 GiB free disk floor, 600 cumulative
execution seconds and 600 cumulative checking seconds, failures included. Other
commands have 120-second limits. Reuse prior immutable source bodies by reference.
Record source preparation, command wall/CPU, arm timers, storage and later
integration/readback separately; never add nested timers twice. Active effort,
charges, energy, peak memory and complete workflow economics remain unknown.

All 1,433 reserved images stay closed. No media, inference/training, paid
compute, hardware, deployment, outreach, delegation or sibling imports. Preserve
the historical controller, all negative findings and the operator-unaccepted
Gate A. Normal guarded integration/push/readback is already authorized.
