# Reconstructing the reference cache from the original metadata

Document ID: `reiyah.cache-selection-audit.2026-09-07`

Version: `0.1.0`

Lifecycle status: `exploratory`

The independently written selection audit agrees with the retained cache on every annotation
identity and every checked metadata field. This is positive evidence for the cache's declared
construction. It does not reverse AO's correction: a correctly constructed class-and-range
reference is still narrower than the complete annotation table or the physical world.

## Question, comparison and sources

The preceding [population replay](REFERENCE_AUDIT_REAL_DATA_2026-09-07.md) verified
cache membership against annotation tokens and positions, but did not reconstruct the
upstream inclusion policy or official validation split. This investigation addresses those
specific gaps. Its specification was written before the new metadata calculation began.

The [new implementation](../tools/measure/audit_cache_selection.py) executes neither the
cache builder nor upstream SDK code. It extracts literal class mappings, class ranges and
validation-scene names from privately retained upstream sources at commit
`b40adc467b919192899405d9b77871afee8efa07`. The current validation-scene list also exactly
matches the historical split file retained by Reiyah. This does not establish the exact
historical SDK environment in which the original cache was produced.

The inspected upstream [category mapping](https://github.com/nutonomy/nuscenes-devkit/blob/b40adc467b919192899405d9b77871afee8efa07/python-sdk/nuscenes/eval/detection/utils.py)
and [evaluation configuration](https://github.com/nutonomy/nuscenes-devkit/blob/b40adc467b919192899405d9b77871afee8efa07/python-sdk/nuscenes/eval/detection/configs/detection_cvpr_2019.json)
define the relevant labels and ranges. The retained
[distance/filter implementation](https://github.com/nutonomy/nuscenes-devkit/blob/b40adc467b919192899405d9b77871afee8efa07/python-sdk/nuscenes/eval/common/loaders.py)
uses the LIDAR_TOP ego pose and a strict planar range comparison. Its later point-count and
bike-rack filters are distinct operations. This cache intentionally precedes those operations;
the new check does not claim full official-benchmark conformance.

The [source ledger](../evidence/cache-selection/source-ledger-0.1.0.json) binds the six
privately retained primary files, including upstream licensing text. Newly retrieved payloads
are not placed in public Git and are not admitted as Gate A evidence. The same four immutable
raw inputs used by the frozen study supply the cache, metadata and two prediction tables.
The public specification is an explicitly marked aggregate projection. Its scene-identifier
list remains private; the full executed specification and that list are separately digest-bound.

## Calculation and results

The audit derives the opportunity census from the retained official validation-scene list
and complete sample table. It resolves each frame's unique keyframe LIDAR_TOP record and
ego pose, then evaluates mapped-category inclusion and strict squared XY range using exact
rational arithmetic on the source decimals. It compares annotation-ID sets, not just totals.
Checked cache fields are sample identity, instance identity, timestamp, mapped and raw class,
lidar/radar point counts, object XY and ego XY. Rounded display distance, visibility and scene
condition labels are outside this particular comparison.

| Quantity | Count |
| --- | ---: |
| Official validation scenes | 150 |
| Official validation frames | 6,019 |
| All validation annotations | 192,041 |
| Unmapped categories | 4,513 |
| Mapped annotations outside the strict class range | 52,963 |
| Annotations selected by the declared cache policy | 134,565 |
| Selected annotations with zero lidar and radar points | 12,694 |
| Validation frames without selected annotations | 66 |
| Expected annotation IDs absent from the cache | 0 |
| Cache annotation IDs outside the expected set | 0 |
| Cached rows with a checked metadata disagreement | 0 |

Both prediction tables contain exactly the 6,019 official validation frames, with no missing
or extra frame identifiers. The source's 150 validation scenes are represented. The
[result](../evidence/cache-selection/result-0.1.0.json) records the class counts, exact-ID
comparison, metadata comparison and complete-frame census. Per-annotation dispositions
remain private and are bound by digest.

The 66 frames without selected annotations are therefore an expected consequence of the
declared class/range policy. They must remain present in a frame opportunity census even
though an object-row cache has nothing to store for them. The cache deliberately retains
12,694 zero-point annotations; removing them here would change the scientific population.
The frozen 240-case detection study remains unchanged.

## Controls, limitations and next action

The nine controls exercise strict distance boundaries, unmapped categories, an equal-count
annotation-ID swap, retained zero-point objects, explicit empty frames, wrong cached geometry,
missing ego poses, duplicate keyframes, non-execution of source Python and a failing CLI
source-closure path. Several controls share a test method; the retained test count is nine.
The [development verification](../evidence/cache-selection/verification-0.1.0.json) binds
successful process captures, sources and outputs, reaggregates private dispositions, and
checks this report's numerical table. It preserves the predecessor artifacts outside the
explicit navigation updates.

The streaming JSON reader is shared with the preceding audit adapter, while the selection
calculation is separate from the original cache builder. Source annotations and predictions
are the same retained data, not independent physical evidence. Exact arithmetic concerns
recorded coordinates, not sensor accuracy. A supported cache-construction claim is not a
physical error-rate estimate, a scientific novelty claim or an accepted release.

This closes the declared cache-selection question for these exact inputs. The next physical
observation remains independent adjudication of the prepared cases. A separate
[reference-noise interpretation correction](REFERENCE_NOISE_INTERPRETATION_2026-09-07.md)
explains why neither correct caching nor a scalar reference-error budget is sufficient to
turn a coincidence coefficient into a reference or safety certificate.
