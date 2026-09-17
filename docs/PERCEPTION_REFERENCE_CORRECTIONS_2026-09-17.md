# Reference corrections can reverse a detector comparison

Document ID: `reiyah.perception.reference-corrections`. Version: `0.1.0`.
Lifecycle status: `exploratory`.

## Checked development result

On two images from a prospectively selected 64-image development subset, the original and
corrected references reverse the preference between Cascade R-CNN (A) and YOLOX (B).
The outputs, matching rule and loss stay fixed. Positive delta prefers B; negative delta
prefers A. The unit is false-negative plus false-positive count on that image.

| KITTI image ID | Delta with publisher Original GT | Delta with corrected reference | Checked interval admitting both |
|---|---:|---:|---:|
| 005532 | 7 | -1 | [-1,7], unresolved |
| 007121 | 1 | -1 | [-1,1], unresolved |

The first image has 16 A detections, 9 B detections, 13 original references and 23 corrected
references under the fixed policy. The second has 0 A detections, 1 B detection, 1 original
reference and 0 corrected references. These are filtered record counts, not independently
established physical object counts or a correspondence between original and corrected objects.

This establishes a concrete input requirement: reference changes can include additional objects
and different geometry. A deletion-only audit cannot cover all of them. The new 2D adapter
feeds mutually exclusive whole-image reference sets into the existing joint-world Engine.
Both configurations see the same chosen reference set. Old and replacement boxes never coexist
merely because their records appear in the two alternative sets.

It is an operand and correctness qualification. No selection-policy advantage, human-time
saving, official detector leaderboard score or deployment judgment is established.

## Complete population accounting

The publisher split has 1,497 validation images. Before correction values were evaluated,
the task selected the first 64 IDs ordered by
`SHA256("reiyah-recd-development-v1:" + image_id)`. The remaining 1,433 were reserved from
outcome evaluation. Their rows occur in retained source containers and were parsed inertly;
this is a local access discipline, not cryptographic blinding or independent preregistration.
Public paper summaries were read. No untouched-image or independent-scene claim is made.

Every Cascade CSV row was paired with the corresponding publisher export row: 6,428 checked
coordinate/score pairs, a one-to-one UUID-to-filename mapping for 1,383 images, maximum
absolute numeric discrepancy below 1.4e-13 against a declared 1e-8 join tolerance.
This qualifies a publisher-derived join, not source-camera or raw KITTI authentication.
It links 58 of the 64 development images. Six lack that join and retain unknown B outputs
and open original references. Missing data was not converted to observed empty.

| Both reference alternatives admitted | Image cases |
|---|---:|
| Strict improvement by B supported | 5 |
| Strict improvement by B excluded | 51 |
| Unresolved | 2 |
| Input blocked | 6 |
| Total | 64 |

Among the 58 available images, 38 have empty retained outputs for both detectors. They remain
in the accounting; their trivial conclusions cannot support a claim of query savings.
The 16 blocks of four images, fixed by the same ordering, yield 4 supported, 6 excluded,
1 unresolved and 5 input-blocked results. These overlapping blocks are joint-semantics checks,
not 16 additional independent observations.

Each image and block was checked under the original-only, corrected-only and admitted-alternatives
models: 240 packets in total. The 207 available-input packets have exact finite-model results
agreeing with a separate rational geometry and residual-network flow calculation.
The remaining 33 packets correctly retain blocked inputs. No resource ceiling was enlarged.

## Source and numerical contract

Sources: the authors' [REC✓D repository](https://github.com/JonathanKlees/rechecked),
commit `1321946698296416d0495999d000dec2deea5e4d`, published 10 December 2025,
tree `71ef214fcdcc9350138e18b63171d7b14a7bcebf`; the
[6 August 2025 paper, v1](https://arxiv.org/html/2508.06556v1); and the
[KITTI source description](https://www.cvlibs.net/datasets/kitti/eval_object.php?obj_benchmark=2d).
Retained bytes, metadata, terms and digests are bound in the private source ledger.
The 2026 publisher bibliographic page was retained separately; this replay does not claim to
reproduce either paper's benchmark or annotation-time estimates.

- A and B are the published Cascade R-CNN and YOLOX outputs, independently filtered at score >=0.3.
- References use the publisher's `Original GT` export and `validated_gt.csv`, with corrected
  probability >=0.5. That threshold defines a reference set; it supplies no distribution over worlds.
- Predictions and references require height >=25 pixels. All image regions are included.
  There is no don't-care suppression, class substitution, extra NMS or hidden image clipping.
- Rectangles use continuous xyxy pixel coordinates, no pixel `+1`, and IoU >=0.5.
  Maximum-cardinality one-to-one matching differs from the source cost script's greedy matching.
- Source binary floats are converted to exact ratios; CSV decimals are read exactly. Join tolerance
  does not round the geometry used for evaluation. Miss and false-positive penalties equal one;
  strict improvement tolerance is zero. Block weights are 1/4.
- The original annotations are a publisher derivative. Official original KITTI label bytes were
  not acquired or authenticated. The source's complete-export interpretation remains a premise.
- Repository MIT and underlying KITTI CC BY-NC-SA 3.0 declarations are retained separately.
  Third-party payloads and coordinate-bearing derivatives remain private; no unrestricted
  commercial data right is asserted.

The retained pickle contains only primitive data opcodes. A bounded inert interpreter read that
subset without `pickle.load`, resolving globals, reconstructing objects or running upstream code.
Unsupported callable/object opcodes are rejected. This is qualification of one pinned source,
not a general-purpose safe pickle service.

## Engine implementation and its limit

`from-box-alternatives` accepts the [versioned rectangle schema](../research/perception-revision/0.1.0/box-alternatives.schema.json).
It checks exact, positive-area geometry, IoU, stable shared-output identity, joint choice variables,
weights, duplicate IDs, resource limits and unknown states. It emits the existing graph input.
The matching kernel and independent cardinality checker are unchanged. A choice variable may be
shared across anchors; clauses and their joint constraints survive compilation.

The two whole-image sets must already be supplied to this adapter. They do not enumerate every
possible annotation error. In a future audit benchmark, giving hidden corrected boxes to the
selector or its stopping calculation would leak the answer. An unaudited image needs a defensible
open-reference bound or a separately justified error model until its response is obtained.
Reference discovery and human error are not solved by having a finite-world compiler.

Validation passes 486 repository tests and 93 measurement tests. Ten new tests cover insertion,
geometry replacement, coupled worlds, exact boundaries, missing/open inputs, shared-output
identity, malformed geometry, limits, omitted worlds and CLI digest/non-overwrite behavior.
They include 768 integer-cross-product checks of rational overlap eligibility.
All 240 real-development packets were regenerated and checked with the final implementation.
Producer/checker agreement and our separate flow calculation are engineering checks, not external
scientific replication. The [verification record](../research/perception-revision/0.1.0/reference-corrections-verification.json)
binds the exact evidence and implementation.

## Next allocation

Engine supplies this qualified development source, common operand format and checked results.
The independent research lane keeps ownership of selectors, conventional baselines and complete
cost accounting; its ongoing census is preserved. No human review or model inference is needed
to consume the development packet.

The next performance experiment must freeze selection rules, query units, unrevealed-outcome
access, error assumptions, dependence groups, stopping obligations and complete costs before
using the reserved population. A substantial advantage over the strongest applicable baseline,
including unresolved and blocked cases, is still the threshold for a headline about reduced
validation work. No public post or outreach is sent by this checkpoint. Gate A remains unaccepted.
