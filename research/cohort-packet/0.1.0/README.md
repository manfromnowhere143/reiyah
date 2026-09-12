# Weighted cohort comparison interface

Version: `0.1.0`

Lifecycle status: `proposed`

A cohort is not the sum of its anchors. This interface computes the declared weighted comparison
over **shared joint reference interpretations** and refuses the per-anchor relaxation.

```text
D(w) = sum_i weight_i * delta_i(w)        over one shared joint world w
enclosure = [ min_w D(w), max_w D(w) ]    widened by any open anchor's count interval
```

## Contract

A case declares the loss penalties and tolerance, a list of anchors with weights summing to one,
and a list of joint worlds. Each anchor declares its base detections, added detections, objects and
a `reference_state` of `finite` or `open`. **Each joint world must cover exactly the finite
anchors**, giving the objects present and the admitted same-class edges at each. Both configurations
are evaluated in that same world before weighting.

An `open` anchor declares no objects and contributes the interval `[-b*r, a*r]`. An open reference
is not a world in which nothing exists; emptying it would assert absence where there is only
ignorance. A finite anchor with no admitted joint world yields `unresolved`, never a computed value.

## Checking

[`check_cohort_packet.py`](../../../tools/measure/check_cohort_packet.py) imports nothing from the
producer and runs no matcher. Every matching is at most every vertex cover, so a matching and a
cover of equal size force optimality for any graph. It additionally refuses a world that omits a
finite anchor, an anchor scored in a different world from its cohort, an enclosure narrower than the
worlds support, and a per-anchor relaxation offered as the joint result.

Shared trusted surface: the JSON module, the identifier and rational string conventions, and
Python's `Fraction` and integer arithmetic.

## Retained cases

| case | result | note |
|---|---|---|
| `oppositely-coupled` | joint `[0, 0]`, relaxation `[-1, 1]` | reproduces the Engine lane's published example |
| `matching-trap` | `[-1, 1]` | one anchor, disputed object reachable only by the base |
| `open-two-anchor` | `[-8, 8]`, state `open_reference_only` | the live comparison's actual state |
| `conditional-inertness-case` | plan depth 1 | from the Engine lane: a question inert on its own and decisive once another is answered absent. Retained so that inert questions are never discarded before planning |
| `adaptive-beats-fixed-case` | plan depth **2**, smallest fixed resolving set **3** | the retained witness that a fixed resolving set bounds the adaptive optimum from above only, and so can never certify it |
| `adaptive-beats-fixed-varying-edges-case` | plan depth **2**, smallest fixed resolving set **3** | the same gap with one anchor and four worlds. `a_and_c` holds a strict superset of the objects of `c_only` and a lower value, because the two worlds disagree about which detection could have matched `dC`. Retained as the instance showing that the gain monotonicity theorem needs its fixed edge set, and that a world value can fall as objects are added |

`answer-prerequisites.json` records which questions have a defined measurement, at what stage each
may be asked, and what is missing. Presence questions are supported. Reachability, calibration and
timing questions are not, and each is recorded as a named missing prerequisite rather than assumed.

## Scope

A confirmation covers the arithmetic of the declared comparison inside the declared interpretations.
It does not establish that any interpretation is admitted by review, that any object exists, or any
physical, planner or risk consequence. No reference interpretation is invented here.
