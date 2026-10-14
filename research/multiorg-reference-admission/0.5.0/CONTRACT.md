# Complete-pair checking contract, 0.5.0

`admit_tile.validate_tile(named_arrays)` admits the corrected observation graph's own ordered 33-output record. It validates origin indices, the explicit appended origin mask, score ordering, direct-removal NMS and final gathers/padding. It does not manufacture an original-model baseline. Neural head execution is observed, not independently recomputed. The helper reuses byte-bound `reference_core.py` from the separately authored 0.4.0 reference; its ORT suppression arithmetic and attribution are described in `THIRD_PARTY_NOTICES.md`.

`check_pair.py` separately reconstructs all 312 input tensor identities, validates the complete retained raw/admission/model/result population and recomputes float32 coordinate transforms and global whole-image NMS. It does not import the numerical producer or perform model inference. Its CLI is:

```sh
python -B reference/check_pair.py --owner OWNER --output OWNER/execution/actual-run --runner-sha256 RUNNER_SHA --manifest-sha256 MANIFEST_SHA --protocol-sha256 PROTOCOL_SHA --report OWNER/reference/ACTUAL_PAIR_CHECK.json
```

The CLI has a 300-second internal checking deadline. It requires exact prospective source/model/component bindings, the original first-image 156-tile roster for each model, the independently reconstructed input roster, and a process receipt beside the output (`actual-run.process.json`). Source dependencies must be beside this checker. Raw retention is bounded to 64 MiB per file and 128 MiB aggregate. Paths and typed array metadata, NPY payload lengths and hashes, names/order, row membership, admission traces and complete-image files are checked before completion is reported. The prospective input replay performed no model inference.

Success is `status: complete_pair_verified`, `complete_pairs: 1`. The report binds exact `result_sha256`, complete `observations` descriptors, `manifest_sha256`, `process_receipt_sha256`, checker bytes, source pins and input reconstruction. This is same-study execution checking, not independent scientific replication or a model comparison. Corrected Faster is an explicitly changed candidate. It is never represented as the released original model.

A retained semantic failure yields `failed_attempt_partial_ledger_checked`, zero complete pairs, qualified/captured/admitted counts and a terminal refusal where found. A malformed or unbound packet raises a refusal rather than producing a passing report. Abrupt termination without a structured worker failure remains unqualified. Partial raw arrays without a receipt are listed but never counted as qualified observations. A genuinely complete empty analysis remains distinct from missing or failed observations.

The supervisor receipt must bind the exact manifest and result, declare the exact worker-only network policy and success/exit state, and retain finite time and sampled RSS observations. The checker requires worker wall time at most 600 seconds and sampled RSS at most 3 GiB; it does not mistake outer preflight time for worker runtime. The parent separately verifies materialized sandbox policy, supervisor/freeze identity and runtime custody. Sampled RSS is not a hard address-space limit.

The 26 authored controls comprise eight origin-admission controls, fifteen saved-pair/scalar controls, and three preprocessing controls. Two development invocations failed before execution: the first preprocessing script had a missing space in a conditional expression; the first pair-control module had an unterminated f-string. Their original stderr logs remain retained. No empirical model attempt occurred during qualification. The prospective full-input replay and the already exposed 0.4 corrected tile replay are separately recorded.
