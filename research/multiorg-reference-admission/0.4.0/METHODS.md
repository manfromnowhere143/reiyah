# Origin-preserving export correction

This method qualifies a distinct, batch-one variant of the exact Faster export
identified in the [preceding graph trace](../0.3.1/README.md). Its purpose is to
prevent the explicitly appended RPN proposal from entering final detection
selection. It makes no claim about detector quality or the original exporter's
intent. Model, input and execution identities belong in the experiment record;
this document specifies the correction and its comparator.

The graph supplies the required origin information. `/Where_6_output_0` contains
RPN rows before the zero-row append. `/TopK_6_output_1` records their subsequent
selection and ordering. For this exact graph and batch size one:

```text
n = Shape(/Where_6_output_0)[1]
valid_origin = /TopK_6_output_1 < n
foreground = Where(Unsqueeze(valid_origin, 2), original_foreground, float32(0))
```

The mask feeds every original foreground-score consumer before TopK 7, final NMS
and the output cap. It excludes the appended operand by provenance, not by box
coordinates or a new confidence threshold. Pre-existing scores and boxes remain
unchanged. A pre-existing candidate is not thereby certified as a physical object
or valid rectangle. Batch sizes other than one are refused: the generic batched
path can contain other-batch masked rows before the append, which this predicate
would not identify.

The original supplied NMS score threshold is positive: float32 bytes `cdcc4c3d`,
value `0.05000000074505806`. A masked zero cannot qualify. RPN selection yields at
most 1,000 rows, below the unchanged pre-NMS cap of 5,000. NMS selects at most 200
per class; the final cap remains 100. The original final structural zero row is
accounted for separately. It is not a detected object.

The direct comparator physically removes the appended origin before selection.
It retains original ROI identities, orders by descending foreground score and
then original ROI index, and applies the same caps. It separately implements
scalar suppression without importing the graph builder. Post-cap deletion is an
illustrative weaker control: it can discard a slot after a valid alternative has
already been excluded.

The comparator follows the retained **ONNX Runtime 1.23.0 CPU** implementation.
A supplied threshold admits scores strictly greater than it; equal scores prefer
the lower input index. This is read from
[`non_max_suppression.cc`, lines 139–197](https://github.com/microsoft/onnxruntime/blob/v1.23.0/onnxruntime/core/providers/cpu/object_detection/non_max_suppression.cc#L139).
The [ONNX version 11 documentation](https://onnx.ai/onnx/operators/onnx__NonMaxSuppression.html)
describes removal of lower scores; the explicit CPU equality rule determines this
runtime-bound comparison. Opposing box corners are normalized, arithmetic uses
float32, and suppression requires IoU strictly greater than 0.5. The
[CPU helper, lines 88–149](https://github.com/microsoft/onnxruntime/blob/v1.23.0/onnxruntime/core/providers/cpu/object_detection/non_max_suppression_helper.h#L88)
returns no suppression for nonpositive intersection or area/union. That behavior
is not a declaration of valid geometry or a computed IoU of zero.

[TopK 11](https://onnx.ai/onnx/operators/onnx__TopK.html#topk-11) specifies lower-index
tie precedence, also present in the retained
[CPU comparator](https://github.com/microsoft/onnxruntime/blob/v1.23.0/onnxruntime/core/providers/cpu/math/top_k.cc#L32).
The exact graph uses sorted, largest-first TopK. Physical removal therefore
preserves the relative order of valid origins. Genuine zero-extent candidates
are retained through selection. A final genuine-origin output above the unchanged
analysis threshold of 0.5 must satisfy the positive-rectangle admission rule;
otherwise the experiment refuses it explicitly.

Authored qualification covers empty origin populations, reordered padding,
coordinate-identical genuine and padded rows, ties, score and IoU boundaries,
unsupported batches, cap behavior and graph preservation. Small actual-runtime
controls qualify selected CPU boundaries; they do not prove universal rounding
or backend equivalence. A corrected-tile comparison additionally requires exact
input binding, unchanged preselection observations, complete retained arrays and
agreement with direct removal. This source decision does not assert that an
empirical comparison has passed.

Upstream review was bounded. MMDeploy main captured on 13 October 2026 resolves
to [`3f8604bd`](https://github.com/open-mmlab/mmdeploy/tree/3f8604bd72e8e15d06b2e0552fe2fdb8f8de33c4).
Its inspected [generic NMS](https://github.com/open-mmlab/mmdeploy/blob/3f8604bd72e8e15d06b2e0552fe2fdb8f8de33c4/mmdeploy/mmcv/ops/nms.py#L212)
and [ROI path](https://github.com/open-mmlab/mmdeploy/blob/3f8604bd72e8e15d06b2e0552fe2fdb8f8de33c4/mmdeploy/codebase/mmdet/models/roi_heads/standard_roi_head.py#L40)
are byte-identical to the previously retained v1.3.1 files. Related
[PR 2584](https://github.com/open-mmlab/mmdeploy/pull/2584) describes an RTMDet-ins
box/mask padding mismatch. Retained metadata says closed with no merge date;
its diff and comments were not inspected. One search returned 23 matches, of
which the first 20 were retained. Neither a directly transferable upstream fix
nor novelty is established.

The [ledger](sources.json) records all 12 captures, including two duplicates:
1,586,880 response bytes. Primary bodies remain private. The scalar suppression
routine re-expresses Microsoft-licensed source and carries the
[software notices](THIRD_PARTY_NOTICES.md); it is not described as wholly original.
MultiOrg-derived observations retain the [prior NC-SA notice](../0.1.0/NOTICE.md).
This remains one assisted investigation on an exposed input, without a complete
model pair, independent replication or work-advantage claim.
