# MultiOrg: a scored zero box traced to an appended proposal

Document ID: `reiyah.multiorg.export-lineage`.
Version: `0.3.1`. Lifecycle status: `exploratory`.

The [previous attempt](../0.3.0/README.md) stopped on a zero-area box scoring
**0.5355819463729858**. A separately frozen, single-tile diagnostic now identifies
its origin in the exact retained Faster R-CNN ONNX export: an appended zero
proposal passed through the ROI head and received a fresh classification score.

The input tensor reproduced exactly. The original model reproduced the prior
output bit for bit; exposing intermediate graph values preserved that output
bit for bit. A separately authored checker traced every final row through
recorded selection indices. **No box was dropped or repaired.** This closes the
origin question for this observed row, not the complete detector comparison.

## The observed route

All indices below are zero-based and refer to the one exposed tile, ordinal 9.

| Stage | Retained observation |
| --- | --- |
| First NMS output before appended row | 65 rows |
| Appended proposal | Row 65; zero coordinates and score 0 |
| ROI head input | ROI row 65 among 66 ROIs |
| Foreground classification | Score 0.5355819463729858 |
| Input to second NMS after score sorting | Row 8 |
| Second NMS selected tuple | Row 2 |
| Final output | Row 2; the same scored zero box |

The six final rows have three distinct origins: four descend from pre-append
RPN candidates, one from the RPN appended row through the ROI head, and one is
separate final padding with score zero. A pre-append candidate is not thereby
asserted to be a physical object, valid geometry, or free of earlier masking.
Coordinates alone did not determine any origin label.

## What the graph and source establish

The exact graph has 1,751 nodes, ONNX opset 11 and producer metadata naming
PyTorch 2.3.1. It explicitly appends a zero proposal after first-stage NMS, sorts
proposals, discards their old scores and passes their coordinates into ROI
processing. Its metadata does not name an exporter commit or configuration.

Pinned MMDeploy source has a compatible
[NMS padding path](https://github.com/open-mmlab/mmdeploy/blob/bc75c9d6c8940aa03d0e1e5b5962bd930478ba77/mmdeploy/mmcv/ops/nms.py)
and [ROI proposal path](https://github.com/open-mmlab/mmdeploy/blob/bc75c9d6c8940aa03d0e1e5b5962bd930478ba77/mmdeploy/codebase/mmdet/models/roi_heads/standard_roi_head.py).
That structural agreement does **not** establish which MMDeploy version produced
this export. The [source ledger](sources.json) retains versions, access dates,
response digests and terms; source payloads remain private.

The evidence consists of graph connectivity and observed index composition.
The checker verifies selected boxes, scores and labels byte for byte; it does
not independently reexecute neural feature extraction, classification, box
regression, softmax or ONNX NMS. This is separate checking within one assisted
investigation, not independent scientific replication. Prevalence, upstream
intent, effects on published empirical rankings and novelty remain unestablished.

## Qualification and execution

Five preprocessing controls, sixteen capture controls and thirteen lineage
controls passed before the probe. They include an authored tiny ONNX model run
through ONNX Runtime, altered-output rejection, equal zero coordinates with
different origins, changed indices, missing final padding and bounded failure
retention. Source-bound controls also inspect the exact static graph metadata.
The public staging script subsequently replayed all 34 controls successfully.
These are software qualification checks, not a performance estimate.

The one diagnostic attempt made two forward passes on the same saved tensor:
original, then instrumented. It completed in 4.864 seconds of outer wall time,
with peak sampled RSS 896,057,344 bytes under the frozen 60-second / 3 GiB limits.
It retained 33 private arrays totaling 19,872 bytes. Network denial applied before
worker Python started. RSS sampling is not an instantaneous hard memory bound.
All 36 frozen bindings and the inspected runtime inventory remained unchanged:
17 distributions, 5,926 hashed RECORD entries, 17 unhashed RECORD self-entries;
system dynamic libraries remain outside the audit.

Exact observations and private evidence bindings are in [result.json](result.json)
and [provenance.json](provenance.json). The prior failed protocols and their
outputs remain unchanged. No correction variant, complete image/model pair,
reference matching result or work-advantage result was produced by this probe.

## Reproduction and next step

[build_taps.py](build_taps.py) adds observation outputs only and checks full
parsed-protobuf preservation. [trace_worker.py](trace_worker.py) requires exact
prior/baseline/instrumented parity. [check_lineage.py](check_lineage.py) verifies
saved index routes independently of those producer modules.

The parser environment uses Python 3.13, ONNX 1.19.0, NumPy 2.2.6,
protobuf 6.32.1, typing_extensions 4.15.0 and ml_dtypes 0.5.3. The empirical
runtime remains the [previous pinned environment](../0.2.0/environment.json).
With the exact independently obtained model, the inspector performs no inference:

```sh
PARSER_PYTHON -B research/multiorg-reference-admission/0.3.1/inspect_graph.py \
  --model EXACT_FASTER_MODEL --output NEW_GRAPH_DIRECTORY
python3 -B research/multiorg-reference-admission/0.3.1/reproduce_controls.py \
  --parser-python PARSER_PYTHON --runtime-python RUNTIME_PYTHON \
  --graph NEW_GRAPH_DIRECTORY/graph/GRAPH.json --output NEW_CONTROL_DIRECTORY
```

The inspector's portable replay reproduced the retained graph description
exactly. The controls use authored arrays and a tiny authored model plus that
static description; they do not rerun this empirical diagnostic. Empirical
reproduction requires private tensor/source custody and a separately frozen
execution budget. This owner is closed to further empirical attempts.

The [next decision](DECISION.md) is a distinct export correction that preserves
proposal validity before final NMS and output caps. A small
[exact counterexample](correction-order-result.json) shows why dropping padding
after a cap can lose a genuine detection slot. This is a possible-input result,
not an observed accuracy improvement. Genuine invalid geometry must remain
visible and rejected. No blanket zero-box filter, threshold tuning, alternative
image or automatic full-pair retry follows.

[Source attribution and terms](../0.1.0/NOTICE.md) remain applicable. Source-derived
numerical observations and summaries are CC BY-NC-SA 4.0; original code retains
the repository code license. Raw images, model weights and intermediate arrays
are not distributed here. No upstream endorsement, physical truth, automotive
transfer, scientific superiority or complete-work advantage is claimed.
