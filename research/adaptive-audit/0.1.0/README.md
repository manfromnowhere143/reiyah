# Adaptive betting on Reiyah endpoint decisions

Document ID: `reiyah.adaptive-audit.report`.
Version: `0.1.0`.
Lifecycle status: `exploratory`.
Date: 19 September 2026.

**The declared ALPHA configurations save no observations on the three retained
perception conditions.** All statistical paths stop at the same point as exact
interval stopping on their matched uniform orders. A conventional ordering by
known prediction-count bound does better on the two resolved conditions.
This completes the stronger adaptive-betting comparison selected by the
[roadmap](../../../docs/ENGINE_ROADMAP_2026-09-19.md); it does not establish a
statistical or commercial advantage for Reiyah.

## Perception comparison

Each condition contains the same 64 already exposed images and frozen YOLO11n /
YOLO26n eligible predictions. Four images have a zero prediction-count bound
and require no query while remaining in membership. For the other 60, a simulated
query reveals previously checked endpoints under the named reference family.
A query is not newly performed annotation or measured human effort.
The mean difference uses equal unit penalties for misses and false positives;
positive means lower declared loss for YOLO26n.

| Reference condition | Full mean interval | Full result | Mean queries: fixed, ALPHA d=10, ALPHA d=100 and matched exact | Conventional count-priority exact |
| --- | --- | --- | --- | --- |
| Exact supplied projection | [37/64, 37/64] | Supported | 3593/64 = 56.140625 for each | 46 |
| Simultaneous translation, radius 5 | [1/64, 67/64] | Supported | 1919/32 = 59.96875 for each | 59 |
| One arbitrary eligible reference edit per image | [-89/64, 173/64] | Unresolved | 60 for each | 60, unresolved |

Means describe 128 frozen uniform permutations per condition; they are not exact
expectations over every permutation. The conditions and their aggregate signs
were already exposed before this exploratory comparison. There are no new
physical ground-truth observations, held-out outcomes, model calls or independent
customer revisions. The parent uncertainty definitions and matching proofs are
exact-bound from the closed loss-tradeoff study, not rerun or newly accepted.

## Authored results and retained statistical errors

Four six-unit populations are checked over all 720 permutations each. The three
statistical arms exactly match logical stopping on those populations, and every
allocated false-decision/crossing probability is zero. They include a strict tie
and a residual interval that remains unresolved.

Five larger authored populations use 128 frozen permutations each:

| Population | Fixed mean queries | ALPHA d=10 | ALPHA d=100 | Matched exact mean | False decisions, respectively |
| --- | --- | --- | --- | --- | --- |
| Constant +1/2 | 15 | 14 | 14 | 43 | 0, 0, 0 |
| Constant -1/2 | 15 | 14 | 14 | 43 | 0, 0, 0 |
| 48 positive / 16 negative binary values | 2451/128 | 2589/128 | 151/8 | 5583/128 | 0, 0, 0 |
| Balanced binary tie | 1959/32 | 3953/64 | 7817/128 | 8071/128 | 4, 2, 4 |
| Residual interval [-1/4, 1/4] | 64 | 64 | 64 | 64 | 0, 0, 0 |

The tie's true decision is exclusion of strict improvement. Its false decisions
are early statistical support, and remain in every mean and transcript. The null
directional crossing counts are [4,2], [2,2], [4,2] respectively. Neither these
128-path counts nor zero observed errors certify the general risk guarantee.
Statistical procedures intentionally permit a nonzero error probability; exact
conditional stopping has a different obligation. We do not present wrong early
decisions as useful savings or choose the best setting after observing results.

Across all twelve full populations: five supported, four excluded, three
unresolved. The larger results illustrate both the potential and limitations
of adaptive betting, without supplying an application advantage.

## What was implemented and checked

[ALPHA's primary method](SOURCES.md) is implemented with two declared shrinkage
settings, compared with the prior fixed half stake. The [mathematics](MATHEMATICS.md)
derives the bounded endpoint transformation and finite-population guarantee.
All arms share information, uniform paths and a two-direction risk allocation:
1/40 per direction, at most 1/20 per fixed population and separately chosen arm.
There is no simultaneous guarantee across the 36 comparisons and no permission
to select a favorable test post hoc.

The [pre-outcome freeze](freeze.json), [plan](PLAN.md) and input/source bindings
cover 11,712 paths. A separate checker imports no producer, reconstructs all
prefixes and summaries, verifies 790,332 factor support cases and 341,952 null
conditional drift cases, and binds 384 source endpoints. It uses a different
algebraic expression for ALPHA's factor. Thirty-one critical controls, four
changed-input rejection controls and three supervisor controls pass. These are
same-session implementation checks, not independent scientific replication.

Actual outcome execution took 13.988490417 outer-process seconds; separate checking
took 9.158979917. Each is below its cumulative 600-second limit. Neither failed
or capped. One HTTP 406 source-metadata failure and an earlier malformed discovery
URL are retained. Full accounting, scope and unknown costs are in [COSTS.md](COSTS.md).
The study keeps its 128 MiB artifact ceiling and 5 GiB free-storage floor.

## Reproduction and custody

Public artifacts include [all aggregate results](result.json), [verification](verification.json),
[comparison](comparison.json), authored inputs/orders/paths and original code.
The per-image empirical inputs and paths remain private under their source terms.
With authorized access to the retained input area:

```sh
python -B run.py freeze.json "$REIYAH_ADAPTIVE_INPUTS" "$REIYAH_ADAPTIVE_NEW_RUN"
python -B check.py freeze.json "$REIYAH_ADAPTIVE_INPUTS" "$REIYAH_ADAPTIVE_NEW_RUN" "$REIYAH_ADAPTIVE_CHECK"
```

Run from this folder with the pinned runtime and the recorded offline supervisor
for a bound replay. The commands alone are development replay, not Gate A release
evidence. Public-only critical controls run with `python3 -B test_controls.py`.
The full empirical replay requires the private operands; it is not advertised as
self-contained from this public folder.

The [distribution record](DISTRIBUTION.md) identifies the nuScenes-derived report
terms. No paper body, third-party implementation, raw geometry or model payload
is published. The perception Engine remains at source
38a50ec014cc83e86ea6f247df803ded2971b386; all 1,433 reserved images stay closed.
Gate A remains operator-unaccepted.

## Next research decision

Retain ALPHA as a qualified comparator and preserve the small proof-checking
Engine. This result does not justify more tuning of the exposed populations or
promotion of statistical sampling into a product advantage. A broader method
family, weighting strategy or observation model would need a new frozen question;
these three configurations do not exhaust the frontier.

The next product-value gate is a consequential, owner-defined decision with an
observation that can distinguish the unresolved worlds, genuine chronological
revisions, an equally equipped conventional workflow and complete measured costs.
Use the existing workflow brief and the updated roadmap. Human work, customer
history, economic savings and demand remain unmeasured.
