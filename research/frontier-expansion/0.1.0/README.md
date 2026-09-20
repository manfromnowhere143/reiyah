# Relational motion evidence: first bounded extension

Document ID: reiyah.frontier-expansion.report. Version 0.1.0.
Lifecycle status: exploratory. Date: 20 September 2026.

The new [roadmap](../../../docs/ENGINE_ROADMAP_2026-09-20.md) selects an
evidence engine spanning perception, proposed behavior, simulation validity and
human–automation recovery. This packet implements the first small motion slice:
a declared minimum longitudinal clearance across a stated time interval.

**All 20 authored cases agree with the equally equipped conventional checker.**
The retained outcomes are three supported, seven contradicted, six unresolved,
three blocked and one inconsistent-premise case, across 24 common-world
alternatives. No real driving outcomes, customer revisions or reserved images
are evaluated. A supported clearance contract is not a safety verdict.

| Demonstration | What the checker preserves |
| --- | --- |
| Ego slows while the lead slows more sharply | Slowing alone does not establish adequate clearance |
| Ego accelerates while the lead pulls away | Acceleration alone does not establish a violation |
| Identical ego motion, different possible lead identities or clock offsets | The answer remains unresolved when allowed worlds disagree |
| Safe supplied endpoints with no qualified interpolation | Continuous-time support is unavailable |
| Violation at an interior knot of the other vehicle's trace | Both time grids matter |
| Missing trace, partial horizon or an empty world family | Blocked, unresolved and inconsistent-premise states remain distinct |

The [method](METHOD.md) specifies inclusive thresholds, exact rational
coordinates, common-world semantics and explicit interpolation. It implements
established affine minimization, not a new monitoring theorem. The producer
merges trace knots; the [checker](checker.py) intersects segment pairs. They
share the strict [format gate](format.py), with a
[structural schema](contract.schema.json), and otherwise use separate arithmetic.

The [plan](PLAN.md) and [corrected freeze](freeze-correction.json) bind all
allocated inputs and code. The [first freeze](freeze.json) remains history.
[Results](results.json), [verification](verification.json) and
[controls](controls.json) retain every outcome. Twenty authored cases,
4,374 finite cross-checks, 18 malformed-input families, eight altered-result
checks and two JSON rejections passed. Seven additional file/CLI bindings,
schema validation of all 20 cases and three supervisor controls also passed;
see [binding controls](binding-controls.json). This is internal checking,
not independent replication. Authored expectations were known during design.

The [source review](SOURCES.md) distinguishes full primary methods, company
statements, abstract-only leads and access failures. The
[public benchmark qualification](qualification.json) is descriptive: 150 index
records and one scene's two JSON sidecars. It does not establish that every
scene lacks relational data. No paper metric is reproduced or compared with
these authored results. A real clearance experiment still needs a qualified lead
trace, common coordinates/clocks, bumper geometry, horizon and motion assumptions.

## Replay

From the repository root with Python 3.10 or newer and no additional dependencies:

```sh
python -B research/frontier-expansion/0.1.0/run.py --output /tmp/reiyah-clearance-results.json
python -B research/frontier-expansion/0.1.0/checker.py --results /tmp/reiyah-clearance-results.json --output /tmp/reiyah-clearance-check.json
python -B research/frontier-expansion/0.1.0/controls.py --output /tmp/reiyah-clearance-controls.json
```

These commands are development replay. The recorded execution used the pinned
local runtime and a supervisor that entered network denial before startup,
verified the runtime/freeze, enforced cumulative budgets and retained receipts.
No Gate A release evidence or runtime deployment is implied.

## Failures, cost and boundaries

Both retained executions total 0.140959375 seconds; their separate checking
totals 0.125685875, both outer-process measurements, not a latency benchmark.
See [costs](COSTS.md) for preparation, controls, retrievals, failures and exclusions.

A retrieval command first failed because its relative script path was resolved
from the candidate. The corrected command fetched the intended sources; the failed
receipt remains. The first verification harness encountered macOS's prohibition
on nested sandbox initialization. Its failure remains; rerunning the harness
outside a parent sandbox allowed its child network-denial control to run.
The isolation policy was unchanged. Final staged review then rejected an extra
EOF blank line in the format gate. The [correction](correction.json) retains the
first projection, removes that blank line with identical Python syntax trees,
and selects an append-only corrected freeze. All 20 cases were re-executed and
checked with identical outcomes; active-freeze binding controls were repeated.
The first results and failed staging attempt remain. The finite arithmetic
controls are exact-bound to their unchanged syntax;
their 4,374 cases are not counted again as a second experiment.
Two Tesla 403 responses, GUARD HTML 404 and the old SpaceX-hostname failure
are retained.

Prior conventional parity, unresolved perception rows and unproven economic
value stand. All 1,433 reserved images remain closed. Gate A is operator-unaccepted.
The core perception engine and historical controller are unchanged.
[Distribution](DISTRIBUTION.md) keeps external payloads private.
