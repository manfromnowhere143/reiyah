# Proportional counts are not a general model of uniform reference error

Document ID: `reiyah.reference-noise-interpretation.2026-09-07`

Version: `0.1.0`

Lifecycle status: `corrected`

This note corrects the broad interpretation of Proposition M4-1 in
[the retained M4 findings](M4_IDENTIFICATION_FINDINGS.md), not its algebra. It also addresses
the same interpretation in the operator-supplied external vision review. The earlier M4
document and synthetic transcript remain retained; no measured result or frozen protocol is
replaced by this correction.

## The valid theorem and the unsupported extension

For contingency counts x = (a, b, c, d), with positive denominator, write the coincidence
ratio as C(x) = a(a+b+c+d)/[(a+b)(a+c)]. M4 correctly proves C(lambda x) = C(x) for every
positive lambda. Equal proportional change in all four counts leaves the normalized table
unchanged. This is a homogeneity identity.

That identity does not prove immunity to every reference-corruption process whose probability
is constant over true channel outcomes. A uniform probability of corrupting a label can move
mass between cells. Moving mass and multiplying every cell by the same factor are different
operators. Uniform random thinning preserves the population distribution under its stated
independence assumptions; it still introduces finite-sample uncertainty and does not cover
general mislabeling or geometric reassignment.

## An exact counterexample and a matched-marginal control

Let two binary error indicators E_A and E_B be independent, each with probability 1/10.
Their true joint-error probability is 1/100 and their true coincidence ratio is 1. A binary
reference label is flipped with probability epsilon = 1/10, independently of both true error
indicators. Because the same reference is used for both channels, the observed correctness
errors are E_A' = E_A XOR R and E_B' = E_B XOR R for the same flip R.

Every true cell has the same reference-corruption probability. In the cell order
(both errors, A only, B only, neither), the exact transformation is:

```text
true probabilities       = (1, 9, 9, 81) / 100
observed probabilities   = (9, 9, 9, 73) / 100
observed marginal rates  = 18 / 100, 18 / 100
observed coincidence C   = (9/100) / [(18/100)(18/100)] = 25/9
```

The ratio changes from 1 to 25/9 despite an outcome-independent, uniform probability of
reference-label corruption. No observer was changed and no common cause was introduced into
the true observer errors. The common cause is in their shared measurement reference.

An ablation supplies independently flipped reference labels to the two channels, each with
the same flip probability. The noisy marginal rates remain exactly 18/100, while the noisy
joint probability becomes 81/2500 and the ratio remains 1. Matching the marginals alone
therefore does not identify the shared-reference mechanism. These are synthetic probability
calculations, not newly observed detector performance.

The [exact-rational implementation](../tools/measure/reference_noise_counterexample.py)
enumerates the transitions and also checks zero noise and proportional rescaling. Its
[retained output](../evidence/cache-selection/reference-noise-control-0.1.0.json) contains
every rational cell value and the source digest. The construction is elementary; no
scientific novelty is claimed.

## What this changes in the research program

M4 can define differentiality as the *net proportional change in cell counts*. Under that
definition, its bounded perturbation model remains a possible sensitivity model. But that
parameter is not automatically the event-level reference-corruption probability, nor its
variation across true outcome cells. A reviewer cannot estimate one and silently use it
as the other. The reference process needs an explicit transition and selection model.

For a fixed, complete opportunity universe, write an observed probability vector q = K p,
where K specifies how true cells become measured cells. Common label flips have
K = (1-epsilon) I + epsilon J, where J flips both error bits. Proportional rescaling is a
different, much narrower construction. Missing true opportunities, false opportunities and
stratum reassignment additionally require selection and insertion terms. Those terms must
remain unknown unless observations constrain them.

The useful next identification question is which entries or structural restrictions of K,
and which opportunity-selection terms, can actually be bounded from independent evidence.
It is not whether a scalar error budget has been called uniform. A finite grid search does
not prove a resulting identification set is sharp. The current M4 solver already disclaims
that stronger guarantee.

The frozen 240-case study examines a sample of detections. It can inform the physical
interpretation of those detections within its declared population. It does not, by itself,
identify every true both-miss opportunity or the complete reference transition process for
a safety-critical coincidence coefficient. That would require a different opportunity
census and prospective study. Do not change the existing sample or endpoint retrospectively.

This counterexample does not assert that binary shared-label flips describe nuScenes
annotation errors. It establishes the narrower logical result: M4's rescaling theorem is
insufficient to justify a general reference-error immunity claim or a reference certificate.
