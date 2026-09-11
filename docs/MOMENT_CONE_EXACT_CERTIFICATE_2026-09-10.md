# An exact certificate for the moment-cone question, replacing a grid argument

Document ID: `reiyah.moment-cone.exact-certificate.2026-09-10`

Version: `0.4.0`

Lifecycle status: `proposed`

Lane: independent research, parallel to the Engine's population-binding work. This document
changes no released byte, no frozen protocol, no claim-register entry and no owner checkout.
It creates no operator acceptance and no scientific authority. Gate A remains unaccepted.

## The question and the result in one paragraph

Audit AV concludes that no probability measure on `[0,1]` reproduces the five subset-averaged
silence moments of the all-annotated-objects population, which is what refutes the exchangeable
version-population model for it. That audit is not on `main`. It belongs to the separately owned
redundancy-scaling lane, read here at branch `research/2026-09-09-tail-dependence`, commit
`9d6c11756165a6efe7126edb6def5d142caeddc4`, document blob
`d848ca7cab8ff7de7e1e07581a840a7303fb11af`. Nothing in that lane is modified by this document, and
its owner remains the only party who may revise it. Its argument is
that the smallest achievable moment error over a rational grid converges to a positive limit under
an eighty-fold refinement. **A grid cannot establish that conclusion.** A grid restricts the support
of the candidate measure, so grid failure is consistent with a measure the grid cannot express.
This lane replaces that argument with an exact algebraic certificate valid over the whole continuum,
and the conclusion survives: AV's verdict was correct and its argument was incomplete.

## The rounding box was avoidable, and is now gone

Version `0.1.0` of this document certified the printed six-decimal moments and their rounding box.
That was one step weaker than necessary. The moments are subset averages of an integer silence
histogram, so where the counts are known the moments are **exact rationals** and no rounding
argument arises at all.

The counts are recoverable from what is already published. For the all-annotated-objects population
the histogram `P(S = s)` printed to six decimals, together with `N = 134565`, admits exactly one
integer vector: each `P(S = s) * N` window of half width `N / 2000000 = 0.0673` contains a single
integer, and the six of them sum to `N` exactly. The same inversion applied to a population's
printed subset-averaged moments recovers its histogram uniquely, which is checked here against the
known case before it is used on the others.

| population | opportunities | silence histogram `s = 0..K` | independent confirmation |
|---|---|---|---|
| all annotated objects | 134,565 | 70970, 25485, 18533, 7727, 5468, 6382 | reproduces the control |
| four channels, truncated channel removed | 134,565 | 75804, 24292, 19683, 6679, 8107 | sums to `N` |
| most observable | 25,049 | 21344, 2475, 864, 232, 79, 55 | AP separately reports all five silent on **55** rows |

The last row is worth pausing on. The inversion was run on the printed moments alone, and the top
bin it returns is 55, which is the number Result AP states in a different section for a different
purpose. That is an independent check on the recovery, not a restatement of it.

For the remaining populations the histograms are not recoverable from anything published, so they
were computed directly from the retained matched-prediction caches by
[an independent extractor](../tools/measure/silence_histograms.py) that imports nothing from the
lane that produced the original table. It refuses to emit unless it reproduces that lane's seven
published row counts and the two histograms already determined by published summaries. All nine
gates passed, and the derived `P_1` and `P_5` for each range band match the values Result AS prints
separately. Only aggregate counts leave that program.

**Audit AV's table is now exact throughout.** Seven populations, decided by certificate rather than
by grid refinement, and the two methods agree on every one. With the four-channel sensitivity case
that is **eight exact cases: four infeasible and four feasible.** They are not eight incompatible
populations, and the four feasible ones prove representability of those summaries rather than
physical validity of any generating model.

Before reading any of these verdicts as a statement about how the channels behave, read
[what the diagnostic distinguishes](MOMENT_CONE_DECISION_VALUE_2026-09-10.md). Heterogeneous rates
alone are enough to produce a rejection with no dependence present, and perfect coupling is
accepted. The legitimate use of these certificates is deciding whether a mixture-based bound has an
identified set, which is the use Audit AV made of them.

