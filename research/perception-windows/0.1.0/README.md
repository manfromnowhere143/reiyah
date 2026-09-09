# Recorded observation windows

Artifact ID: `reiyah.perception-windows.contract`

Version: `0.1.0`

Lifecycle: `exploratory`

This offline adapter inventories the raw camera and lidar observations available for a
source-bound comparison. It selects no study cohort, supplies no object judgments and does
not establish physical-reference completeness. See the [checkpoint](../../../docs/PERCEPTION_WINDOW_CHECKPOINT_2026-09-09.md)
and [machine record](checkpoint.json) for the executed development audit.

## Window and population

The caller names 1–128 distinct anchors already present in a hash-bound
[input catalog](../../perception-inputs/0.1.0/README.md). The adapter recomputes complete
selected-scene clocks from the same metadata archive and checks catalog agreement, including
scene endpoints, every selected-scene sample, anchor time and context eligibility.

For each anchor, the profile `all_recorded_captures_closed_plus_minus_2s.0.1.0` requests every
recorded capture whose sensor timestamp lies in the **closed** interval `[t−2s,t+2s]`, for
`LIDAR_TOP` and all six cameras. This includes non-keyframe sweeps. It verifies increasing
timestamps, reciprocal previous/next links, scene/channel boundaries, unique capture identities
and paths, raw encoding, dimensions and the catalog's anchor-keyframe bindings.

The first recorded capture at or before the start and at or after the end provides a metadata
bracket. Outside-window payloads are never opened. A missing bracket remains a recorded-stream
endpoint or absent stream; it is not replaced by a repeated frame. No selection, window
shortening, interpolation, nearest-frame borrowing or substitution follows a missing file.

The report lists every requested capture and both the recorded and decoded timing: first/last
times, boundary distances and maximum inter-capture gap. With fewer than two captures the
inter-capture gap is null. It does not invent a sampling frequency or assert an acceptable
gap for physical review. Internally consistent metadata can itself omit an acquisition.

## Inputs and command

Use a Python environment with the dependencies in [requirements.txt](requirements.txt)
installed before offline execution. The recorded audit uses Python 3.14.2 and Pillow 12.3.0;
the report retains decoder version, native module digest and JPEG-library versions.

```sh
python -m tools.perception_windows \
  --request /private/task/window-request.json \
  --request-sha256 EXPECTED_REQUEST_SHA256 \
  --output /private/task/new-window-report.json
```

The request has exactly these fields:

| Field | Required value |
| --- | --- |
| `artifact_id` | `reiyah.perception-windows.request` |
| `version` | `0.1.0` |
| `catalog` | `path`, `byte_size`, `sha256` of the existing full catalog |
| `metadata` | The same descriptor for the archive bound by that catalog |
| `inventory` | The same descriptor for the raw custody inventory |
| `raw_root` | Explicit absolute directory containing the sensor files |
| `anchors` | Nonempty array of distinct `{anchor_id, sample_token}` pairs |

Descriptors bind exact file bytes before parsing. Parsing uses the verified copy; later source
path changes do not change its operands. Catalog and inventory limits are 128 MiB and 64 MiB;
the archive limit is 1 GiB compressed/4 GiB expanded. The existing bounded archive reader is
reused with an explicit table list. Required tables are `scene`, `sample`, `sample_data`,
`sensor` and `calibrated_sensor`. Their exact byte identities are also reported.

The custody inventory contains exactly `artifact_id`, `version` and `assets`. Its identifier
is `reiyah.perception-windows.assets`, version `0.1.0`. Each asset is one of:

```json
{"filename":"samples/CAM_FRONT/example.jpg","state":"retained","byte_size":1234,"sha256":"EXPECTED_SHA256"}
{"filename":"sweeps/LIDAR_TOP/example.pcd.bin","state":"unavailable","reason":"not retrieved"}
```

These are shape examples, not real source identities. Inventory rows are unique by filename;
unknown properties/states and invalid identities reject the inventory. There are at most
200,000 rows and 64 MiB per asset. A required capture absent from the inventory stays
`not_listed`. An empty inventory therefore produces explicit incomplete windows.

## Custody and decoding

| Dimension | States and interpretation |
| --- | --- |
| Custody | `not_listed`, declared `unavailable`, retained path `missing`, identity/path `invalid`, or exact bytes `verified` |
| Payload | `not_checked`, `sensor_invalid`, or `decoded` |
| Window | Whether every recorded in-window capture decodes, both metadata brackets exist and scene context is present |
| Physical reference | `not_established`, including when the recorded window is complete |

Raw files are opened relative to an explicit directory descriptor. Every relative path component
rejects symlinks; files must be regular and bounded. The expected length and SHA-256 are checked
before the decoder consumes those same bytes. A changed path cannot substitute different
bytes between identity verification and decoding. Custody expectations themselves are supplied
by the inventory; this is not independent publisher authentication.

JPEG checking requires a complete envelope, RGB format and the metadata dimensions, then
forces full pixel decoding. Pillow's truncated-image tolerance must be disabled. Header
inspection alone is insufficient. Missing or differently configured decoding capability
leaves the file unchecked, distinct from a malformed sensor payload.

Lidar checking requires nonempty little-endian five-float records and finite values in all
five fields. It does not infer point acquisition times, validate ring/intensity physics or
establish that the returns observe a target. Repeated verified hashes across filenames are
reported; separate records are not automatically independent observations.

Required input/metadata defects abort with machine-readable diagnostics. Individual absent,
unbound, unreadable or corrupt payloads remain in the report. A successful command means a
complete **assessment** was written; callers must inspect its state dimensions. Output is
atomic and cannot overwrite an existing identity. Code/runtime changes during the audit reject
the output. The adapter has no network client; this is not an OS-hermetic execution claim.

## Limits and next interface

This profile is an engineering proposal to support the [selected study plan](../../perception-decision/0.1.0/study-plan.json),
not a retrospective preregistration or a change to its released bytes. The eventual study
freeze must bind the actual raw-window/reviewer procedure. The implementation does not validate
calibration accuracy, coordinate transforms, camera exposure duration, per-point lidar timing,
online availability, physical visibility or reference exhaustiveness.

No annotation, detector overlay, historical candidate center or model-assisted judgment enters
the raw audit. Operational source catalogs and audit reports remain private; they are not
automatically suitable for the blinded reviewer interface. Locked independent observations and
an explicit coverage/uncertainty model are still needed before the
[reference compiler](../../perception-reference/0.1.0/README.md) can narrow an open reference.

Run the focused checks with `python -m unittest tests.test_perception_windows -v`. The fixtures
exercise non-keyframe inclusion, exact window boundaries, broken/omitted/cross-scene links,
clock and keyframe substitution, malformed states, resource limits, missing channels and
files, path/symlink escape, altered identities, point corruption, JPEG truncation, changed
decoder configuration, same-byte decoding and non-overwriting output. A constructed fully
decoded window still has no physical-review-readiness claim.
