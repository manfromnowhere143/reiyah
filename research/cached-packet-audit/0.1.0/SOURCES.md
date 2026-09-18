# Cached prediction sources and remaining bindings

Version `0.1.0`, 18 September 2026. This follows the
[original acquisition findings](../../public-predictions/0.1.0/SOURCES.md).
The source ledger retains private bytes, retrieval times, response status,
size and SHA-256. Public [sources.json](sources.json) exposes selected custody
metadata without temporary download credentials, host identifiers or payloads.

The three concrete leads are the public EdgeFirst validation sessions
[v-e89](https://edgefirst.studio/public/validation/v-e89/details?mode=charts),
[v-e93](https://edgefirst.studio/public/validation/v-e93/details?mode=charts) and
[v-e9c](https://edgefirst.studio/public/validation/v-e9c/details?mode=charts).
Actual prediction Parquet files, session/trainer metadata, platform records
and the listed timing files were obtained through documented public routes.
No authenticated requests were used.

The retained [profiler v1.14.2 release](https://github.com/EdgeFirstAI/profiler-cli/releases/tag/v1.14.2)
was published 30 July 2026 at commit
`528466f1075ac937d8059a3c01feaedaa7370c14`. Its release metadata includes
binary digests and its changes include platform metadata. These identify a
release, not the binary used in a historical validation run. No profiler
binary was downloaded or executed. The public platform records identify
version 1.14.2 and an ONNX/CUDA platform, but do not supply complete arguments.

Public training records name checkpoint artifacts. A newer public model tree
also lists ONNX files with content digests. A matching model name or renamed
artifact does not bind those bytes to the historical validation task. The
public session's `model_params` object is empty; source defaults and apparent
score floors do not establish the actual preprocessing/decoding settings.

The pinned public client documents `task.get`. One request for the first
already published task ID returned HTTP 200 carrying a JSON-RPC Unauthorized
error. This is an application-level denial, not a successful metadata read.
That route ended; the other two task IDs were not tried. The earlier protected
checkpoint denial remains retained. No authentication, enumeration or bypass
followed either response.

The [publisher's dataset format](https://doc.edgefirst.ai/latest/datasets/format/)
describes absent coordinate metadata using the legacy normalized `cxcywh`
convention. That convention is an explicit interpretation assumption here.
Observed label/name pairs are checked separately against the official COCO
category IDs and their sorted dense 80-category ordering. No automatic remap,
weight identity or historical training claim follows from a match.

The official COCO val2017 index supplies expected image IDs, dimensions and
category names. This audit computes no reference accuracy and reads no image
pixels. It does not convert the original local development comparison into
a COCO benchmark. The earlier separate-family RT-DETR findings are unchanged;
this follow-up does not establish absence of outputs elsewhere.

Reader versions are Polars 1.44.2 and PyArrow 25.0.1, from already retained
wheels and installed runtime bytes. Their official
[Parquet reader](https://arrow.apache.org/docs/python/generated/pyarrow.parquet.read_table.html)
and [metadata writer](https://arrow.apache.org/docs/python/generated/pyarrow.parquet.write_metadata.html)
documentation were retained during compatibility investigation. The final
operation does not use the generic metadata writer.

The authored bounded footer cursor follows the primary
[Thrift Compact specification](https://github.com/apache/thrift/blob/fd8763dd95b58bc6b789e947f2c7282f285d6cdd/doc/specs/thrift-compact-protocol.md)
(commit 21 May 2026) and
[Parquet format definition](https://github.com/apache/parquet-format/blob/bb22d0171b47000308e24209db79876b8dbe9566/src/main/thrift/parquet.thrift)
(commit 11 September 2026). Exact specification and license bytes are retained
privately. This narrow implementation is not a general Thrift/Parquet reader
or a claim of conformance to every format extension.

All three cached packets still lack a historical checkpoint byte binding,
full actual preprocessing/decoding settings and established prediction-payload
redistribution permission. Content/decoder agreement cannot replace any of
these fields. No cached packet is admitted to a detector comparison.
