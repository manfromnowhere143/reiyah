# Prediction preparation without annotation reads

Document ID: `reiyah.engine.prediction-inputs-checkpoint`. Version: `0.1.0`. Status: `exploratory`.

The Engine now prepares **4,876 original submitted predictions** across the same 16 exposed
development keyframes: 3,077 from configuration 1 and 1,799 from configuration 2. Two runs
produce identical packet and array bytes. A separately structured conventional reader agrees
on every selected row, including original zero-based indices, source offsets and hashes.

The deficiency was practical: existing common assistance includes annotations, while Fable's
earlier research caches include only predictions matched to annotated objects. The new
[bounded input interface](../research/perception-predictions/0.1.0/README.md) supplies exact
submitted arrays for independent research without inheriting that cache's selection. It does
not perform Fable's association, overlap, uncertainty or detector-decision calculations.

## Selection and information boundary

The two original submissions are the retained Megvii and Mapillary validation outputs, totaling
568,897,545 bytes. Their expected digests are independently selected in the private request.
All 16 historical development frame identities are retained, in order. Request construction
projects only frame keys and original prediction-source identities from the previously bound
custody record. That older record contains annotations; these frames are already exposed.
The claim is **no annotation-bearing data reads during extraction**, not annotation-independent
historical selection, unexposed evaluation or a newly selected study.

The producer scans both complete originals and copies 32 exact arrays totaling 2,164,695 bytes.
It does not remove low scores, distant predictions, unknown classes, duplicates or unmatched
predictions, and it does not convert missing output to an empty array. Source numeric values
are preserved lexically. Shape and sample-key checks do not validate physical geometry or
make all numeric fields suitable for downstream computation.

Each real run executes with a Python file-access audit hook after imports. The request, two
original submissions, exact implementation files, new temporary snapshots and new output
paths are allowed. Controls attempt to open the prior annotation-bearing custody, common
assistance and metadata archive; all are denied. Preparation has zero unexpected access
attempts. This is a checked Python execution boundary, **not an OS or native-code sandbox**.
It neither undoes previous benchmark exposure nor inspects all imported native dependencies.

The [official nuScenes format](https://github.com/nutonomy/nuscenes-devkit/blob/b40adc467b919192899405d9b77871afee8efa07/python-sdk/nuscenes/eval/detection/README.md#results-format)
defines submitted arrays by sample and nominal global geometry. The selected 6 August 2026
repository version, format bytes and license are retained privately in the source ledger.
The Engine copies those submitted outputs; it has not obtained pre-NMS network outputs or
established physical object correspondence. No third-party payload is added to public Git.

## Verification and measured cost

The full repository suite passes **418 tests**, including 14 new input-fidelity and failure-path
tests. Eight further forged-packet controls pass with Engine producer functions disabled in the
conventional audit process. They reject omitted frames/rows, changed indices, a substituted
equal-valued duplicate, false absence, false reference admission, changed source identity and
changed numeric bytes. The selected real arrays all agree with the conventional reader.
The existing research consistency check passes; its retained experiment identities are checked,
not replayed. Prior 93 measurement tests remain retained evidence, with unchanged source bindings.

| Captured command | Elapsed seconds | Child peak RSS, bytes | Scope |
|---|---:|---:|---|
| First guarded preparation | 21.729 | 50,200,576 | Full-source scan, exact extraction and access controls |
| Second guarded preparation | 22.758 | 50,774,016 | Same request; identical output bytes |
| Conventional selected retrieval | 6.865 | 382,402,560 | Original hashes and all selected arrays/rows; narrower parser scope |
| Full repository suite | 61.952 | 292,814,848 | 418 tests |

These are captured wall intervals and macOS child peak RSS, not isolated algorithm benchmarks.
The second preparation, conventional reader and suite ran concurrently. Their different scopes
do not establish a speed ranking. Human preparation, review and integration effort remain
unmeasured. Exact command/input/output identities and the final scoped checks are in
[verification.json](../research/perception-predictions/0.1.0/verification.json).

The initial targeted run passed. Before execution, review caught a possible filename collision
from concatenating user labels; positional names replaced it and a discriminating test pins the
choice. An edit initially targeted the wrong loop and was corrected before execution. The
primary-source license URL returned 404; the actual license filename was then selected from a
commit-bound listing. These are retained development corrections, not erased failed evidence.

## What changes next

The private packet is ready for both analysts to consume under the same explicit research
selection. Fable can trace an association to exact original rows, preserve unmatched detections
and quantify the effect of its declared association choices. The consumer action is to select
and verify this packet before adapting a research reader; no Engine ownership transfers.

Actual human inspection remains the priority when a participant return becomes available.
The staged review protocol, joint reference alternatives, weights, loss, tolerance and matching
competition are unchanged. The real comparison remains **[-8,8]**, with no admitted human
references, participant-usability evidence or external scientific review. Gate A is unaccepted;
the frozen prospective physical study has no selected cohort or seed and has not run.
