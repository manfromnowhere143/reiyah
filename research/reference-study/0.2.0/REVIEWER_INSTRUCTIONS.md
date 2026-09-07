# Independent reference review

Document ID: `reiyah.reference-study.reviewer-instructions.0.2.0`

Version: `0.2.0`

Lifecycle status: `proposed`

Read the [frozen protocol](protocol.json) before opening a case. Assignment and reviewer
independence must be established externally. Do not receive the source mapping, selection key,
reference strata, detector outputs or another reviewer's answers before completing your review.
Do not look up the public scene's annotations. The study designer's rendering inspection is not
an independent review.

For each assigned case, inspect the current six camera views, available neighboring frames and
lidar views. Open original assets when the displayed scale is insufficient. The cyan point is a
fixed world location; adjacent-frame markers do not follow object motion. A lidar display covers
a local XY region and cannot establish empty space from absent returns.

Judge whether the observations support an object whose center is compatible with the candidate
location within 2 m XY at its stated reference time. Any object class qualifies. Do not turn a
class or shape disagreement into absence. Choose `unresolved` whenever visibility, geometry,
timing or center localization is insufficient. Choose `inconsistent` only when affirmative
evidence and adequate visibility support incompatibility. Cite that evidence and explain the
reason. Missing assets and annotation absence do not provide that evidence.

Submit a JSON array of records following the [review schema](review.schema.json). Each record
contains your assigned `reviewer_id`, the exact case and protocol IDs, UTC review time, outcome,
validity, evidence IDs and hashes, reason, timing assessment and visibility assessment. The
case page supplies evidence IDs and hashes; its companion packet JSON supplies the protocol
digest. Do not invent a citation for an unavailable asset. When abstaining, use `unresolved`
with validity `abstained` and explain the limitation.

Keep your answer separate from the other reviewer. Agreement remains a fallible observation;
disagreement remains unresolved under this version. Submit data only through the operator's
authorized private process. No outreach or external upload is implied by these instructions.
