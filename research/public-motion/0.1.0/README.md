# Recorded vehicle pairs and physical clearance

Document ID: reiyah.public-motion.report. Version 0.1.0.
Lifecycle status: exploratory. Date: 20 September 2026.

Reiyah now reads a bounded set of public NGSIM vehicle pairs through a checked
source adapter. **All eight preselected pairs qualify for the recorded
longitudinal calculation; none qualifies a continuous physical-clearance
claim.** This closes a concrete source investigation in the
[roadmap](../../../docs/ENGINE_ROADMAP_2026-09-20.md), while preserving its
measurement gate.

The source supplies identities, timestamps, front-centre coordinates and vehicle
lengths that the previously inspected benchmark sidecars lacked. Its uncertainty
documentation does not supply calibrated error bounds, projected bumper geometry
or between-sample motion bounds. Exact arithmetic cannot fill those gaps.
The full [qualification](qualification.json) retains both the admitted and
unadmitted scopes.

## What ran

Before retrieving trajectory coordinates, the private allocation fixed the
first eight distinct ego identifiers from the first 200 preceding-positive
US-101 rows in chronological/identity order. Each retains its initial lead
identifier and a two-second window. The retrieval returned 541 rows covering
12 identities. Each allocated pair supplies 21 matching recorded instants:
168 paired assignments, with shared vehicles/times, not 168 independent events.

The authored question is whether the lead's recorded front coordinate minus
its reported length minus the ego's front coordinate, with an explicitly stated
foot-to-metre conversion, stays at least five metres at those recorded instants.
Five metres is an example threshold, not a safe-distance rule.

| Question | Result |
| --- | --- |
| Do all eight selected windows have the required source bindings? | Eight admitted for annotation-level use; no candidate replaced or discarded |
| Does the recorded proxy satisfy the sampled five-metre statement? | Eight supported on their 21 supplied instants each |
| Does this establish physical continuous clearance? | Eight unresolved; the proposed physical comparison was not admitted |
| Does the separate conventional calculation agree? | Eight agreements; no comparative-value conclusion |

[Summary](summary.json), [verification](verification.json) and
[method](METHOD.md) separate those meanings. Per-case coordinates, minima and
margins remain private. The separate source headway field differs from the
front-coordinate difference in all eight windows; those nonzero residuals
remain recorded, with no correction or tolerance inferred.

The producer indexes rows by identity/time. The conventional checker separately
selects identities, joins rows and calculates each value. Both derive the
annotation verdict from actual values. They share input-shape and byte-binding
validation. This is internal checking by one session, not an independently
authored workflow-value comparison or external replication. Physical non-admission
comes from the reviewed source contract; agreement on that field is not an
independent empirical finding.

## Verification and reproduction

The [freeze](freeze.json) binds source bytes, code, plan, runtime and supervisor.
All 37 authored boundary/rejection controls and 27 scalar-grid cases pass.
They cover wrong actor or length, changed lanes, missing boundary/interior
samples, frame-clock disagreement, row-order invariance, malformed data and
forged results. [Integrity controls](binding-controls.json) additionally reject
six altered code/source/metadata/freeze bindings and pass four supervisor checks,
including a network-denied child and exhausted budget. Expected control
rejections are retained. These controls are not additional real incidents.

Authored controls require only Python 3.10 or newer:

```sh
python -B research/public-motion/0.1.0/controls.py --output /tmp/reiyah-public-motion-controls.json
```

Actual-source reproduction needs the five privately retained source files named
by the freeze, obtained under appropriate source terms. The code refuses changed
bytes and existing output files. With those exact files in LOCAL_SOURCE_DIRECTORY:

```sh
python -B research/public-motion/0.1.0/run.py \
  --sources LOCAL_SOURCE_DIRECTORY \
  --freeze-sha256 830b3f32ec4843d29c0ea4dc0c5766ba792ada5c90adbe7f89d5d76e636bf210 \
  --output /tmp/reiyah-public-motion-result.json
python -B research/public-motion/0.1.0/check.py \
  --sources LOCAL_SOURCE_DIRECTORY \
  --freeze-sha256 830b3f32ec4843d29c0ea4dc0c5766ba792ada5c90adbe7f89d5d76e636bf210 \
  --results /tmp/reiyah-public-motion-result.json \
  --output /tmp/reiyah-public-motion-check.json
```

These are development commands. Recorded execution used the pinned local
runtime through a supervisor that denied networking before runtime startup,
bound the freeze, enforced cumulative limits and placed temporary files under
the owned research root. There is no Gate A release replay or deployment.

## Boundaries and next decision

[SOURCES.md](SOURCES.md) records official definitions, the approximate accuracy
statement, absent attribute-accuracy assessment, possible gaps, unverified
equivalence to original TXT data, and inconsistent source-rights declarations.
All external payloads stay private under the [distribution boundary](DISTRIBUTION.md).
Two mistaken local read paths and web rendering failures are retained; direct
public capture succeeded. The first [publication precheck](publication-precheck-failure.json)
also stopped because its wrapper expected nine report rows and did not account
for the separately recorded optional attack-suite skip. The corrected wrapper
requires nine passes and that explicit skip; the underlying checks and all
scientific code/results are unchanged. No allocated science failure or resource cap was
hidden. All earlier Reiyah negative findings remain.

Execution and separate checking cost 0.123961 and 0.123305 outer-process seconds.
These are complete command measurements for two different tasks, not matched
latency trials or savings. [Costs](COSTS.md) retain retrieval, controls, setup
and packaging cutoffs, storage, exclusions and unmeasured effort.

The next useful input is a calibrated uncertainty model, or an independently
documented error envelope, covering position, dimensions, clocks, projected
geometry and intervening motion. A statistical model would require its own
coverage assumptions and protocol; an approximate accuracy statement cannot
silently become a deterministic guarantee. This investigation does not show
that no suitable public source exists.

The perception kernel, historical controller and earlier closed studies are
unchanged. All 1,433 reserved images stay closed; Gate A remains operator-unaccepted.
No inference, training, media access, paid compute, outreach, delegation,
deployment or physical control ran.
