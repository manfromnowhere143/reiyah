# A cohort is not the sum of its anchors

Document ID: `reiyah.cohort-comparison.2026-09-12`

Version: `0.1.0`

Lifecycle status: `proposed`

Lane: independent research and conventional comparator, parallel to the Engine. Changes no Engine
file, no shared handoff, no frozen protocol and no owner checkout. Creates no acceptance, no
reference admission and no reviewer. Gate A remains unaccepted.

## The question and the result

Can this lane compute the Engine's declared comparison, or must it name a precise unsupported state?

**It can now compute the declared form, and on today's real operands the honest answer is the
unsupported one.** The declared comparison is a weighted cohort over shared joint reference
interpretations. The single-anchor packet this lane published could not express it, and combining
per-anchor enclosures by addition is a relaxation rather than the answer.

Reproducing the Engine lane's own published example with a differently structured implementation:

| quantity | this lane | Engine lane |
|---|---|---|
| joint enclosure, oppositely coupled anchors | `[0, 0]` | `[0, 0]` |
| separate per-anchor relaxation | `[-1, 1]` | `[-1, 1]` |
| matching trap, single anchor | `[-1, 1]` | `[-1, 1]` |
| unreachable disputed object | `[1, 1]` | `[1, 1]` |
| two open anchors, `r = 9` and `7` at half weight | `[-8, 8]`, state `open_reference_only` | `[-8, 8]` |

The last row is the live comparison. Every anchor's reference is open, so the enclosure is the
weighted count bound and nothing more. **That is the expected honest result, not a failure.** A
finite number becomes available only when genuinely admitted interpretations exist, and none do.

## The defect this fixes, in my own work

My published `decision_packet` verifies one anchor. Applied to a cohort it would produce per-anchor
enclosures, and adding them gives `[-1, 1]` where the joint answer is `[0, 0]`. I verified that
against my own implementation before building the replacement. The cause is that anchors can share
constraints: if a disputed object is present at one anchor exactly when it is absent at another, the
two contributions cancel in every admitted world, and no per-anchor extremum can see it.

The replacement computes `D(w)` once per shared world, evaluating **both configurations in that same
world before weighting**, and takes the range over worlds. It also reports the separate relaxation,
labelled as a relaxation, so the gap is visible rather than implied. The checker refuses a report
that offers the relaxation as the result, and refuses an enclosure narrower than the worlds support.

## Open is not empty

An anchor whose reference is open contributes the interval `[-b*r, a*r]`. It may not declare
objects, and it is never rewritten as a world in which nothing exists. Emptying an open reference
would assert absence where there is only ignorance, and it would silently convert an unresolved
comparison into a confident negative one. A finite anchor with no admitted world returns
`unresolved` with the decision `not_evaluated`.

## Verification

Nineteen tests. Three conformance cases against the Engine lane's published reference results. Ten
adversarial refusals: the relaxation offered as the result, a world omitting a finite anchor, a
dropped adverse world, an anchor scored in a different world from its cohort, altered weights,
altered tolerance, an uncertified count, a wrong weighted value, a decision not following from the
enclosure, and weights that do not sum to one.

One independently structured control: a brute-force calculation that enumerates candidate matchings
by permutation rather than by augmenting paths, agreeing on **all 400** bipartite graphs across four
size classes. The count is asserted exactly so a silently shrinking enumeration cannot pass as a
full sweep.

## Costs

The producer, checker and all nineteen tests run in about 0.03 seconds on the standard library with
exact rational arithmetic. No dataset, service, model or network. The retained reports are
byte-identical across runs.

## What this does not establish

No reference interpretation is admitted, invented or implied. No object is asserted to exist. No
human judgement is created or predicted, and no review cost is claimed; the withdrawn judgement
count is not reinstated here in any form. The synthetic cases are labelled synthetic. Nothing here
bears on physical coverage, planner behaviour or risk, and nothing here demonstrates product
differentiation against a competent analyst, which remains untested.

## Reproduce

```sh
python3 -B -m unittest discover -s tools/measure -p test_cohort_packet.py
python3 -B tools/measure/cohort_packet.py research/cohort-packet/0.1.0/oppositely-coupled.json
python3 -B tools/measure/check_cohort_packet.py \
    research/cohort-packet/0.1.0/oppositely-coupled.json \
    evidence/cohort-packet/oppositely-coupled-report.json
```

## Non-claims

An internal research artifact, retained as `proposed`. Not independent external scientific review,
not an operator acceptance, not a safety, compliance or vendor claim. No released `1.2` byte, frozen
protocol, claim-register entry, Engine file or other owner's work is modified.
