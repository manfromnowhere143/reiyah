# A checked sequential audit with explicit reference uncertainty

Document ID: `reiyah.sequential-audit.result`.
Version: `0.1.0`.
Lifecycle status: `exploratory`.
Date: 19 September 2026.

**The specified methods pass the finite validity check. Their efficiency result
is modest, and no Reiyah advantage over a competent conventional workflow is
established.** This packet implements an offline research method, a separately
written checker and replayable authored fixtures. It does not add production
runtime or change the existing perception Engine.

## What ran

The pre-outcome [plan](PLAN.md) and freeze.json bind 28 authored populations,
four methods and all **38,816 complete sampling orders**. Every population has
at most six members. Sampling probabilities, wealth factors, stopping points
and error probabilities use exact rational arithmetic. Full observation leaves
11 populations supported, 12 excluded and **five unresolved** under their
reference boxes. These are authored mathematical cases, not independent
customer decisions, observations or benchmark samples from an application.

The four arms use uniform, weight-proportional and proxy-guided sampling, with
the last also using a residual control variate. The [mathematical specification](MATHEMATICS.md)
derives a nonnegative betting factor for each endpoint. Each procedure has a
1/20 two-direction error allowance, split into 1/40 per direction. There is no
simultaneous 95% statement across all 112 population/arm comparisons.

The same-session separate checker imports no producer. It reconstructs every
order and prefix, checks exact probability mass, all stopping decisions,
46,336 factor-support cases, 8,064 conditional-mean identities and 5,396
null-drift cases. The false-decision and false-endpoint-crossing probabilities
are zero on every allocated population/arm. This is a result for these fixtures,
not a claim of zero error for every possible application.

The native exact interval path agrees on every order with conventional
enumeration of the reference box vertices. Twenty critical input/transcript
controls and two actual changed-loss/membership binding attacks pass. Expected
rejection exits are retained. No scientific run or actual-result check failed
or reached its cap. No allocated outcome was discarded.

## What the efficiency comparison says

| Comparison, at the same registered statistical error allowance | Fewer expected observations | Same | More |
| --- | ---: | ---: | ---: |
| Weight sampling versus uniform | 7 populations | 21 | 0 |
| Proxy sampling versus weight sampling | 1 | 25 | 2 |
| Proxy plus control variate versus the same proxy sampler | 1 | 27 | 0 |

The weight-selection gains are available to conventional methods using the
same known weights. They are not evidence of unique Reiyah technology.

In `proxy_aligned`, the control variate reduces expected queries from
`4930237/2198133` (about 2.242920) to `467906311/209119680` (about 2.237505).
The difference is `28917/5339840`, about **0.005415 queries**. Earlier statistical
stopping occurs with that same probability, about 0.5415%. The simple
conventional descending-weight exact procedure needs **two queries** on this
case. Thus the observed small statistical gain does not beat that conventional
comparison, and it carries a different guarantee from all-world exact checking.

Misleading proxy scores increase work: `proxy_reversed` needs about 0.568498
more expected queries than weight sampling. Extreme sampling imbalance also
produces a smaller loss. The fixed control variate yields no other query
reduction in this allocation. These results do not establish either universal
benefit or universal uselessness of proxy-assisted auditing.

The fully revealed unresolved cases are `interval_straddling`, `wide_reference`,
`missing_heavy`, `invalid_heavy` and `all_unavailable_states`. Sampling does not
turn their reference intervals into ground truth. Missing, unmeasured,
out-of-distribution, sensor-invalid and abstained states remain explicit.

## Evidence and replay

The public authored paths are in paths.csv; result.json is the producer report,
verification.json is the separate checker report, and comparison.json contains
the derived pairwise counts above. Fixtures, code and source metadata are bound
by freeze.json. Source papers are retained privately under their source terms;
see [SOURCES.md](SOURCES.md) and [DISTRIBUTION.md](DISTRIBUTION.md).

From the repository root, development replay uses the standard-library Python
scripts below. Each output path must be new. The retained canonical run used
the pinned Python 3.14.2 runtime, network denial before interpreter startup,
and the byte-bound owned supervisor recorded in freeze.json. These direct
commands are development replay, not the controlled run's timing evidence or
a Gate A release validation:

```sh
python3 -B research/sequential-audit/0.1.0/test_controls.py
python3 -B research/sequential-audit/0.1.0/run.py research/sequential-audit/0.1.0/freeze.json /absolute/new/run
python3 -B research/sequential-audit/0.1.0/check.py research/sequential-audit/0.1.0/freeze.json /absolute/new/run /absolute/new/check.json
```

The code is an explicitly specified fixed-stake specialization of an established
method family. It is not a full implementation of ApproxKelly, ALPHA, PPAT or
every stronger published sequential method. Those methods were not defeated
by this experiment. The six-unit allocation is a correctness gate, not a
representative power or scalability benchmark. No practical observation,
human-cost, inference-cost or commercial advantage is established.

## Resulting decision

Retain the checked research module and its guarantee separation. Before claiming
an efficient statistical Engine, qualify and compare a stronger published
adaptive-betting baseline on a separately frozen, relevant population; keep
the weight-aware conventional workflow in that comparison. Do not tune these
28 exposed cases into a superiority demonstration. Genuine revision evidence,
an owner-defined observation process and complete measured costs remain the
entry conditions for the product-value claim in the
[current roadmap](../../../docs/ENGINE_ROADMAP_2026-09-19.md).

Engine source remains `38a50ec014cc83e86ea6f247df803ded2971b386`.
All 1,433 reserved images remain closed and Gate A remains operator-unaccepted.
Costs and the limits of their measurement are in [COSTS.md](COSTS.md).
