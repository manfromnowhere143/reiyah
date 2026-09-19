# Sequential auditing with residual reference uncertainty

Document ID: `reiyah.sequential-audit.plan`.
Version: `0.1.0`.
Lifecycle status: `exploratory`.
Date: 19 September 2026.

## Question and allocation

Can a specified weighted or proxy-assisted sequential audit reduce observations
while preserving a declared error bound and the residual uncertainty in each
observation? This is the next methods task in the
[roadmap](../../../docs/ENGINE_ROADMAP_2026-09-19.md). It is an authored-fixture
method check, not a prospective empirical study, customer comparison, or novelty claim.
Prior development results and literature are known. Fixture purposes are chosen
to exercise boundaries; their construction is not random sampling from applications.

Before any outcome run, bind this plan, mathematical specification, exact 28
populations in fixtures.json, generator, producer, separate checker, controls,
source bindings, runtime identity and supervisor digest in freeze.json. Every
population has at most six members. Retain all allocated populations, four arms
and all positive-probability sampling orders. Zero-weight members remain in the
population and observation-status record; they need no query for this target.

The fixture set covers strong and small margins, strict ties, unequal and zero
weights, misleading and constant proxies, correlated/clustered member values,
full and partial reference intervals, every nonresponse status, boundary
thresholds, and very unequal sampling probabilities. No held-out outcome,
image, model output, customer record, inference or training is involved.

## Fixed methods and information

All arms receive the same population identities, weights, threshold and fixed
proxy scores before queries. Querying a member reveals its declared lower and
upper endpoint and observation status, never its latent truth. Methods cannot
read unqueried endpoints when choosing their sampling probabilities or stakes.
The exhaustive experiment can access them solely to enumerate and verify outcomes.

Four registered arms use the same nonnegative linear-betting construction:
uniform sampling; sampling proportional to target weight; sampling proportional
to weight times a positive proxy score; and that same proxy sampling with a
fixed residual control variate. Exact formulas are in MATHEMATICS.md. No learned
policy, oracle betting fraction, tuning after results, or claim to reproduce a
paper's complete optimized implementation is included. The published methods
motivate this explicitly specified comparison.

Each arm uses total error allowance 1/20, split into 1/40 per direction. This is
per fixed population and per separately selected arm. There is no simultaneous
95% claim across the 112 comparisons, nor permission to select a favorable
test after observing these outcomes. The checker evaluates the exact error
probability for every registered population/arm; it does not estimate coverage
from Monte Carlo repetitions.

At every prefix, first apply the exact logical interval. Otherwise stop at the
first single directional wealth reaching 40, except that full observation
always returns the logical result, retaining residual ambiguity. Simultaneous
directional crossings produce an unresolved conflict. Every stopping decision
and its first prefix are retained. For diagnostic optional-stopping checks the
mathematical wealth is continued through all prefixes of each enumerated order;
these suffix calculations are computation, not additional charged observations
for a policy that already stopped.

Compare the statistical arms under the same error allowance. Also retain the
exact native interval rule along each identical order, checked against a
separate conventional enumeration of every box vertex. Include a conventional
descending-weight query order. Fewer statistical queries are not superiority
over an exact all-world guarantee. Weight/proxy selection alone is not a novel
Reiyah advantage over an equally equipped conventional implementation.

## Checking and decision rules

The separate checker imports no producer. It reconstructs probabilities,
every prefix factor, nonnegativity over the full allowed observation range,
the importance-corrected conditional mean and null supermartingale drift.
It enumerates every complete order, verifies its exact rational probability,
first stopping point, exact comparison, summary and full-population result.
It computes each one-sided crossing probability, their union and false-decision
probability and rejects any breach of the allocated bound. Every comparison
has probability mass exactly one and exactly the factorial number of orders.

Controls reject missing/invalid values encoded as zero, unknown properties,
invalid weights/rationals/statuses, absent or zero sampling support, forged
wealth/probability/stopping/decision, duplicate queries and changed-threshold
reuse. A change to loss, population or any frozen file invalidates its binding.
Corrected implementation requires a new freeze and retained failed attempt.

Advance only to the conclusion the results support. A correct but costly or
unhelpful procedure remains a valid negative result. A validity violation stops
that claim. No population is dropped and no margin, alpha or proxy is changed
to obtain a favorable result. Report unresolved outcomes and all cost limits.

## Bounds and costs

Hard cumulative outer-process elapsed ceilings: 300 seconds of outcome execution
and 300 seconds of actual-result checking, including retries and failures.
Single-worker child user/system CPU time is recorded separately. Controls,
source reading, packaging and publication are separate categories. The owned
supervisor enters network denial before starting the pinned language runtime.
It kills the owned process group at its remaining cap and preserves partial
files, stdout/stderr and receipt. A cap is incompleteness, never a pass.

At most 64 MiB of new study artifacts, counting public packet files and private
outputs separately when both copies exist; the inherited checkout is separate.
Stop growth below 5 GiB free space. No new dependencies are needed. Source
payloads are reused by exact binding to the closed audit, not copied. Record
all known process and publication intervals without counting nested timers twice.
Reading, authoring, useful/human effort, whole-session billing and economics
remain unmeasured unless separately recorded. No dollar or human savings inferred.

The historical controller, closed candidates and Engine source remain unchanged.
Safe normal publication and exact publisher readback are authorized. This packet
does not accept Gate A, deploy a system, contact customers or open reserved data.
