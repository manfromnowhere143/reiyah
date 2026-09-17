# Whole-image correction observations

Version 0.1.0, 17 September 2026. Status: exploratory development research.

**The four fixed arms use the same number of observations and reach the same
decisions.** No selection or certified-stopping advantage appears here. Once an
image audit may retain one erroneous reference record, 19 of the 20 images with
nonempty detector outputs cannot determine strict improvement. Concrete geometric
worlds prove each of those ambiguities. Product economics remain inconclusive;
the observation and full-cost investment gates are not met.

This continues the [current-bound comparison](../../value-disproof/0.1.0/README.md).
It uses the 64 already exposed REC✓D development images, including six unavailable
inputs. The 1,433 outcome-reserved images remain closed. These are old detector
comparisons, not modern chronological release pairs or independent customer cases.
Read the [source qualification](../../../docs/PERCEPTION_REFERENCE_CORRECTIONS_2026-09-17.md)
for the publisher derivative, joining limitations, custody and attribution.

## Fixed comparison

There are 82 dependent cases: 64 images, 16 fixed blocks of four, the complete
64-image cohort and the 58-image cohort admitted by input availability. Missing
outputs block their cases; they are never replaced with empty predictions.
The 38 images with two observed empty output lists are zero-query draws.

Before a query, the complete reference set is open. Original annotations provide
optional selection hints, without restricting the possible corrected set.
A whole-image query reveals the publisher's corrected reference rectangles.
Workers receive visible inputs and requested answers over stdin, never an oracle
path or hidden corrected alternatives, counts or hashes. This is process dataflow
separation, not an OS security boundary or independently blinded study.

The existing policy is unchanged: pedestrian operands, detector score at least
0.3, reference threshold 0.5, height at least 25 pixels, exact continuous IoU at
least 0.5, unit false-positive/false-negative penalties and strict tolerance zero.
The reference threshold is an operational filter, not a probability over worlds.
The quantity is paired loss difference Δ = L_A − L_B; positive means B improves.
It is not official KITTI AP or a physical-safety metric.

| Arm | Selection | Nominal stopping calculation |
|---|---|---|
| A | Largest open interval first | Independent conventional max flow |
| B | Same as A | Native matching/cover proofs and checking |
| C | Original-reference margin hint | Native matching/cover proofs and checking |
| D | Same as C | Independent conventional max flow |

Both backends use the same residual-error mathematics and observation budgets.
The native proof establishes the nominal matching; the research layer handles
residual edits and composition. This experiment does not add an Engine audit API.

All four arms have the following results in the fixed assay:

| Assumed residual uncertainty after an audit | Supported | Excluded | Unresolved | Blocked | Queries |
|---|---:|---:|---:|---:|---:|
| Exact publisher reference | 10 | 60 | 0 | 12 | 51 |
| At most one record edit per image | 0 | 39 | 31 | 12 | 57 |
| At most one record edit across the case | 1 | 40 | 29 | 12 | 57 |

An edit is an insertion, deletion or replacement of an eligible reference box.
It covers a missing object or changed box; no original/corrected object
correspondence is assumed. Eligibility, outputs and metric remain fixed.
This is a declared worst-case stress family, not an estimated annotation-error rate.

Counts above include overlapping cases, not independent workloads. Exact-reference
queries split into 20 for singletons, 14 for blocks and 17 for the admitted cohort.
Each residual family uses 20, 17 and 20 respectively. A/B and C/D have identical
ordered query histories as well as decisions; A/C also tie on per-case query counts.
The [machine-readable table](results.json) retains all 984 assigned arm/family/case
rows, plus full-observation follow-up results. No unresolved or blocked row is dropped.

## Separating loose bounds from insufficient observations

One replacement can change each model's maximum matching by at most one, so it
can move Δ by up to four under unit penalties. The initial bound clips those rank
changes to the detection counts. A replacement is not an addition-only operation.

