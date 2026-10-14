# Conditional matching after a complete pair

This adapter admits one exact, separately checked analysis-only pair: the corrected
Faster observation variant and unchanged YOLO on the frozen first image. It then
evaluates the three complete recorded annotation procedures separately. The
recorded reference counts are 88, 61 and 64. These observations are not physical
truth, independent raters or a complete four-image cohort.

The adapter does not manufacture `storage_predictions`. It requires exact image
and model identities, all 312 forwards, complete tile coverage, a successful
supervisor receipt and the qualified whole-pair checker. The checker must bind
the exact result and both complete image files. Its execution receipt must have
return code zero and bind the qualified checker and report. Parent admission and
a separate execution freeze are required before actual scoring.

`DEPENDENCIES.json` binds the unchanged native schemas, kernels, checkers and the
existing `references`, `fixed_case` and `compose` functions. Reference objects
retain source-file plus object-key identities. Continuous source coordinates
remain un-clipped. Exact IoU at least one half defines an edge; maximum-cardinality
matching gives unit false-positive and false-negative loss. Neither duplicate
geometry nor score ties merge otherwise distinct source identities.

Native limits remain 128 reference objects, 1,024 detections per output, 2,048
combined edges, 2,000,000 work units, 4 MiB input and 16 MiB proof. Counts alone do
not establish admission. Every native gate still applies; excess causes refusal,
without truncation or replacement.

The historical private oracle's `derive()` incorrectly imposed a 128-detection
limit. Its old bytes remain untouched. `maxflow_reference.py` retains only its
unchanged exact-IoU and Edmonds–Karp functions, with the source digest in its
header. The new checker independently parses reference coordinates, recomputes
cardinalities and composes the one-image result. It shares `input_gate.py` for
custody and endpoint admission. It binds native proof bytes; the native checker
is executed by the producer, not reexecuted by this separate arithmetic checker.
This is checking within the same investigation, not independent replication.

For one image, the global-procedure and imagewise-procedure intervals necessarily
coincide. Their zero boundaries remain unresolved. The four-image coupling
endpoint remains `inconclusive_incomplete_selected_cohort` regardless of the
three conditional loss values. No accuracy, safety, generalization, superiority
or work-saving claim follows automatically.

The private input manifest has exactly these keys: `artifact_id` equal to
`reiyah.multiorg.analysis-matching-input`, `version` equal to `0.5.0`,
`contract_sha256`, `pair`, `supervisor`, `pair_checker`, `checker_execution`,
`reference_manifest` and `reference_root`. Every file descriptor has exactly
`path` and `sha256`; paths are absolute private locations. `reference_root`
contains the three files at their original manifest-relative paths. The retained
55-image reference manifest is unchanged; this adapter reads only the first
image's three annotations.

```text
python3 -B match_analysis.py --input INPUT.json --input-sha256 INPUT_SHA \
  --repository REIYAH_CANDIDATE --output NEW_RESULT_DIRECTORY
python3 -B check_matching.py --input INPUT.json --input-sha256 INPUT_SHA \
  --repository REIYAH_CANDIDATE --result NEW_RESULT_DIRECTORY/result.json \
  --result-sha256 RESULT_SHA --output NEW_CHECK.json
```

Each actual command requires its own external 120-second supervisor and 3 GiB
sampled-RSS boundary with network access denied. Internal deadline checks do not
replace host supervision. Preserve a failed attempt and its partial files. Do
not infer a completed result from existing packet files if `result.json` was
not produced and the separate check did not pass.

`test_matching.py` exercises real unchanged native arithmetic, generic max-flow,
boundary refusals and authored mock pair/checker receipts. Its reference-manifest
hash substitution is confined to the authored fixture. The controls do not read
empirical predictions or annotations and do not perform inference.
