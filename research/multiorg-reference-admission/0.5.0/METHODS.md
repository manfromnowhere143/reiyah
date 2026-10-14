# A complete image before a detector comparison

The next dependency is a complete paired input under the declared method. Keep
the tested Faster **observation** variant, the original YOLO candidate, the first
image and the [existing analysis contract](../0.3.0/contract.json). The
[preceding correction](../0.4.0/README.md) establishes one exposed tile; it does
not establish a complete image or ordinary untapped-export parity.

Current [ONNX Runtime documentation](https://onnxruntime.ai/docs/api/python/api_summary.html)
provides named output requests, output metadata, fetch-path options and fallback
controls. The retained 1.23.0 Python wrapper makes the relevant behavior precise:
`run(None, ...)` expands to every declared output name. Request the same complete
33-name Faster roster explicitly, check its metadata and map `dets` and `labels`
by name. Merely taking the first two returned values would hide a changed roster.
Keep the existing CPU, thread, execution and optimization settings.

The installed wrapper also exposes a failure-policy gap: it can retry both
session creation and execution. Construct sessions with `enable_fallback=False`
and disable run fallback before any forward pass. This is a separately declared
failure-policy guard, not a claim that earlier runs retried. The installed source
is bound in [the ledger](sources.json), including its matching prior RECORD audit.
Qualification must verify that a provider failure is retained after one attempted
forward rather than silently recovered by the wrapper.

The [optimization documentation](https://onnxruntime.ai/docs/performance/model-optimizations/graph-optimizations.html)
describes rewrites, fusions and layout changes, and binds saved optimized models
to target options and hardware. That is not a promise of byte equality across
new fetch rosters, graphs or backends. Fewer taps, an untapped model, different
precision or a new execution provider need their own qualification.

The current [SAHI main commit](https://github.com/obss/sahi/tree/80ebdb699851facf87def03c0597e1aeb87a9a2d),
dated 30 September 2026 and titled Release 0.12.8, supplies useful contrasting
choices. Its [sliced predictor](https://github.com/obss/sahi/blob/80ebdb699851facf87def03c0597e1aeb87a9a2d/sahi/predict.py#L176)
defaults to greedy non-maximum merging with intersection over smaller area,
adds a full-image prediction, and offers buffered intermediate merging that its
source warns can affect AP. Its [slicing code](https://github.com/obss/sahi/blob/80ebdb699851facf87def03c0597e1aeb87a9a2d/sahi/slicing.py#L26)
shifts edge windows inward; its [postprocessor](https://github.com/obss/sahi/blob/80ebdb699851facf87def03c0597e1aeb87a9a2d/sahi/postprocess/combine.py#L20)
can dispatch to different implementations. These are different experimental
choices, not drop-in improvements to the frozen padded lattice and global IoU-NMS.
No SAHI code is copied, installed or benchmarked here.

| Choice | Decision for this milestone |
| --- | --- |
| Exact observed graph, all named outputs, original ordered lattice | Qualify the missing complete-image adapter. |
| Untapped export, fewer fetches or another runtime configuration | Require separate evidence before substitution. |
| SAHI defaults, buffered merging, inward edge shifts or extra full-image predictions | Preserve as alternatives for another comparison; do not change this one. |
| Active or statistical evaluation from the prior 2026 review | Defer until the target and required paired evidence exist. |

The competent reference physically removes only identified RPN padding before
per-tile selection, then separately reconstructs the frozen coordinate mapping
and whole-image postprocessing. On new tiles, use the corrected graph's own
origin and raw-head observations. Do not fabricate an original-model baseline
from them. The earlier original-versus-corrected preservation result remains
limited to the tile where both graphs were observed.

Every planned tile must have an identity, input digest, complete named output
record and validation outcome. Preserve all raw final-detection rows before
analysis selection. After every tile completes, concatenate high-score candidates
in declared tile/row order and run the single frozen hard NMS. Keep float32
transforms, flooring, original-index ties and outside-image coordinates. Do not
clip, merge online, replace a failed tile or report a partial image as empty.

The prospective ceiling is one attempt, 600 seconds and 3 GiB sampled RSS.
The known roster is 156 tiles per model. Static output-shape bounds now give
66,823,136 retained array bytes including conservative per-file overhead, within
a separately declared 128 MiB ceiling. This replaces the preliminary 256 MiB
allowance before execution; it does not enlarge any scientific or resource cap. Freeze the
adapter, separate checker, roster and budgets. Any unknown origin, nonfinite or
invalid high-score geometry, selected-identity mismatch, missing tile or resource
overrun stops the attempt and preserves partial evidence. Reference matching
requires a qualified complete pair and its own admission conditions.

This review retained seven primary responses totaling 470,462 bytes, with no new
model, image or dependency acquisition. It is a targeted current-method check,
not an exhaustive 2026 literature review or a superiority claim. The reused
suppression implementation retains its [software attribution](THIRD_PARTY_NOTICES.md);
MultiOrg observations retain the [prior source terms](../0.1.0/NOTICE.md).
