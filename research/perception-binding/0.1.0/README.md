# Comparison and observation binding

Document ID: `reiyah.perception-binding.interface`

Version: `0.1.0`

Lifecycle status: `exploratory`

Does this observation package describe the samples and times used in this detector comparison,
and do its delivered assets match the retained source inventory? The offline command checks
both questions and emits a private report. A package seal alone establishes neither join.

The [implementation](../../../tools/perception_binding.py) uses the existing
[observation verifier and projection](../../perception-observation/0.1.0/README.md) and
[reference compiler's detection join](../../perception-reference/0.1.0/README.md).
It does not execute a loss comparison, admit reference constraints or perform study selection.
See the [checkpoint](../../../docs/PERCEPTION_BINDING_CHECKPOINT_2026-09-10.md) for the captured check.

## File interface

Use Python with the pinned [observation dependencies](../../perception-observation/0.1.0/requirements.txt).

```sh
python -B -m tools.perception_binding \
  --request "$REIYAH_BINDING_REQUEST" \
  --request-sha256 "$REIYAH_BINDING_REQUEST_SHA256" \
  --output "$REIYAH_BINDING_PRIVATE_REPORT"
```

Select the expected input identities before the run. The request is a closed JSON object:

| Field | Required value |
| --- | --- |
| `artifact_id` | `reiyah.perception-binding.request` |
| `version` | `0.1.0` |
| `comparison` | Closed `path`, `byte_size`, `sha256` descriptor; at most 4 MiB |
| `normalizations` | Same descriptor; at most 64 MiB |
| `catalog` | Same descriptor; at most 128 MiB |
| `observation_custody` | Same descriptor; at most 128 MiB |
| `package` | Closed `path`, `seal_sha256` object; seal digest selected separately from the package |

Request operand paths are explicit absolute paths. Sizes are bounded integers, never Booleans.
Digests are 64 lowercase hexadecimal SHA-256 characters. The request itself is limited to
32 KiB. Duplicate JSON properties, noninteger JSON numbers, nonfinite values, unsupported
versions and unknown request/descriptor properties are rejected. Existing upstream documents
retain their own contracts; their unused descriptive fields are not new binding authority.

The expected custody file binds its original window report, geometry report and inventory.
Those exact descriptors are reopened through verified snapshots. The catalog and both reports
must name the same catalog and metadata byte identities. The inventory must be the one named
by the bound window report. Metadata size is additionally checked for a valid bounded value;
two matching invalid descriptors do not form a valid identity.

The request must select the package location recorded in custody. Relocation requires a
separately selected custody record. An operator who changes every expected source identity has
changed the premises; this tool does not authenticate the operator or the original inventory.

## What is checked

1. Verify the whole package against the expected seal, then reopen the exact manifest bytes.
2. Replay the neutral projection from the exact window and geometry reports. After replacing
   only delivered-manifest evidence records with `not_checked`, require exact structural
   equality, including order, relative times, nominal matrices and neutral identities.
3. Require a bijection between comparison anchors and observation windows, with one distinct
   source sample per anchor and exact sample, scene and integer microsecond clock agreement.
   Check normalization source roles, normalized anchor digests and nominal ego coordinates
   using the existing detection join. Missing nominal anchor pose remains a rejection.
4. Read each delivered asset again by its expected identity. Compare original JPEG bytes to
   the inventory. For lidar, verify the fixed PLY profile and compare the unchanged point body
   to the inventory. A valid substitute image or PLY with a new package seal still fails this check.
5. Cross-check copied custody mappings and accounting against the rederived values. Rehash
   required source files and compare recorded code/runtime identities before completing output.

No anchor or capture is dropped to satisfy a resource limit. The package profile retains its
existing 128-window, 10,000-distinct-capture and 2-GiB-delivery limits. The report is limited to
128 MiB. Every output file is written atomically without replacing an existing identity. The
private report must be outside the reviewer package, including through resolved directory aliases.

`not_listed` and `unavailable` must agree with the inventory. Retained sources may remain
`missing`, `invalid`, `sensor_invalid`, `not_checked` or `withheld`. Their reasons are retained
assertions and are not reobserved from the original raw directory. A nondelivered capture has
`source_content_check: not_delivered` and a null delivered-body identity. A missing detector
output also remains missing; the binding report does not convert it to an empty detection set.

## Report and failure behavior

The report has artifact ID `reiyah.perception-binding.report`, version `0.1.0`, and contains
exact private anchor/window/source mappings, input identities, per-capture content checks,
unchanged availability states, package summary and code/runtime identities. The report's
`status: bound` means the declared population and delivered-byte checks succeeded. Its
`decision_evaluated`, `reference_constraints_admitted` and `study_selection_performed` fields
remain false. Physical reference coverage and human review remain `not_established`.

Exit zero accompanies the report digest and summary on stdout. Invalid required operands or
I/O failures return exit 2 with a deterministic diagnostic code and no completed binding report.
Existing output identities are preserved. Filesystem error detail can depend on the host.
The report describes the bytes consumed; it is not a simultaneous snapshot of a hostile mutable
filesystem. A later consumer must freshly verify the exact package and report identities.

| Diagnostic | Obligation that failed |
| --- | --- |
| `BINDING_REQUEST` | Closed request, expected identity or absolute path |
| `BINDING_CUSTODY` | Custody identity, location, request hash or rederived accounting |
| `BINDING_SOURCE` | Catalog/metadata identity or metadata size |
| `BINDING_POPULATION` | Comparison/window/sample/scene/time correspondence |
| `BINDING_PROJECTION` | Exact neutral projection |
| `BINDING_ASSET` | Delivered image or point-body identity |
| `BINDING_AVAILABILITY` | Inventory and disclosure state consistency |
| `BINDING_INPUT` | Malformed required structure at an upstream join |
| `BINDING_CODE_CHANGED` | Recorded code or runtime changed during the run |
| `BINDING_PRIVATE_OUTPUT`, `BINDING_LIMIT`, `OUTPUT_EXISTS` | Output boundary |

Source snapshot, JSON parser, comparison schema, observation profile and reference-join
diagnostics retain their original codes. They are not downgraded to successful bindings.

## Trusted scope and next dependency

The source catalog, complete prediction-source validation, normalization and nominal geometry
are bound upstream premises, not independently recomputed here. The code records its shared
parsers, package verifier, projection and detection join, as well as the comparison schema.
Python imports, jsonschema and image decoding remain trusted runtime dependencies. Equality of
hashes is an integrity check; it cannot establish correct calibration, accurate objects,
independent reviewers, physical completeness or operator acceptance.

The next step is a versioned admission contract connecting locked discovery records, assisted
proposals and adjudication to shared reference alternatives. That consumer must use this binding
and freshly verify the exact sources. It must preserve disagreement and open coverage. An
external record digest alone must not make a reference interpretation physically supported.
