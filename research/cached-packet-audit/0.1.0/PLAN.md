# Complete cached prediction content audit

Version `0.1.0`. Status `exploratory`. Audit the three already retained public
EdgeFirst prediction files for v-e89, v-e93 and v-e9c. Earlier membership checks
cover 5,000 COCO val2017 members each; historical checkpoint/configuration and
payload redistribution bindings remain absent. A clean content audit cannot
fill those gaps or admit a benchmark comparison.

Before full row diagnostics, freeze the input bytes, implementation, selected
reader versions and logical policy. No image pixels, accuracy against reference
annotations, model inference, training, reserved outcomes or new dependency
installation are part of this audit. Use only the existing Polars 1.44.2 and
PyArrow 25.0.1 readers. Maximum three files, one million rows per file, 5,000
expected images per file and 1,200 process seconds per analysis/check phase.
Retain a failure or resource limit; never silently omit a file or image.

Check every logical row: required image membership/dimensions, label/index
consistency, finite scores in [0,1], exactly four finite box coordinates,
strictly positive width/height, and consistent image metadata across rows.
Interpret absent box metadata under the retained publisher specification's
legacy normalized center/width/height convention. Preserve the absence as an
explicit assumption; this is not proof of the actual preprocessing pipeline.
Out-of-canvas extents are diagnostics, not silently clipped or automatically
declared invalid. Preserve exact duplicate detections. A wholly null annotation
tuple is a publisher empty placeholder; partial nulls, duplicate placeholders,
and placeholders mixed with predictions are invalid content, never missing.
Represent every expected image, including missing and invalid images.

Report observed label-index/name pairs. Compare them separately with the COCO
source IDs and with the sorted 80-category dense convention. Do not silently
remap IDs or infer checkpoint provenance from a familiar class list.
Optional nonfinite instrumentation retains its exact floating bits in an
explicit invalid-measurement object. It is neither zero latency nor a missing
prediction. Its presence is reported separately from invalid detection data.

The initial synthetic experiment reproduced PyArrow's fixed-size nullable-list
failure, including attempted explicit-schema/list-type overrides. It also
showed that a separate physical-list view can be read. For that view, retain
the complete original file and its serialized Arrow schema. Copy the original
bytes through the start of its footer unchanged. Rebuild only a metadata
footer with `ARROW:schema` omitted, preserving all other metadata, physical
schema, row groups, column chunks, statistics, offsets and counts. Reject
external chunk paths and unsupported structures. Preserve surviving compact
footer fields byte for byte and record creator/footer sizes. Do not claim the
derived file has original bytes. The generic Arrow writer was rejected during
synthetic preparation because its format-1 compatibility policy changes a
UInt32 physical type; no such rewrite is allowed in the actual audit.

Read the original with Polars and the derived view with PyArrow. Compare all
logical rows in original order by a canonical digest that retains binary
floating values, nulls and ancillary fields. Validate fixed list lengths
explicitly after the read. The independent decoder check confirms logical
agreement for these files; it is not scientific replication or a way to erase
the original reader failure.

Compare retained per-image timing with the public inline charts under three
declared orderings only: original first appearance, emission timestamp, and
lexical image ID. Check contiguous offsets 0 through 5 against the complete
four-component timing tuple. Record exact or declared float32-rounding matches
and ambiguity. A matching five-image omission can establish a relationship
between retained artifacts, not the publisher's unrecorded warmup intention.
Charts and throughput remain publisher measurements, not this mission's
inference costs or evidence of detector quality.

Retain every image record, all row-indexed diagnostics, source/view identities,
first failures, controls, phase costs and unresolved provenance. Publish only
authored code, synthetic fixtures and aggregate findings. Raw predictions,
metadata joins, timing vectors and derived views remain private.
