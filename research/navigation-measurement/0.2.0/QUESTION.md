# Fixed tail navigation-fidelity follow-up

Document: reiyah.navigation-measurement.question, version 0.2.0.
Status: exploratory question to freeze before tail capture or numeric inspection.

The initial 72,000-byte attempt at version 0.1.1 is retained as blocked: all
1,000 packets reported initialization. It is not replaced or pooled into a
successful result. This separate follow-up chooses one disjoint fixed final
slice because initialization at file start prevented the previous experiment.
This is an eligibility-motivated, disclosed exploratory follow-up, not a held-out
benchmark or independent replication. There will be no additional slice search.

Source: Oxford Technical Solutions NCOMdecoder commit
6bd95e9a5f826556e1c4c0bc586fec3f973c76e3, example/171019_031603.ncom.
The retained Git tree declares 8,205,840 bytes, 113,970 aligned 72-byte packets,
Git blob 1f0f7cce3dac5776c2924305cd33cd2bd7b3fd04. Request exactly bytes
8,133,840 through 8,205,839 inclusive, the final 1,000 packets. Require supported
HTTP 206 with that exact Content-Range. Refuse a full-body fallback or another
offset if this access fails. The full Git blob is not verified by a partial hash.
Private payload custody, recorded terms and independent vendor input checking
remain mandatory. All source indices and byte offsets emitted by the inherited
decoder are relative to this slice: add 112,970 packets or 8,133,840 bytes for
the original file position. Carry this mapping explicitly in the frozen sources.

Decision: can 10 Hz piecewise-linear reconstruction replace the selected 100 Hz
encoded north-velocity trace while its uniform error stays at most 0.05 m/s?
The tolerance is the same authored numerical fidelity requirement (0.18 km/h,
500 stored encoding quanta), not a physical safety or customer specification.
The original recorded reference is piecewise linear between native samples.
The conditional original-velocity rate premise stays 5 m/s². Check it on all
100 selected native intervals; if violated, reject empirical binding without
tuning the rate or changing the sample. Physical calibration is unresolved.

Select the first 101 consecutive eligible mode-4 synchronous records with a
previously reported valid GPS-minute anchor and exactly 10 ms increments.
Preserve the inherited checksum, signed-value sentinel, status-only, asynchronous,
minute-wrap and unexplained-rewind distinctions. Never backfill the minute anchor
from a later packet. Invalid or unusable regular packets and native time gaps
break a run; status-only and asynchronous records are explicitly excluded.
If there is no eligible run in this fixed slice, retain another blocked result
and close this source route. Do not relax eligibility or select another slice.

The one-second selection gives five adjacent 0.2-second parts, 21 native knots
per part. They share endpoints and are dependent parts of one example, not five
independent trials. Each arm initially receives indices 0, 10 and 20 of each
part and may request any of the other 18 native samples, at most 90 queries per
arm. At each stage, query the unrevealed native instant with largest possible
absolute residual; choose the earliest index on ties. Stop at support,
contradiction, inconsistent premises or exhaustion. Preserve every response,
complete continuous response partition, decision bound and witness stage.

Keep the inherited methods fixed. Reiyah uses two residual margins under the
conservative residual Lipschitz rate Q = 5 + maximum coarse-baseline slope
magnitude. It may lose information. The competent conventional arm retains the
original 5 m/s² velocity cones and coarse baseline, including strict response
polyhedron projections. Compare independently computed bounds and response sets;
do not force equal verdicts, query sequences, costs or parity. Preserve stronger
baseline results. The earlier authored control already demonstrates a possible
representational disadvantage, and this follow-up cannot claim that weakness
was newly discovered in recorded data if no actual case executes.

Reuse the separately authored, unchanged manufacturer C decoder to check all
packet outputs, the complete eligible set and exact selected stored values.
Use separate geometry/LP calculations for the mathematical checks. Both decision
methods, protocol wrappers and experiment still have one author. No model,
simulator, robot, vehicle-control, physical clearance or deployment outcome runs.

Pre-controls: the inherited 25 directed mathematical, input and custody checks.
After an actual case executes, run the inherited eight result mutations. If
selection is blocked, do not count those unavailable tests as passed. Empty
empirical error lists have denominator zero when no applicable case executes.

Count the full captured and decoded slice, vendor checking, preparation,
calculation, verification, controls, integration and readback costs, including
failures. Logical reveals do not establish physical acquisition savings. Tiny
single-run timers are not a controlled speed benchmark. Active effort, charges,
energy, peak memory and complete workflow economics remain unknown unless measured.
Caps stay 8 MiB new source/derived bytes, 128 MiB owned artifacts and temporary
files, 5 GiB free disk, and 600 seconds each for execution and checking. Retained
prior sources reused privately are byte-bound and separately accounted. No new
dependencies, inference, training, paid compute, outreach, delegation or control.
All 1,433 reserved images remain closed. Continue the mission after this checkpoint.
