# Prediction qualification findings

Version `0.1.0`, 18 September 2026. Retained source identities, access dates,
sizes, terms and exact blockers are in [sources.json](sources.json). All
third-party payloads remain private. No account or authenticated route was used.

The three specified [EdgeFirst public sessions](https://edgefirst.studio/public/validation/v-e89/details?mode=charts)
were read through their public page and the documented public JSON-RPC client
routes. `val.data.list` and `val.data.download` yielded actual Parquet files;
model cards and aggregate charts alone were not counted as prediction evidence.

| Session | Claimed model | Actual Parquet bytes | Table rows | Complete image index | Explicit empty placeholders |
| --- | --- | ---: | ---: | ---: | ---: |
| [v-e89](https://edgefirst.studio/public/validation/v-e89/details?mode=charts) | YOLOv8n | 14,754,709 | 744,885 | 5,000/5,000 | 0 |
| [v-e93](https://edgefirst.studio/public/validation/v-e93/details?mode=charts) | YOLO11n | 14,293,625 | 722,891 | 5,000/5,000 | 1 |
| [v-e9c](https://edgefirst.studio/public/validation/v-e9c/details?mode=charts) | YOLO26n | 11,860,096 | 595,786 | 5,000/5,000 | 2 |

Every image ID and dimension matches the official COCO val2017 index; there
are no missing or extra members. Empty placeholders have null annotation
fields and present image/dimension fields, consistent with the pinned client
writer. Initial PyArrow fixed-size nullable-list reads failed for the latter
two files; retained Polars decoding inspected the actual null representation.
The failure did not become an empty output. The profiler timing count is 4,995,
which is not prediction membership; the exact timing exclusion rule is unknown.

Public trainer metadata names checkpoint artifacts, but does not bind their
bytes to these historical runs. A documented checkpoint GET returned HTTP 401.
Earlier HEAD 200 frontend headers did not establish access. Protected annotation
and sample endpoints returned explicit 401 responses; no authenticated retry or
bypass followed. Available platform metadata does not prove all actual
preprocessing and decoding arguments. Payload redistribution terms remain
unestablished. Thus membership qualifies, while experiment admission remains
blocked for all three cached candidates.

Browser availability was checked once through its supported interface and no
connection was available. The direct public downloads above demonstrate why
that tool limitation was not evidence of missing exports or authentication.

The bounded separate-family pass refreshed the official RT-DETR source at
`29320b6fd828f8e0987a71426cf2d961b09dfed7`. Public release artifacts remain
weights rather than qualified prediction packets. R18 conversion, v2 rerun
and v4 backbone candidates retain their different meanings. Two RT-DETR-named
Hugging Face dataset trees point to the same annotation object; its inspected
65,536-byte prefix contains COCO train2017 image metadata, not a demonstrated
checkpoint-bound prediction contract. No full image archive was downloaded.
The bounded pass admits no RT-DETR outputs and does not establish universal
absence of public outputs.

## Qualified local fallback

Official `ultralytics/assets` release `v8.4.0` supplies `yolo11n.pt` and
`yolo26n.pt`; retained bytes match the publisher's SHA-256 assertions. Both run
through Ultralytics 8.4.155 at commit
`6900c83b16eebee55c7b9de23b9ef447e6ff11e7`, inspected and retained before use.
The configuration pins the complete 80-class mapping, 640-square letterbox,
confidence strictness, coordinate inversion/clipping, FP32 values, batch one,
maximum 300 detections, and each model's explicit NMS/end-to-end contract.
CPU PyTorch 2.10.0 runs with two threads; private missing dependencies are
byte-bound and installed offline. Global and earlier study runtimes are unchanged.

The actual Ultralytics settings directory is checked with integrations off.
OS network denial applies before import. OpenCV's GCD backend reports a
different thread count after `setNumThreads(1)`; the first preflight rejected
that mismatch before inference. The source-backed sequential setting
`setNumThreads(0)` is then required and observed as one thread. The original
failure, diagnostic and correction remain retained.

The lawfully held 64-image allocation is frozen before inference, with exact
JPEG bytes and dimensions verified. The two full packets have no missing or
failed rows and distinguish explicit empty from processed detections. Their
configuration and packet hashes are published in the ledger. This creates two
usable packets from one family; it does not fulfill the two-family/three-real-
revision acquisition target.

The held nuScenes archive's retained terms explicitly cover derived tables.
Only derived research summaries are distributed with the attribution and
scope in [DISTRIBUTION.md](DISTRIBUTION.md). No source accessibility, hash,
publisher-default assumption or passing admission check supplies missing
historical provenance or independent scientific authority.
