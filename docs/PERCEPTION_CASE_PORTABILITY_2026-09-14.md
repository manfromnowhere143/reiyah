# Preparing the next case through the existing Engine

Document ID: `reiyah.engine.case-portability`. Version: `0.1.0`.
Status: `exploratory`. Dated 14 September 2026.

The existing normalization and common-operand interfaces can prepare the 14 remaining frames
from the previously exposed 16-frame development packet. The preparation retains **588 base
detections and 94 additions** from **4,228 original prediction rows**. No Engine implementation
or core schema change was needed. The first two anchors reproduce exactly.

This is an input-preparation result. The new case's detector loss has **not** been evaluated.
The [first annotation case](PERCEPTION_ANNOTATION_CASE_2026-09-14.md) and its pending Fable
challenge remain separate. The new frames come from the same two source scenes, so this does
not establish performance on independent scenes or a held-out population.

## Declared selection and checked preparation

The private `PLAN.json` was recorded before normalization. It selects every frame in the
existing prediction-only packet except `frame-0005` and `frame-0012`, preserving order.
No candidate was replaced or clipped. Configuration-2 remains base, configuration-1 supplies
additions. Score >=0.30, nominal XY range <=50 m, strict same-class suppression distance <2 m,
full qualifying base retention and candidate ordering remain fixed. The new input declares
equal weights 1/14, unit penalties and tolerance 1/10.

The preparation rechecks both full original prediction-file digests and all 32 selected arrays.
It compares the 4,876 literal prediction rows with their original file offsets, sizes, hashes
and zero-based indices. The 648 rows at the original two anchors reproduce their previous
normalization receipts and anchor inputs byte for byte. The remaining 4,228 rows produce 1,111
qualified records and the retained base/addition sets above.

Original sample identities join the existing catalog's nominal clocks and poses. The existing
reference-lineage checker accepts the new normalization. The existing neutral projection and
inverse structural check preserve every retained node, weight and open reference. A request
for the existing annotation adapter is prepared for later use. No annotations were read and
no reference judgment was admitted by this preparation.

| Frame | Source rows | Retained base | Additions |
|---|---:|---:|---:|
| 0001 | 291 | 45 | 11 |
| 0002 | 277 | 49 | 8 |
| 0003 | 292 | 48 | 7 |
| 0004 | 285 | 51 | 7 |
| 0006 | 349 | 52 | 5 |
| 0007 | 361 | 56 | 6 |
| 0008 | 425 | 60 | 9 |
| 0009 | 282 | 30 | 6 |
| 0010 | 261 | 35 | 6 |
| 0011 | 267 | 31 | 8 |
| 0013 | 294 | 31 | 7 |
| 0014 | 304 | 35 | 5 |
| 0015 | 282 | 34 | 5 |
| 0016 | 258 | 31 | 4 |
| Total | **4,228** | **588** | **94** |

## Separate source check and first failures

A separate private accounting script parses the original arrays, reconstructs literal row
boundaries, recomputes score/range eligibility and suppression, and checks the normalized and
neutral retained records, weights, mappings and traces. It calls neither the Engine normalizer
nor its projection. It shares the snapshot helper and the previously bound catalog clocks/poses;
it does not establish physical accuracy or independently reproduce upstream model inference.

The first preparation attempt incorrectly used the core wire-JSON parser for raw decimal
predictions. It failed before producing a packet. The recipe was corrected to preserve exact
source decimals and rerun into a fresh output. The Engine parser was behaving correctly.

The first separate audit omitted the neutral trace comparison. A forged retention entry in
the common trace was accepted; the counterexample and original audit source are retained.
The corrected audit checks that trace too and rejects nine mutations: dropped base detection,
changed weight, wrong source index, false original retention, wrong sample mapping, false finite
reference, false evaluation claim, false admission and false common trace. No Engine defect was
demonstrated by either failure; both were in the new private orchestration/checking code.

Successful preparation took **1.239 command seconds**, with 169,492,480 bytes peak child RSS.
The corrected source audit took **1.221 seconds**, with 180,109,312 bytes peak child RSS. These
measure different work and are not a speed comparison. The failed preparation and earlier audit
remain in the cost record. Writing, interpretation, integration and repair outside captured
commands are unmeasured. Composition still required a new private recipe and audit; this does
not demonstrate low total integration cost.

## Reproduction, scope and next step

Source is main `91af9b59947d136b359a79135f3b2efdf7d687ff`, tree
`296c5a9c3584946d98e317920294ed5411c13ff9`; no Engine code changes in this checkpoint.
The original prediction packet SHA-256 is
`330b91ca70e885a073274cc4fabacad7274a59aeb2d445300a9c69c86ee04356`.
The prepared packet SHA-256 is
`07cc20eaac68039fb063b266ec1afcbfc1bef382f7cfa87fb49604a28d517ad2`.

Complete plans, executable recipes, expected source bindings, outputs and fresh command captures
are retained under `~/.codex/reports/reiyah/engine-case-portability-2026-09-14-idui4k54/`.
The [public verification record](../research/perception-case-portability/0.1.0/verification.json)
binds the aggregate result and checks without redistributing source predictions. Use new output
paths when replaying the retained recipe. Original catalog pose/clock validity remains an
inherited premise; full metadata qualification is not repeated here.

The next step is to consume Fable's separately sealed first-case reconstruction and single-label
challenge. Then run the prepared second case through the same annotation and decision interfaces,
retaining adverse, invalid or unresolved outcomes. Fable retains its comparator ownership;
this checkpoint creates no overlapping assignment. Current main implementation tests remain
the earlier 430 repository/93 measurement checks; this private audit does not rerun or recount
those suites. Gate A acceptance and the prospective physical study remain unchanged.
