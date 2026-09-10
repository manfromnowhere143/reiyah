# Unassisted observation review

Guide ID: `reiyah.perception-rehearsal.discovery-guide`; version `0.1.0`.

Your task is to record possible objects and what the supplied observations leave unresolved.
This is a development workflow rehearsal on previously used evidence. Your own prior exposure
still needs to be recorded. No completed review is supplied in this folder.

The coordinator supplies this folder and the matching observation package separately. Compare
the package identity with `package-identity.json`; use the package's `READ_ME.txt` and manifest
to understand its coordinates, timing and unavailable states. The capture index is a navigation
aid. An empty asset path means no delivered asset, not an empty scene. Paths in that column are
relative to the observation package. The manifest is authoritative for nominal geometry.

1. Record your assigned handle and actual prior exposure in a copy of
   `discovery-record.draft.json`. The five exposure fields distinguish annotations,
   predictions, configuration identities, other reviewer records and prior rankings. Leave
   uncertainty as `unknown`; do not claim blinding from being given this folder.
2. Work independently with the supplied raw observations and permitted viewing tools. Do not
   obtain annotations, prediction overlays or another reviewer's findings during discovery.
   If exposure occurs, record it and tell the coordinator. Keep your observations.
3. Account for every listed window/capture occurrence. A capture appearing in two windows has
   two rows. Use `inspected`, `partly_inspected`, `unviewable` or `not_inspected` according to
   what you actually did. Supply limitations for every state except a fully inspected capture.
   Do not mark all captures inspected by default or treat a sparse sampling as full inspection.
4. Describe possible objects with explicit class alternatives or unresolved class. Proposals
   use sequential IDs (`proposal-00001`, etc.), one window ID, a description and evidence.
   A capture reference can name the whole capture; an image region uses integer half-open
   pixel bounds; raw lidar indices are sorted unique zero-based point-record positions.
   Preserve ambiguous associations and competing interpretations in your descriptions. Do not
   turn a viewing limitation into evidence that an object does not exist.
5. Record actual completion time if known. Return a separate completed record and your effort
   account to the coordinator. Keep the original draft. The coordinator validates and seals
   each record before any assisted phase; a local seal does not prove exposure order.

You are not being asked to infer precise anchor-time object coordinates from a still image
without support. Relative transforms are nominal, and capture-time geometry does not compensate
for object motion. State inability to judge position, identity, class, occlusion, completeness
or time explicitly. An empty proposal list does not establish an empty physical scene.

Tell the coordinator where the workflow itself fails: unreadable evidence, inadequate viewing
tools, unclear instructions, excessive bookkeeping or questions the data cannot answer. Record
active time, interruptions and repairs separately; missing measurements remain missing. Honest
inability to complete a step is a useful outcome of this rehearsal.
