# Moment-cone decision interface

Version: `0.1.0`

Lifecycle status: `proposed`

Decide whether any probability measure on `[0,1]` reproduces a declared vector of subset-averaged
`k`-wise all-silent rates, and return a witness either way. This is the admissibility question for
any bound that extrapolates from measured channels to an unmeasured one through an exchangeable
mixture representation. A bound computed on a population where no such measure exists has no
identified set to report.

## Contract

Input is a bounded JSON task in one of two forms. [`input.schema.json`](input.schema.json) is the
published contract and is exercised in the tests; the command-line tools do not load a JSON Schema
validator, and instead enforce the same semantics in code, including refusing a key that is present
with a null value rather than reading it as the default. Where the two could drift, the tests are
what keeps them together.

**Preferred: an exact silence histogram.** `silence_histogram[s]` is the integer count of
opportunities on which exactly `s` channels were silent. The subset-averaged moments are then exact
rationals, there is no rounding box, and the verdict is unconditional on the counts.

**Fallback: printed decimals.** `moments` are exact plain decimal strings; floating point is refused
rather than rounded. `rounding_half_width` declares the interval each printed digit string stands
for, so a verdict can be asked of the whole box rather than of one point. Use this only when the
counts are unavailable, because a rounding box can change the answer: see the retained test showing
that the six-decimal print of a point mass at `1/7` is genuinely infeasible.

Output is a report with one of seven verdicts. The two exact verdicts appear only for a histogram
task, and the box verdicts only for a decimal task; the checker enforces that correspondence.

| verdict | witness | meaning |
|---|---|---|
| `infeasible_exact` | nonnegative polynomial | no measure has the histogram's exact moments |
| `feasible_exact` | one atomic measure | the histogram's exact moments are representable |
| `infeasible_over_box` | nonnegative polynomial | no measure has any moment vector in the box |
| `infeasible_at_centre_only` | nonnegative polynomial | the printed vector is excluded, the box is not |
| `feasible_over_box` | one atomic measure per box corner | every vector in the box is representable |
| `feasible_at_centre` | one atomic measure | the printed vector is representable, the box is not decided |
| `unresolved` | none | neither witness was found; nothing is asserted |

`unresolved` is never upgraded by default, and a failure to find a measure on the atom grid is
never reported as infeasibility. A grid restricts the support of the candidate measure, so it can
establish feasibility and can never establish its negation.

## Producing a histogram

Where the counts are not already determined by published summaries,
[`silence_histograms.py`](../../../tools/measure/silence_histograms.py) derives them from the
retained matched-prediction caches. It takes the cache directory as an argument and never records
it, emits aggregate counts only, and refuses to emit at all unless it reproduces the published row
counts and the histograms already recoverable from published summaries. An unvalidated population
definition would otherwise certify the wrong set silently.

```sh
python3 -B tools/measure/silence_histograms.py /path/to/local/cache
```

## Checking

[`check_moment_cone_certificate.py`](../../../tools/measure/check_moment_cone_certificate.py)
imports nothing from the producer. It expands the certificate from its declared multiplier and
polynomial, confirms the expansion, recomputes the linear functional and the box worst case, or for
a feasible verdict confirms that the atoms lie in `[0,1]`, the weights are nonnegative and sum to
one, and the moments are reproduced exactly. For a whole-box verdict it derives the declared corner
set from the task and requires the supplied corners to equal it as a set, each with its own measure.
The trusted surface shared with the producer is the JSON module, the decimal and rational string
conventions, and Python's `Fraction` and integer arithmetic.

Version `0.1.0` of the checker instead confirmed that every supplied corner was a corner and that
the count was right. A report that padded each corner with an extra unconstrained coordinate
defeated its duplicate test and presented two copies of one corner as both, concealing a corner
whose variance is negative. The retained input is under
[`evidence/moment-cone/retained-failures/`](../../../evidence/moment-cone/retained-failures/).
Counting is not coverage.

## Cost

Standard library only, no network, no dataset, no service. Measured on one host for five channels:
an infeasible verdict takes under a millisecond, a feasible centre about `0.4` seconds, and a
feasible verdict over all 32 corners of a five-moment box about `7` seconds.
