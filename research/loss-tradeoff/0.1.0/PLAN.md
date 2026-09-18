# Reference uncertainty and the false-positive/miss tradeoff

Plan ID: `reiyah.loss-tradeoff.development-plan`.
Version `0.1.0`. Status: `exploratory`.

The completed comparisons use equal penalties for false positives and misses.
Their nominal, arbitrary-edit, axis-translation and simultaneous-translation
results are already known. This exploratory follow-up tests that equal-penalty
decision premise. Freeze this plan and implementation before calculating the
new weighted outcomes. Preserve every previous result and its exact criterion.

## Fixed operands and new obligation

Reuse the same 64 exposed images, two frozen qualified prediction packets,
eligible car predictions/reference rectangles, exact IoU at least 1/2 and
maximum one-to-one matching. Reuse the same 73 overlapping cases. There are no
new images, model calls, downloads, training, annotations or human observations.
All 1,433 REC-D outcome-reserved images remain closed. This is not a selector
experiment and does not establish customer demand or economic savings.

Let `p` be the miss-penalty share in `[0,1]`. A false positive has cost `1-p`
and a miss has cost `p`. These are dimensionless decision weights common to
both outputs, all images and all objects. They are not measured prices, human
work, safety costs or a recommendation for an operational release gate.
Multiplying both weights by a positive constant does not change the decision.
For `p < 1`, the miss/false-positive penalty ratio is `p/(1-p)`. At `p=1`
only misses count. At equal penalties, `p=1/2`, this normalized loss is half
the prior unit loss and has the identical sign and strict decision rule.

An output with `n` predictions, `t` references and maximum matching size `m`
has loss `(1-p)(n-m) + p(t-m)`. Report the old-minus-new mean difference.
Strictly positive difference supports the proposed replacement; zero or
negative difference excludes strict improvement. Under reference uncertainty,
support requires a strictly positive universal lower bound, exclusion requires
a nonpositive universal upper bound, and otherwise the decision is unresolved.
An attained excluding world alone does not exclude the entire family.

The fixed displayed shares are `0, 1/5, 1/3, 1/2, 2/3, 4/5, 8/9, 16/17, 1`,
corresponding to miss/false-positive ratios `0, 1/4, 1/2, 1, 2, 4, 8, 16` and
miss-only. Retain all nine settings, including unfavorable and endpoint cases.
Also solve the entire share domain exactly as rational point/open-interval
cells, so the displayed grid cannot hide a decision threshold or its equality.

## Declared uncertainty families

Evaluate these 19 previously defined families for every one of the 73 cases:

- exact supplied projection;
- at most one arbitrary eligible reference edit globally;
- at most one arbitrary eligible reference edit per image;
- one-axis translation at radii 1, 2, 4, 8, 16, 32 and 64 pixels;
- simultaneous two-coordinate translation at radii 1, 2, 4, 5, 161/32, 8, 16,
  32 and 64 pixels.

The radius-zero geometric families duplicate exact projection and are not
counted again. The two extra 2D radii are the already verified bracket endpoints;
their per-image operands are retained from the completed search. Using those
known radii is explicit exploratory follow-up, not an unseen evaluation set.
All family definitions, boundary/eligibility rules and correlation permissions
remain as in their source packets. This gives 1,387 case/family allocations
and 12,483 displayed case/family/share rows. Their dependence remains explicit.

## Exact reuse argument and verification

For fixed predictions, write `N = nA-nB` and `M = mB-mA` in each world.
The new difference is `D(p) = (1-p)N + M`. The previous unit difference is
`D_unit = N + 2M`. Therefore

`D(p) = D_unit/2 + (1/2-p)N`.

Reference counts cancel between the outputs even when the world inserts or
deletes a reference. Since the coefficient of `D_unit` is positive and `N`
does not depend on the reference world, previous universal bounds and attained
extremizers remain valid for every declared share, including zero and one.
This argument depends on common constant weights and fixed predictions. It
does not authorize object-specific/class-specific costs, changed confidence
filters, different eligibility, new matching thresholds or reference-dependent
prediction sets. Reject incompatible source context rather than silently reuse.

Bind exact predecessor freezes, result/verification bytes, image membership,
prediction counts and source world identities. Use only families whose source
extrema were verified and attained. Report incomplete/blocked allocations if a
required source is absent or inconsistent; do not treat it as zero or substitute
a complete-case subset. Do not rerun closed selector experiments.

An independent verifier recomputes the retained world graph matching with a
separate algorithm, checks source-native proofs and computes each weighted
world directly from false-positive and miss counts. It checks the affine
enclosure transfer separately and verifies the complete `[0,1]` partition,
including strict support and closed nonpositive equality. Every unresolved
cell must have a supported and excluding source world valid for its share.
Any remaining proof or source gap must be explicit.

Before freezing, test exhaustive small graphs and weight endpoints, exact
break-even equality, positive/negative/zero count differences, inserted/deleted
reference-count cancellation, all interval orientations, failed membership,
changed source geometry/weights and proof reuse. Derive the conventional
algebra openly; no special capability or computational advantage is asserted.

## Reporting and costs

Retain every displayed row and every continuum cell. State exact primary
tradeoff thresholds, directions and endpoint decisions, with numerical plots
only as presentations of the rational results. Report the unchanged references'
aggregate false positives and misses for each output to make the proxy's
tradeoff concrete; these are counts against the supplied projection, not
physical errors or benchmark AP. Separate universal support, universal exclusion
and attained opposite worlds under each uncertainty family.

Preserve known costs of source preparation, this derivation, verification,
failed attempts and report generation. Do not double-charge reused source
inference/search/proofs, count nested times twice, or invent human/economic
values. Retain all source terms for derived reports. Keep raw geometry,
individual answer operands and native payloads private. A new weighting result
cannot reopen the closed equal-penalty selector-superiority claim or establish
an owner-approved replacement decision. Post-freeze changes require an explicit
retained amendment and new run identity.
