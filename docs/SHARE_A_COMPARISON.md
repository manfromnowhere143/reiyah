# Share a saved comparison

Document ID: `reiyah.comparison-submission-guide`. Version: `0.1.0`.
Status: proposed contribution guidance, 11 October 2026.

Reiyah is looking for existing records that can answer a concrete evaluation
question: did a model revision change the result, did an evaluator change the
decision, or could a review process reach the same justified decision with less
work? A small, well-described case is useful. Start with what already exists.

[Propose a comparison](https://github.com/manfromnowhere143/reiyah/issues/new?template=comparison.yml)
using the short form. A description and public source links are enough to start
the review. Existing file formats are welcome, incomplete records remain useful
as leads, and unavailable information should be marked **unknown**.

GitHub issues are public. Share only material you are authorized to disclose
publicly. Keep personal or confidential information, credentials, raw images and
model weights out of the issue. Use opaque image, model and reviewer identifiers
where appropriate. A public link is a source pointer until its contents, version,
terms and provenance have been qualified. Submission does not grant a new license
to third-party material or automatically admit an experiment.

## Choose the question the records can answer

| Intended check | Useful existing records | What the result could establish |
| --- | --- | --- |
| Scoring behavior | Original saved outputs, applicable reference, expected image roster and exact evaluator configuration | Whether a software behavior changes a score on that declared population. A single model can be useful; a ranking claim needs the compared models. |
| Model or software revision | Both saved outputs on the same assigned opportunities, revision/configuration bindings and the existing comparison script | Output compatibility; quality needs an appropriate reference and loss. Different boxes alone do not identify the better model. |
| Decision workflow | A real decision and owner, qualified reference-review procedure, complete records for both methods and measured work | Whether the same decision obligations are met with less total effort in that case. |

Work measurements are needed for a work-saving claim. They are not required to
propose a software-impact check. No new training, inference, annotation job or
reconstructed timing estimate is requested by this guide.

## The smallest useful description

Explain the change and the decision or calculation it affects. Link the source
and version, the existing script or configuration, the relevant outputs and
reference if available, and the applicable access and sharing terms. State what
is missing. A pointer to the original format is preferable to an undocumented
conversion that changes thresholds, geometry or class probabilities.

For each assigned opportunity, distinguish **successful with detections**,
**successful empty**, **failed**, **missing** and **status unknown** using actual
run records. An absent detection row cannot establish a successful empty run.
If the roster or status records do not exist, say so; do not infer them from
the images that happen to appear in the output table. Include the rule used to
select any shared subset and whether results were inspected before selection.

For the currently reported soft-label evaluator behaviors, the useful source
files are the original per-image JSON outputs, their expected image roster,
the reference JSON and evaluator settings. The upstream loader uses `boxes`,
`scores`, `labels` and `calibrated_probs_ir`; complete class-probability vectors
are necessary for this scoring path. A saved scalar confidence file alone is
insufficient. The [existing upstream report](maintainer-reports/evaluator-populations-2026-10-11.md)
describes the two constructed failures and their current empirical limits.

For a workflow comparison, preserve actual review answers and unresolved cases,
procedure versions and pseudonymous task/reviewer identities. Record preparation,
acquisition, review, adjudication, duplicate removal, retries, checking, repair
and integration, including shared or reused work. Keep machine duration,
annotation duration and human active work distinct. Missing stages stay unknown.
The more detailed [workflow brief](../research/value-disproof/0.1.0/WORKFLOW_BRIEF.md)
explains these requirements; they are acquisition targets, not existing customer
evidence or a condition for submitting a useful partial lead.

## What happens after a proposal

The first review identifies which question the records can support and names
the missing fields. Source identity and previous exposure are checked before
acquisition. Access and redistribution terms are checked before payloads enter
retained evidence or public Git history. A public issue does not authenticate
the data, confer operator acceptance or launch an automatic download or run.

An admitted experiment freezes its endpoint, comparator, inputs, exposure,
resources and stopping rule before diagnosis. The conventional process receives
the same evidence and applicable corrections. Unresolved and negative results
remain visible. A software reproduction can be useful without establishing
physical truth, driving safety, complete work savings or product value.

The [current research decision](NEXT_SESSION.md) remains in force. Reiyah has
not yet demonstrated its proposed complete-work advantage. This form creates
a way to propose evidence for review; it does not change that finding.
