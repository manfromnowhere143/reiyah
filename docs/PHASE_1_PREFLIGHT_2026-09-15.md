# Phase 1 preflight: what the inputs actually support, and three corrections closed

Document ID: `reiyah.phase-1.preflight.2026-09-15`

Version: `0.1.0`

Lifecycle status: `proposed`

Date: 2026-09-15. Lane: independent research.

Artifacts: [`research/phase-1/0.1.0/input-preflight.json`](../research/phase-1/0.1.0/input-preflight.json),
[`research/label-dependence/0.3.0/PREREGISTRATION_CORRECTION_0_3_1.json`](../research/label-dependence/0.3.0/PREREGISTRATION_CORRECTION_0_3_1.json),
[`research/label-dependence/0.5.0/second-case-insertions.json`](../research/label-dependence/0.5.0/second-case-insertions.json)

## The gating question, answered

The consumer was right that the matched caches cannot carry this study. Each holds an annotation
index to matching score map and a scalar reconstructed mAP. It preserves no prediction identity, no
coordinate and no false positive, so it cannot support rematching after a deletion. Holding five
caches does not mean holding five detector inputs, and the earlier claim that the data was already
in hand pointed at the wrong hand.

The complete original submissions are a different matter, and they qualify.

| detector | bytes | frames | predictions | missing coordinates | classes |
|---|---:|---:|---:|---:|---:|
| centerpoint | 221,909,038 | 6,019 | 478,401 | 0 | 10 |
| fcos3d | 204,826,448 | 6,019 | 444,706 | 0 | 10 |
| mapillary | 343,998,291 | 6,019 | 799,060 | 0 | 10 |
| megvii | 224,899,254 | 6,019 | 483,959 | 0 | 10 |
| pointpillars | 895,962,772 | 6,019 | 3,009,500 | 0 | 10 |

All five cover the full 6,019 frame validation census, carry every prediction with a translation, a
class and a score, and use only the ten detection classes. 5,215,626 predictions in total, each
bound by digest in the artifact.

That makes the study runnable on ten unordered pairs or twenty ordered additions. It does not make
those independent experiments: they share scenes, objects and detectors, and the counting unit has
to be declared before any outcome rather than assumed from the frame count.

Two population facts must not be silently merged. The 134,565 row annotation cache uses a class
dependent inclusion range, cones and barriers at 30 m, pedestrians and two wheelers at 40 m,
vehicles at 50 m. The existing decision cases use a common 50 m range. These are different
populations and the study will declare which one it means.

## Three open issues, closed

**A partial coordinate map dropped an eligible edge.** A map holding some same class detections and
not others silently skipped the missing ones, so an insertion looked less reachable than the
declared rule makes it. Reproduced on a two detection control where the omitted detection sits 1 m
away and is eligible. Required geometry is now required in full per anchor, and an incomplete map is
refused rather than used.

**The second case insertion family was planned and never run.** Now executed: 119 unmatched
retained detections, 119 singles ranging `[2/7, 3/7]`, all 7,021 pairs ranging `[2/7, 4/7]`, zero
criterion changes. Insertions only raise the decision here, as in the first case, so the direction
asymmetry replicates alongside the fragility ratio.

**The preregistration claimed the second case did not exist. It did.** The prepared case operands
existed at `2026-09-14T16:23:49Z`, twenty one minutes before the preregistration was recorded at
`16:45:20Z`. The `CASE.json` this lane consumed was written at `16:46:01Z` and the preregistration
was pushed at `16:48:18Z`. No file carrying the decision `2/7`, `293/14` or `297/14` existed before
the preregistration, so the computed outcome did not exist anywhere findable.

What is true is an exposure statement, not an existence statement: the measure was fixed before this
lane received, read or computed any part of the case, and before its decision existed. That is the
property that mattered scientifically, and it survives. The claim as published does not, and version
`0.3.0` is retained unchanged with the correction as a versioned successor.

## A named failure mode

This lane has now asserted absence from local absence three times: that nobody runs this analysis,
that its rigor exceeds two named companies', and that a case did not exist because it had not
arrived here. All three are withdrawn, and the register now carries ten withdrawals against four
standing headlines.

The pattern is worth naming because it is not carelessness about evidence, which this lane guards
well. It is carelessness about the boundary of the inbox. Anything outside it is unobserved, and
unobserved is not absent.

On the specific comparisons: NVIDIA publishes robot policy evaluation and diagnostics work, and
Foretellix sells traceable verification analysis. Those are standards to measure against, not claims
to have beaten.

## Prior art this study has to position against

Northcutt, Athalye and Mueller, NeurIPS Datasets and Benchmarks 2021, established that pervasive
test set label errors can destabilize benchmark rankings. That is the same broad phenomenon and it
predates this work by five years. The minimal explanation and hitting set literature, including
arXiv:1604.08229, established the formalism behind a minimum set with a dual bound.

So the mathematics here is standard and the phenomenon is known. What this lane has that is
narrower: a matching aware minimum, where deleting a label lets the matching reassign so the effect
is not additive across items; a proved arithmetic floor from the weights, penalties and margin; and
a ratio that makes two decisions with different weights and margins comparable. Whether that
narrower thing is a contribution is for reviewers to say, and this lane will not assert it.

## What comes next

A fresh versioned protocol before any scale outcome, declaring the decision unit, the pair
direction, the inclusion policies, the correction unit, the search and certification budget, every
stopping outcome including unresolved, and the counting denominators with scene clustering made
explicit. The earlier two case protocol does not preregister this study and will not be reused for
it.

The reportable form is fixed in advance: among N declared annotation conditional decisions under
loss L and error family F, X were certified at their arithmetic floor, Y above it, and Z remained
unresolved. A null or uninteresting distribution is a publishable result.
