# Nominal spatial and time operands

Document ID: `reiyah.perception-geometry.interface`

Version: `0.1.0`

Lifecycle status: `exploratory`

This offline adapter resolves the coordinate operands for an existing
[raw-window report](../../perception-windows/0.1.0/README.md). It checks nominal calibration,
poses, transforms and recorded time relations. It does not make an object observation or
change the [paired-loss comparison](../../perception-decision/0.1.0/README.md).

## Input and command

The request is a closed JSON object with these exact fields:

```json
{
  "artifact_id": "reiyah.perception-geometry.request",
  "version": "0.1.0",
  "window_report": {"path": "...", "byte_size": 123, "sha256": "..."},
  "catalog": {"path": "...", "byte_size": 123, "sha256": "..."},
  "metadata": {"path": "...", "byte_size": 123, "sha256": "..."}
}
```

The ellipses are placeholders, not valid identities. Supply each file's exact byte size and
lowercase SHA-256. Request and generated artifact JSON reject nonfinite literals, floating-point
tokens and duplicate fields. Original metadata numbers use the bounded Decimal source parser.

```sh
python -B -m tools.perception_geometry \
  --request /private/request.json \
  --request-sha256 ACTUAL_REQUEST_SHA256 \
  --output /private/new-geometry-report.json
```

Install the version in [requirements.txt](requirements.txt) in the caller's Python environment.
No model endpoint, GPU, image decoder, network call or raw sensor file is needed by this step.
Output parents must exist. The destination must be new. Exit 0 means the complete assessment
was written; transforms inside that assessment may still be unavailable. Exit 2 records an
invalid request, binding, source or computation and does not publish a partial report.

## Population and source binding

Verify each source's size and SHA-256 before parsing the same private snapshot bytes. Require
the catalog and metadata identities to agree with the window report, and the catalog's metadata
identity to agree with the request. Extract only the six named metadata tables to unlinked
files: scene, sample, sample_data, sensor, calibrated_sensor and ego_pose. Check the original
five table identities against the window report; retain the added ego-pose table identity.
Annotation tables are not parsed or used.

Replay the existing clock and window construction from the catalog and original metadata.
The bound report must agree on the exact selected windows, all captures and sweeps, order,
source identifiers, times, dimensions, stream links and boundaries. This reuses the window
implementation; it is not an independent validation of that implementation. Structural
comparison preserves types: Boolean true cannot stand for integer one. Reject unknown channels,
empty window populations, repeated anchor identities and inconsistent overlapping captures.
No missing channel or capture is removed to make a join succeed.

The report inherits prior custody and decoder states by exact window-artifact identity. It
checks their consumed state fields and requires a decoded payload to have verified prior
custody. It does not reopen raw files, repeat decoding, authenticate the earlier publisher or
infer continued availability of the original raw paths.

## Coordinate and arithmetic contract

Profile: `nominal_wxyz_column_rigid_capture_time.0.1.0`.

Use homogeneous column vectors, translation in meters, scalar-first quaternions (w,x,y,z),
microsecond metadata times, sensor-to-ego calibration and ego-to-global pose. For a capture at t
and an anchor at a:

```text
T_global_from_sensor(t) = T_global_from_ego(t) T_ego_from_sensor
T_sensor_from_global(t) = inverse(T_global_from_sensor(t))
T_anchor_ego_from_sensor(t) = inverse(T_global_from_ego(a)) T_global_from_sensor(t)
```

The last expression changes the coordinate frame of the point measured at t. It does not
transport a moving object from t to a. The report retains t-a with its sign and keeps
`object_position_at_anchor_time: unmeasured`, including when metadata times are equal.

Parse each required numeric source operand as an integer or finite Decimal with at most 32
significant digits, Decimal exponent from -32 through 12 and magnitude at most 10^12. Reject
Boolean, binary float, string and nonfinite operands. Use exact rational arithmetic after this
boundary. In the rotation formula divide the quadratic quaternion terms by s = w²+x²+y²+z².
Require |s-1| <= 10^-6. This near-unit format screen and scale removal are explicit numerical
policies; neither quantifies physical rotation uncertainty. Retain the original rational
quaternion, its squared norm, the translation and the resulting matrix.

Camera intrinsics must be a finite 3-by-3 upper-triangular pinhole matrix with positive focal
diagonals and bottom row (0,0,1). Skew is permitted. Principal-point location is not used as a
validity threshold. Lidar intrinsics are `not_applicable`. A usable intrinsic matrix does not
establish distortion correction, image rectification or projection accuracy.

The [source basis](source-basis.json) binds the privately retained nuScenes SDK 1.1.11 source
and publisher metadata used to check conventions. The adapter is Reiyah code; no third-party
source or dataset payload is included here.

## Availability and time

| Condition | Result |
| --- | --- |
| Required calibration/pose numeric field absent or null | Operand state `missing`; no rigid transform using it |
| Required numeric field malformed, nonfinite or outside profile | Operand state `invalid` with diagnostic; no rigid transform using it |
| Referenced pose row absent | Retained `missing` pose and time; associated captures remain present |
| Duplicate requested pose identity | Invalid join; no output report |
| Calibration row absent during original window replay | Invalid source join; no fallback sensor or silently reduced population |
| Capture and pose timestamps differ by any amount | Explicit signed mismatch; no nominal capture transform |
| No LIDAR_TOP anchor keyframe, or keyframe/pose/anchor times disagree | No anchor-frame transform; no nearest-pose substitution |
| Camera intrinsic invalid but rigid operands usable | Intrinsic remains invalid; rigid transform keeps its own state |
| Prior raw payload missing or undecoded | Prior state retained; nominal metadata geometry does not upgrade it |

The source pose and calibration fields are evaluated separately from their physical accuracy.
Unknown physical calibration and pose errors, synchronization accuracy, camera exposure duration,
lidar point-acquisition times, object motion and online availability remain explicit. There is
no interpolation, distortion model, moving-object reconstruction or temporal adequacy threshold.

## Bounds and verification

Requests are at most 4 MiB. Window and catalog artifacts are each at most 128 MiB; the metadata
archive is at most 1 GiB compressed and 4 GiB expanded. The inherited parser limits apply to
individual values, table rows and selected-scene streams. Geometry adds a 10,000-distinct-capture
limit to the 128-window limit. It refuses larger jobs rather than clipping them. Report size is
at most 128 MiB. The CLI checks its source and runtime identities before and after assessment.
This is offline application behavior, not an operating-system isolation guarantee.

The tests check known axis landmarks, noncommuting transform order, an independently structured
Hamilton-product oracle, exact inverses, quaternion sign, numeric/profile boundaries, missing
and invalid states, source drift, joins, timestamp mismatches and output non-overwrite.
The real development check compares original source operands against all four affine basis
points for three transform families: 8,700 exact comparisons across the same 725 captures.
Custody and JSON framing remain shared code. This is separately computed verification by the
same authoring process, not independent human scientific review.

See the [checkpoint](checkpoint.json) and [development report](../../../docs/PERCEPTION_GEOMETRY_CHECKPOINT_2026-09-09.md).
