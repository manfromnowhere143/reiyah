# MultiOrg: an explicit analysis endpoint still refuses the pair

Document ID: `reiyah.multiorg.analysis-projection`.
Version: `0.3.0`.
Lifecycle status: `exploratory`.

The [diagnostic](../0.2.3/README.md) identified a zero-area prediction below the
unchanged analysis threshold. We qualified a separate analysis-only contract,
then tried the same first whole image and model pair once. It passed nine Faster
tiles and stopped on the tenth: a raw float32 prediction had coordinates
**[0, 0, 0, 0]** and score **0.5355819463729858**, above the analysis threshold.

This is a failed endpoint qualification. There is no complete model output,
paired comparison, detector ranking or scientific null result.

| Evidence retained | Result |
| --- | --- |
| Frozen image/model selection | Original first whole image; Faster, then YOLO |
| Faster tiles retained | 10 of 156; zero-based ordinals 0 through 9 |
| Faster tiles qualifying for analysis | First 9; 153 raw rows |
| Failing tile | Ordinal 9, row 0, column 2304; 6 raw rows |
| Offending high-score row | Original row 2; zero extent in both axes |
| Total raw rows retained | 159 |
| YOLO execution | Not started |
| Private raw evidence | 20 NPY files; 7,012 bytes |
| Completed model outputs / pairs / comparisons | 0 / 0 / 0 |

## What changed, and why

Fixed-score greedy hard NMS processes candidates in descending score order.
Every candidate scoring above 0.5 precedes every candidate scoring at most 0.5.
Its keep/suppress decisions on that high-score prefix therefore depend only on
earlier high-score candidates. The [proof and assumptions](PROOF_AND_CONTRACT.md)
establish the same high-score result over every numerically valid completion of
the low-score geometry. This is an ordinary algorithmic property, not a new NMS
method or a defined result for malformed full input.

The new [supplemental contract](contract.json) uses this property explicitly.
It retains every returned raw array, counts every raw row against the unchanged
work cap, and reports excluded low-score anomalies. All raw and converted
coordinates must still be finite, all scores must be finite and in range, and
the original storage-eligible class check remains. High-score geometry must
qualify before and after the unchanged coordinate transform. No complete
storage output is defined or exported by this contract.

The [adapter](analysis_pair.py) reuses exact-bound original preprocessing,
coordinate decoding and stable NMS. It changes neither the >0.5 analysis
threshold nor the model, image, coordinates, NMS threshold or tie order. Earlier
failed protocols remain unchanged. A missing or failed tile cannot become an
observed empty result.

## Qualification and actual execution

Eighteen [projection controls](test_projection.py) passed, including 500 authored
full-input comparisons against a separately implemented scalar NMS and 256 valid
low-coordinate completions. Ten [mocked execution controls](test_analysis_pair.py)
checked raw retention, source/roster identity, work caps, result scope and failure
handling. Three [checker controls](test_check_analysis.py) checked hand-calculated
outputs, partial failure and altered evidence. These are constructed software
controls; the finite test counts are not a scientific performance estimate.

The separately frozen actual attempt stopped after 19.116 seconds of outer wall
time. Peak sampled worker RSS was 1,102,692,352 bytes, within the original
600-second / 3 GiB limits. Network denial applied to the worker before Python
started. No new source download, model replacement or empirical retry occurred.

A [separately authored checker](check_analysis.py) verified all retained raw files,
source hashes, TIFF header dimensions, contiguous tile membership and the first
nine tiles' scalar coordinate calculations. It independently identified the
high-score geometry failure on tile 9. No Reiyah whole-image NMS was reached;
NMS comparison evidence remains authored-control evidence. Tensor hashes bind
recorded metadata but this checker does not reconstruct input tensors or rerun
inference. The checks are within one assisted investigation, not independent
scientific replication.

All 38 execution bindings and the inspected installed runtime inventory remained
unchanged. The runtime audit checks 5,926 hashed entries across 17 distributions;
17 RECORD self-entries lack hashes and system dynamic libraries are outside that
audit. Exact facts and private evidence hashes are in the [attempt](attempt.json)
and [provenance](provenance.json).

## Next decision and reproduction

The [decision packet](DECISION.md) identifies the next dependency: qualify the
source-specific meaning and production of a nonzero-score zero box. The retained
failure rules out treating this case solely as an overly strict low-score storage
check. It does not establish a model defect or identify the responsible stage.
No higher threshold, silent deletion or alternate image is an accepted repair.

For offline replay, use the [pinned runtime](../0.2.0/environment.json) and the
[authored-control staging script](reproduce_authored.py):

```sh
python -B research/multiorg-reference-admission/0.3.0/reproduce_authored.py --output /tmp/reiyah-authored-controls
```

The output directory must be new. The script copies the exact original worker,
diagnostic, projection and checker programs into the required private layout,
creates explicitly authored source placeholders, and runs all four control files.
Logs and a result record remain in that directory. It uses authored arrays and
mocked sessions, not empirical models. Empirical reproduction additionally
requires the exact source payloads and separately bounded execution records;
the closed attempt is not permission for an automatic retry.

[Source attribution and terms](../0.1.0/NOTICE.md) remain applicable. Source-derived
numeric observations and summaries here and in `attempt.json` are CC BY-NC-SA 4.0;
original code retains the repository code license. Raw images, weights and arrays
remain private. No upstream endorsement, physical truth, automotive transfer,
superiority or complete-work advantage is claimed.
