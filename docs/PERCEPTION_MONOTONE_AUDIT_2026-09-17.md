# Audit sufficiency from ordered reference sets

Document ID: `reiyah.perception-monotone-audit`. Version: `0.1.0`.
Lifecycle status: `exploratory`.

## What changed

The optional `audit --proof-method monotone` checks preserved-base additions by
certifying the smallest and largest reference sets consistent with the supplied
observations. It preserves complete joint reference worlds and the shared error
budget. A separate checker validates both endpoint matchings and covers; it does
not invoke a search, matching routine or integer optimizer.

The underlying property is specific: with fixed output membership, a shared
matching graph and A contained in B, adding reference vertices cannot decrease
`TP_B-TP_A`. General A-to-B replacements do not have this property. The method
checks membership and returns `scope_unavailable` when the required relation is
absent. Existing comparison and audit methods remain available and keep their
defaults.

The research lane's local committed insertion-monotonicity note at `475ad6e`
motivated this check. This checkpoint retains its own argument, exhaustive
controls, source bindings and certificates. It does not adopt the research lane's
unsealed localization results or change its working files. The argument uses
established maximum-matching properties; no new theorem or scientific-priority
claim is made.

## Why the rank difference is monotone

Consider a reference set S and one additional reference x. Each maximum matching
cardinality can increase by at most one.

If A's cardinality does not increase, the difference cannot decrease. Otherwise:

1. Take an optimal A matching on `S + x`. It must match x to some detection d.
2. Remove that edge. The remaining matching is optimal for A on S, and d is free.
3. Regard that matching as a B matching, since B contains A with the same edges.
   Augment it to a maximum B matching on S. Augmenting paths preserve previously
   matched vertices.
4. Detection d must still be free. If it were matched, restricting this B matching
   to A would give more than A's maximum number of matched detections on S.
5. Add the edge from d to x. B's cardinality also increases by one.

Thus every reference insertion changes the rank difference by zero or one. Repeat
the argument for larger supersets. The declared nonnegative penalties and weights
preserve this ordering in the loss improvement. Output counts, preprocessing and
existing matching eligibility must remain fixed.

## The conditional audit proof

Within each admitted joint world, first apply required-absent observations and
reject worlds inconsistent with confirmed-present observations or the error budget.

- **Upper endpoint:** retain every reference except required absences. It is always
  feasible in a remaining compatible world.
- **Lower endpoint:** retain only confirmed-present references. Monotonicity makes
  its value a valid lower bound for every remaining allowed reference set.

Deleting all unconfirmed references may exceed a bounded error budget. In that
case the lower endpoint remains a bound; it is not an admissible counterexample.
Intersect it with the existing budget-aware deletion bound. The checker marks
the interval exact when the lower endpoint is admitted, or when the bounds
coincide at the admitted upper endpoint. Otherwise it keeps a conservative bound.
Only an admitted endpoint can establish insufficiency. A bound crossing the
threshold without an adverse witness remains unresolved.

Apply these operations in every compatible **joint** world, then take global
extrema. Do not independently choose a convenient interpretation for each anchor.
An empty compatible family is inconsistent, never vacuously sufficient. Unequal
nonnegative anchor weights and nonnegative penalties are supported by this audit
argument.

The 2,000,000-work limit is unchanged. Admission reserves the existing full
upper-endpoint estimate and adds the lower-endpoint matching work on its actual
remaining vertices and edges. Input, packet, world and graph limits are also
unchanged. Unsupported scope and exhausted work remain explicit.

## When a confirmation count is provably minimum

This additional calculation has narrower scope: one unconditional finite world,
uniform anchor weights, positive total loss penalty, all supplied answers present,
and a deletion budget at least as large as the entire declared reference population.

Let q be the number of confirmed labels, w the common weight, a/b the miss/false
positive penalties, and `D_B-D_A` the count change per anchor. The family permits
deleting every unconfirmed record. In that world, `TP_B-TP_A` cannot exceed q across
all anchors, because B cannot match more than q remaining references and A's count
is nonnegative. Therefore sufficiency requires:

```text
(a+b)*w*q - b*sum(weight*(D_B-D_A)) > tolerance.
```

The checker derives the integer lower bound from this strict inequality. If a
separately checked sufficient request attains that count, it reports
`minimum_confirmed_present_count`. A sufficient larger request gets only the
necessary bound; it is not promoted to minimum. The bound can exceed the available
population and does not establish that a sufficient set exists.

This counts confirmed-present records under the declared family. It does not
minimize human time, scene visits, sequential queries with contradictory answers,
or review cost under correlations and unequal query prices. An inclusion-minimal
set can be larger than a different set of minimum cardinality.

## Checked development result

The retained forty-frame comparison has 2,299 reference records, 738 retained
additions, equal weights 1/40, unit miss/false-positive penalties and strict
tolerance 1/10. Its full-reference improvement is 51/20. The necessary inequality is:

```text
(2*q - 738)/40 > 1/10, so q >= 372.
```

