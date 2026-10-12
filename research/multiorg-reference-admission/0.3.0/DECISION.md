# Decision: qualify the zero-box contract before another inference attempt

Document ID: `reiyah.multiorg.zero-box-decision`.
Version: `0.1.0`.
Lifecycle status: `proposed`.

The concrete bottleneck is an undefined high-score geometry in the current
source-specific adapter. The new analysis contract reached tile 9 and then
refused a zero-area raw float32 prediction scoring 0.5355819463729858. The first
low-score diagnostic is explained; a complete detector pair is still unavailable.

| Alternative | Evidence and disposition |
| --- | --- |
| Raise the score threshold or remove invalid high-score rows | Changes the selected candidate population after observing the failure. Rejected as a repair to this study. |
| Replace the image/model or acquire more images | Avoids the unresolved source-output contract and changes the frozen selection. Not authorized by this attempt. |
| Count a zero box as a false positive | Requires explicit source/scoring semantics, row-validity policy and NMS behavior for degenerate geometry. It is not a consequence of the current positive-rectangle contract. Keep as an alternative to qualify, not an assumed fact. |
| Inspect the exact export and documented output contract | Directly addresses whether the row is a sentinel, an export/runtime behavior or a preprocessing/decoding compatibility issue. Recommended next milestone. |

First inspect the retained implementation, model metadata and graph lineage for
the output coordinates, scores and any validity encoding. Preserve source
versions and distinguish an intentional invalid/padded row from an actual
candidate. The retained upstream wrapper lacks Reiyah's same early extent guard;
that difference alone does not define valid behavior for this row or prove an
upstream bug.

A subsequent falsifying experiment should use the already identified tile and
bind its reconstructed input tensor to the retained pre-inference tensor hash.
Compare the precise coordinate-producing stage or a separately qualified source
reference path under declared runtime/export conditions. Freeze that probe before
execution. Agreement on a documented sentinel/validity rule could justify a new
adapter contract; disagreement would locate a compatibility boundary requiring
further investigation. Neither outcome retroactively completes these attempts.

Acceptance requires an explicit rule for every returned row, preserved confidence
and provenance, authored rejection controls, no unaccounted deletion, and then
complete first-pair coverage with the same scientific parameters. The next source
investigation needs retained model/code bytes, a read-only graph inspector and,
only if necessary, a bounded primary-source capture. A new inference probe needs
its own prospective budget; the existing owners are closed. No training, paid
service, alternate cohort or product expansion is the immediate dependency.

The separately recorded conditional three-procedure matching plan did not run:
its complete-pair prerequisite failed. The four-image primary endpoint and the
comparison against a competent analyst's complete work remain unmeasured. Keep
the broader HARBOR mission and its explicit unknowns intact while resolving this
narrow boundary.
