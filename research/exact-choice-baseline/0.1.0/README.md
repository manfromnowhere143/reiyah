# Exact choice: sufficient labels and acquired labels

Study ID: `reiyah.exact-choice-baseline`, version `0.1.0`.
Status: exploratory mathematical qualification, 12 October 2026.

A small certificate does not mean a procedure can find it with equally few
queries. Reiyah's next comparison needs a baseline that handles shared labels
correctly and charges for the labels actually acquired. This study qualifies an
authored implementation of the exact finite-pool stopping and integer covering
formulation in Tetsuji Kuboyama's
[*How Many Labels Does Model Choice Need? Certificates and Budgets for Selective
Prediction*, arXiv:2609.18622v1](https://arxiv.org/html/2609.18622v1),
16 September 2026. It also computes a small exhaustive decision-tree benchmark.
Neither method is presented as a Reiyah invention.

## What was tested

The frozen [protocol](protocol.json) includes every binary prediction vector,
every ordered confidence ranking including ties, and every ordered tuple of
candidates with replacement for `(rows, candidates)` equal to `(1,2)`, `(2,2)`,
`(3,2)`, `(1,3)` and `(2,3)`. Identical candidates are included. Every possible
binary label completion and every partial observation history is checked.
Smaller candidate indices break model-choice ties. The metric is trapezoidal
area under the **generalized** risk–coverage curve (AUGRC): cumulative accepted
error divided by the full pool size, integrated over coverage. It is not area
under conditional selective risk.

The [producer](reproduce.py) uses integer risk coefficients, exact pairwise
contrast bounds and the paper's integer covering formulation. A
[separate checker](verify.py) integrates risk curves with rational arithmetic,
averages every order within confidence ties, enumerates label completions and
finds distinguishing subsets. It imports neither the producer nor the existing
Reiyah engine. Full canonical traces are compared, including every bound,
winner, certificate size, adaptive decision and acquisition count.

The preread paper examples and anticipated named outcomes are disclosed in the
protocol. This is not blinded or preregistered research. The protocol was bound
before implementation and execution; the trace format and implementations were
bound before their execution. See [provenance](provenance.json).

## Results

The two implementations agree over **12,700 candidate tuples, 308,916 partial
histories, 94,040 complete labelings and 534,168 fixed-order acquisition paths**.
These are exhaustive counts within the declared small population. They are not
independent trials, an empirical sampling distribution or a deployment error
rate. Four additional named examples are checked separately.

| Named example | Certificate for the stated labels | Queries in the stated order | Optimal worst-case depth across all labels |
|---|---:|---:|---:|
| Paper's four-row example | 3 | 4 | 4 |
| Three-row majority | 2 | 3 | 3 |
| Metric convention | 1 | 1 | 1 |
| Identical candidates | 0 | 0 | 0 |

The majority example makes the distinction concrete. Two candidates predict
all zeros and all ones, with tied confidence on all three rows. Any two equal
labels certify the majority winner. If the first two queried labels differ,
the third is necessary. Every complete labeling has a two-label certificate,
but even the best adaptive procedure needs three queries in its worst case.

Across the grid, optimal worst-case depth exceeds the largest hindsight
certificate size by one for **4,640 of the 12,700 ordered candidate tuples**;
it equals that size for the other 8,060. Duplicates, orderings and the unequal
sizes of the grid cells are retained intentionally. This fraction is not a
population prevalence estimate. The decision-tree oracle enumerates hypothetical
responses before choosing a row; its executed path reads only that row's actual
label. It is exponential and is used only as a finite benchmark.

A fixed input-only order prioritizing the largest pairwise coefficient width
uses one more label than the hindsight minimum for 15,504 of the 94,040 complete
labelings, and equals it for the remainder. The minimax policy optimizes
worst-case depth with row-index tie breaking. It does not optimize average
queries or pointwise regret; its per-label costs need not beat the width order.
No realistic label distribution is imposed and no policy superiority is claimed.

The metric-convention control also matters: trapezoidal scaled risks are `5`
and `4`, so candidate B wins. Right-endpoint integration gives `6` and `6`, so
the stated tie rule selects A. Scaling is `2 n² = 18`. That switch changes the
metric, not just its implementation. Identical candidates supply a separate
shared-evidence control: the earlier candidate wins without acquiring labels,
even though each candidate's risk remains individually uncertain.

Exact results, per-grid counts and histograms are in [result.json](result.json).
[Verification](verification.json) records complete trace agreement.
[Execution receipts](execution.json) record repeated byte-identical producer output. [Controls](controls.json) retain deliberate
rejections of corrupt, incomplete and noncanonical evidence. The canonical
trace digests are published. Compressed bytes repeat exactly in the recorded
environment; compressor versions can change those bytes without changing the
canonical records. The bulky traces are retained privately and are not needed
as download inputs.

## Mathematical boundary

Let a confidence tie occupy zero-based positions `[s,e)` among `n` rows. Its
integer weight is `w = 2n − s − e`. A candidate's scaled risk is

`r_j(y) = Σ_i w_ji [prediction_ji ≠ y_i] = c_j + Σ_i a_ji y_i`.

For each pair, unread labels contribute the minimum or maximum of zero and
their difference coefficient. These endpoints are attainable because every
unread binary completion is allowed. A candidate is selected only when it wins
against every rival for every completion, retaining the strict inequality when
the rival would win an index tie. Missing labels remain unknown; they are not
silently replaced by zero.

The certificate computation knows the complete labeling. Acquisition does not.
The adaptive benchmark minimizes the maximum remaining depth over the two
possible responses to each proposed query. None of these counts includes human
review time, mistakes, unavailable responses, packet preparation, computation,
channel qualification or audit overhead. Actual AUGRC weights, ranks and
predictions must be fixed before acquiring labels; this study does not address
training or recalibration on revealed outcomes.

## Reproduce

Python standard library only; no source downloads, packages or model inference.
Run from the repository root, using a new output directory:

```sh
experiment_dir=$(mktemp -d)
python3 -B research/exact-choice-baseline/0.1.0/reproduce.py --output-dir "$experiment_dir/run"
python3 -B research/exact-choice-baseline/0.1.0/verify.py --trace "$experiment_dir/run/trace.jsonl.gz" --named "$experiment_dir/run/named.jsonl.gz" --result "$experiment_dir/run/result.json" --output "$experiment_dir/verification.json"
python3 -B research/exact-choice-baseline/0.1.0/controls.py --named "$experiment_dir/run/named.jsonl.gz" --output "$experiment_dir/controls.json" --workdir "$experiment_dir/controls"
```

The retained executions started under a macOS `sandbox-exec` policy denying
network access before Python started. This is an offline research check, not
Gate A release-launch evidence. The [trace format](trace-format.json) fixes
ordering, integer scaling and serialization.

## Consequence for Reiyah

The exact shared-label comparator is now qualified on this finite domain for
use in a **compatible** future experiment. It does not replace the current
object-detection matching engine: fixed row-additive AUGRC and coupled detector
matching have different assumptions. Do not compare those outputs as if they
answered the same decision.

Keep hindsight sufficiency, feasible acquisition and complete work as separate
quantities in the [proposed value comparison](../../../docs/research-decisions/next-comparison-2026-10-12.json).
The next useful step remains a fresh consequential paired decision with an actual
observation process and retained cost records. This bounded qualification is
complete; enlarging the synthetic grid would not establish that advantage.

This is not a reproduction of the author's executable code, LP solver,
empirical tables or asymptotic theorem. Separate implementations within one
assisted investigation are not independent scientific replication. No physical
validity, work saving, novelty, state-of-the-art superiority, product readiness
or Gate A acceptance is established. The [source record](sources.json) preserves
version, custody and attribution; no third-party payload is redistributed here.
