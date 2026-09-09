# Nominal geometry and recorded-time checkpoint

Document ID: `reiyah.perception-geometry.checkpoint`

Version: `0.1.0`

Lifecycle status: `exploratory`

The offline Engine now resolves nominal calibration, poses and spatial transforms for the
existing [development windows](PERCEPTION_WINDOW_CHECKPOINT_2026-09-09.md). The input population
and raw evidence are unchanged. These checks prepare physical reference review; they do not
provide that review or narrow the earlier paired-loss interval.

## What was checked

The adapter replays the declared window population from its bound catalog and metadata before
joining spatial operands. It retains the original numeric operands, exact rational transforms,
source identities, prior raw custody/decoder states and signed capture/anchor offsets. Missing
or invalid inputs produce explicit unavailable transforms, with no pose interpolation or
object-motion assumption. The [interface](../research/perception-geometry/0.1.0/README.md)
defines the arithmetic, source limits and distinct failure states.

| Development observation | Retained result |
| --- | --- |
| Existing windows / distinct captures | 2 / 725 |
| Requested calibration records / ego poses | 14 / 725 |
| Nominal sensor-to-global transforms available | 725 |
| Pose timestamps equal their capture timestamps | 725 |
| Camera intrinsic matrices within the declared format | 12; 2 lidar records are not applicable |
| Nominal transforms into the corresponding anchor ego frame | 725 |
| Capture timestamps different from the corresponding anchor | 723; 2 equal |
| Capture minus anchor time range | -1,998,383 to +1,999,798 microseconds |
| Separate exact Hamilton-product checks | 8,700 affine-basis point comparisons; all agree |

The second calculation reads original calibration and pose operands and uses quaternion
products rather than the producer's rotation-matrix formula. It checks all four affine basis
points in sensor-to-global, global-to-sensor and sensor-to-anchor-ego transforms. It shares
source custody/framing code and the source data; it was authored in this same session and is
not independent human validation.

## What those results mean

A nominal transform into the anchor ego frame expresses a capture-time point in another
coordinate system. It does not establish where a moving object was at the anchor time.
Recorded timestamp equality also does not establish simultaneous exposure, per-point
acquisition or online availability. Calibration accuracy, pose accuracy, synchronization,
exposure duration, point times and object motion remain unmeasured.

Both previously exposed development anchors therefore retain their open-reference unit-loss
enclosure **[-8,8]**. No fresh anchor, cohort, seed, physical judgment, detector fit, benchmark
result or vehicle safety conclusion was produced. No cloud operation was needed for
this slice; it used the already retained local inputs.

## Verification and publication scope

The 21 new geometry tests exercise transform orientation, independent algebra, numeric
boundaries, nonfinite required fields, explicit Boolean types, missing poses/calibrations,
duplicate and incomplete joins, time mismatches, source identities and non-overwriting output.
All 278 offline tests pass (185 repository tests and 93 measurement tests), as does the Gate B
integrity/document checker. It verifies the 52 retained transcript identities without rerunning
the original experiments. The implementation and tests are public; source-derived reports and
raw material remain private.
Exact code, input, output and retained verification identities are in the
[machine checkpoint](../research/perception-geometry/0.1.0/checkpoint.json).

The first test attempt failed in the fixture writer because it correctly refused to serialize
NaN. The deliberate malformed-source fixture now uses an explicit legacy-source encoder; the
production writer was unchanged. A later measurement-regression run detected README links to
this not-yet-written document. Both failed transcripts are retained, and the final checks run
against the completed candidate. No expected rejection was relaxed.

## Architecture and README alignment

The full README, its six diagrams, the static Gate A architecture and the selected Engine design
were reviewed. README navigation and its current-development section still privileged the older
training campaign and described historical cache work as running. They now point to the
[selected perception-comparison architecture](PERCEPTION_DECISION_ARCHITECTURE_2026-09-09.md),
the implemented pipeline and the unselected 60-scene study. One diagram now depicts that
pipeline; the evidence diagram includes its separate decision-packet branch. All six research
and evidence diagrams remain represented, with the earlier training design linked as history.

The original Gate A architecture and selected design bytes remain intact. Gate A is still
operator-unaccepted. This offline research checkpoint and navigation update do not amend or
claim replay of an accepted Gate A release. Console work and parallel research retain their
owners; no parallel result has been admitted by this change.

## Next executable boundary

Build the locked phase-1 observation package from these same development windows. It must expose
raw evidence, declared coordinate conventions and timing without annotations, detector names,
scores, historical candidate hints or prediction overlays. Preserve unavailable regions and
separate phase-2 assistance from the original discovery observations. The operational catalog
and geometry report contain identifiers and source paths; they are not themselves blinded
reviewer packets.

Two independent reviewers, a competent independent conventional analyst, adjudication and the
full method/input/reviewer freeze remain prerequisites to the prospective 60-scene study.