| population | opportunities | verdict | witness | grid verdict |
|---|---|---|---|---|
| all annotated objects | 134,565 | `infeasible_exact` | `x(100x^2 - 115x + 23)^2`, `E[h] = -217693/1345650` | REFUTED |
| range 30 to 40 m | 26,386 | `infeasible_exact` | `x(4x^2 - 5x + 1)^2`, `E[h] = -359/65965` | REFUTED |
| range 40 to 50 m | 15,312 | `infeasible_exact` | `x(10x^2 - 12x + 3)^2`, `E[h] = -351/6380` | REFUTED |
| most observable | 25,049 | `feasible_exact` | exact six-atom measure | not refuted |
| radar returns at least 3 | 21,890 | `feasible_exact` | exact six-atom measure | not refuted |
| range 0 to 20 m | 54,624 | `feasible_exact` | exact six-atom measure | not refuted |
| range 20 to 30 m | 38,243 | `feasible_exact` | exact six-atom measure | not refuted |
| four channels, truncated removed | 134,565 | `infeasible_exact` | `x(1 - x)(8x - 3)^2`, `E[h] = -8057/538260` | not in that table |

The 30 to 40 m witness factors as `x((4x - 1)(x - 1))^2`, with rational roots at `1/4` and `1`. A
reader can expand it, take the inner product with the exact moment vector and read the sign in under
a minute. Each infeasible verdict costs about one millisecond; each feasible one about half a
second.

Agreement across two methods is worth stating carefully. The grid argument could not have
established its negative verdicts, as this document sets out. That it nonetheless reached the right
three is now known rather than assumed, and the four positive verdicts are upgraded from a residual
that fell to zero into explicit measures a checker re-evaluates.

Both negative witnesses are small enough to check on paper. `h` is nonnegative on `[0,1]` because
`x` and `1 - x` are and a square is; expand, take the inner product with the exact moment vector,
and read the sign.

The sections below retain the printed-decimal route, because it is what a reader has when only
rounded summaries are published, and because the rounding box is a real hazard worth showing.

## The certificate

For the printed moments `m = (0.207356, 0.102807, 0.069423, 0.055554, 0.047427)` with `m_0 = 1`,
the procedure emits

```text
h(x) = x * (1000x^2 - 1145x + 233)^2
```

`h` is a product of `x`, which is nonnegative on `[0,1]`, and a square, which is nonnegative
everywhere. Any probability measure on `[0,1]` therefore satisfies `E[h] >= 0`. Its expectation
under the declared moments is

```text
E[h] = -22834531/1000000 < 0
```

so no such measure has these moments. This is a proof, not a numerical observation. It needs no
grid, no solver, no root finder and no floating point.

Allow every printed moment its entire nearest-six-decimal rounding interval of `+/- 1/2000000`.
The largest value the same functional can take anywhere in that box is `-20007089/1000000`, still
strictly negative, so **every** moment vector consistent with the printed digits is incompatible
with a measure on `[0,1]`. The rounding box is not a nuisance here; it is load bearing, and the
retained-failure section shows why.

The certificate is not unique, and a shorter one is easier to check by hand. The three-integer
polynomial `(23, -115, 100)` gives

```text
h(x) = x * (100x^2 - 115x + 23)^2 = 529x - 5290x^2 + 17825x^3 - 23000x^4 + 10000x^5
E[h] = -164731/1000000, box worst case -136409/1000000
```

which certifies the same conclusion with a box margin ratio near `5.82` against `8.08` for the
emitted one. The procedure selects on box margin, so it prefers the longer polynomial; the short
one is retained as a test because a witness a reader can verify in a minute is worth keeping.

## Why the certificate has this shape, and how it is found

The truncated problem on `[0,1]` for moments `m_0..m_K` with `K = 2j+1` requires two matrices to be
positive semidefinite: `A = (m_{i+p+1})` and `B = (m_{i+p} - m_{i+p+1})` for `i, p <= j`. A vector
`v` with `v^T A v < 0` corresponds to `E[x * P(x)^2] < 0` for `P(x) = sum_i v_i x^i`, and a vector
with `v^T B v < 0` corresponds to `E[(1-x) * P(x)^2] < 0`. For even `K` the matrices are `(m_{i+p})`
and `(m_{i+p+1} - m_{i+p+2})`, giving the forms `P(x)^2` and `x(1-x)P(x)^2`. Each multiplier is
nonnegative on `[0,1]`, so every such vector is a certificate.

