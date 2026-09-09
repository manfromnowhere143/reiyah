# Engine continuation at the discovery checkpoint

Document ID: `reiyah.perception-engine.continuation`

Version: `0.1.0`

Lifecycle status: `exploratory`

This is the Engine handoff to a fresh session. It records completed implementation and the next
bounded task. It does not release a protocol, accept Gate A or report a new scientific result.
The [machine record](../research/perception-engine-handoff/0.1.0/handoff.json) binds the selected
design and completed checkpoints. Earlier handoff blocks and study files remain historical at
their own dates; their former "next" instructions do not supersede this continuation.

## Direction and evidence standard

The first user is a perception-validation lead deciding whether an added detector merits a
further integration study. Reiyah compares the base and augmented outputs on the same recordings,
under the same reference interpretation and declared loss. It returns a checked enclosure and
the supported, excluded or unresolved proposition. The long-term value must be earned through
consequential decisions that survive independent review and competent conventional comparison.

The selected laboratory is automotive perception. The first comparison uses retained
Megvii/CBGS lidar outputs versus those same outputs plus retained Mapillary/MonoDIS camera
outputs. Those historical outputs do not benchmark current frontier models. A general assurance
platform, cross-domain expansion, a new world model, the query-allocation challenge and the
shared/disjoint detector-training campaign are not the next Engine implementation task.

Read the [selected architecture](PERCEPTION_DECISION_ARCHITECTURE_2026-09-09.md) and
[study plan](../research/perception-decision/0.1.0/study-plan.json) for the exact definitions.
The operator authorized offline Engine implementation and professional integration. Gate A
remains operator-unaccepted; this does not authorize deployment, physical control or a safety claim.

## Mathematical contract to preserve

For one common reference interpretation, let a and b be nonnegative FN and FP penalties,
r the retained additions, and TP the maximum same-class one-to-one matched count:

```text
delta = loss_base - loss_augmented
      = (a+b) * (TP_augmented - TP_base) - b*r
0 <= TP_augmented - TP_base <= r
-b*r <= delta <= a*r
```

Positive delta favors the addition under that loss. These are conventional identities. The
shared target count cancels only under the specified additive loss and common population.
Unknown objects can still change the matching through the base detector. Preserve the synthetic
base-neighbor counterexample and all admitted cross-anchor alternatives. Do not substitute F1,
planner loss or crash risk into this identity.

Exact rational arithmetic prevents numerical boundary drift; it does not establish calibration,
timing or physical truth. Maximum matching is certified by a matching and an equal-size vertex
cover. The checker must not invoke the producer's matcher. Their shared parser and representation
remain an explicit trusted surface. A model-relative enclosure is not a physical confidence
interval. A wide enclosure alone is not a proof of non-identifiability.

When unlisted matchable objects remain possible, retain an open reference and the verified count
bound. Resource limits must not remove adverse interpretations. Invalid required inputs leave
the decision unevaluated; an optional tighter calculation may fall back only to a separately
checked valid bound. Improvement greater than a tolerance and preference between configurations
are distinct propositions.

## Implemented and committed

The implementation parent for this handoff is `9b9097f57ef32b19b0eaff0af911c09ef1e15234`.
This handoff adds documentation only. Its final commit is obtained from Git and the private
delivery record, avoiding a self-referential commit field inside committed content.

| Component | Entry point and scope |
| --- | --- |
| Paired-loss kernel and checker | [Core interface](../research/perception-decision/0.1.0/README.md); normalized contracts, matching certificates, joint finite models, open fallback and atomic packets |
| Complete source and clock adapter | [Input interface](../research/perception-inputs/0.1.0/README.md); source identities, every parent anchor, normalization and history exclusions |
| Joint reference compiler | [Reference interface](../research/perception-reference/0.1.0/README.md); explicit presence/class/alias/geometry/time alternatives and coverage assumptions |
| Raw windows | [Window interface](../research/perception-windows/0.1.0/README.md); recorded sweeps, gaps, availability and payload validation |
| Nominal spatial/time operands | [Geometry interface](../research/perception-geometry/0.1.0/README.md); exact nominal transforms with separate physical uncertainty |
| Restricted observation package | [Observation interface](../research/perception-observation/0.1.0/README.md); neutral IDs, relative times, original image bytes and PLY-wrapped lidar |
| Discovery record custody | [Discovery interface](../research/perception-discovery/0.1.0/README.md); inspection/exposure states, proposal evidence, immutable seals and structural pair checks |

The observation and discovery commits are respectively
`b3423d0d9d917587c1ffebcbe0f0aa23be402835` and
`9b9097f57ef32b19b0eaff0af911c09ef1e15234`. Both were pushed and every changed file was read back
at the exact public commit. That is publisher-authored readback, not independent transport evidence.

The same two previously exposed development windows contain 725 captures: 566 camera images and
159 lidar files, with 5,521,024 point records. Every package asset was delivered. The separately
sourced Stanford PLY reader recovered every point-field byte; its initial compiler failure and
one-line linkage compatibility change remain retained privately. No third-party reader code or
raw payload entered public Git. Complete recorded captures do not establish complete observation
of the physical scene.

The sole real-data discovery draft is unassigned: 725 occurrences not inspected, no proposals,
unknown exposure and no human judgment. Sealing it was correctly rejected with
`DISCOVERY_REVIEWER`; no sealed output exists. Complete and paired reviewer examples are synthetic
tests only. Distinct reviewer handles and local timestamps do not prove human independence or
blinding. The pair checker cannot release assisted information or authorize phase 2.

