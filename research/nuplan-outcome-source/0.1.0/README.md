# nuPlan supplies an explicit sampled outcome contract

Document ID: `reiyah.nuplan-outcome-source`. Version: `0.1.0`.
Lifecycle status: `exploratory`. 16 October 2026.

**Qualified at the source level for a sampled simulator outcome, with native
execution and trial admission still pending.** nuPlan provides an inspectable
collision rule, software clock and normal/error termination paths. Those are
enough to specify what a later controlled evaluation would need to retain.
They do not qualify physical recovery, human readiness or real-world safety.
No trials, logs, model outputs or native simulator runs were acquired or executed.

The source is Motional's [nuplan-devkit v1.2 release](https://github.com/motional/nuplan-devkit/releases/tag/nuplan-devkit-v1.2),
published 27 April 2023, pinned to
[`ce3c323af01c0d7ec5672f7832ef53f9c679aab0`](https://github.com/motional/nuplan-devkit/tree/ce3c323af01c0d7ec5672f7832ef53f9c679aab0).
This is a versioned reference contract, not a claim about the newest implementation
or current competition server. The selected composition is the local step time
controller, nonreactive track observations, two-stage ego controller and bicycle
motion model, with the collision metric enabled. A future run must bind its
actual resolved configuration; inspecting defaults does not establish that binding.

## Outcome, clock and termination

| Requirement | What the retained source establishes | Remaining boundary |
| --- | --- | --- |
| Event rule | First detected overlap per track token: a strict radius precheck followed by 2D polygon intersection, evaluated over saved history samples. | No swept-volume or continuous-contact detection; object identity, geometry and annotation coverage need their own qualification. |
| At-fault rule | Front/stopped-track contacts, plus selected lateral contacts under a map-association rule. | A heuristic subset of collisions, not causal responsibility or proof of collision avoidance. |
| Event time | The first retained detection uses `ego_state.time_point.time_us`. | A sampled detection time, not measured physical impact onset. Aggregate metric output has no event time series. |
| Clock | `TimePoint` declares microseconds since epoch; the scenario reads database timestamps and the selected controller propagates their differences. | Physical synchronization/error bounds and actual timestamp gaps are unmeasured. `perf_counter` report times measure host execution separately. |
| Normal stop | The selected controller stops at index `N−1`; history is appended before advancing. For `N≥2`, the normal history contains indices `0…N−2`. | The requested duration and last scenario token are not the observed history endpoint. Actual membership must be reconciled. |
| Errors | The executor records synchronous failures and checks asynchronous metric/log callback futures. | Killed workers, missing reports, incomplete output delivery and shortened source windows remain explicit unknowns until accounted for. |

The [21 source findings](findings.json) bind each interpretation to exact retained
lines and byte spans. The [qualification record](qualification.json) separates
source-level support from unresolved empirical requirements.

## Four distinctions that affect a later decision

**Run completion is separate from driving outcome.** The runner starts with
`succeeded=True` and changes status through exception handling. The selected
normal loop does not terminate on a collision or mission-goal test. Metrics are
computed after the loop, and they can be disabled. A successful report therefore
needs a matching, enabled metric and complete output receipt before any outcome
interpretation. Even then it does not mean successful driving.

**No at-fault collision is different from no collision.** Stopped-ego and rear
contacts can remain outside the at-fault subset. Once a track has its first
detected collision, the metric excludes that token at later samples, including
possible later contact episodes. The default object-group score is one half for
one at-fault object collision; a positive score is not a zero-collision assertion.
These are the metric's defined conventions, not evidence that benchmark labels
are defective. A future endpoint must choose and name its actual event set.

**The observed window must come from history.** The SQL extraction selects
available rows in a requested inclusive time window and subsamples by row number.
The retained mapping requests 15-second scenarios with nominal 10 Hz sampling,
but those settings do not establish complete, regularly spaced data. In an
authored example with 151 regular timestamps from 0 to 15 seconds, the selected
normal control flow produces 150 history samples ending at 14.9 seconds. This is
a conditional source deduction, not an observed dataset result or a finding about
every nuPlan configuration. A four-point irregular example ends at 0.25 seconds
although its final scenario timestamp is 0.45 seconds. Zero-span and empty windows
must not become successful follow-up.

**Simulation and wall clocks answer different questions.** Microsecond fields
give a software convention and permit exact recorded differences. They do not
supply sensor calibration, synchronization or continuous event-onset uncertainty.
The competition document also specifies a one-second planner budget; enforcement
of that server rule is outside this local runner audit. The runner's normal
`end_time` is captured before end callbacks, so it is not even a complete-work
measurement of metric computation and delivery.

## Qualification decision

Retain nuPlan as a concrete candidate for **sampled simulator outcome research**.
Use an explicit first-contact or at-fault endpoint, the actual saved timestamp
vector, and separate execution and outcome records. Do not reuse the score as a
takeover-recovery label or infer a physical accident time from its software clock.
Nonreactive agents replay logged observations; this does not measure their causal
reaction to a counterfactual ego trajectory.

Before trials, freeze and check a bounded native source-fixture protocol covering
positive/negative collisions, first-track de-duplication, the terminal sample,
disabled metrics and failed/missing execution receipts. The release names seven
upstream collision test functions, including positive contacts. Their fixture
bodies were not acquired and their tests were not run here. The next check must
establish native behavior without a model campaign or full simulator rollout.

The [decision](DECISION.md) and [proposed record obligations](CONTRACT.md) retain
the admission conditions. A real trial population, complete coverage and a common
outcome horizon are still unmeasured. Gate A remains operator-unaccepted.

## Checks, custody and cost

The offline [audit](audit.json) checks 37 inputs: 33 source files and four metadata
responses. It reconstructs 253 Git tree objects from 1,576 entries and binds the
source files to their declared Git blobs. A [separate checker](verification.json)
uses Git's own blob/tree hashing and checks four authored endpoint calculations.
[Eleven controls](controls.json) reject missing/substituted/rebound sources,
duplicate/unsafe paths, changed tag/tree bindings, corrupted spans, unsupported
acceptance and zero substituted for unknown uncertainty. These checks establish
integrity and the stated arithmetic, not independent scientific replication.

The first check rejected an incorrect assumption that GitHub's tree-response
envelope was the root tree ID: the endpoint requested by commit echoed that
commit. The correction reconstructs the tree objects and checks the root against
commit metadata. The failed attempt is retained; no source interpretation changed.
The final runs denied network and writes to the 43 source/code inputs before
Python started. Those inputs remained unchanged. No upstream code was imported
or executed. [Provenance](provenance.json) records actual execution and failures.

Source acquisition closed at 41 requests and 806,830 retained response bytes,
including four failed requests. The 257,910 decoded source bytes are derived
copies, not additional network bytes. The recorded source chain now totals
647 requests and 695,711,040 response bytes. One web call supplied discovery only.
An overlapping early request caused stale aggregate accounting; complete individual
records allowed exact reconciliation, followed by an exclusive capture lock.
Unknown active effort, full-history budget, billing and transport overhead remain
unknown. [Custody](source-custody.json) retains all attempts and corrections.

Motional's source is Apache-2.0; [attribution and boundaries](SOURCE_LICENSE.md)
are explicit. This packet redistributes authored analysis and identities only.
No dataset license, source checksum or passing check grants empirical admission
or operator acceptance.

## Reproduce the source checks

Obtain the exact files in [inputs.json](inputs.json), arranging its `metadata/`
and `upstream/` paths under one private source directory. These checks require
Python and Git, but no dataset, simulator environment or model. Retained execution
used Python 3.14.2. Use a fresh output directory:

```sh
reiyah_study=research/nuplan-outcome-source/0.1.0
reiyah_sources=/absolute/path/to/qualified-source-files
reiyah_run=/absolute/path/to/new-run
mkdir "$reiyah_run"
python3 -B "$reiyah_study/audit.py" --sources "$reiyah_sources" \
  --inputs "$reiyah_study/inputs.json" --findings "$reiyah_study/findings.json" \
  --qualification "$reiyah_study/qualification.json" --output "$reiyah_run/audit.json"
python3 -B "$reiyah_study/verify.py" --sources "$reiyah_sources" \
  --inputs "$reiyah_study/inputs.json" --findings "$reiyah_study/findings.json" \
  --result "$reiyah_run/audit.json" --output "$reiyah_run/verification.json"
python3 -B "$reiyah_study/controls.py" --sources "$reiyah_sources" \
  --inputs "$reiyah_study/inputs.json" --findings "$reiyah_study/findings.json" \
  --qualification "$reiyah_study/qualification.json" > "$reiyah_run/controls.json"
```
