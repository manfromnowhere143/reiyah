# From sampled clearance to conditional continuous evidence

Document ID: reiyah.continuous-envelope.report. Version 0.1.0.
Lifecycle status: exploratory. Date: 20 September 2026.

Reiyah now computes the exact least and greatest possible minimum clearance
under one explicit scalar observation model: interval-valued samples, a global
bound on relative clearance rate, and one shared clock offset. It returns
feasible extremal trajectories, an additional error allowance where applicable,
and a same-time observation separating two opposing explanations when unresolved.
The premises are authored assumptions; no physical calibration is inferred.

For example, two exact observations of six metres, two seconds apart, allow a
four-metre dip halfway between if clearance can change by two metres per second.
A different permitted trajectory stays at least six metres away. Both fit the
same observations. The engine identifies the midpoint as a distinguishing time.
That query distinguishes these witnesses; it does not guarantee that every
possible measurement answer resolves the full decision.

| Twenty authored cases | Retained outcome |
| --- | --- |
| Requirement holds in every admitted world | 5 supported |
| Every admitted world violates it somewhere | 2 contradicted |
| Both satisfying and violating worlds exist | 6 unresolved, with opposing witnesses |
| Missing observations or assumptions | 5 blocked |
| Observation intervals and rate bound cannot coexist | 2 inconsistent premises |

[Results](results.json) retain every case and rational bound. The separate
[reference calculation](reference.py) uses exact linear-program vertices;
the [producer](producer.py) evaluates cone intersections. All 20 results and
witnesses agree with separate checking. They share strict input/custody code,
and both were authored in this session. This establishes no independently
authored workflow comparison, external replication or performance advantage.

The [method](METHOD.md) derives feasibility, tightness and witness construction.
The shared-clock distinction matters: expanding the horizon gives the worst
case, but the best case requires one consistently shifted window. The authored
shared-clock point example retains possible minima from two to six metres;
the expanded-horizon shortcut for both ends would falsely report contradiction
of a five-metre requirement. This is a known-bad shortcut, not our competent
comparator. No novel mathematical primitive or general STL completeness claim
is made. [Current primary research](SOURCES.md) constrains the novelty claim.

## Checks and correction

[Controls](controls.json) pass all 972 finite two-observation combinations,
2,484 uniform interval expansions, twelve hand-derived expectations, 26 malformed
input families, fifteen forged outputs, four strict boundaries and one check
with producer execution disabled. These dependent authored tests are not an
empirical coverage estimate. [Binding controls](binding-controls.json) reject
eight changed file/freeze bindings and four changed result memberships/identities;
four supervisor controls pass, including denied network access and exhausted
budget. [Validation](validation.json) distinguishes current checking from the
52 historical transcript identities, which were not replayed.

The first rejection suite failed because its alleged precision mutation assigned
the already-valid value. The [correction](freeze-correction.json) changes that
test assignment from two to three, retaining its expected rejection. The
initial freeze, test source, actual results and verification remain public.
The initial partial control run is not counted as passed. Scientific input,
producer, reference, method and decision rules did not change. The two actual
runs have identical case results. A pre-freeze lint failure and three mistaken
read-only paths are retained in [preparation observations](preparation-observations.json).
Web rendering and one article's version/date ambiguity remain explicit.

## Reproduce the authored development result

From the repository root, use Python with the standard library. These portable
commands are development replay, not Gate A release evidence. Choose fresh
output names; existing files are refused.

```sh
python -B research/continuous-envelope/0.1.0/run.py \
  --freeze-sha256 8ae40dbb2e974d964c021a8a5ff6d50d71cb22c467b048748550916806e20688 \
  --output /tmp/reiyah-continuous-result.json
python -B research/continuous-envelope/0.1.0/check.py \
  --freeze-sha256 8ae40dbb2e974d964c021a8a5ff6d50d71cb22c467b048748550916806e20688 \
  --results /tmp/reiyah-continuous-result.json \
  --output /tmp/reiyah-continuous-check.json
python -B research/continuous-envelope/0.1.0/controls.py \
  --freeze-sha256 8ae40dbb2e974d964c021a8a5ff6d50d71cb22c467b048748550916806e20688 \
  --output /tmp/reiyah-continuous-controls.json
```

Recorded execution used Python 3.14.2 through the bound supervisor, with network
denial before runtime startup, cumulative time/space limits and owned temporary
paths. [Costs](COSTS.md) include the failed control and repeated binding runs;
different command scopes do not establish a latency ratio or savings.

## What this enables next

The engine can now evaluate a supplied error contract and describe a useful
distinguishing measurement. It cannot supply that contract's physical truth.
The model permits all Lipschitz scalar signals, without acceleration, footprint,
association, independent timestamp jitter or clock drift constraints. A witness
is not asserted physically realizable by a particular car.

The next public-source qualification must document projected bumper geometry,
position/dimension errors, common-clock registration and relative motion over
the whole horizon. A probabilistic route additionally needs whole-trajectory
coverage and its dependence assumptions, frozen separately. For example, a
measurement record must say what supports its stated ten-centimetre error
allowance; a field labelled accuracy is not enough.

The closed NGSIM study remains annotation-conditional, with eight physical
results unresolved. It was not rerun or tuned here. All 1,433 reserved images,
the perception kernel, historical controller and previous negative findings
remain unchanged. Gate A remains operator-unaccepted. No control, deployment,
training, inference, paid compute, outreach or delegation is part of this slice.