The latest implementation checkpoint passed 238 repository tests and 93 measurement tests,
331 in total, plus Gate B integrity checks. These are retained development checks at the
implementation parent. This documentation closeout exact-binds unchanged implementation and
test bytes; it does not relabel those executions as fresh tests or Gate A release validation.
Historical empirical transcripts and claim-register entries are unchanged.

## Exact stopping point and next task

The next slice is **comparison/observation population binding**. A private export was prepared
from the implementation parent, but it has no implementation changes, new tests or experimental
runs. It is a design/preflight only. Start a fresh candidate from current main after identity and
worktree checks; preserve the old export as a record.

The problem is specific: an internally valid review package could be attached to a comparison
of different anchors, samples or clocks. A separately resealed asset could also differ from the
original source inventory. Reject those substitutions before reference observations constrain
the comparison.

1. Bind exact comparison, normalization, catalog, observation custody and separately expected
   package-seal identities. Reverify package bytes before consuming its manifest.
2. Replay the neutral projection from the exact window and geometry reports. Derive private
   mappings from those source-bound reports; do not trust a copied custody mapping by itself.
3. Require a bijection between comparison anchors and review windows, with exact sample, scene
   and time agreement. Bind window/geometry/catalog metadata identities and normalization roles.
4. Check delivered JPEG bytes against the original retained inventory. For PLY, check the
   unchanged point body after the fixed, verified header. Preserve nondelivered states.
5. Produce a small private binding report. Exercise wrong population, wrong source, swapped
   assets, duplicate/omitted anchors, unavailable data and output-reuse rejection with fixtures.
6. Recheck the same two development windows. This verifies integration only; it must not create
   reference judgments, select a study cohort or close unknown physical coverage.

Reuse the existing package verifier and projection and the reference compiler's joined-detection
checks where their assumptions fit. Record the resulting trusted surface. A successful binding
does not independently prove normalization, nominal geometry or observation validity.

After that slice, connect locked discovery, assisted proposals and adjudication to the shared
reference alternatives, preserving original records and unresolved coverage. This remaining
source-content connection is not implemented by the existing reference compiler merely because
it accepts digests naming external records.

## Study state and stopping rules

The proposed study has 60 scenes, one eligible anchor per scene, equal weights and unit FN/FP
penalties. Its research improvement threshold is greater than 0.1 error units per anchor.
Selection follows exact method/input/protocol/reviewer/comparator/adjudication freeze. Preserve
score >= 0.30, 50 m XY range, strict 2 m same-class suppression/matching and the declared ties.
This is not the official class-dependent nuScenes evaluation protocol.

There is no selected cohort or random seed. No independent reviewers, conventional comparator or
adjudication arrangement have been secured. The current two-anchor open-reference enclosure is
[-8,8] under unit penalties. No physical study outcome exists. Reviewer availability blocks
physical study execution, not the next authorized offline binding implementation.

Both unassisted records must be locked before assisted annotations/predictions are disclosed.
The conventional analyst gets the same staged evidence and may compute the same mathematics.
Do not weaken the comparator. Record total preparation, review, integration, computation and
repair effort. No substitutions for difficult selected cases, outcome-driven tuning, fabricated
humans or self-adjudicated superiority. Preserve negative and unresolved outcomes.

## Engineering and lane discipline

- Resolve the canonical Reiyah root, Git root, AGENTS, live main and worktrees before action.
  The owner checkout can remain on older Gate A while main contains the Engine. Do not reset,
  switch or merge over another session's checkout to make those identities look alike.
- Use isolated main-based exports and a private Git index, or an equivalently safe established
  workflow. Preserve exact unrelated bytes. Inspect the complete diff, update the handoff,
  commit as Daniel Wahnich with no AI coauthor trailer, update refs by compare-and-swap and push
  normally. Resolve newer main changes before integration; never force-push to erase them.
- Work on the Engine only. Console/UI and the parallel tail-dependence research lane retain
  their owners. Do not wholesale merge that older lane over current Engine main. Review any
  proposed scientific contribution on its own source, population, inference and provenance.
- Keep raw assets, private paths, source-derived identities and review records outside public
  Git. Expected hashes must come from a separately selected record. Reject malformed input,
  nonfinite values, ambiguous identities and unavailable-state coercion with explicit diagnostics.
- Test consequential inference and failure paths, including the independent checker, exact
  boundaries and adversarial fixtures. Preserve failed run transcripts. Run relevant offline
  checks after code changes; do not repeatedly rerun unrelated empirical experiments.
- Keep absence, missingness, unmeasured state, sensor invalidity, abstention and outside support
  distinct. Lifecycle, execution, model validity, physical coverage, authority and preference
  must never be collapsed into one PASS/FAIL.
- The README and six Mermaid diagrams were aligned at the geometry checkpoint. Preserve that
  coherent direction; do not rewrite them wholesale for this handoff. Measure and Console are
  evidence production and consumption surfaces, not independent sources of truth or authority.

The required quality is reviewable mathematics, meaningful failure tests, explicit uncertainty
and a useful engineering decision. Code size, test counts, model agreement, polished prose and
ambition do not establish novelty, frontier superiority, safety or commercial value.

## Resume entry

Read this document, the machine record, selected architecture, current discovery/observation
interfaces and the private continuation packet indexed by the operator's Reiyah Research
START_HERE document. The private packet contains exact local inputs, expected hashes, retained
commands, unresolved implementation details and the communication follow-up record. It also
identifies the prepared but untouched binding export. No background continuation is implied by
this handoff; the receiving session must resume the next task explicitly.
