# Joint penalty and retained operating-policy envelope

Version `0.1.0`. Status `exploratory`. The original qualified local comparison
uses a shared confidence cutoff and unit false-positive/miss costs. Subsequent
studies vary either the penalty share at that fixed cutoff or the threshold
at unit loss. They do not establish the joint relation when both detectors
receive their own competent operating-policy comparison.

Use only the already verified complete nominal detector curves: 299 YOLO11n
threshold cells and 220 YOLO26n cells on the same 64 exposed development
images, 305 eligible projected car references and frozen matching convention.
These outcomes have already been exposed. Freeze this plan, code, inputs and
controls before computing new envelope intervals; no preregistration of the
earlier outcomes or untouched evaluation population is claimed.

For each retained cell j, let its total loss at penalty share p in [0,1] be
L_j(p) = (1-p) FP_j + p FN_j. Characterize the exact lower envelope separately
for each detector, retaining every minimizing cell, including ties confined
to one point and the endpoints. The miss/FP ratio is p/(1-p) for p<1; p=1
is miss-only. This is retrospective oracle characterization on development
data, not training, selected deployment thresholds, calibrated scores or an
estimated out-of-sample gain. No randomization or below-export-floor output
is introduced.

Compute each line's minimizing domain by intersecting all exact linear
inequalities against the other cells. Keep never-minimal cells as explicit
outcomes. Partition the full closed penalty domain at optimizer changes and
at zeros of old-envelope minus new-envelope. Retain singleton boundaries,
open intervals, all optimizer ties and exact rational coefficients/values.
Positive means lower nominal loss for new, negative lower nominal loss for
old, and zero is a tie that excludes strict improvement. These intervals are
not independent experimental decisions or observations.

Compare this envelope relation with the original fixed-cutoff affine
difference on the same complete partition. Report where the two conclusions
differ. Keep the earlier conditional reference-uncertainty and conventional
query-parity findings intact. No conclusion here extends to uncertain-reference
independent-threshold pairs, which were not evaluated by the original curves.

Separately verify with a slope-ordered exact lower-hull construction and
direct evaluation of every original line at all boundaries and an interior
rational point of each open interval. Affine endpoint checks must prove the
claimed optimizer dominates all original lines throughout each interval;
rechecking just a numerical grid is insufficient. Verify source curve
coverage, FP/FN/rank identities and retained original unit-loss regressions.
Use synthetic oracles including duplicates, same slopes, endpoint-only ties,
unsupported nondominated points and sign reversals. Exhaustively compare
small finite line sets with a separate crossing partition.

Maximum two curves, 600 cells per detector, 360,000 pairwise line constraints
per detector, 10,000 final cells and 1,200 seconds per run/check phase. Retain
every allocated cell, failure and resource limit. No new image or annotation
reads, inference, training, dependency installation, network acquisition,
reserved-outcome access, outreach or platform work. All 1,433 reserved images
remain closed. Publish only authored code and derived scalar results with
the inherited nuScenes attribution and conditions.
