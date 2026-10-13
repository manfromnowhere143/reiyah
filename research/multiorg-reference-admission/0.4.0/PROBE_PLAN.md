# Prospective corrected-tile check, 0.4.0

Status: proposed execution contract, frozen before any empirical forward pass
in this owner. This is an exploratory correction qualification on an already
exposed tile. It is not an untouched accuracy test or a replacement result for
an earlier failed protocol.

## Question and competing explanations

Does excluding only the proven appended RPN origin before final selection remove
its promoted detection while preserving genuine proposal scores, decoded boxes
and the selected population required by a direct validity-aware implementation?
An apparent improvement caused by threshold tuning, coordinate filtering,
changed neural computation, cap displacement or hidden geometry repair fails.

The original export is pinned by SHA256 fbf748e6d8b896bed9ee1eb15d5dd1409369de5e32c4746c4173aa4c10e7bebd.
The tested variant is the corrected **observation** graph with SHA256
a26f494f548ed8410a809252b2acaae97e2efa189fcee963a5b8a09dd4c13b63.
The ordinary corrected graph is statically checked but is not executed here;
no empirical parity with that untapped graph is claimed.

## Fixed inputs and procedure

Use only the reconstructed tile 9 of the predeclared first MultiOrg image,
MultiOrg_v2/test/Macros/Plate_4/image_7/image_7.tiff. Tensor: float32,
[1,3,800,800], C-order data SHA256
675a5f2aba2565e568feeb93fddc20aaed89a43a9bbeea393bf6336b84ae49d1.
Keep the prior CPU ONNX Runtime 1.23.0 environment and session settings.

1. Execute the prior observation graph once. Every output must reproduce its
   retained predecessor bitwise, not merely the final detections.
2. Execute the corrected observation graph once. Save every declared output,
   including unmasked scores and the explicit origin mask. Refuse nonfinite
   observations. Preserve partial arrays and exceptions on failure.
3. Separately check unchanged prefix, neural and decoded values, recompute the
   mask by origin, and compare each selected identity and copied byte against
   direct physical removal before sorting, NMS and caps.

The reference uses the retained ORT CPU score threshold, float32 IoU semantics
and lower-index tie behavior. The original final score > 0.5 positive-extent
obligation remains: genuine invalid high-score geometry causes refusal. It is
never reclassified as padding. Final zero-score output padding remains metadata.

## Admission and falsification

Require static graph preservation, passing authored mask/reference/capture
controls, bound code and data, before/after runtime audits and an explicit freeze.
Acceptance requires all prior taps reproduced bitwise, unchanged genuine
scores/coordinates, exactly the declared origin mask, exact reference agreement
in NMS identities and final outputs, and no unexplained high-score geometry.
Any mismatch, unexplained origin, nonfinite value, input mutation or resource
overrun refuses the milestone; retain the result and do not retry automatically.
Independent code checking belongs to this assisted investigation, not independent
scientific replication.

## Budget and stop

One attempt, one exposed tile, at most two model forwards, 60 seconds worker
wall time, 3 GiB sampled RSS and 64 MiB saved arrays. The unchanged supervisor
denies worker network before Python and monitors it from the host. Sampled RSS
is not an instantaneous process-tree memory bound. No dependency downloads,
model training, paid service, new image/model acquisition or threshold tuning.

Close empirical execution after this attempt. A complete first-image pair needs
a separate contract and prospective admission, preserving the chosen correction
variant and the original image/cohort/analysis semantics. This check alone cannot
establish prevalence, accuracy, published-ranking impact, automotive transfer,
novelty, scientific superiority or a complete-work advantage.
