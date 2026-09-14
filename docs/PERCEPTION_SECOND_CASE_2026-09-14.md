# A second annotation-conditioned detector comparison

Document ID: `reiyah.engine.second-case`. Version: `0.1.0`.
Status: `exploratory`. Dated 14 September 2026.

The same Engine procedure evaluates the 14 additional frames selected in the
[preparation checkpoint](PERCEPTION_CASE_PORTABILITY_2026-09-14.md). Weighted loss decreases
from **297/14 to 293/14**, an improvement of **2/7** (approximately 0.286). The declared
criterion is **supported** at tolerance **1/10**. Seven anchors improve, six worsen and one
is unchanged. Every selected anchor remains in the result.

The preparation, annotation adapter, reference compiler, common projection and decision interfaces
required no Engine code or schema change. A new private export recipe, reused source auditor and
one repaired audit control were still necessary. This establishes a second executable comparison;
total integration effort and decision value have not been measured.

## Selection, target and source accounting

The selection was recorded before evaluation: all frames in the existing 16-frame packet except
`frame-0005` and `frame-0012`, preserving order. They come from the **same two scenes** as the
first case. This is an exposed retrospective development case, not an independent scene test.

The unchanged target uses configuration-2 as base, configuration-1 additions, score >=0.30,
nominal XY range <=50 m, strict same-class suppression and reference matching distance <2 m,
full qualifying base retention, unit false-positive/false-negative penalties and equal weights
1/14. The [annotation policy](../research/perception-annotations/0.1.0/README.md) retains its
category map, zero-point annotations and explicit exclusions.

All **4,228 original prediction rows** yield **588 base detections and 94 additions**. The
adapter scans all **1,166,187 annotation rows** and selects **841** at the exact sample keys.
**737** meet the target; **101** are outside the nominal 50 m boundary and **3** have unmapped
categories. Original table digests,
row indices, byte offsets, joins and geometric edges are checked by the separate source audit.
No annotation was inserted or relabeled to obtain the result.

| Frame | Included labels | TP base | TP augmented | Loss base | Loss augmented | Improvement |
|---|---:|---:|---:|---:|---:|---:|
| 0001 | 58 | 41 | 49 | 21 | 16 | 5 |
| 0002 | 54 | 41 | 47 | 21 | 17 | 4 |
| 0003 | 56 | 44 | 49 | 16 | 13 | 3 |
| 0004 | 61 | 43 | 49 | 26 | 21 | 5 |
| 0006 | 63 | 45 | 48 | 25 | 24 | 1 |
| 0007 | 66 | 46 | 51 | 30 | 26 | 4 |
| 0008 | 66 | 50 | 55 | 26 | 25 | 1 |
| 0009 | 44 | 28 | 31 | 18 | 18 | 0 |
| 0010 | 43 | 30 | 32 | 18 | 20 | -2 |
| 0011 | 44 | 29 | 30 | 17 | 23 | -6 |
| 0013 | 45 | 29 | 31 | 18 | 21 | -3 |
| 0014 | 46 | 29 | 31 | 23 | 24 | -1 |
| 0015 | 46 | 32 | 33 | 16 | 19 | -3 |
| 0016 | 45 | 27 | 27 | 22 | 26 | -4 |

The original physical-reference question is still **[-8,8]**, with zero admitted human readings.
The new point result is conditional on the benchmark labels and the target above. It is not an
official nuScenes score, a physical validation or a deployment recommendation.

## Checking the first-case challenge

Fable's selected source is `284c2d711fa5de323912fedce07c3c0c8ad084f4`, outbox manifest
`809a8800e9079bc51db2b38caf96417bbd45229e4e32cf8f29ebdc43d971729d`.
All 18 payloads match their hashes; all 14 declared committed payloads match their source blobs.

The Engine independently recomputed the first baseline and all 106 single deletions with its
existing matching implementation and certificate checker. The baseline is +1; six deletions
produce 0 and exclude the improvement criterion; the other 100 remain supported. None of these
deletions produces a strictly negative loss difference. The six named witnesses are confirmed.
This checks the declared graph calculation. Fable's reported original-table reconstruction and
its 732/309 test runs are retained claims, not newly replayed in this consumer check.

Three corrections matter to further use:

1. The outbox's top-level case digest names the old open case. Its deletion and insertion reports
   correctly name the annotation case `ebfebf67...`. The source selection retains both identities
   and the mismatch; the incorrect header is not accepted as the scientific input binding.
2. The reported insertion range [1,2] applies to singles. Recomputing all 190 selected pairs gives
   **[1,3]**, with no criterion changes. On this case all 20 single-insertion edge sets and all
   190 pair outcomes agree with exact supplied geometry.
3. The implementation constructs insertion edges from shared-object graph neighborhoods rather
   than coordinates. This happens to agree on the checked first case, but is not a general
   implementation of the declared distance rule. Two same-class detections at x=0 and x=3 can
   both match an object at x=1.5 under a strict 2 m rule; an inserted object at x=3 cannot match
   the detection at x=0. The function includes that edge. The executable counterexample is
   retained, and the second exchange supplies the existing coordinate-bearing operands.

The finite insertion family does not cover every possible missed object, localization change,
class change or combination of errors. Six deletion witnesses are not measured human review
savings. Two cases cannot establish industry practice. Preregistration timing claims also remain
bounded: the insertion declaration explicitly follows the deletion result; it must be described
as preceding its own family, not as preceding every result in the checkpoint.

## Verification, cost and remaining work

The source audit does not call the annotation adapter or reference compiler. It shares the
JSON/archive readers and the core certificate checker. It checks all selected original label
records and graph edges, and refuses eight meaningful mutations. Existing Fable producer and
checker code agree on **[2/7,2/7]** in an Engine-lane compatibility replay. Both configurations,
objects, edges, weights and original mappings survive the existing cohort export.

The inherited audit initially failed because its forged-result control assigned numerator 2,
which was already the new result's numerator. It changed nothing. The repaired control adds the
denominator to the numerator and checks that every adversary actually changes the input. The
failed auditor, failed command and corrected successful run are retained. This was a private
audit reuse failure; the Engine computation did not change.

Annotation evaluation took **26.306 command seconds**, peak child RSS **255,885,312 bytes**.
The failed audit took **27.289 seconds**; the corrected audit took **27.687 seconds**, peak RSS
**210,534,400 bytes**. Export and compatibility took **0.169 seconds**. These are work-accounting
measurements, not a speedup against another method. Writing, interpretation, human effort and
integration outside commands remain unmeasured. The unchanged Engine's prior 430 repository
and 93 measurement tests are not rerun or recounted as new evidence.

The [verification record](../research/perception-second-case/0.1.0/verification.json) binds the
aggregate evidence. The complete private exchange, recipes and captures are under
`~/.codex/reports/reiyah/engine-second-case-2026-09-14-zw58_irx/`.
The Engine packet SHA-256 is `329fc44df95dde7c49348bf9ff0ad6a66db0952a51c3c6b247aa6d16c2129b0c`;
the Fable case SHA-256 is `d5d84eaf8eb558733ee619e657a73655c38c0b8be5263d5b0099cbe87fd3b5b7`.

Fable owns the next conventional reconstruction and bounded sensitivity study on these exact
inputs. Geometry-dependent edits must use coordinates, and differences between cases must account
for anchor weights, tolerance and margin. The Engine has not run a sensitivity family on this
second case. A robustness result, an adverse finding or unresolved evidence are all valid outcomes.
