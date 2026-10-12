# MultiOrg: the rejected output, retained

Document ID: `reiyah.multiorg.output-diagnostic`. Version: `0.2.3`.
Lifecycle status: `exploratory`.

The [preceding attempt](../0.2.2/README.md) failed without retaining the offending
row. A separately frozen diagnostic attempt now identifies a rejected row:
Faster's first
tile returned a float32 row with XYXY coordinates **[0, 0, 0, 0]** and score
**0.3579423129558563**. It was already degenerate in the returned model output.
Float32 conversion did not cause this refusal.

| Observed boundary | Retained result |
| --- | --- |
| Image | First frozen whole image, `Macros/Plate_4/image_7` |
| Model and tile | Faster; zero-based tile 0 of 156; row 0, column 0 |
| Raw detector rows on this tile | 2 |
| Rows retained at the 0.05 storage floor | 1 |
| Degenerate retained rows | 1; both extents zero in the raw output |
| Relation to the unchanged analysis threshold | Score does not exceed 0.5 |
| Whole-image predictions or completed pair | None |

The original numerical worker was unchanged. A wrapper called its decoder and,
only after an exception, retained raw arrays and the original decoder's
intermediates. It captured model, image and tile identity from the verified
original execution frame, then re-raised the same exception. Six private NPY
files retain 862 bytes; no capture refusal or truncation occurred. A separate
scalar enumeration checked their hashes, row membership, extents and tile roster.
These checks belong to one assisted investigation, not independent scientific
replication.

Twenty authored controls qualified successful-output equivalence, raw-array
preservation, malformed outputs, score boundaries, conversion collapse,
conversion overflow, later arithmetic/floor failure, bounded capture and logging
failure. The context control uses the actual worker body with mocked inputs and
sessions; it is not another empirical inference run.

The one actual diagnostic attempt failed in 5.635 seconds of outer wall time.
Peak sampled worker RSS was 915,193,856 bytes. Original limits remained 600 seconds
and 3 GiB; the worker entered network denial before Python started. Before/after
runtime audits and frozen input bindings matched. Timing includes instrumentation
and is not a speed comparison with the preceding run.

## What this resolves

The stricter storage-output contract refused a row that does not meet the chosen
analysis score threshold. This identifies a concrete adapter-contract issue to
investigate. It does not prove a released-model bug, validate other tiles or
establish how upstream NMS behaves on invalid geometry. The original failed
protocol remains failed. No repair, clipping, dropping, threshold change, model
replacement, matching or empirical retry occurred in this diagnostic owner.

For fixed-score greedy hard NMS in descending score order, lower-score candidates
cannot suppress candidates above a fixed score threshold. A separate analysis
contract may use that property while explicitly retaining low-score anomalies.
It requires its own qualification and complete image coverage; a single failed
tile does not establish that every invalid row is below the analysis threshold.

## Inspect and reproduce the authored controls

The [attempt](attempt.json) and [provenance](provenance.json) bind the exact
programs, receipts and private arrays. The [wrapper](diagnose.py) and
[controls](test_diagnose.py) are independently authored. Raw source images,
weights and diagnostic arrays are private. Follow the recorded runtime pins in
[the original environment](../0.2.0/environment.json).

Stage a new private directory with this layout, copying the original worker
without modification:

```text
private-owner/
  inference/
    diagnose.py
    run_pair.py       # from ../0.2.0/run_pair.py
  qualification/
    test_diagnose.py
```

Then run the pinned environment's Python with `-B qualification/test_diagnose.py`
from that private directory. The tests use constructed arrays and mocked model
sessions. This command does not reproduce the empirical failure or download data.

The [source attribution and terms](../0.1.0/NOTICE.md) apply. The source-derived
numeric observations and summaries on this page and in `attempt.json` are
distributed under CC BY-NC-SA 4.0; original code retains the repository code
license. No source-author endorsement is implied. Scientific superiority,
physical truth, automotive transfer and complete-work advantage remain
unestablished.
