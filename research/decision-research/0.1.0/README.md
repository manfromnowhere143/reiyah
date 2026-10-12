# From a paper to a reviewable engineering proposal

Study ID: `reiyah.decision-research`. Version: `0.1.0`.
12 October 2026. Prototype and exposed development controls; no efficacy trial.

The next engine decision needs more than an interesting paper. A proposed method
must fit the actual metric, available observations and decision obligation. This
pilot connects those requirements to the new
[offline intake helper](../../../tools/research_intake/README.md).
The [current research review](../../../docs/research-decisions/research-to-build-2026-10-12.md)
explains the choice of architecture and its limits.

The full proposed workflow is:

**Decision → bounded discovery → retained methods and code → assumption review →
intake checks → smallest falsifiable test → measured decision and complete work.**

This release implements intake checks and examples. Discovery and semantic
review use the existing assistant and primary-source tools. There is no new
search service, trained research model, recurring scheduler or shared coordinator.

## Four development decisions

All four reuse already exposed, authored Reiyah records. Their expected statuses
are declared in [cases.json](cases.json). The records bind exact existing source
bytes, including the quoted intervals. We intentionally do not reinterpret these
cases as unseen evaluation data or reopen the original studies.

| Supplied question and assessment | Expected intake result | Consequence |
| --- | --- | --- |
| Fixed binary rows and confidence ranks, with the qualified trapezoidal AUGRC convention. | `ready_for_review` | The method can receive substantive applicability review; no real workflow is supplied. |
| Substitute that AUGRC method directly for the geometric WOD rater score. | `incompatible` | The reviewer identifies a different mathematical target. A new method needs its own justification. |
| Treat mathematical qualification as evidence of actual review responses. | `needs_evidence` | A method description does not supply the missing observation process. |
| Reinspect unchanged evidence from the closed WOD lead. | `closed_no_new_basis` | A later inspection date supplies no new bytes or admission field. |

The compatibility judgments are supplied interpretations, not discoveries made
by the helper. A digest proves byte identity; a literal quotation proves text
membership. Neither establishes entailment, channel validity or usefulness.

## Reproduce

No download, external package or model call is needed. From the repository root:

```sh
python3 -B research/decision-research/0.1.0/reproduce.py
```

The stdout should match [result.json](result.json). The
[verification record](verification.json) binds the tested files and records the
offline execution and adversarial tests. This is development validation, not
Gate A release-launch evidence. The examples were chosen with their expected
outcomes known; neither blinding nor preregistration is claimed.

## The actual engine work this prepares

For a fresh complete perception-revision packet, first determine whether the
existing matching/FP–FN engine fits. For a fixed binary confidence-ranked packet,
the qualified AUGRC calculation may justify a narrow adapter with a separate
curve checker. The geometric rater score requires a different argument; it must
not inherit an AUGRC guarantee by analogy.

For the observation process, preserve what each reviewer saw, raw responses,
dependencies, missing/unresolved outcomes and actual work. Existing discovery,
assisted-review and observation-identifiability contracts remain the starting
point. Literature can challenge an assumption or propose a test; it cannot
manufacture missing paired runs or real observations.

No fresh complete-work case is admitted by this prototype. Prior closed data,
held-out restrictions and acquisition budgets remain closed. Next action is to
apply the intake record to a genuinely new decision or a material source change
that fills a named gap. Do not expand the helper or rerun closed studies merely
to generate another successful demonstration.

## How usefulness will be tested

The [utility pilot criteria](utility-pilot.json) are proposed, not run. Compare a
competent analyst with a bounded research workflow under the same evidence
access, decision requirements and budget. Test parallel roles separately only
where a separable bottleneck is identified. Freeze architecture and assessment
rules after development and before fresh held-out decisions.

Correctness comes first: critical claims need substantive source support at the
stated scope, contradictory evidence must remain visible, and abstention stays
distinct from a supported engineering recommendation. Then measure all work:
setup, reading, model/tool use, coordination, review, corrections and subsequent
reversals. Unmeasured costs stay unknown. Count actual decisions as units, not
citations or agent messages. Set the minimum useful effect and precision before
choosing a sample size; this four-case control set supplies neither.

The research function must itself earn its ongoing cost. No complete-work saving,
state-of-the-art superiority, novel scientific method, production readiness,
sibling integration or operator acceptance is established here.
