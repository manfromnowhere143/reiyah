# Independent opportunity discovery: proposed study design

Document ID: `reiyah.independent-opportunity-study-design.2026-09-07`

Version: `0.1.0`

Lifecycle status: `proposed`

## Question, hypothesis and why now

Can independently selected raw recording windows support a defensible census of physical
object opportunities, including objects absent from both detectors and the reference?

The hypothesis is that model-blind multiview and temporal inspection can reveal some
consequential omissions and constrain reference ambiguity enough to change what Reiyah
can identify. The hypothesis includes the possibility that the available recordings are
insufficient. The [exact counterexamples](REFERENCE_IDENTIFICATION_FINDINGS_2026-09-07.md)
show why more output-only samples cannot settle this question.

This is the next design investigation alongside the already frozen 240-detection study.
It does not replace, extend or relabel that cohort. No scene selection or human observations
are claimed completed by this proposed design.

## Minimum discriminating experiment

Use a reviewability pilot with 24 distinct scenes, one anchor per scene. This count budgets
the workflow; it is not powered to estimate a rare joint-failure rate or certify completeness.
Before sampling, freeze the official scene census, clock-based anchor eligibility, random
selection procedure, spatial/class definitions, evidence presentation and analysis rules.

Choose scenes uniformly without replacement from the eligible official validation scenes,
then an anchor uniformly from each selected scene's eligible anchors. Anchor eligibility
uses timestamps and scene boundaries: at least two seconds of scene extent before and after
the anchor. It must not depend on detections, annotation presence, disagreement, apparent
difficulty, or a known reference error. Missing sensor records and unreviewable content
remain sampled outcomes, not post-selection exclusions. If S scenes are eligible and scene
s has n_s eligible anchors, an anchor's inclusion probability is (24/S)/n_s.

At each anchor, the proposed object population comprises the ten declared nuScenes detection
classes with centers within 50 meters in the horizontal plane, including the cases that
cannot be resolved from the recording. This is a distinct research population with a common
range; it is not the official class-range-filtered detection benchmark. Unknown class, depth,
center, identity or boundary membership remains unresolved. The first protocol must enumerate
the exact class mapping and freeze the spatial rule before selection.

Each reviewer first inspects the original cameras and lidar over the anchor and its temporal
context, with sensor timestamps and calibration available. No detector or dataset annotation
overlay, case-selection key, previous result or algorithm identity is shown. Reviewers record
candidate physical objects, evidence for presence at the anchor, uncertainty in identity and
geometry, and regions where the recording cannot establish coverage. A later visible object
is not automatically proof of its earlier position; that inference needs a time/motion argument.

Only after both independent records are locked should the instrument reveal annotations and
predictions. Match them under a separately frozen uncertainty-aware rule and record reference
omissions, detector misses, disagreements, scope differences and unresolved alternatives.
Original judgments remain retained. Reviewer agreement alone does not turn a shared visual
ambiguity into truth. Any resolution procedure needs explicit evidence and a new retained
record; there is no automatic consensus-to-truth conversion.

Using future frames to establish an offline reference is permissible only with explicit
provenance. A prospective monitor must receive solely the information available by its
decision time. Capture timestamp, reference-use time and online availability time must not
be collapsed into a single field.

## Baselines and ablations

Compare against the original annotation reference and a competent manual review of those
annotations. Give both workflows the same raw evidence and time budget when testing workflow
value. A detector-generated reference is a deliberately dependent comparator, not an oracle.

The informative ablations are single-frame versus temporal review, camera-only versus lidar-only
versus combined evidence, and discovery without overlays versus annotation-guided inspection.
Use distinct assignments to prevent the discovery pass from inheriting what an earlier guided
pass revealed. An ablation cannot reconstruct the counterfactual by asking the same reviewer
to forget an object. Vary timing/pose uncertainty only within independently defensible ranges,
retaining the resulting alternative matches rather than selecting the most convenient one.

A separate calibration panel needs independently established answers: visible objects,
actual empty regions, uncertain occlusions and time-alignment cases. Failed calibration,
misunderstood labels and missing evidence must be visible. Seeded omissions can test the
workflow after the underlying physical case is independently established; they do not count
as naturally occurring errors or establish reference completeness.

## Metrics

Measure reviewable and unreviewable anchors, missing evidence, reviewer disagreement before
reconciliation, unresolved object identity/geometry, and time per independently supported
finding. Count newly supported physical opportunities absent from the reference and from both
detectors, keeping duplicate identities and ambiguous matches distinct.

Report absolute joint-error counts, marginal counts and opportunity exposure alongside any
coefficient. For unresolved cases, carry feasible classifications and population coverage
forward to an identified set under an explicit model. If unobserved regions permit an
unbounded or unknown count of target objects, do not manufacture a finite denominator by
ignoring those regions. A descriptive estimate on resolvable objects is a separately named
conditional estimand; it cannot stand in for the full proposed population.

For a later population study, use the frozen sampling probabilities and scene-level design
to estimate totals; a ratio of estimated totals needs its own uncertainty treatment. Treat
sampling uncertainty, ambiguity in physical interpretation, and numerical enclosure error
as separate inputs. The small pilot supplies no claim of simultaneous worst-group coverage.
The authored binary model's eight-percent threshold is not an acceptance threshold here.

## Failure and success criteria

Broken blinding, failed calibration or lost source identity invalidates the affected study
evidence. If the raw recordings cannot constrain object presence and relevant time/geometry,
the reference method is inadequate for the proposed full-population claim. This is a useful
failure: specify the missing observation instead of collecting more of the same outputs.

A naturally occurring, independently supported omitted joint-miss opportunity falsifies
the assertion that the retained object population is complete. It does not by itself estimate
the omission rate. Conversely, finding none in 24 windows is not evidence of completeness.
An informative null requires a future precision/power calculation tied to a stated tolerance.

Scientific success requires that independent observations narrow the set of compatible
physical interpretations, with the narrowing surviving plausible timing, geometry and
reviewer alternatives. A favorable point estimate obtained by suppressing unresolved cases
fails. Before any headline population coefficient, a new protocol must show that the sampling
design and the remaining reference uncertainty can support the intended claim.

## Second-order consequence and immediate work

If the recordings are adequate, design the powered independent-reference study and measure
the value of the resulting correction on a separately selected pipeline. Only then evaluate
a prospective joint-miss monitor against calibrated input-only and disagreement baselines.
If the recordings are inadequate, the next investment is a small independently instrumented
reference collection with explicit coverage, timing and calibration, not a larger detector
or a hosted service.

The [completed clock-and-sensor-metadata census](OPPORTUNITY_CLOCK_AUDIT_2026-09-07.md)
parses no annotation or prediction table. It establishes the candidate anchor population,
channel metadata gaps and capture-time offsets before reviewers are assigned. It cannot establish payload validity,
physical completeness, online availability or adjudication quality. Independent reviewers
remain a missing external input; neither a model nor a generated signature can substitute.
