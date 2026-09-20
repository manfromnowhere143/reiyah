# Relational clearance contracts

Document ID: reiyah.frontier-expansion.method. Version 0.1.0.
Status: exploratory. This is an offline authored development model.

A natural-language statement is not automatically a specification. This packet
accepts one explicitly authored interpretation: **the lead rear bumper remains
at least d metres ahead of the ego front bumper throughout [a,b]**, in a declared
common one-dimensional road coordinate. It does not parse reasoning, infer lanes,
decide which actor is the lead, judge traffic rules, or issue vehicle commands.
A satisfactory clearance alone establishes neither safe driving nor correct
reasoning. Direction, bumper reference, units, frame, clock offsets and the
intended actor must be supplied; no defaults turn missing evidence into truth.

## Conditional mathematics

Let W be the explicitly enumerated, exhaustive **authored** set of common
scene alternatives. Each w binds both traces, an actor identity and clock
shifts. Define g_w(t) = s_lead,w(t) - s_ego,w(t). The obligation in that world is

`for every t in [a,b], g_w(t) >= d`.

The threshold is inclusive. A gap strictly below d refutes the obligation.
An exact rational representation avoids floating-point boundary changes.
A trace timestamp plus its declared clock shift is the common time.
The current representation expresses finitely many alternatives, not a
continuous clock-error interval, a physical reachable set or a probability law.

For explicitly piecewise-linear traces, g_w is affine between consecutive
knots in the union of the two aligned grids. Its minimum on every nonempty
overlapping segment occurs at an endpoint. The producer evaluates the merged
knots, clipped to the requested interval. The conventional checker instead
intersects every ego/lead segment pair and evaluates each overlap's endpoints.
Both preserve the same w; they never combine one alternative's ego with another's
lead or select a favorable actor after seeing the result.

Interpolation is an assumption, not something validated by these samples.
With `unspecified` interpolation, only coincident supplied sample times are
usable. A below-threshold sample can refute a continuous obligation. Safe
samples cannot establish it between observations. Neither path extrapolates
beyond its input horizon. A violation on an observed part refutes a longer
obligation; a satisfactory partial trace leaves the remainder unresolved.

| Returned state | Conditional meaning |
| --- | --- |
| supported | Every listed world satisfies the complete obligation under the stated interpolation |
| contradicted | Every listed world has a checked violation; the violation times may differ |
| unresolved | Worlds disagree, a relevant horizon/inter-sample segment is unknown, or some alternatives lack inputs |
| blocked | Every world lacks a bound ego/lead trace or actor identity |
| inconsistent_premises | The declared exhaustive world set is empty; no vacuous support |

Malformed input is rejected as `invalid`, separately from these semantic states.
The missing-world and physically impossible-world problems are not solved by a
checksum or by enumerating a convenient list. Real inputs need qualified bounds
and an appropriate family before these conditional conclusions become applicable.

## What is and is not new

Exact affine minimization, three-valued monitoring and incomplete-trace semantics
are established methods. This implementation is a small Reiyah extension with
explicit identity/time/missingness contracts and checked evidence bindings.
It is not a new temporal-logic theorem, a full STL engine, a replacement for
RSS, or a comparison against the Drive the Thoughts LLM monitors.

The comparator has the same inputs, motion assumptions, threshold and conclusion
obligations. Agreement is the intended correctness check; neither simplicity nor
proof output is asserted to reduce full workflow cost. Authored bad shortcuts
(ego-only inference, endpoint-only inspection, discarded worlds or automatic
interpolation) are rejection demonstrations, not competent baseline opponents.
