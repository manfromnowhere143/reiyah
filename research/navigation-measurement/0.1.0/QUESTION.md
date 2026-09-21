# Frozen question and source selection, before navigation outcome inspection

Document: reiyah.navigation-measurement.question, version 0.1.0.
Status: exploratory development protocol. 21 September 2026.

Decision: may a consumer replace a 100 Hz encoded north-velocity trace with its
10 Hz linear reconstruction while retaining uniform recorded-velocity fidelity
of 0.05 m/s over the selected one-second interval? This authored tolerance is
0.18 km/h and 500 encoding quanta; it is a numerical reconstruction requirement,
not a safety threshold, customer requirement or physical accuracy bound. Acceptance
would permit this specific reduced representation for that declared fidelity
question; contradiction requires retaining more original measurements. Uncertainty
requires more evidence rather than an invented assurance.

Source is the manufacturer's public example/171019_031603.ncom at
OxfordTechnicalSolutions/NCOMdecoder commit
6bd95e9a5f826556e1c4c0bc586fec3f973c76e3. Capture only its first 72,000 bytes,
starting at byte zero, with supported Range or a deliberately bounded public
GET prefix. The full declared blob is 8,205,840 bytes and will not be fetched.
The partial sample's SHA-256, transport response and incomplete whole-blob
verification must stay explicit. Do not infer physical collection conditions
or a calibration guarantee from a repository example or filename.

Parse every complete 72-byte packet in this fixed prefix, retaining checksum,
navigation status, synchronous/asynchronous type, reported clock and validity.
Choose the first run of 101 consecutive valid structure-A synchronous navigation
records, status 4, with exactly 0.01 s reported-time increments and a resolved
GPS-minute anchor under the published NCOM format. A missing eligible run is
blocked; do not inspect later bytes or substitute a favorable window. Reject
unsupported fields or version interpretation. Decode no new numeric outcomes
until this question record is hash-bound. Retain the complete prefix population
and explain any unsupported records without converting them to zero.

The original encoded velocities define a piecewise-affine recorded function;
this is a reconstruction convention, not a physical motion law. The conditional
global rate premise is 5 m/s^2 on that recorded function. Do not fit or raise this
bound after seeing outcomes. Check every selected original interval in the final
reference: if it is violated, the empirical binding of the conditional decision
is rejected, with the offending interval retained. An authored bound is not a
calibrated physical bound even if this finite recorded trace satisfies it.

Use source indices 0,10,...,100 as coarse knots. Analyze the five adjacent
0.2-second intervals, sharing boundary knots; they are dependent segments of
one example, not five independent physical experiments. In each segment, use
the residual between the original and coarse north-velocity interpolants.
Its conservative rate allowance is 5 plus the maximum absolute coarse slope
in the segment. The coarse knots give zero residual. Available measurements
are the other 18 exact encoded original samples in that segment, with registered
reported time, zero uncertainty about their stored integer value, and no claim
of zero physical measurement error.

For both signs of the residual, compute complete response sets before each
acquisition. Combine them in the same scalar world: support means the entire
remaining family stays in [-0.05,0.05]; contradiction means every family member
violates that requirement. A query that distinguishes two witnesses is insufficient.
All observations and queries lie inside the fixed horizon and share the known
recorded axis. Prove the joint decision rule for this scope before implementation.
Reveal an actually stored numeric response and recompute the full family.

Query the as-yet-unrevealed source instant with largest current possible absolute
residual; tie by earliest index. Both arms have the same coarse observations,
available queries, deterministic rule, error/rate assumptions and stopping rule.
Stop on complete support/contradiction, inconsistency or all 18 query opportunities
used. The conventional arm independently calculates bounds and query partitions.
Use the manufacturer's separately authored decoder for a second input calculation
if its pinned code, terms and existing offline compiler qualify; do not install
dependencies. Shared authoring of the decision comparison remains explicit.

The final full-data reference evaluates the maximum absolute affine residual at
all original knots and validates the rate premise. Retain decisions, false
acceptances/refusals against that recorded reference, abstentions, every reveal,
costs and baseline parity. All prefix acquisition, decoding and reference work
counts even if logical reveals stop early. No physical acquisition savings,
independent replication, statistical generalization or frontier performance.

Before scientific execution, freeze the implementations, controls, source bytes,
this question identity and runtime/supervisor. Any frozen correction is a retained
successor. Existing limits persist: 8 MiB new sources/derived bodies, 128 MiB
owned artifacts/temporary bytes, 5 GiB floor, 600 s execution and 600 s checking.
All prior failures, closed studies, historical controller and reserved images
remain preserved. This experiment is a checkpoint in the active mission.
