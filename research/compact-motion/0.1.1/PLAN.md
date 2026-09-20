# Compact motion serialization and clock qualification

Document ID: `reiyah.compact-motion.plan`. Version: `0.1.0`.
Status: exploratory development. Date: 20 September 2026.

## Question and allocation

Can a compact public two-vehicle record preserve the geometry and clock
information needed by the existing physical measurement contract?

ViF-GTAD v2, Zenodo record 7808255, supplies the selected files. The metadata-only
[selection](selection.json) chooses the smallest ego GPS CSV among its five
scenarios, then the alphabetically first target CSV in that scenario. This is
scenario 3 and BME Honda. Inspect both complete streams; do not select a favorable
time window. These are dependent records from one scenario, not independent
drives or a population performance estimate.

The first data row of each CSV was exposed to establish its schema. The target's
coarse coordinate text motivated the separately frozen
[companion selection](companion-selection.json), before that MAT payload was
retrieved. The README describes CSV and MAT as the same data in different formats.
The MAT variable name, dimensions, header row and second-row types were then
inspected. These exposures precede the analysis freeze; this is not a held-out
test or a wholly prospective source choice.

## Frozen analysis

1. Census every selected CSV record, its numeric missing/nonfinite fields,
   coordinate text precision, time ordering and ego navigation status.
2. Compare target CSV and MAT strictly by row and exact timestamp text. If lengths
   or timestamp identities disagree, report that failure and do not repair the
   correspondence by matching nearby coordinates or times.
3. On finite matched coordinates, quantify CSV-versus-MAT angular differences and
   nominal spherical displacement. Compare the other numeric columns separately.
   The MAT representation is a serialization reference, not physical ground truth.
4. Compare the ego log's calendar text, header epoch and GPS-week time through
   explicitly named arithmetic. A difference between clock fields is not a
   calibrated latency, timezone correction or synchronization bound.
5. Stop physical clearance admission unless the inherited geometry, joint pose,
   clock and intersample uncertainty requirements actually qualify. No trajectory
   interpolation, actor joining, clearance threshold, vehicle outcome or monitor
   comparison is allocated in this source diagnostic.

## Checking and controls

Use a separately implemented checker for census, temporal differences, MAT/CSV
identity and all reported arithmetic. It may share the pinned SciPy MAT decoder
and byte-binding code, but cannot import the producer's calculations. The producer
uses haversine distance; the checker uses unit-vector chord distance. This is
internal implementation verification, not independent calibration or replication.

Before actual results, test analytic displacement, antimeridian handling,
nonfinite preservation, calendar/epoch arithmetic, nanosecond range, invalid GPS
seconds, malformed rows and source identity. Afterward retain result-mutation
controls. Do not change frozen code to obtain a pass without a new explicit freeze.

## Bounds and completion

Use existing pinned Python, NumPy and SciPy; no installation. Enforce offline
execution/checking before the child runtime. Cumulative process ceilings are
600 seconds execution and 600 seconds checking, including failures. New source
bodies, compressed ranges and derived text stay below 8 MiB; owned artifacts and
temporary files below 128 MiB, checkout separately counted, free disk above 5 GiB.
Ceilings are not duration targets. Retain every failed attempt and unknown cost.

All 1,433 reserved images stay closed. No bags, videos, images, inference,
training, paid compute, outreach, other model, deployment or physical control.
Preserve the controller, closed studies and original completed mission clock.
Finish with exact results, source limitations, costs, relevant checks, reviewed
integration and authorized normal push/readback. No scientific or Gate A
acceptance follows from a test, signature, hash or publication.
