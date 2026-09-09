# Discovery record custody checkpoint

Document ID: `reiyah.perception-discovery.checkpoint-note`

Version: `0.1.0`

Lifecycle status: `exploratory`

The Engine can now account for and seal unassisted discovery records against an exact
[raw observation package](PERCEPTION_OBSERVATION_CHECKPOINT_2026-09-09.md). Every recorded
window/capture occurrence has an explicit inspection state. Proposals cite inspected evidence
and can identify an image region or original raw lidar point indices without being promoted
to adjudicated physical objects.

The live development check created **one unassigned draft with 725 uninspected occurrences**
for the same two exposed windows. It generated no human observations, and its attempted
submission was rejected specifically because no reviewer was assigned. The attempted sealed
output does not exist. Synthetic fixtures exercise completed, partial, contaminated and paired
records; none are real reviewer judgments.

See the [record interface](../research/perception-discovery/0.1.0/README.md),
[machine checkpoint](../research/perception-discovery/0.1.0/checkpoint.json) and
[implementation](../tools/perception_discovery/records.py). The tool retains missing review,
unknown exposure and unresolved class hypotheses explicitly. An empty proposal list does not
establish an empty physical scene.

A sealed record preserves the canonical submitted content and its evidence binding. Two records
with distinct handles may be structurally eligible for external review while reviewer identity,
independence, actual exposure order and physical completeness remain unestablished. The pair
checker cannot authorize or perform assisted-data release. A local timestamp and a file digest
are custody evidence, not independent human validation.

The next substantive integration is the staged reference workflow: preserve these locked
proposals alongside assisted proposals and adjudication, then bind any explicitly constructed
shared reference alternatives to their exact source records. Do not infer object truth or
coverage from the presence of records, locators or a passing validator. Actual independent
reviewers, comparator, adjudication and a full freeze remain prerequisites to the 60-scene study.

No prospective cohort or seed exists. The previous open-reference paired-loss enclosure remains
[-8,8] under unit penalties. Gate A remains unaccepted. Owner checkouts, Console, the separate
research lane and every retained empirical transcript/register row remain unchanged.
