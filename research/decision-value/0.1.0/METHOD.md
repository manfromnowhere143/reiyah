# Complete-cohort recorded-reference decision, 0.1.0

Status: exploratory. Same-author development experiment, with an independently
authored publisher baseline underneath a same-author conventional wrapper.
The question and all16source-file identities were frozen before deliberate
numeric inspection. Author-reported aggregate outcomes were already exposed.

## Meaning of the decision

For each full frozen sequence, replace the stored online trajectory with the
stored offline trajectory for the completed map if its mean squared distance
to the published checkpoint coordinates is strictly smaller. Positive difference
contradicts that replacement rule; zero is a null/tie. Missing operands block
the full-cohort conclusion. Invalid rows remain invalid, with no imputation.

This does not choose a causal real-time estimator: offline uses future data.
These are handheld mapping records, not driving, control, readiness, collision
clearance, economic benefit or customer acceptance. The87visits are not87
independent replications. Each of four sequences stays separate.

## Data and semantics

Use every row of all four named checkpoint files and both complete trajectories,
as fixed in [the question](QUESTION.md) and [source identities](sources.json).
Strict checks require exact columns, finite numbers, unique visit IDs, increasing
times, eight TUM tokens, a finite three-element origin and complete input custody.
Times must fall in the published2025recording year in Unix seconds. This detects
gross unit/epoch errors, not clock bias within that year. Quaternion components
are checked as finite tokens; orientations are not used in this position metric.

The publisher selects the first source row attaining nearest absolute time,
only if the offset is at most2s. The native path enumerates rows and explicit
(source-offset,row-index) order; the conventional path uses the original NumPy
selector. Repeated source times are refused before either decision. Exact
midpoint ties among distinct times retain the publisher's first-row rule.
Actual selected offsets and missing IDs are reported, not interpreted as
a calibrated motion or stationary-window guarantee.

Both arms trust the pinned publisher coordinate conversion. It subtracts48.22m
from ENU up before WGS84-to-GRS80/UTM32N conversion. The public calibration file
does not establish a deterministic uncertainty bound for that correction.
The trajectories are documented as already using the base-center reference;
no second IMU offset is applied. A source/frame hash check cannot establish that
the publisher's coordinate or clock metadata correctly describes physical reality.

## Arithmetic and comparison

C0 is the unmodified publisher nonplotting entry point. It can print metrics
over available associations without displaying cohort counts. C0 is a
reproduction, not the competitive value baseline.

C1 is a competent conventional wrapper: same input identity and strict checks,
same complete-cohort decision rule, original publisher parser/selector/converter
and absolute RMSE. It squares the original RMSE to obtain MSE and subtracts
offline minus online. Its wrapper is authored in this session. It does not
import Reiyah's computed decision or expected result.

The Reiyah path uses separately parsed rows and source-order nearest selection,
then exactly sums squared differences of the resulting finite binary64
coordinates using rational arithmetic. It decides from the exact rational sign.
This is exact arithmetic for rounded nominal operands, not exact geodesy or
physical truth. C1 uses ordinary floating point. The separate checker reconstructs
selection and verifies the exact difference through
(B-A) dot (B+A-2Q), rather than calling either arm's decision function.
It rejects a floating-path sign disagreement; it does not tune a tolerance to
force matching. Per-mode C1 numerical values may differ by at most1e-10relative
or1e-12absolute for reproduction checks, fixed before execution; sign itself has
no tolerance. No near-zero result will be upgraded through rounding.

Both arms share strict input code and the coordinate backend. The checker shares
that backend, but not final decision functions. Same-author agreement is
development cross-checking, not independent replication. A defect in the shared
conversion can affect all paths undetected.

## Controls, costs and investment

Before actual workflows, execute authored finite arithmetic, selection and
refusal controls. Afterward mutate actual result records: wrong decision,
changed metric/identity/coverage, missing case, inflated physical claim,
modified frame and reordered trace. Mutations must fail for their own reason.
Invalid input controls exercise semantic checks independently of source hashes.

Each arm's whole subprocess and internal workflow times are retained. One
fixed-order run gives execution cost only, not a speed benchmark. Preparation,
source acquisition, validation and storage costs are separate; nested timings
are not summed twice. Engineering effort, physical acquisition, charges, energy,
network overhead and peak process memory remain unmeasured.

No comparative value is established by C0's omissions if C1 handles them equally.
Parity or extra overhead is a valid negative investment result. Do not expand
a monitoring framework solely because these nominal records reproduce.
All third-party bodies and per-visit traces stay private; only authored code,
metadata and permissible aggregate facts are eligible for distribution.

