# One complete image, three checked comparisons

Document ID: `reiyah.multiorg.complete-pair`. Version: `0.5.0`.
Lifecycle status: `exploratory`. 14 October 2026.

**The first complete detector pair is now available.** The corrected Faster
observation variant and unchanged released YOLO each completed all 156 declared
tiles of the first selected image. A separate checker reproduced the inputs,
verified every saved output and recomputed whole-image postprocessing.

Under the fixed `FP + FN` loss and each of the three recorded reference sets,
YOLO has the lower error. The native engine, conventional matcher and separate
maximum-flow implementation agree. This is one exposed image; the four-image
primary endpoint remains inconclusive.

## What the comparison says

The image is `MultiOrg_v2/test/Macros/Plate_4/image_7/image_7.tiff`. Predictions
use float32 confidence strictly above 0.5. An exact continuous-coordinate IoU
of at least 1/2 permits a match; each prediction and reference can match once.
False positives and false negatives each cost one. These are conditional
counts against recorded annotations, not independently established physical truth.

| Recorded reference | Objects | Faster matches / FP / FN | YOLO matches / FP / FN | Faster loss | YOLO loss | Difference A − B |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `t0` | 88 | 77 / 145 / 11 | 12 / 2 / 76 | 156 | 78 | +78 |
| `t1_A` | 61 | 47 / 175 / 14 | 12 / 2 / 49 | 189 | 51 | +138 |
| `t1_B` | 64 | 56 / 166 / 8 | 12 / 2 / 52 | 174 | 54 | +120 |

The interval across these procedures is **[78, 138]**, supporting YOLO under
this declared loss. Faster matches substantially more reference objects, while
producing many more unmatched detections. This loss preference does not imply better recall, a suitable safety tradeoff
or general detector superiority. Changing
error costs would change the decision question and requires a separate contract.

The engine and competent conventional baseline reach the same answer. No saving
in total analyst work has been demonstrated. For one image, whole-cohort and
imagewise reference intervals coincide by construction; their equality supplies
no evidence about cross-image coupling.

## What now works

| Evidence boundary | Retained result |
| --- | --- |
| Inputs | All 312 model-input tensor identities reconstructed separately and matched. |
| Complete coverage | 156 tiles per model; 312 forwards; one attempt, no retry or substitution. |
| Raw custody | 5,460 arrays, 5,343,183 bytes; all checked against their receipts. |
| Faster origin handling | All 156 corrected tiles agree with direct removal of identified appended RPN origin before selection. |
| Whole-image endpoint | 222 Faster and 14 YOLO detections after the unchanged global NMS; none outside the image. |
| Reference comparison | Three complete fixed-reference cases; native and separate exact matching agree. |
| Resource observation | 306.21 seconds outer inference supervision; peak sampled RSS 1,263,566,848 bytes, within 600 seconds / 3 GiB. |

The correction excluded 156 explicitly appended origins. Fifty-one carried an
unmasked foreground score above 0.5. These are internal observations of the
corrected graph, **not a count of false detections removed from a complete
original-model run**. No such whole-image counterfactual was executed. The
[prior bitwise original-versus-corrected comparison](../0.4.0/README.md) remains
limited to its exposed tile. The ordinary untapped corrected graph remains
unexecuted. The complete lower-threshold storage endpoint is not defined here.

The [current-method review](METHODS.md) led to an explicit failure-policy guard:
ONNX Runtime's constructor and execution fallback are disabled. Its successful
numeric settings, named fetch roster, thresholds and padded tile lattice remain
fixed. Current SAHI defaults would change that experiment and were not adopted.

The [matching adapter](matching/README.md) preserves the native 1,024-detection
limit. Its historical predecessor mistakenly imposed 128. That defect was
identified and the new boundary qualified before comparison outcomes; no
prediction was truncated to pass admission. The old adapter remains unchanged.

## Reproduction and limits

[The protocol](protocol.json), [prospective plan](PROBE_PLAN.md),
[array budget](ARRAY_BUDGET.json), [checking contract](CONTRACT.md),
[controls](controls.json), [exact summary](result.json) and
[provenance](provenance.json) bind the methods and retained evidence.
The separate matching contract and controls are under [matching](matching/README.md).

Seventy-six authored or static controls passed before their respective executions:
23 worker, 26 reference and 27 matching cases. The public pair replay runs 43;
the six additional worker checks require the private prospective manifest.
The public matching replay runs 27. Test counts describe software cases, not
independent empirical replications. Two pre-execution syntax errors and their
corrections remain in the private qualification history.

Use the pinned inference environment described in the
[preceding runtime record](../0.2.0/environment.json): Python 3.13.5, NumPy 2.2.6,
ONNX Runtime 1.23.0, scikit-image 0.25.2, opencv-python-headless 4.11.0.86 and
tifffile 2025.6.11. From this directory:

```sh
python -B reproduce_controls.py --output /tmp/reiyah-0.5.0-controls
```

The destination must be new. This executes authored arrays and mocked sessions,
including the installed runtime's failure-handling wrapper. It performs no
detector inference or download. Counts come from actual completed cases.
Matching controls use the existing Python 3.14.2 / jsonschema 4.26.0 environment:

```sh
python3.14 -B matching/test_matching.py --repository /path/to/reiyah \
  --output /tmp/reiyah-0.5.0-matching-controls.json
```

Raw models, image, annotations, arrays and actual execution packets remain
private under the recorded [source terms](../0.1.0/NOTICE.md). The real-image
result requires those exact retained bytes; the public authored replay does not
recreate it. Derived MultiOrg observations retain CC BY-NC-SA 4.0 terms; source
models retain CC BY 4.0. [Software notices](THIRD_PARTY_NOTICES.md) are preserved.

Runtime inventories and all 84 inference-freeze and 49 matching-freeze bindings
remained unchanged. RECORD checks do not authenticate every system library or
provide a reproducible rebuild. Checksums, same-study separate code and a process
exit are not independent scientific replication, operator acceptance or truth.
The reported execution time excludes investigation, implementation, qualification
and integration; complete-work accounting remains incomplete.

Next follow the [remaining-cohort decision](DECISION.md). Gate A remains
operator-unaccepted; broad product expansion remains stopped pending useful
decision advantage. No automotive transfer, novelty or state-of-the-art
performance is established by this packet.
