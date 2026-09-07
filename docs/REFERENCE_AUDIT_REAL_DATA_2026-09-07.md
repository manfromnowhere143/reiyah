# Reference audit on the retained camera and lidar data

Document ID: `reiyah.reference-audit-real-data.2026-09-07`

Version: `0.1.0`

Lifecycle status: `exploratory`

The [portable reference auditor](REFERENCE_AUDIT_DEMO_2026-09-07.md) was executed against
private copies of the four source files bound by the frozen reference study. Its independently
written rational-distance calculation reproduces AO's aggregate population correction. It also
makes the frame-selection boundary explicit and measures a separate extension to omitted
frames. No detector was run, no physical object was adjudicated, and the frozen study is unchanged.

## Reproduction of the declared AO population

The [adapter](../tools/measure/replay_reference_population_audit.py) verifies every cached
annotation token and its XY position against the original annotation table. It also checks
timestamps and sensor prediction sample coverage. Original decimal coordinate tokens are
preserved; they are not rounded into the auditor's input. The adapter does not independently
reimplement the upstream evaluator's class/range/ignore policy.

The [aggregate replay](../evidence/developer-value/real-replay-0.1.0.json) records:

| Quantity | Camera | Lidar |
| --- | ---: | ---: |
| Frames represented in the cache | 5,953 | 5,953 |
| Score-qualified predictions | 103,008 | 119,670 |
| Near an included evaluation annotation | 78,576 | 95,830 |
| Evaluation-unmatched but near an excluded annotation | 3,151 | 5,728 |
| Unmatched in the supplied wider annotation table | 21,281 | 18,112 |
| Unknown-reference predictions in this supplied population | 0 | 0 |

The two evaluation-unmatched proximity categories recover the existing 24,432 and 23,840
evaluation-unmatched counts. The zero unknown-reference count means reference tables were
available for this calculation. It does not establish that their annotations are complete or
correct. Every physical false-positive rate remains null.

The [completed supervisor capture](../evidence/developer-value/real-replay-capture-0.1.0.json)
records the observed exit, stream digests and numerical environment. Its elapsed time includes
input verification, metadata parsing, audit execution and private report writes; it is a local
development observation, not a latency benchmark or production service claim.

## A separate frame-coverage sensitivity

The cache contains object rows rather than a complete frame census. Both prediction files
contain the same 6,019 frame identifiers, and those identifiers equal the sample-table census
for the same 150 observed scenes. Only 5,953 frames occur in the cache, leaving 66 outside
the original analysis. This check does not independently reconstruct the official dataset split.

The [coverage audit](../tools/measure/audit_reference_frame_coverage.py) reads the complete
sample and annotation tables for those omitted frames. Its
[retained result](../evidence/developer-value/frame-coverage-0.1.0.json) gives:

| Quantity on omitted frames | Camera | Lidar |
| --- | ---: | ---: |
| Score-qualified predictions | 22 | 202 |
| Near an annotation absent from the cache | 2 | 26 |
| Unmatched in the supplied wider table | 20 | 176 |

Across the omitted frames, 63 have annotation records and 3 have an explicitly empty
annotation table; there are 303 annotations in total. An empty table is a known property of
the supplied data and remains distinct from an unavailable table. It is not proof of an empty
physical scene.

The extended prediction population contains 103,030 camera and 119,872 lidar detections at
the same threshold. These are a separate retrospective population, not corrected denominators
silently substituted into AO or the probability sample. The study's released protocol expressly
conditions on frames present in the cache, so this observation does not invalidate its selection.
It prevents that conditional result from being casually described as covering every frame.

## Independent numerical comparison and interpretation

The [comparison implementation](../tools/measure/compare_reference_replays.py) imports
neither the auditor nor its adapter. It rebuilds proximity classifications using floating-point
spatial indexes on every retained bundle and checks each prediction's classification against
the rational implementation. There are zero classification disagreements across 222,902
predictions: 222,678 in the cache-conditioned replay and 224 in the omitted-frame extension. The
[comparison record](../evidence/developer-value/numerical-comparison-0.1.0.json) reports its
executed scope and any disagreement. The bundle construction and original source evidence are
shared; this is numerical cross-checking, not independent annotation truth or new model inference.

Per-frame bundles, sample identifiers and prediction-level reports remain private. Their
digests are retained with the aggregate records. Neither this implementation nor matching
aggregate counts certifies the upstream reference or grants a physical interpretation.

The architectural lesson is concrete: an object-level reference cache must not silently define
the frame opportunity universe. A reusable audit needs the census, inclusion policy, explicit
empty cases and unavailable cases separately. The next scientific step still requires the
independent sensor judgments in the already prepared reference study.
