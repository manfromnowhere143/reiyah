# Reference-compiler implementation checkpoint

Document ID: `reiyah.perception-reference.checkpoint-2026-09-09`

Version: `0.1.0`

Lifecycle status: `exploratory`

The Engine can now derive conditional matching graphs from explicit joint point-reference
interpretations. The [contract and example](../research/perception-reference/0.1.0/README.md)
define the interface; the [machine checkpoint](../research/perception-reference/0.1.0/checkpoint.json)
binds tested implementation and result bytes. This extends the input pipeline committed at
`ac3c450327ba1e6e5b36ee6324b482c369f9977c`.

The compiler preserves one shared reference choice across the cohort, rejects alias
double-counting and population mismatches, and derives matching edges using exact same-class
geometry. It includes matches through base-detector neighbors. Unknown joint coverage, unlisted
objects, geometry or time retain an open reference. Resource limits also widen the affected
reference instead of returning a truncated finite graph.

Finite point positions and completeness remain explicit assumptions. The compiler does not
approximate continuous geometric uncertainty by choosing convenient points, infer a reference
from detector agreement, or provide independent physical judgments. The core checker validates
the resulting graph computation; it does not independently validate compilation or its inputs.

## Checks and demonstrations

All 238 offline unit tests passed: 145 repository tests and 93 measurement-tool tests. Fifteen
new reference tests include exact gate/range boundaries, missing predictions, ambiguous aliases,
clock/source substitution, malformed records, resource fallback and complete world encodings.
An independent partial-injection calculation computes both full detection losses directly from
coordinates for 16 three-world fixtures and agrees with every compiled enclosure. This avoids
using compiler graph edges as the reference for that test.

The original geometric matching trap produces `[-1,1]`. A constructed two-anchor example
couples opposite reference interpretations and produces `[0,0]`: treating those anchors as
independent would lose that constraint and return the looser `[-1,1]` enclosure. The runnable
example is source-bound and its core packet passes certificate verification. Neither example
establishes empirical detector performance or physical coverage.

The same two previously exposed development anchors used by the input checkpoint also passed
the four-file reference boundary, followed by separate core `run` and `verify` processes.
Without physical reference judgments, both anchors remain open and the interval remains
`[-8,8]`, with unresolved preference. No additional sample selection, human judgment, model
fit or detector inference occurred.

The original source pipeline, graph core, 52 empirical transcripts, 57 claim-register rows,
selected study plan and main README remain unchanged. Gate B closeout checks existing evidence
integrity and document consistency; it is not a replay of those experiments or a Gate A release.
Gate A remains operator-unaccepted. Owner checkouts and UI work remain separate.

## Next work

Check raw sensor-window identity, decodability and timing on existing development inputs, then
connect locked reviewer observations to explicit shared reference alternatives. Preserve the
unreviewable cases and the distinction between a finite assumption and a justified physical
outer model. The new interface is a narrow integration boundary for complementary reference
research; it does not adopt other sessions' estimands or conclusions automatically.

The 60-scene study remains unselected and unrun. Two independent reviewers, a competent
independent conventional comparator, adjudication and checked observation windows are still
required before the specified method/input/reviewer/comparator freeze and fresh sampling.
Current engineering progress does not establish the product hypothesis or a breakthrough claim.

Work was prepared in a fresh private export from the preceding main commit. Resolve final
main integration and publisher readback from Git and the task delivery record. No public
third-party payloads, released Gate A artifacts or historical author records were changed.
