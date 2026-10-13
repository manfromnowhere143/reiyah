# A correction that preserves proposal origin

On the previously exposed Faster tile, a separately named export correction
excludes the proven RPN padding descendant before final selection. The four
selected non-padding detections retain their exact scores and coordinates.
A separately authored direct-removal reference agrees with every selected
identity and final output byte. This is a successful correction check on one
tile, not a completed detector comparison or an accuracy result.

## What changed

The [preceding trace](../0.3.1/README.md) found that an appended zero proposal
passed through the ROI head and received foreground score 0.5355819463729858.
Its origin, rather than its coordinates, identifies it as padding.

The [builder](build_correction.py) preserves the exact source weights and graph
except for a batch-one input guard, one output rename and seven nodes. The new
mask compares each sorted proposal's index with the number of rows before the
explicit RPN append. It keeps pre-existing scores unchanged and sets only the
appended descendant's selection score to zero, before the existing TopK, NMS and
output caps. The original positive NMS threshold excludes that masked row.
Genuine malformed boxes remain available for explicit refusal.

| Observed quantity | Original observation graph | Corrected observation graph |
| --- | ---: | ---: |
| ROI rows | 66 | 66 |
| Selected non-padding candidate rows | 4 | 4, bitwise preserved |
| Selected descendants of explicit RPN padding | 1 | 0 |
| Separate final zero-score metadata rows | 1 | 1 |
| Total final rows | 6 | 5 |
| Final rows above the unchanged 0.5 analysis threshold | 4 | 3 |

The final cap of 100 was inactive here. No recovered output slot or improved
accuracy was observed. The [constructed cap example](../0.3.1/correction_order.py)
explains why exclusion must occur before capping in general; deleting a final
row happens to give the same retained rows on this particular tile.

## How it was checked

The [prospective plan](PROBE_PLAN.md) allowed one attempt and two forwards.
All 31 baseline observations reproduced their retained predecessor bitwise.
The corrected graph preserved all 15 observed prefix, neural and decoded tensors
that the checker designates unchanged, along with the original unmasked scores.
Only ROI row 65 was masked; its zero coordinates were not used to identify it.

The [separate reference](check_correction.py) physically removes the appended
origin before sorting, NMS and caps. It does not import the graph builder,
capture code, ONNX or ONNX Runtime. Its scalar suppression routine re-expresses
the pinned runtime's arithmetic and is attributed in the
[third-party notices](THIRD_PARTY_NOTICES.md). It checks identities and copied
bytes, including thresholds and ties. The [conditional equivalence argument](PROOF_AND_SCOPE.md)
states the graph-specific assumptions; the [source review](METHODS.md) records
their evidence and limitations.

Twenty graph controls, 20 capture controls and 15 reference controls passed.
Five graph controls inspect or mutate the exact source graph without executing it.
They include cap displacement, empty genuine populations, equal-coordinate
different-origin cases, genuine invalid geometry, score and IoU boundaries,
ties, unsupported batches, input changes and partial failures. These are software
controls, not independent scientific replication. The initial tiny-fixture
integer-Min load failure is retained; its fixture was corrected before the
experiment, without changing the correction's mask helper.

Execution retained 64 private arrays / 39,362 bytes, within the 60-second / 3 GiB
budget. Peak sampled RSS was 764,739,584 bytes. Worker network was denied before
Python. All 125 frozen bindings and the before/after runtime inventory matched;
the audit checks 5,926 hashed RECORD entries across 17 distributions, with 17
unhashed RECORD self-entries and system libraries outside its scope.
Exact timing and identities are in [result.json](result.json) and
[provenance.json](provenance.json).

## Reproduction and boundaries

Run [reproduce_controls.py](reproduce_controls.py) with the retained parser and
runtime environments and exact graph description:

```sh
python3 -B reproduce_controls.py --parser-python PARSER_PYTHON \
  --runtime-python ORIGINAL_ORT_PYTHON --graph EXACT_GRAPH_JSON \
  --source EXACT_ORIGINAL_ONNX --output NEW_CONTROL_DIRECTORY
```

The graph description can be produced with the preceding
[inspector](../0.3.1/inspect_graph.py) and the pinned original model. The control
replay uses only authored tiny-model inputs and mocked capture sessions; it
does not reproduce the private empirical run. With `--source`, it replays all
55 controls; omitting that argument replays 50 and skips the five static source
checks. The replay reports actual checked counts. Building the variant additionally
requires the exact original model and ONNX 1.19.0. Its [build record](build.json),
[observation roster](taps.json) and [capture contract](protocol.json) are published.
Raw images, weights, tensors and tapped arrays remain private under the
[source terms](../0.1.0/NOTICE.md).

Only the corrected **observation** graph was executed. The ordinary corrected
export has static preservation checks, but no empirical parity check with its
observed counterpart. The result is limited to this exposed tile, source graph,
batch one, single foreground class and retained CPU runtime. Pre-append origin
does not establish a real object, correct localization or absence of earlier
masking. Exact original exporter configuration remains unknown.

The [next decision](DECISION.md) is a separately frozen complete first-image pair
using an explicitly named variant. Earlier failed studies remain failed. No
whole-image metric, prevalence, published-ranking effect, automotive transfer,
novelty, superiority or complete-work advantage is established. Gate A remains
operator-unaccepted and broad product expansion remains stopped.

MultiOrg-derived numerical observations and summaries retain CC BY-NC-SA 4.0.
Code follows the repository license with the stated third-party notices. Source
authors do not endorse this correction or its interpretation.
