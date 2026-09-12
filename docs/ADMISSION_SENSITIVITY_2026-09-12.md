# How much of a verdict comes from the detectors, and how much from the admission

Document ID: `reiyah.admission-sensitivity.2026-09-12`

Version: `0.1.0`

Lifecycle status: `proposed`

Lane: independent research and conventional comparator, parallel to the Engine. Changes no Engine
file, no shared handoff, no frozen protocol and no owner checkout. Creates no reference admission,
no reviewer and no human judgement. Gate A remains unaccepted.

## The question this lane had been avoiding

The conventional comparator established that on a finite cohort this instrument is exactly the
conventional method run once per admitted reading. The whole value of the apparatus therefore rests
on the **set of admitted readings**, and nothing in this lane has ever said what makes that set
valid. Every number published here inherits the assumption. This measures what it carries.

## The asymmetry

If the admitted set `W` is contained in `W'`, the enclosure over `W` is contained in the enclosure
over `W'`. The enclosure is the range of the world values plus a fixed open contribution, and a range
over a larger set contains the range over a smaller one. Checked exhaustively over every subset of
every retained case.

Two consequences, and they point in opposite directions:

- **Removing admitted readings can only narrow the enclosure**, so it can only make a verdict *more*
  decisive. A `supported` stays supported, an `excluded` stays excluded, an `unresolved` may become
  decided. Asserted as a test across every retained case, with the flag reported in every report so
  that a failure would be visible rather than silent.
- **Admitting one more reading can only widen it**, so it can only *destroy* a decisive verdict,
  never create one.

Therefore a decisive verdict rests entirely on the claim that the admitted set is complete, and **no
evidence inside the cohort can support that claim**. And an unresolved verdict cannot be rescued by
admitting more readings; it can only be settled by ruling readings out, which takes evidence, which
is what the resolution plan is for. The two kinds of answer rest on two different assumptions, and
only one of them is the kind an observation can discharge.

## How much is asserted

The coarse bound is the structural limit given the anchors, the retained additions and the loss. It
holds whatever anyone admits. The admitted enclosure sits inside it, and the gap is the part of the
possible answer space eliminated by the choice of readings rather than by the detectors:

```
asserted_share = ( (E_low - C_low) + (C_high - E_high) ) / ( C_high - C_low )
```

## The result, on this lane's own retained cases

| decisive case | readings | enclosure | coarse bound | asserted share |
|---|---|---|---|---|
| `oppositely-coupled` | 2 | `[0, 0]` | `[-1, 1]` | **1** |
| `separated-geometry-observation-case` | 4 | `[1, 1]` | `[-1, 1]` | **1** |
| `worst-group-flip-case` | 2 | `[0, 0]` | `[-1, 1]` | **1** |
| `worst-group-masking-case` | 1 | `[3/5, 3/5]` | `[-1, 1]` | **1** |

**Every decisive verdict this lane has ever produced is carried entirely by the admission decision.**
In each one the admitted readings pin the value to a single point, the detectors narrow nothing that
the admission had not already narrowed, and the coarse bound permits a reading that would destroy the
verdict. Each of those conclusions stands only if the admitted set is complete, and that is not
something the cohort can establish.

This is not an arithmetic error and it is not a defect in the cases. It is a true statement about
where the information in a decisive answer comes from, and it was not visible until it was measured.

The unresolved cases sit at the other extreme: most have an asserted share of `0`, their enclosure
equal to the coarse bound, because nothing was admitted that eliminated anything. The live
two-anchor comparison is one of them, and it eliminates nothing at all, which is the honest position
for a comparison with no admitted reference.

## What this says about the instrument's advantage

Put together with the comparator result, the picture is exact rather than rhetorical.

A cohort with one admitted reading **is** the conventional analyst: a point answer, an asserted share
of one, and the comparator agreeing exactly. Both facts are asserted as tests on the same case. The
instrument's advantage over conventional practice is not a property of the instrument. It is
proportional to the **plurality of the admitted set and the disagreement within it**. With a single
reading admitted there is no advantage at all, and the honest report says `confirmation only`.

That gives the programme a sharper target than "build a better comparison". The comparison is
finished. What is not finished, and what the value now provably depends on, is a defensible account
of which readings are admissible and whether the set of them is complete. No amount of further work
on the arithmetic moves that.

## Limits

The asserted share measures **dependence, not error**. A share of one is what a true, complete,
single reference would also produce, and nothing here says the admitted sets are wrong. It says the
conclusions are inherited from them rather than measured against them, and that the distinction has
never been reported.

The coarse bound is itself a declared structure: it takes the anchors, the retained addition counts
and the loss as given. A reading outside the declared anchors is outside this analysis entirely. No
reading is invented, admitted, ranked or excluded here, and this program cannot discharge the
dependence it measures. The cases are synthetic except the live two-anchor comparison.

## Reproduce

```sh
python3 -B tools/measure/admission_sensitivity.py research/cohort-packet/0.1.0/worst-group-masking-case.json
python3 -B tools/measure/admission_sensitivity.py research/cohort-packet/0.1.0/open-two-anchor.json
python3 -B -m unittest discover -s tools/measure -p 'test_admission_sensitivity.py'
```

Fourteen tests, about 0.3 seconds. Exact rational arithmetic, standard library only, no data read.

## Non-claims

An internal research artifact, retained as `proposed`. Not independent external scientific review,
not an operator acceptance, not a safety, compliance or vendor claim. It admits, excludes and ranks
no reference interpretation, and creates no reviewer or judgement. No released `1.2` byte, frozen
protocol, claim-register entry, Engine file or other owner's work is modified.
