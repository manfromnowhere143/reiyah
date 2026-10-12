# Corrected supervisor: numerical-output refusal

Artifact ID: `reiyah.multiorg.corrected-supervisor.attempt`, version `0.2.2`.
12 October 2026. **Failed feasibility attempt; no paired result.**

The [corrected supervisor](../0.2.1/README.md) reached numerical output validation.
The one allowed attempt stopped when the unchanged worker rejected a retained
detector row with nonpositive width or height. The earlier
[supervisor failure](../0.2.0/README.md) remains preserved.

A new bounded private owner reused the same first whole image, Faster R-CNN /
YOLOv3 pair, virtual environment and byte-identical numerical worker. The manifest
changed only absolute paths. The original scientific protocol, 600-second worker
budget, 3 GiB sampled RSS limit, thresholds and native caps stayed fixed. An initial
planning ceiling of 6 GiB was explicitly corrected to 3 GiB **before freezing and
launching**. This is a separately recorded corrected-supervisor attempt, not a
rewrite of the stopped predecessor.

The [attempt record](attempt.json) binds that chronology and all inputs. All 165
reference files were already exposed, as were the first image and authored input
preflight. Previous execution saved no predictions; its internal execution point
was unknown. This is not an untouched source cohort.

| Observation | Retained result |
|---|---:|
| Empirical attempts / retries | 1 / 0 |
| Outer launch wall time | 5.015 s |
| Supervisor wall time, including its preparation | 4.868 s |
| Peak sampled worker RSS | 1,028,620,288 bytes |
| Saved prediction files / complete pairs | 0 / 0 |
| Native or separate matching comparisons | 0 |

The worker returned exit 1 with `ValueError: degenerate retained detector box`.
The guard runs **after conversion to float32 and retention at
score ≥ float32(0.05), before spatial scaling, flooring or NMS**. At least one
retained row had `x2 ≤ x1` or `y2 ≤ y1`. The traceback establishes that an ONNX call
returned and reached this guard. The fixed model order and empty output directory
place the failure during Faster processing, before YOLO started. This does not
establish complete-model qualification.

The frozen worker did not save the offending coordinates, score, tile index, row
index or number of offending rows. Those values remain unknown. In particular,
we cannot say whether the row met the later analysis threshold of score > 0.5,
whether the first tile failed, or whether the source model is defective. No model
pair or native eligibility result exists. This is a numerical-interface refusal,
not an empty prediction, scientific null, detector ranking or coupling finding.

Before and after execution, installed-runtime audits passed on 5,926 hashed RECORD
entries across 17 distributions and all 17 retained wheel archives. The inspected
collections were unchanged. Seventeen RECORD self-entries have no recorded hash;
no bytecode entries or unrecorded extras were reported. This verifies the declared
installed files and retained pins, not a reproducible rebuild or every system
library. All 165 annotation files and 2,615 candidate files were rechecked. Exact
bindings and audit scope are in [provenance](provenance.json).

Execution stopped without a retry, threshold change, box repair, model/image
replacement or remaining-image acquisition. There were no new source downloads, numerical-execution network requests or
paid services. Separately budgeted publication traffic is outside this attempt. Source terms and attribution remain those in the
[original notice](../0.1.0/NOTICE.md); no third-party image, weights or annotation
payload is published here.

The next dependency is diagnostic instrumentation that records the offending
output row and tile context before the existing rejection. It must preserve
decoding, thresholds and scientific settings, pass authored controls, and be
frozen before a future separately recorded run. This owner performs no such
empirical retry. A single-image result, if later qualified, would still establish
only source-specific engineering feasibility. It would not establish the
four-image coupling endpoint, physical truth or a human-work advantage.