### Where a cited theorem is load bearing, and where it is not

The pairing of those matrices with the `[0,1]` problem is a classical result and it is not proved
here. It is worth being exact about what depends on it. **No verdict does.** A certificate is
verified by expanding a declared multiplier times a declared square and evaluating a linear
functional, all in exact rational arithmetic; if the expansion and the sign check pass, the
conclusion follows from nonnegativity of the multiplier alone. A feasible verdict is verified by
evaluating an explicit measure. The checker implements exactly those two verifications and never
appeals to the Hankel structure.

What the theorem supplies is **completeness of the search**: the guarantee that when a certificate
exists, looking in these matrices finds it, so that `unresolved` is rare rather than routine. If
the pairing were wrong the procedure would return `unresolved` more often than it should. It could
not return a wrong verdict. For two channels, where the answer has an elementary closed form,
completeness is checked empirically over more than a hundred rational moment pairs in the retained
test suite: every infeasible pair receives a certificate and every feasible pair receives a measure.

For the population above, exact rational elimination gives leading principal minors

| matrix | order 1 | order 2 | order 3 |
|---|---|---|---|
| `A = (m_{i+p+1})` | `+2.0736e-01` | `+3.8260e-03` | **`-8.7386e-08`** |
| `B = (m_{i+p} - m_{i+p+1})` | `+7.9264e-01` | `+1.5531e-02` | `+3.3364e-05` |

The infeasibility is entirely in `A`, which is why the certificate has the `x * P(x)^2` form. The
negative direction is read off the elimination exactly, then rounded to the smallest integer vector
that still certifies across the rounding box. Starting from that exact direction and optimising the
box margin over small integer roundings recovers, independently, the same polynomial proposed in the
Engine-side review, which had been obtained by a different route. Two structurally different
searches arriving at one witness is corroboration of the witness, not of either method.

## What the procedure does when the answer is the other way

A decision procedure that only ever says no is worthless. On the most-observable population,
`m = (0.043834, 0.010316, 0.004383, 0.002826, 0.002196)`, both matrices are positive semidefinite,
no certificate exists, and the procedure instead returns an explicit atomic measure on `[0,1]` with
six rational atoms whose moments equal the declared ones exactly. It further returns one such
measure for each of the 32 corners of the rounding box. Because the set of representable moment
vectors is convex and the box is the convex hull of its corners, certifying all 32 corners certifies
the whole box. Both retained AV verdicts are therefore reproduced exactly, by a method that shares
no code with the original.

## A population the retained audit did not report

Result AP recomputes its law with the count-truncated channel removed, on the remaining four
detectors, giving subset-averaged moments `(0.215738, 0.109442, 0.072654, 0.060246)`. Audit AV's
table does not cover that population. The procedure decides it in 31 milliseconds, on the
even-degree branch, with the shortest witness in this document:

```text
h(x) = x(1 - x)(200x - 69)^2
E[h] = -1619193/125000, box worst case -12881183/1000000
```

Both `x` and `1 - x` are nonnegative on `[0,1]`, so `h` is, and the expectation is negative across
the whole rounding box. **The four-channel summaries are incompatible with a mixing representation
too.** That matters because the truncated channel was the one AP itself flagged as an upper bound
on its own silent rate, so the incompatibility does not depend on it. This is a new fact about a retained
population, produced from published summaries with no new data run, and it is offered to the lane
that owns those results rather than asserted over them.

The asymmetry is the design principle and it is enforced in the implementation:

| direction | sound instrument | why |
|---|---|---|
| feasible | a grid, or any explicit measure | a measure on grid atoms is a measure on `[0,1]` |
| infeasible | an exact nonnegative polynomial only | a grid restricts the support and cannot exclude the continuum |

When neither witness is available the verdict is `unresolved`. It is never resolved favourably by
default, and a grid failure is never reported as a refutation.

## The failure this lane kept, and the threat it exposes

