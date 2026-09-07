# Reference identification and opportunity-clock checkpoint

Document ID: `reiyah.reference-identification-closeout.2026-09-07`

Version: `0.1.0`

Lifecycle status: `exploratory`

This revision extends `2ae14e78e63fe674fcfd216d9dbb67765c2adff2` on the local
`research/2026-09-07-reference-identification` branch. Its final private `delivery.json`
records the commit, tree, patch digest and changed-blob readback. Every commit is authored
and committed solely by Daniel Wahnich. The canonical Gate A and separate Gate B worktrees
remain under their existing ownership; neither is switched or edited by this continuation.
No push, merge, service or outreach occurs.

## Completed investigations

The [exact identification construction](REFERENCE_IDENTIFICATION_FINDINGS_2026-09-07.md)
produces two complete binary probability worlds with identical observable detector/reference
laws but true coefficients 1 and 25/9. It derives sharp sensitivity bounds for one specified
observed table under a total reference-flip budget, with complete extremum witnesses. It also
separates the additional ambiguity created by unrecorded object opportunities. These are
synthetic mathematical results, not measured reference errors or new perception performance.

The [clock census](OPPORTUNITY_CLOCK_AUDIT_2026-09-07.md) streams the retained metadata,
including 2,631,083 sample-data rows. Official scene membership and sample clocks alone give
4,682 context-eligible anchors across 150 validation scenes. All 6,019 sample anchors have
required camera/lidar keyframe metadata. Capture times differ across cameras; online
availability and physical observability remain unknown. The full calculation completed in
about two minutes locally; this is an execution observation, not a runtime performance claim.

The [independent opportunity design](INDEPENDENT_OPPORTUNITY_STUDY_DESIGN_2026-09-07.md)
specifies model-blind discovery from independently sampled times, followed by a locked
comparison against annotations and predictions. It remains proposed: no pilot selection,
reviewer assignment or physical annotation is claimed completed. The original 240-detection
study is unchanged and still awaits its independent reviewers.

A read-only check of all 240 rendered study case pages confirms that they already disclose
fixed-world marker semantics, sensor time offsets, unknown motion/calibration/per-point timing,
and the need to retain unresolved judgments. The pages were not regenerated. The private
`packet-readonly-disclosure-check.json` retains their digests and the disclosure counts.
This checks presentation text, not projection accuracy, physical truth or reviewer comprehension.

Primary review reused the exact retained WACV 2026 annotation-correction paper and retained
the Hui-Walter paper privately. The attempted Duan et al. publisher retrieval returned HTTP
403 and remains failed. Browser challenges were not bypassed, and no full-paper claim relies
on those failed routes. The WACV PDF text extraction completed with parser warnings; no new
claim of PDF rendering or layout validation is made. Public records contain source pointers,
digests and access/redistribution limits, not third-party payloads.

## Validation and exact boundaries

Eight probability-model tests and six clock-census tests pass, with source-bound process
captures. They exercise full observable equivalence, conditional coefficients, feasible
extremum worlds, small-budget truth assignments, missing timestamps, broken clock chains,
duplicate channels and missing calibration/scene identities. Unknown online availability
and physical outcomes remain explicit.

The [development verifier](../tools/measure/verify_reference_identification.py) recomputes
the latent-world probability witnesses without importing their producer, reaggregates the
private frame-clock rows, binds the completed processes and verifies the numerical tables.
It rejects a deliberately altered coefficient and an unmeasured physical outcome changed to zero.
Its [result](../evidence/reference-identification/verification-0.1.0.json) concerns these
exact artifacts. The [Gate B development check](../evidence/reference-identification/gate-b-check-0.1.0.json)
checks inherited transcript digests, custody, claim reconciliation and document consistency;
it explicitly does not repeat every historical experiment.

Every predecessor file except the README and three navigation documents is byte-preserved.
This includes M4, its corrected bound implementation, the reference-study protocol and selection,
claim register, replay manifest and Gate A release operands. Development checks do not create
Gate A release evidence or operator acceptance; the latter remains unaccepted. The two newly
written numerical implementations are not independent human scientific review.

## Resume from exact custody

Begin at `/Users/danielwahnich/workspace/reiyah`, read the current instructions and handoff,
and inspect the local research branch without changing the other worktrees. Read the
[continuation ledger](RESEARCH_CONTINUATION_2026-09-07.md). The current task root is:

```text
/Users/danielwahnich/.codex/reports/reiyah/reference-identification-2026-09-07/
```

`baseline/` exports the parent commit; `implementation/` holds the candidate; `checks/`
retains process streams; `external-sources/` holds private source custody; and
`private/clock-audit-1/` contains the frozen input specification, completed result and
private frame/scene rows. Files named `running-*` retain the state at process creation;
the completed process capture and result, not that historical marker, establish completion.
The original metadata archive remains in the preceding developer-value task's private inputs.

From `implementation/`, the local checks are:

```sh
python3 -B tools/measure/reference_identification_counterexamples.py
python3 -B -m unittest discover -s tools/measure -p test_reference_identification.py -v
python3 -B -m unittest discover -s tools/measure -p test_opportunity_clock.py -v
python3 -B tools/measure/verify_reference_identification.py --task-root .. --baseline-root ../baseline
```

The full clock run's argument vector is retained in its process capture. Use a new output
directory for a new run; the tool rejects reuse. None of these programs requires a model,
network service or cloud instance. The current calculation processes completed, and the
operator's earlier laptop deadline remains canceled.

## The next scientific action

The laboratory priority remains independently supported physical reference observations.
The frozen detection study and the proposed independent-opportunity study answer different
questions. Do not merge their populations or borrow the synthetic model's error budget as
a measured fact. Before delivering cases to reviewers, audit the interpretation of timestamps,
geometry and overlays in their evidence packets against the now-measured capture offsets.
If the available evidence cannot constrain the target, report that limitation and specify
the missing observation rather than generating a confident coefficient or certificate.
