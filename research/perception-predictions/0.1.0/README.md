# Exact submitted prediction inputs

Artifact family: `reiyah.perception-predictions`, version `0.1.0`, exploratory.

This offline Engine preparer copies selected original prediction arrays without filtering,
association or numeric rewriting. It keeps row order, duplicates, unfamiliar fields and source
nonfinite literals. It validates bounded containers and sample joins; downstream calculations
must validate their own numeric, class and geometry premises. This packet is not a reference,
an admitted comparison, an annotation-free physical estimator or a disclosure to human reviewers.

The only data inputs during preparation are a separately hash-bound request and the original
submissions it names. No catalog, annotation or matched cache is an input. Frame selection is
explicit and **exposed retrospective development** only; its historical independence from
annotations is not established by hiding annotation files during this extraction.

## Request and commands

Use an absolute private request path and a fresh output whose parent exists. The output must
be outside the request directory, original-source directories and code checkout. Source
contents stay private. The selected interpreter needs the existing Engine dependencies;
no new dependency is introduced.

```json
{
  "artifact_id": "reiyah.perception-predictions.request",
  "version": "0.1.0",
  "exposure": "exposed_retrospective_development",
  "sources": [
    {"id": "configuration-1", "state": "observed", "path": "/private/inputs/submission.json",
     "byte_size": 123, "sha256": "<separately selected 64-character SHA-256>"}
  ],
  "frames": [{"id": "frame-1", "sample_token": "<32 lowercase hexadecimal characters>"}]
}
```

This is a shape illustration; placeholders and the example size are not executable evidence.
Unavailable sources instead carry exactly `id`, `state` and a nonempty `reason`. Supported
states are `missing`, `unmeasured`, `sensor_invalid`, `abstained`, `outside_support` and `unknown`.
An observed empty array is distinct from an absent key in a verified source and from an unavailable
source. Neither missing case is filled with an empty array.

```sh
python -B -m tools.perception_predictions prepare \
  --request /private/requests/request.json --request-sha256 EXPECTED_REQUEST_SHA256 \
  --output /private/outputs/new-packet

python -B -m tools.perception_predictions check \
  --request /private/requests/request.json --request-sha256 EXPECTED_REQUEST_SHA256 \
  --packet /private/outputs/new-packet --packet-sha256 EXPECTED_PACKET_SHA256
```

`PREDICTIONS.json` is written last. It binds original sources and selected frame files, with
every row's zero-based `source_index`, absolute `byte_offset` in the original submission,
`byte_size` and SHA-256. Positional filenames avoid ambiguity from concatenated caller labels.
Array files contain their exact original bytes, including whitespace and numeric spelling.
The source's modality flags are unverified producer declarations. Global coordinates are nominal
submission values; common sample keys establish neither physical synchronization nor correspondence.

Inputs are copied to verified unlinked snapshots before parsing. Subsequent replacement of the
original path cannot change consumed bytes. `check` reconstructs the expected packet from sources
using the same producer: it is a source replay, not an independent checker. It rejects altered
or extra files, symlinks and rehashed changes to packet claims. The output separation guard assumes
a stable filesystem, as do the existing Engine preparers; concurrent directory or mount replacement
is outside that guard.

## Bounds and separate conventional calculation

The request is at most 1 MiB, with 1–8 sources and 1–256 distinct frames. Each source is at most
1 GiB; its complete document is scanned, with at most 50,000 result keys, 512 rows per frame
and a 1 MiB JSON value bound. These are Engine parser bounds, not a claim that all admitted
payloads satisfy the official challenge rules. Selected arrays total at most 24 MiB and 65,536
rows; the complete packet is at most 64 MiB. Out-of-scope inputs fail explicitly without dropping
records or treating them as evaluated empty outputs.

The separate [conventional reader](read_original.py) uses memory mapping, literal selected-key
lookup and the standard-library JSON decoder, with no Engine producer/parser imports:

```sh
python -B research/perception-predictions/0.1.0/read_original.py \
  --request /private/requests/request.json --request-sha256 EXPECTED_REQUEST_SHA256 \
  --packet /private/outputs/new-packet --packet-sha256 EXPECTED_PACKET_SHA256
```

Its scope is narrower: each selected frame must be observed and have one literal ASCII key
occurrence. It checks complete selected arrays, original row order, indices, offsets and bytes.
It does not independently prove complete-source JSON validity, full-file counts, absence or
unavailable states. Both implementations trust the Python runtime, standard library and separately
selected source identities. Use the shown command without Python optimization flags; this research
comparator uses assertions for its proof obligations. It is not a production security boundary.

The [checkpoint](../../../docs/PERCEPTION_PREDICTIONS_2026-09-13.md) and
[verification](verification.json) record real source selection, costs and tests. Exact source
payloads, frame keys and selection provenance remain in the private sealed Engine exchange.