The first fixture written for the "grid failure must not become a refutation" test used the moments
of a point mass at `1/7`, printed to six decimals as `0.142857` and `0.020408`. The test asserted
that the procedure would return `unresolved`. It returned `infeasible_over_box`, and the procedure
was right: `0.142857^2 = 0.020408122449` exceeds `0.020408`, so the printed vector falls below the
Cauchy-Schwarz boundary by `1.2e-07` and no measure on `[0,1]` has it.

That is not a curiosity. **Rounding a feasible moment vector to six decimals can make it
infeasible.** Every refutation computed from printed moments must therefore be shown to survive the
rounding box before it can be read as a statement about the population rather than about the digits.
For the all-annotated-objects population that check is done above and it passes with a margin ratio
near eight. **Superseded as of version `0.3.0` of this document, 10 September 2026.** The paragraph that stood
here said that ranges 30 to 40 m and 40 to 50 m had not had the box check performed and named it as
the next step. Both are now certified exactly from their integer histograms, with no rounding box at
all, in the table above. The sentence is retained in Git history; the current result is the complete
table. The general point it was making survives and is worth keeping: a refutation computed from
printed moments must be shown to hold across the rounding box before it is read as a statement about
the population rather than about the digits.

The fixture is retained as a test rather than corrected away, together with a second retained case
showing that a moment vector on the Cauchy-Schwarz boundary has a rounding box that straddles it,
which the report labels `contains_infeasible_corner` rather than silently calling the box feasible.

## Fair comparison with the conventional alternatives

Three methods decide the same question on the same two populations, with costs measured on one
host. The comparison tool reimplements the first two rather than importing the predecessor's, so it
does not depend on them.

| method | refutes the refutable population | sound for infeasibility | cost on the refutable population |
|---|---|---|---|
| complete-monotonicity screen | no | yes when it fires, but it cannot fire here | `3.0e-05` s |
| grid error minimisation | apparently, by a positive error floor | **no** | `85.8` s |
| exact certificate, this lane | yes, with a witness | yes | `0.001` s |

The screen's entry needs care, and a first draft of this document flattened it. A negative finite
difference is a valid rejection: no Hausdorff moment sequence has one, so the screen is **sound
whenever it fires**. Checked directly, the invalid vector `(1, 1/2, 9/10)` is rejected by it at
`i = 1, j = 1`. What is true of the inputs here is narrower and is the point Audit AV makes: for
subset-averaged moments derived from a genuine finite `S` histogram, those differences are the
probabilities `P(S = s)` up to binomial factors and are nonnegative by construction, so the screen
is passed automatically and decides nothing. It is a sound filter that this problem never trips,
not an unsound method.

The grid probe reproduces the retained observation: on the refutable population an error of
`1/100000` is reachable and `1/1000000` is not, at grid denominators 200 and 800 alike, so the
floor does not fall with refinement. On the most-observable population every probed level down to
`1/10000000` is reachable at both denominators. The two methods agree on both verdicts. Only one of
them is entitled to the negative one.

On the feasible side the exact procedure returns a measure for the printed vector in about `0.4`
seconds and for all 32 corners of the rounding box in `7.2` seconds, at 121 grid atoms, against
`58.8` seconds for the grid probe on the same population.

The grid method reproduces the right verdict on both populations while being unsound in the
direction it is used for, which is the exact shape of error that stays invisible until a case
appears whose only representing measure is off-grid. The retained test suite contains such a case.

The two feasible-side outputs are also not the same kind of object and must not be read as one. The
grid probe reports that some measure on its atom lattice comes within a stated error of the target
moments. The procedure here returns an explicit rational atomic measure whose moments equal the
target **exactly**, which a separate checker re-evaluates. A small numerical residual is evidence;
an exact measure is a proof.

Two engineering defects found in this lane's own first implementation are retained rather than
quietly repaired. A degenerate rounding box was enumerated as `2^K` copies of one point, so a
centre-only feasible verdict performed 33 identical solves and took 112 seconds instead of 0.4.
The default atom grid was four times finer than any fixture needed, which cost a further factor of
fifteen. Neither affected a verdict; both were found by measuring rather than by reading.

## A defect in the checker, found by the coordinator

