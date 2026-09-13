# From selected points to an evidence location

Interface assessment `reiyah.selection-evidence`; version `0.1.0`; status `exploratory`.

The existing discovery locator already represents an exact native selection. No new production
interface or automatic proposal creator is justified by this audit. The source-verified retained
development selection maps directly to the current capture ID and original point-index array,
without changing any of the three indices. Its original source records remain byte-identical.

## Coordinator procedure and review boundary

1. Retain the separately selected observation seal, binding, returned scene and extraction report
   identities. Run the current native extraction procedure on the selected source and scene.
   A digest identifies the selected file; it does not establish who operated the viewer.
2. Take the capture ID from the verified binding and the complete original `point_indices` array
   from the verified extraction result. The existing evidence shape is:

   ```json
   {"capture_id":"capture-000001","locator":{"kind":"point_indices","indices":[0,1]}}
   ```

   This is an illustrative location, not a human proposal. The actual indices must come from
   the actual selected report. Retain that report separately in private custody rather than
   adding unsupported fields to the closed discovery record.
3. Check the capture belongs to the proposal's declared window. The record must report that
   occurrence as inspected or partly inspected. Descriptions, class hypotheses and limitations
   remain the person's reported content; a selected point does not supply them or an anchor-time
   object position. Unknown class can remain explicitly unresolved.
4. Validate the complete proposed discovery record against the same verified manifest/seal.
   Existing validation checks location shape, bounds, window membership and reported inspection;
   it does not authenticate the visual origin of a manually entered location. Keep an exact
   transcription check against the separate selection report when that is the stated origin.
5. If more than 4096 points were selected, retain the complete extraction and the refusal.
   Do not truncate, split across invented proposals, replace the selection by a whole-capture
   locator or infer absence automatically. The reviewer can make an explicit different evidence
   choice, or a separately reviewed future interface can represent the larger selection.

An empty selection is `VIEW_EMPTY_SELECTION`, not an observed empty scene. An unsuccessful
interaction stays unviewable/not inspected, or partly inspected when that is what the person
actually reports. Missing measurements remain unknown. Existing discovery controls preserve
these states and forbid proposals on uninspected captures.

The ready development exercise asks only for opening and selection, uses already exposed
material and explicitly requests no object judgment. Even a successful return cannot become
independent unassisted discovery. Actual discovery requires separately assigned people,
appropriate observation delivery and locked independent records before assistance. No selection,
typed handle, structural validator result or generated fixture supplies that evidence.

## Bounded checks and cost

The source audit reverified the selected package, binding, scene/report identities, all 34,720
original point records and direct slices at indices 0, 17,360 and 34,719. The current locator
accepts the exact array unchanged. This reuses a previously programmatic selection; no new native
UI operation, participant record, object proposal or physical judgment was produced.

One new cross-interface regression uses 5000 explicitly synthetic byte records. The viewer's
all-record check preserves both a 4096-point and a 4097-point selection. Discovery accepts the
first and rejects the second as `DISCOVERY_LOCATOR`; both arrays remain intact. This tests the
pure selection/locator boundary, not an observed native or human selection. Run:

```sh
python -B -m unittest tests.test_perception_selection_evidence -v
```

The new test passed in 0.128 seconds including process startup. The complete development source
audit took 3.396 seconds and 88,653,824 bytes peak process RSS. These are local machine costs,
not human time or a performance comparison. The previous 379 repository tests and 93 measurement
tests are retained with unchanged prior source; neither suite was rerun for this test/docs-only
change. See [verification](verification.json), the
[discovery contract](../../perception-discovery/0.1.0/README.md) and the
[current native preparation procedure](../../perception-viewer-preparation/0.1.0/README.md).

The next independent Engine task should assess compiler representation cost across admitted
joint alternatives. A conservative resource fallback is explicit and safe, but repeated copies
of the same object may waste that budget and hide a conditional decision. Establish a concrete
case and compare direct per-world results before proposing any compaction. Preserve all worlds,
matching competition, adverse interpretations, source mappings and explicit open reasons.
