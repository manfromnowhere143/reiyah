# Open a checked annotation dependency

Document ID: `reiyah.annotation-trace.interface`. Version: `0.1.0`.
Lifecycle status: `exploratory`. Dated 14 September 2026.

The offline [trace consumer](replay.py) follows an already selected label-deletion witness
through existing Engine records. It writes an evidence index, the exact original annotation,
sample, instance, category and incident prediction rows, and checked links to supplied captures.
It preserves multi-label deletions as groups. It does not discover dependencies, create a new
reference interpretation for admission, or decide whether an annotation is physically correct.

The [actual replay](../../../docs/PERCEPTION_DEPENDENCY_TRACE_2026-09-14.md) covers six individual
dependencies from the first benchmark case and two two-label groups from the second. One group
spans anchors; the other stays within one anchor. Original core, compiler and common interfaces
remain unchanged. This is a reusable research command, not a deployed Console workflow.

```text
python -B research/perception-annotation-trace/0.1.0/replay.py \
  --selection /absolute/SELECTION.json \
  --selection-sha256 EXPECTED_SELECTION_SHA256 \
  --output /absolute/NEW_PRIVATE_DIRECTORY
```

The selected JSON has exact fields `artifact_id: reiyah.annotation-trace.selection`,
`version: 0.1.0`, `inputs`, `targets` and `deletion_groups`. Inputs are absolute
`{path, byte_size, sha256}` descriptors for:

- `case`: the existing finite, single-world cohort export;
- `source_map`: the existing world/anchor/graph-to-original reference map;
- `annotation_packet`: the existing Engine annotation `PACKET.json`;
- `witness_review`: the identified external report motivating these selections;
- `catalog`, `normalizations`, `operands`, `renamings`, `observation_custody`: existing Engine inputs.

An external report may contain decimal measurements; it is read with the strict source JSON
parser. Engine operands retain their rational-only parser. The report is cited by identity;
the caller explicitly selects its claimed targets and groups, and the consumer checks the
result independently of its prose. It does not certify every claim made by that report.

Each target has `world_id`, `anchor_id`, `local_index`, `graph_id`, `class`. Local indices are
zero-based positions in that exact case's object array. Each deletion group has `target_indices`
into the selected target list, `expected_delta` as a rational string, `expected_criterion` and
`expected_preference`. Select between one and 128 targets and groups. Every target must belong
to a group. No repeated target or repeated index within a group is allowed.

For example, a group with `target_indices: [0,1]` removes both selected objects from the same
comparison before recomputing both matchings. It does not assert that either object alone
changes the decision. The test suite retains a matching competition example where either
individual deletion is absorbed but their joint deletion changes the preference.

The consumer checks the complete exported finite graph and its baseline certificate. Each
target must agree with its case position, compiler mapping, original reference record and
nominal sample clock. It scans the bound original metadata tables, verifies both row indices
and literal byte spans, and writes those spans without reformatting. Incident prediction rows
use persistent original `source_index`; a displayed neutral row suffix is not that index.

Capture lookup requires the exact catalog `sample_data_token`. The selected observation seal
and manifest are checked. Original camera bytes must equal delivered camera bytes; lidar record
bytes must equal the delivered PLY body. Missing metadata, a capture outside the supplied
package, unavailable bytes and an invalid identity have distinct outcomes. Camera timing offsets
remain visible. A capture link supplies no object-to-point/pixel locator, motion compensation,
physical synchronization or human observation.

`OPEN_EVIDENCE.md` links each dependency page and its original records. `TRACE.json` retains
the complete source descriptors, checked group certificates and source-code identities.
`PACKET.json` is written last, after successful checks. An earlier failure may leave partial
files without a success packet. The command refuses a consumed output or a destination within
its selected source directories or repository; every replay uses a fresh private directory.

Shared trusted code includes the Engine source snapshots, JSON/archive readers, category map,
matching producer, certificate checker and input schema. The earlier full source/geometry
audits remain separately bound evidence. This trace does not audit the completeness of an error
family or benchmark labels, establish label error rates, or measure human effort. Its source
receipts prove selected bytes and declared joins, not independent physical truth.

The validation and actual command costs are in [verification](verification.json). Both analysts
may use the same direct joins, maximum-matching algorithms, deletion bounds and witness shortcuts.
No advantage over a competent analyst's total effort has been demonstrated.