Version `0.1.0` of the separate checker accepted a forged whole-box feasibility report. On a task
with `K = 2`, moments `(1/2, 1/4)` and widths `(0, 1/100)`, the lower corner `(1/2, 6/25)` has
variance `-1/100` and is impossible, so the box is not feasible. The forged report supplied two
copies of the upper corner `(1/2, 13/50)`, each padded with a different valid third moment. The
checker confirmed that every supplied corner was a corner, that the count was right, and that no
two were identical, and accepted it.

The violated invariant is coverage. Counting corners and testing them pairwise for equality is not
the same as proving that the supplied set is the declared set, and unconstrained extra coordinates
defeat the equality test. The repaired checker derives the corner set from the task, requires the
supplied set to equal it exactly, requires every corner to carry exactly `K + 1` moments, and
verifies a measure for each. Ten independently constructed forgeries are now retained as tests,
including the original, two copies of one corner at the correct dimension, a corner outside the box,
omitted and extra corners, a report that narrows its own box, and a whole-box claim on a degenerate
box. Seven of the eleven coverage tests fail against the version `0.1.0` checker, which is what
makes them regression tests rather than decoration.

The exact conclusions were unaffected: the certificate path was never in question, and the three
retained certificates were rerun through the repaired checker and confirmed, with task and report
digests matching the coordinator's independent record. The failing input is retained at
`evidence/moment-cone/retained-failures/corner-forgery-accepted-by-b0c33d9.json`.

## What is established, and what is not

**Established, by proof:** the printed moment summaries of the all-annotated-objects population,
and every vector within their stated rounding, admit no representing probability measure on `[0,1]`.
Equivalently, those summaries cannot arise from channels that are conditionally independent and
identically distributed given a single scalar failure intensity.

The scope of that sentence is the retained summaries and their declared rounding box, and it stops
there. It is not a statistical rejection of a superpopulation model, because a sample moment vector
can fall outside a cone whose generating population lies inside it, and no sampling or reference
uncertainty enters this calculation. Phrases of the form "the model is refuted for the population"
appeared in a first draft of this document and in the lane's commit message; they outrun what is
proved and are corrected to the summary-level statement wherever they can still be edited. The
commit message is history and is left as written, with this paragraph as its correction.

**Not established.** These are eight cases, four infeasible and four feasible, and every one is a
statement about retained summaries, not about a physical population. An infeasible verdict is
not evidence of coupling: see the controls in
[the decision-value document](MOMENT_CONE_DECISION_VALUE_2026-09-10.md).
A sample moment vector can fall outside a model cone when the underlying population lies inside it;
sampling and reference uncertainty are not part of this calculation and no confidence statement is
made. Five deliberately heterogeneous named detectors are not a random draw from a version
population, so this refutes the applicability of that representation to these summaries and does not
refute Eckhardt and Lee's theorem, whose primary text is not retained in this lane and was not read
for this work. Feasibility on the most-observable population likewise does not establish that its
physical generating model is exchangeable. Nothing here bears on Result AP, which assumes no mixing
model, and nothing here is a safety, compliance or vendor claim.

## Reproduce

```sh
python3 -B tools/measure/moment_cone_certificate.py \
    research/moment-cone/0.1.0/all-annotated-objects.json > report.json
python3 -B tools/measure/check_moment_cone_certificate.py \
    research/moment-cone/0.1.0/all-annotated-objects.json report.json
python3 -B -m unittest discover -s tools/measure -p test_moment_cone_certificate.py -v
python3 -B tools/measure/compare_moment_cone_methods.py
```

Standard library only. No network, no dataset, no service, no model. Measured costs are in
[the retained comparison](../evidence/moment-cone/method-comparison.json). The producer and the
checker share only the JSON parser, the decimal-string convention and Python's `Fraction`; the
checker imports nothing from the producer and re-derives every quantity it confirms.

## Non-claims

An internal research artifact, retained as `proposed`. Not independent scientific review, not an
operator acceptance, not a safety or compliance finding, not a comparative claim about any detector
or vendor, and not a statement about any deployed system. No released `1.2` byte, frozen protocol,
claim-register entry or other owner's work is modified.
