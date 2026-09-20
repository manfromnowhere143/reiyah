# Public motion qualification plan

Document ID: reiyah.public-motion.plan. Version 0.1.0.
Lifecycle status: exploratory. Date: 20 September 2026.

This is the next bounded gate of the [roadmap](../../../docs/ENGINE_ROADMAP_2026-09-20.md):
qualify a public actor/ego source before a physical clearance comparison.
The earlier Drive the Thoughts scope lacked an identified lead trajectory.
One new source, the official NGSIM US-101 table, supplies explicit vehicle
identifiers, common timestamps, front-centre positions, lengths and preceding
identifiers. Published metadata was reviewed before any trajectory retrieval.

The privately retained qualification plan and its digest were frozen before
retrieving trajectory rows. Select the first 200 preceding-positive US-101
rows ordered by global_time, vehicle_id and frame_id. Select the first eight
distinct vehicle identifiers in that response and bind their initial preceding
identifiers. Retrieve the union of those identities over their inclusive
two-second windows, retaining the full response. No geometry, margin, speed or
outcome determines selection. These are dependent development cases, not a
representative, reserved or blinded population. The eight cases may share
vehicles and times. They remain allocated if a check fails.

The fixed five-metre/two-second example is inherited from the preceding
research question. It is an authored example, not a legal or safe following
distance. Source inspection exposed only field shapes, row/identity counts and
time coverage before this implementation freeze. The source bytes were
available, so no held-out claim is made.

## Admission decision before a physical experiment

The retained documentation has an approximate accuracy estimate, an explicit
lack of an attribute-accuracy assessment and a possible-gap warning. No
deterministic position/dimension error envelope, common-clock error envelope,
projected bumper geometry or inter-sample motion bound qualifies from these
records. **The proposed continuous physical-clearance experiment is not
admitted.** No physical monitor comparison or safety estimate runs.

A narrower annotation-level interpretation is admissible for investigation.
The [method](METHOD.md) specifies the exact longitudinal proxy and the 21
expected recorded instants. The software checks whether each of all eight
candidates supplies those records with stable identity, lane, dimension and
clock bindings. Only a qualified candidate receives the discrete annotation
calculation. Unknown physical evidence stays unknown whatever that result.

A separate conventional implementation derives selections, joins, reasons and
numbers directly from the same source rows. It shares the strict source-shape
and byte-binding gate. No candidate answer is written as a constant. This is
same-session internal verification and a correctness comparison; it does not
measure engineering-workflow advantage or independent scientific replication.

Before actual calculation: run the authored boundary, missingness, wrong
identity, wrong reference-point, row-order, numerical and result-forgery
controls, plus a finite scalar grid. Freeze code, method, plan, source contract,
query/selection-plan identity, raw source hashes, runtime and supervisor.
Retain every actual result and failure. Code changes after this freeze require
a new explicit freeze; do not repair a result in place.

## Bounds and publication

At most eight allocated candidates, 200 seed rows and 5,000 trace rows; a
5,001-row sentinel response is refused. No whole-corpus completeness is
inferred. Each horizon expects 21 paired samples at 100 ms spacing. The
fetched response can contain additional rows for the same query envelope;
their identities and time membership are checked too.

Execution and checking each have 600 cumulative outer-process seconds,
including failed/retried attempts. Other recorded commands have 120 seconds
each. The recorder enters network denial before offline runtime startup and
uses one owned temporary root. Eight MiB of source payload and 128 MiB of new
artifacts are ceilings; the checkout is accounted separately. Keep five GiB
free. Point samples do not establish an unseen storage peak.

All source bodies, row-derived coordinates and per-case numerical results stay
private. Public code, authored controls, hashes, source metadata and aggregate
findings follow [distribution boundaries](DISTRIBUTION.md). Keep source terms
and their conflicts visible. No source payload receives Reiyah's code license.

The Nisayon handoff motivates deriving observations instead of constant
comparative answers and accounting for temporary files. No sibling code,
records, conclusions or authority enter this study. Preserve the historical
controller, perception kernel, previous failures and all 1,433 reserved images.
No inference, training, media, paid compute, delegation, outreach, deployment
or physical control. Gate A remains operator-unaccepted. Normal reviewed
Reiyah publication and publisher readback are already authorized.
