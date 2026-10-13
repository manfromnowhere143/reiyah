# Decision: preserve proposal validity through detection stages

Document ID: `reiyah.multiorg.export-lineage-decision`.
Version: `0.1.0`. Lifecycle status: `proposed`.

The single-tile trace identifies the high-score zero box as a descendant of an
appended RPN proposal. The next question is how to preserve that validity boundary
through final selection. A box's coordinates alone are insufficient: a generated placeholder and a
real proposal clipped to zero area can have identical coordinates. Any validity
rule must distinguish their origins and retain unresolved genuine geometry.

## Why confidence does not recover validity

For a zero proposal, the ordinary delta decoder has width and height zero and
center zero. With finite regression values, center displacement is multiplied
by zero and the decoded size is zero times a finite exponential. The decoded
coordinates therefore remain zero. A separately computed softmax classification
score need not be zero. This algebra explains how a placeholder can remain
geometrically empty while receiving a substantial score; it does not identify
the origin of an observed row without graph-index evidence.

## Correction alternatives

| Alternative | Decision |
| --- | --- |
| Raise the confidence threshold | Reject: changes the scientific selection after observing the failure. |
| Drop every zero-area box | Reject: conceals genuine invalid geometry and confuses it with padding. |
| Remove a padding descendant only after final selection | Insufficient in general: it may already have consumed a capped output slot. |
| Propagate proposal origin and exclude proven padding before final selection | Recommended correction candidate, subject to explicit specification and controls. |
| Count every malformed output as a false positive | A separate metric extension, with undefined zero-union NMS still requiring a rule. It is not a repair to the existing study. |

The [authored counterexample](correction_order.py) makes the placement issue
concrete. With cap two, padding scored 0.99 and two nonoverlapping genuine
proposals scored 0.90 and 0.80, excluding padding before NMS/capping keeps both
genuine proposals. Excluding it after capping keeps only one. This is a possible-
input result, not evidence that the observed tile lost a slot or that accuracy
improves. An equal-zero-coordinate genuine-origin control remains available for
explicit geometry refusal.

A correction changes the exported computation and must be named as a separate
variant. It cannot retroactively turn earlier failed attempts into completed
comparisons or inherit the released model's performance claims. Removing a row
from final outputs is not generally equivalent to preventing it from entering
selection. An explicit origin mask also needs defined behavior when there are
no genuine proposals, tied scores, multiple batch members, or more candidates
than a cap.

## Recommended milestone and falsifying experiment

Qualify a narrowly defined validity-preserving export variant. Bind it to the
exact source graph and expose the mask's lineage; keep original weights,
preprocessing and scientific thresholds fixed. On authored controls, compare
against a straightforward implementation that removes only known padding
before final NMS and caps. Test empty genuine populations, cap displacement,
score ties, batch padding and genuine invalid boxes. Preserve every raw row
and exclusion reason. A coordinate-only filter must fail the origin control.

Then freeze a separate bounded check on the already exposed tile. It must
remove only the proven padding lineage, preserve genuine candidates under its
declared selection rule, and agree with the direct comparator. Reject if an
unexplained genuine row changes, geometry is silently repaired, or origin is
unresolved. Do not use the corrected result to tune thresholds or choose another
image. Full first-image coverage of both predeclared candidates is a later
prerequisite for reference matching; the four-image primary endpoint remains
separate.

Required resources are the retained model and image, existing CPU runtime,
small authored controls and a new prospective execution budget. No training,
paid service, replacement cohort or product expansion is needed for this
milestone. Exact upstream export configuration remains a useful missing source,
but graph-specific correction claims must stand on the retained graph and tests.

The competent comparison is a direct, transparent validity-aware implementation
using the same inputs and decision obligations. Demonstrating that the corrected
variant handles padding does not demonstrate less total work than that analyst,
physical accuracy, automotive transfer or scientific superiority. Gate A remains
operator-unaccepted.
