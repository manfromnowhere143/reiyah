# Opportunity clock and sensor metadata census

Document ID: `reiyah.opportunity-clock-audit.2026-09-07`

Version: `0.1.0`

Lifecycle status: `exploratory`

The metadata-only census finds **4,682 candidate anchors across 150 official validation
scenes** with at least two seconds of scene extent on each side. The complete scene census
contains 6,019 sample anchors. Every anchor has keyframe metadata for the six cameras and
top lidar, with different capture timestamps across those channels. No pilot was selected,
and no new physical annotation or prediction was evaluated.

This is a preflight for the
[independent opportunity study](INDEPENDENT_OPPORTUNITY_STUDY_DESIGN_2026-09-07.md).
The selection logic consumes official scene membership, sample timestamps and scene boundaries.
It does not depend on whether any observer proposed an object. It therefore addresses the
sampling-frame problem exposed by the
[identification construction](REFERENCE_IDENTIFICATION_FINDINGS_2026-09-07.md), while
leaving physical coverage and reference validity unresolved.

## Exact execution scope

The [program](../tools/measure/audit_opportunity_clock.py) streams five tables from the retained
metadata archive: scene, sample, sample_data, sensor and calibrated_sensor. It parses no
annotation or prediction table. It checks official scene membership, scene endpoint identities,
sample counts, strictly increasing timestamps and the exact previous/next sample chain.
Duplicate keyframes for a required channel or unresolved sensor calibration identities fail.
Its streaming JSON reader is inherited from the previously checked research adapter.

The [specification](../evidence/reference-identification/clock-spec-0.1.0.json) binds the
archive digest, exact sources, official split, required channels and context duration before
execution. The [result](../evidence/reference-identification/clock-audit-0.1.0.json) is copied
from successful process stdout; the
[capture](../evidence/reference-identification/clock-audit-capture-0.1.0.json) retains the exit,
elapsed time and source/stream digests. The archive contains metadata for 850 train/validation
scenes, 34,149 samples and 2,631,083 sample-data rows; only the 150 official validation scenes
contribute to the reported anchor population.

Frame and scene identities remain in private JSONL files, with aggregate-only public results.
The private output closure permits reaggregation without disclosing dataset identifiers.
The previous annotation-policy audit, prediction replay and frozen reference study are unchanged.

## Capture-time offsets

Each offset below is the sensor keyframe timestamp minus the sample anchor timestamp, in
microseconds. Negative means an earlier capture. The p95 is the nearest-rank order statistic
of absolute offsets, with rank ceil(0.95 n). It is a census summary of these retained metadata,
not a confidence bound or a latency guarantee.

<!-- CLOCK_TABLE_BEGIN -->
| Channel | Keyframe metadata present | Missing | Earliest offset, us | Latest offset, us | Absolute p95, us | Captured after anchor |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| CAM_BACK | 6,019 | 0 | -17,202 | -7,473 | 12,917 | 0 |
| CAM_BACK_LEFT | 6,019 | 0 | -7,355 | 2,106 | 3,053 | 1,117 |
| CAM_BACK_RIGHT | 6,019 | 0 | -26,647 | -17,296 | 22,403 | 0 |
| CAM_FRONT | 6,019 | 0 | -42,356 | -33,055 | 38,049 | 0 |
| CAM_FRONT_LEFT | 6,019 | 0 | -49,961 | -40,362 | 45,666 | 0 |
| CAM_FRONT_RIGHT | 6,019 | 0 | -34,278 | -24,665 | 30,023 | 0 |
| LIDAR_TOP | 6,019 | 0 | 0 | 0 | 0 | 0 |
<!-- CLOCK_TABLE_END -->

LIDAR_TOP timestamps equal the sample anchor timestamps on these inputs. Camera capture
offsets extend to -49,961 microseconds. CAM_BACK_LEFT has 1,117 captures after the anchor,
with a maximum offset of 2,106 microseconds. Adjacent anchors within a scene are separated
by 398,234 to 650,830 microseconds; an assumed exact half-second step would discard that timing.

As a kinematic illustration only, an object moving at a constant 30 meters/second travels
about 1.499 meters in 49.961 milliseconds. This is not a measured annotation displacement:
the object's actual motion and the reference/prediction time convention must be established.
Existing models may already account for such offsets. The metadata alone do not show that
a detector result is wrong or that a historical benchmark has leaked future information.

## What remains unknown

Metadata presence does not show that an image or point-cloud payload is present, decodable,
adequately exposed, calibrated, unoccluded or sufficient to identify every target object.
Payload validity remains `not_checked`; physical opportunity completeness remains `unknown`.
Online availability times are `unmeasured`. A capture time is neither a reception time nor
proof that the inference result existed by a decision deadline.

The 4,682-anchor rule measures scene extent, not continuous visibility or guaranteed sensor
coverage over the context window. It is a candidate sampling population for the proposed
pilot, not a completed selection or a new sample of physical opportunities. Sensor-invalid
and unreviewable windows must remain visible when the pilot is later executed.

Six [controls](../tools/measure/test_opportunity_clock.py) pass: they preserve missing camera
offsets as null, keep anchors despite missing camera metadata, reject duplicate channel records,
reject broken sample chains and invalid timestamps, and reject missing scene/calibration
identities. The retained test also establishes that later capture counts do not become known
online availability times. The
[development verification](../evidence/reference-identification/verification-0.1.0.json)
reaggregates all private frame rows and checks source/output closure. It does not independently
establish sensor truth or reread the raw metadata calculation.

The next physical step is still independent observation under a frozen protocol. This census
makes that step concrete without selecting cases for their model or annotation outcomes.
