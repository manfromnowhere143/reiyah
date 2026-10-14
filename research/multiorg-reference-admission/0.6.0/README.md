# Selected inputs qualified; cohort execution stopped at its storage boundary

The remaining three preselected images are now acquired and their complete input
rosters are qualified. One bounded attempt on the next image stopped when the
supervisor observed free disk space below its 4 GiB floor. Neither of the later
images was started. No new complete model pair or reference comparison resulted.

The scientific question remains unchanged: does using one recorded reference
procedure across the cohort support a different conditional decision from allowing
the recorded procedure to vary by image? The original four complete image pairs
and twelve reference cases are still required. This execution failure leaves that
question unanswered.

## What was established

Three version-6 MultiOrg TIFFs were acquired in three requests, with no retry:
132,782,057 bytes. Each has 156 tiles per model. The unchanged numerical functions
produced prospective digests for all 936 inputs; a separate reconstruction matched
every digest before inference. The new worker accepts only these three literal
image contracts. It preserves the corrected Faster observation graph, unchanged
YOLO, original preprocessing, threshold, coordinate mapping, global NMS and
origin checks. The first-image worker and all historical owners remain unchanged.

Forty worker controls passed, including eighteen checks against the actual private
manifests; 34 separate reference controls passed. The four-image matching adapter
passed 28 authored controls, including exact composition against all 81 imagewise
procedure combinations. Matching remains qualified and **unexecuted on the cohort**.
Tests and internal separate checking do not establish independent replication.

| Selected image | Retained state |
| --- | --- |
| Macros / Plate 4 / image 7 | Prior complete pair and three checked reference cases, retained in [0.5.0](../0.5.0/README.md). |
| Macros / Plate 23 / image 0 | New attempt stopped at the disk floor; 70 raw tile ledgers and 70 worker admission receipts persisted. |
| Normal / Plate 31 / image 6 | Inputs qualified; inference not started. |
| Macros / Plate 23 / image 1 | Inputs qualified; inference not started. |

## The actual attempt

The attempt ran for 109.43 seconds under a 600-second ceiling. Peak sampled RSS
was 1,259,700,224 bytes, below the 3 GiB ceiling. The supervisor stopped the worker
with SIGKILL for `disk_floor`. There are 2,310 saved tensor files and 140 ledger/
admission files, totaling 4,469,802 bytes. The worker could not write its final
record after being killed. Forward starts or an in-flight completion beyond the
persisted records are unknown.

The complete-pair checker refused this missing terminal record. Its refusal is
preserved. There is no whole-image NMS result, YOLO image, model ranking, scientific
null, or four-image comparison from this attempt. The separate
[postmortem](POSTMORTEM.md) has the narrower task of checking persisted evidence;
it cannot complete the missing observation.

All 69 pre-execution bindings remain unchanged. Before/after runtime inventories
agree apart from their timestamps: 17 distributions and 5,926 hashed RECORD entries,
with 17 unhashed entries recorded separately. System libraries and existing bytecode
execution remain outside full authentication. No model or dependency was downloaded.

## Resources and limits

Before execution, replacing this owner's duplicate model copies with byte-identical
APFS clones recovered physical storage. The later failure shows that a successful
preflight did not ensure the shared volume would retain its reserve. The saved
attempt occupies 4.47 MB; the records do not identify the cause of the larger free-
space change. No historical evidence was deleted and the floor was not lowered.

The earlier preparation tuple-unpacking error and coordinator invocation without
a freeze are retained in the [contract](CONTRACT.md). Both preceded inference.
The present empirical attempt is closed. Prior attempts, qualification work and
the first complete pair remain part of the cost history; this is not a complete-
work advantage measurement.

Read the [exact result](result.json), [methods](METHODS.md),
[source ledger](sources.json), [provenance](provenance.json) and
[next decision](DECISION.md). Broader HARBOR capability, automotive transfer,
scientific superiority and Gate A operator acceptance remain unestablished.

## Replay the authored controls

In the qualified NumPy/ONNX Runtime/scikit-image/OpenCV environment:

```sh
python -B research/multiorg-reference-admission/0.6.0/reproduce_controls.py --output /tmp/reiyah-cohort-controls-new
```

This executes 56 controls: 22 worker and 34 reference cases. The eighteen private
manifest-binding cases are excluded. It does not download data or run a model.
In the qualified Python/jsonschema environment, from the repository root:

```sh
python -B research/multiorg-reference-admission/0.6.0/matching/test_matching.py --repository . --output /tmp/reiyah-cohort-matching-new.json
```

That executes 28 authored matching controls, with no actual cohort comparison.
Postmortem controls and their distinct scope are described in [POSTMORTEM.md](POSTMORTEM.md).

MultiOrg-derived observations retain CC BY-NC-SA 4.0 and source attribution under
[the study notice](../0.1.0/NOTICE.md). Code licenses and required
[third-party notices](THIRD_PARTY_NOTICES.md) are separate. Raw source images,
models, annotations and prediction arrays remain private.