A checked B matching contains 416 references with no eligibility edge to A.
Selecting 372 distinct reference endpoints from this matching supplies a candidate
whose A rank is zero and B rank is 372 after every other reference is deleted.
The endpoint checker proves the full conditional interval [3/20, 51/20]. The lower
bound exceeds 1/10, and the count attains the necessary floor. Therefore **372 is
the minimum number of confirmed-present records** for this case and error family.
The 371-member control has lower endpoint 1/10 and fails the strict criterion.
The earlier 373-member proposal is sufficient but is not a cardinality minimum.

These are hypothetical confirmations on exposed development data. No person was
queried. A smaller final certificate does not refund queries already incurred by
another procedure, nor does this construction guarantee favorable future answers.

| Supplied request | Previous component result | New endpoint result | New interval |
|---|---|---|---|
| First case, 9 confirmations | Sufficient | Sufficient; count minimum 9 | [1, 1], exact |
| Second case, 53 confirmations | Sufficient | Sufficient | [1/7, 2/7], exact |
| Forty frames, 373 confirmations | Unresolved | Sufficient | [3/20, 51/20], exact |
| Forty frames, constructed 372 | Unresolved | Sufficient; count minimum 372 | [3/20, 51/20], exact |
| Forty frames, constructed 371 | Unresolved | Insufficient | [1/10, 51/20], exact |
| Forty frames, 480 confirmations | Sufficient | Sufficient | [3/5, 51/20], exact |
| Forty frames, 530 confirmations | Sufficient | Sufficient | [1/5, 51/20], exact |
| Pool of 354, at most 49 deletions | Sufficient | Unresolved | [1/10, 51/20], conservative |
| Pool of 354, unrestricted deletions | Unresolved | Insufficient | [-3/4, 51/20], exact |
| Independent replacement, at most 49 deletions | Sufficient | Scope unavailable | No endpoint claim |

The new method does not dominate existing methods. It leaves the original 49-label
request unresolved under its bounded budget; the separately supplied disjoint
adverse witness still checks and proves insufficiency. Both old explicit adverse
packets are retained and rechecked. No prior counterexample is withdrawn.

## Validation and cost scope

The [verification record](../research/perception-revision/0.1.0/monotone-audit-verification.json)
binds the complete 13-request assay, all method results and retained artifacts.
It includes 24 previous packets, 39 newly produced packets and ten fresh-process
CLI commands. All pass their declared result checks, including the replacement
method's explicit unsupported-scope exit.

All 501 repository tests and 93 measurement tests pass. The nine new tests include
65,761 reference-insertion comparisons calculated by independent partial-injection
enumeration and 9,481 small audit problems checked against independently enumerated
worlds and deletion sets. Controls cover coupled worlds, unequal weights, absent
answers, inconsistency, strict thresholds, infeasible endpoints, general replacement
counterexamples, certificate mutation and unchanged resource limits. The first
assay stopped at an incorrect inventory assertion before generating results: the
sealed source contains eleven requests, not twelve. The corrected assay retains
all eleven, both new controls and both explicit previous counterexample packets.

Five rotating-order repetitions per method/request give 195 local kernel timings.
Each includes proof production and a separate check on the same validated in-memory
operands; preparation and fresh CLI costs are retained separately. The machine was
not isolated from other owners' workloads. These are development timings, not a
complete validation-cost benchmark.

| Request with equal exact intervals | Component median | Endpoint median |
|---|---:|---:|
| First case, 9 | 4.63 ms | 7.62 ms |
| Second case, 53 | 60.82 ms | 35.48 ms |
| Forty frames, 480 | 284.03 ms | 134.74 ms |
| Forty frames, 530 | 302.43 ms | 169.20 ms |

For the new 372 request, the endpoint median is 114.62 ms while the component
method remains unresolved. That is a change in proof strength, not an equal-result
speed comparison. The 354/k49 case above favors the component method's proof
strength. Retain the cheap existing bound when it already establishes the decision.

## Scope and next experiment

The executable request family remains reference deletions. Monotonicity also
explains why pure reference insertions cannot lower this loss difference under
the fixed-graph premises. It does not authorize reusing the reported exact upper
endpoints for an insertion family, or treating changed geometry, matching rules,
detector preprocessing or independent replacements as deletions.

The common checker is now a stronger baseline for selection experiments. The
research lane should measure actual additional queries and complete computation
using the same error family and checked stopping rule for all methods. A direct
matching construction belongs among the applicable conventional baselines.
Current exposed cases and hypothetical confirmations do not establish human
savings, held-out performance or frontier superiority.

The fresh private root is
`~/.codex/reports/reiyah/engine-monotone-audit-2026-09-17-pqt93y5g/`.
Read its PLAN and amendment, selected-source checks, controls, assay, verification,
closeout and seal. The previous packets remain unchanged. Gate A remains unaccepted.
No inference, cloud compute, human audit, public post or outreach is performed here.
