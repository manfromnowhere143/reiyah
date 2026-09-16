# Independently checked stopping for conditional reference audits

Document ID: `reiyah.perception-audit-components-result`. Version: `0.1.0`. Lifecycle status: `exploratory`.

## Result and scope

The Engine can now check several delivered sufficient reference sets without trusting a
mixed-integer solver's optimality claim. The optional [component proof](../research/perception-audit-components/0.1.0/README.md)
uses graph factorization, equivalent reference neighborhoods, checked matching witnesses and
one shared deletion budget. Both standalone replacement and augmented comparisons are supported.
Existing commands keep their default behavior.

The forty-frame case is **Mapillary camera base plus retained Megvii lidar additions**: 2,007
base detections, 738 additions, 2,299 reference objects, baseline improvement 51/20 and strict
tolerance 1/10. All confirmations below are hypothetical premises on exposed development data.
No human audit, independent physical reference or lower total customer effort is established.

| Delivered set and deletion family | Engine enclosure | Checked conclusion |
|---|---:|---|
| First case, 9 confirmed, any remaining deletions | [1,1] exact | Sufficient; minimum size not checked here |
| Second case, 53 confirmed, any remaining deletions | [1/7,2/7] exact | Sufficient; minimum size not checked here |
| Forty-frame simple-priority set, 480 confirmed | [3/5,51/20] exact | Sufficient |
| Forty-frame guided set, 530 confirmed | [1/5,51/20] exact | Sufficient |
| Forty-frame shrunken set, 373 confirmed | [1/10,51/20] conservative | Unresolved at the strict threshold |
| Forty-frame additive pool, 354 confirmed, at most 49 deletions | [11/10,51/20] conservative | Sufficient |
| Same pool, arbitrary remaining deletions | [-3/4,51/20] conservative | Bound alone unresolved; a separately checked 181-record adverse set disproves sufficiency |

The research lane reports solver-tier sufficiency for 373. This Engine checkpoint does not
independently establish that claim. It also does not check the reported optimality bounds of
9, 53 or [306,373]. The 373 set was obtained after 480 queries and further computation; removing
labels from the final certificate does not refund queries already performed.

The same-budget controls retain the original outcomes: no confirmations are needed at k=48;
the original 49 confirmed records still admit the earlier disjoint 49-record counterexample.
The standalone replacement is already supported at k=49 without confirmations. These outcomes
must not be presented as new query savings.

## Why this is the next Engine step

The selected research exchange reports 480 queries for a simple adjacency priority and 530 for
its counterexample-guided policy on the forty-frame case. Its stronger conclusion is the stopping
criterion, not universal selector superiority. We consume the candidate sets and check their
sufficiency; the policy runs and complete costs remain the independent lane's responsibility.

The original graph has 1,223 connected components, of which 806 have equal role graphs and cancel.
This supports a finite proof far smaller than enumeration of all 2,299 reference-label subsets.
Two early implementations exceeded the work limit on 373. Their source snapshots and results
remain in the private checkpoint. The final method preserves the limits, uses conservative local
bounds when necessary and retains unresolved outcomes. It does not increase a limit to obtain
the desired verdict.

The 480-set API run takes approximately 0.15 seconds for proof generation with its initial check
and a separate check in the development assay. Input preparation, command startup, serialization
and repeated CLI measurements are recorded separately. The existing conservative bound is cheaper
but unresolved on this set. These different conclusions do not establish a speedup. Neither
measurement includes human review, inference, simulation, or training.

The repeated three-sample CLI medians are 0.380 s for the existing bound and 0.502 s for the
component proof, including input loading, proof production/checking, serialization and process
startup. The former is unresolved and the latter sufficient on the 480-set request. This is a
cost of obtaining a stronger conclusion, not an equal-result speed comparison.

## Evidence and validation

The selected research source is `6fbd5f3b89f60698c3acca27f42d99aee0ab9d27`, outbox
`audit-sufficiency-0.1.0`, manifest
`4ffbc3219e11e495ff8e8a6e9481823d9e60141738832c6cb2b773a36cc07265`.
All eight public outbox payloads match; seven committed origins agree. The named candidate sets
were consumer-selected from separate private files, copied and digest-bound here. They were not
covered by that public manifest, so no research-owner attestation is inferred. Their mathematics
is checked directly against the Engine input.

Independent global-subset/direct-loss tests cover 1,728 small replacement/observation/budget
cases and 128 forced-bound cases. Further controls cover shared worlds, incompatible observations,
required absences, equal graphs, identical names on opposite graph sides, neighbor equivalence,
global budgets, omitted states, forged matchings, resource limits and checker operation with
producer functions disabled. Current commands, compatibility and final suite receipts are bound
in the [verification record](../research/perception-audit-components/0.1.0/verification.json).
The complete repository suite passes 476 tests and the measurement suite passes 93. All twelve
prior packets preserve their results, 22 new packets check, and sixteen CLI run/verify commands
pass. These tests establish engineering conformance, not external scientific validation.

The private checkpoint is `~/.codex/reports/reiyah/engine-audit-components-2026-09-17-jqq_taoy/`.
It retains source bindings, both failed-to-resolve drafts, commands, costs and the sealed consumer
exchange. Gate A remains operator-unaccepted. No cloud resources, inference or publication
campaign were started.

## Next consumer

Use the common checker for every selector, with the cheap existing bound first. Measure actual
queries and all stopping computations. Check both contradictory audit answers and remaining
counterexamples. Compare reuse with and without applicable prior observations on a genuinely
changed comparison, preserving zero-savings cases. The
[mission and benchmark gates](REIYAH_NEXT_MISSION_2026-09-17.md) define the two lanes and the
conditions for a broader result worth sharing.
