# Direct removal and masking at this graph boundary

This is a separately authored reference for one exact export variant. It uses retained outputs from an already exposed tile. It is neither independent scientific replication nor an unexposed performance test.

Let the ROI rows reaching the final head be indexed in their original order. Each carries its observed TopK6 index into Concat87. If the pre-append row count is n, index n denotes the unique explicitly appended RPN row; indices less than n are origin-valid at this boundary. "Origin-valid" does not mean real object, correct localization, or absence of earlier masking.

The reference physically removes index-n descendants before final score sorting, NMS and caps. It leaves every other candidate's score and decoded coordinate bytes unchanged. The candidate correction instead sets the appended descendant's foreground score to float32 zero at Slice14, before TopK7 and the second NMS. It does not use geometry to decide validity.

These constructions have the same selected genuine population under the following graph-specific conditions:

1. Batch size is exactly one and there is one foreground class. Unsupported batches are rejected by the corrected graph's fixed input dimension and by this checker.
2. There are at most 1,000 ROI rows after TopK6, while TopK7 permits 5,000; it only sorts this population and cannot truncate it. No excluded row can occupy a preselection slot at this boundary.
3. Supplied NMS score threshold is float32 .05 and ORT 1.23.0 CPU admits strictly greater scores. A masked zero row never enters its priority queue. No assumption that a zero-area box has low confidence is used.
4. Scores are fixed and finite. TopK sorts ties by lower input index. Removing a row while preserving the order of remaining rows therefore preserves the order of equal-score genuine candidates. CPU NMS uses score descending and lower pre-NMS input index for ties; after TopK, that is the same original ROI tie order.
5. Both paths use the same corner-coordinate NMS semantics, float32 threshold .5, maximum 200 selected candidates and final TopK 100. By induction over the identical genuine priority queue, each genuine candidate encounters the same previously selected boxes and has the same keep/suppress result. Both append the same final zero-score metadata row before the final cap.

This is a conditional algorithmic equivalence. It does not justify placing a validity filter after a cap, changing a threshold, discarding all zero-coordinate boxes, removing earlier unidentified masking, or changing the scientific endpoint. Other batch/class/cap regimes need their own contract.

## Geometry and precision

The scalar NMS follows the retained ORT v1.23.0 CPU source: opposite corners are ordered for the IoU computation; nonpositive intersection or area/union returns no suppression; suppression requires float32 IoU strictly above 0.5. This internal calculation does not rewrite output coordinates. Every finite genuine candidate is retained through NMS, including malformed geometry. A genuine final row with score strictly above 0.5 and nonpositive original extent causes an explicit refusal, preserving the previous analysis-output obligation.

Intermediate scalar operations use NumPy float32 with explicit rounding between the source operations. Nonfinite scalar arithmetic refuses. This is not a proof that all compiler builds or hardware produce identical rounding. The prospective empirical check must agree in selected identities and copied bytes. Authored threshold, IoU-boundary, tie, zero-box, cap and empty controls qualify the declared implementation; they do not establish accuracy.

## Evidence checked

The new baseline observation must reproduce every retained prior instrumented array byte for byte. The corrected trace must preserve all prefix, neural, unmasked-score and decoded-coordinate observations. Its origin mask is recomputed from indices, its only changed score population is checked explicitly, and its TopK7, NMS indices, selected rows, final cap, output scores, boxes and labels must match direct physical removal. Final appended padding is kept as metadata, never claimed as a detected object.

Primary implementation references are retained under sources/frontier: ort-nms.cc, ort-nms-helper.h and the official ONNX TopK11 documentation. Runtime sources are version 1.23.0; graph opset is 11. Their licensing and exact capture bindings are in that source ledger. This reference imports no graph-builder or capture-producer code, ONNX or ONNX Runtime. Original code follows the repository code license; source-derived observations follow the retained dataset/model terms.

## Prospective check and portable authored replay

```text
PYTHON -B reference/check_correction.py \
  --prior-result PRIOR/trace/actual-run/result.json \
  --result NEW/execution/actual-run/result.json \
  --process NEW/execution/actual-run.process.json \
  --graph NEW/execution/original-graph.json \
  --contract NEW/reference/input-contract.json \
  --output NEW/reference/ACTUAL_COMPARISON.json
```

The prospective contract pins the manifest, worker, protocol, tap roster, build
receipt and supporting capture module. It is separate from an execution result
and must be retained in the pre-execution freeze. Both successful comparisons
and refusals produce a new report; existing output files are never overwritten.
The checker itself does not retry inference or modify any input.

Fifteen authored controls include complete file-level fixtures and mutations
of input digests, model identity, CPU provider, completion and bound code. Run
with NumPy 2.2.6 and the exact graph description obtained by the public inspector:

```text
REIYAH_GRAPH_DESCRIPTION=/path/to/GRAPH.json \
  PYTHON -B -m unittest discover -s reference -p test_reference.py -v
```

The separate builder qualification also exercised the actual pinned CPU runtime
on tiny authored graphs: exact/adjacent score boundaries, exact/adjacent IoU
boundaries, equal-score index order, empty origin-valid populations, genuine
zero geometry and unsupported batch size. No public detector inference is part
of these software controls.