The separately frozen follow-up computes exact ranks after every possible single
reference deletion, then bounds the addition of one arbitrary new reference node.
If those ranks are m_A and m_B, and output counts are n_A and n_B, the interval is

```text
[2(m_B − min(n_A, m_A+1)) − n_B + n_A,
 2(min(n_B, m_B+1) − m_A) − n_B + n_A].
```

Take the union over the unchanged and single-deletion graphs, then intersect the
count bounds. This encloses insertions, deletions and replacements. It is exact
for arbitrary new neighborhoods when outputs are disjoint; geometric constraints
can make it conservative. Conventional and native methods may both use it.

The follow-up also tests actual rectangles at exact IoU boundaries, deduplicates
their graph neighborhoods, and checks selected adverse worlds with native proofs
and independent max flow. It tests 1,097 geometries and 1,427 candidate graph worlds.
The result is:

- All **31** cases unresolved under one edit per image have concrete
  opposite-decision worlds: 19 singletons, 11 blocks and the admitted cohort.
- With one shared edit, the tighter bound resolves one additional block. Every
  remaining **28** unresolved case has an opposite-decision world.
- The admitted cohort's nominal Δ is **5/58**. Every single edit leaves Δ at least
  **1/58**. Two retained geometric edits give **−1/58**, proving that the minimum
  number of arbitrary eligible reference edits needed to exclude improvement is
  **two** for this fixed cohort. This is a post-hoc sensitivity corollary.

These worlds share the same supplied audit answers and obey their stated residual
budgets. Even a full audit cannot distinguish them under that observation contract.
They are mathematical counterexamples, not allegations that the publisher made
those errors. The follow-up evaluates full-audit adequacy only; it does not claim a
new query-saving experiment or overwrite the original assay.

## Cost, verification and continuation

The fixed assay takes 3.54 seconds locally. Per-arm selection, measurement and
stopping time sums are approximately A 0.27 s, B 0.51 s, C 0.54 s and D 0.42 s.
These are single-run compute observations with separate startup, preparation and
verification records. Human preparation, engineering, integration, adjudication,
actual image-audit time and agreed prices remain unmeasured. Neither 3× fewer
expensive observations nor 2× lower total cost is established.

Thirteen targeted tests pass. They include 512 independent matching graphs,
12,800 one-edit worlds for the initial bound, and 256 graphs with 13,056 worlds
for the stronger bound. Replay checks 984 rows, 660 observation events, 1,644
stopping points and 330 native nominal proofs. Analysis verification checks 12
initial witness proofs, 164 follow-up packets, all 246 full-observation rows and
59 opposite-decision compositions. All 69 selected source bindings and both
implementation freezes match. The separate reproduction command reproduces the
scientific results in a fresh private directory. The default research consistency
check passes; this is not Gate A release validation. The future 1,000 rejection
control pilot target has not been run.

Stop selection/stopping superiority claims for this family and keep platform
expansion stopped. The next useful input is a concrete chronological model-release
decision with a qualified observation-error model and measured review costs.
The existing [workflow brief](../../value-disproof/0.1.0/WORKFLOW_BRIEF.md) prepares
that discussion locally. No outreach, paid service, publication, deployment or
main update occurred. Gate A remains operator-unaccepted. There is no basis to
consume reserved outcomes merely to tune these methods or rescue the hypothesis.

To reproduce, use the retained Python environment with jsonschema. From this
candidate root, choose a new private output directory outside Git:

```sh
env -u PYTHONPATH /path/to/python -B research/correction-observation/0.1.0/reproduce.py \
  --source /path/to/engine-reference-corrections-2026-09-17-n4s6r72u \
  --output /path/to/new-private-reproduction
```

The command reads only the allowlisted development exports, verifies source
bindings, records fresh freezes, runs every arm and both analyses, and checks all
results. Raw coordinates, original source identities, oracle answers and proofs
remain outside Git. Public files contain experiment code and derived results.
