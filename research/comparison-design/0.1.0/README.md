# Comparison design and baseline audit, 0.1.0

Status: exploratory. Research cutoff: 21 September 2026.

**Decision: MODIFY the research direction.** Active selection of informative
measurements is established prior art. Reiyah has not demonstrated a practical
advantage over a competent equal-information method. This increment qualifies
a statistical baseline and identifies a bounded engineering question; it does
not deliver a new statistical estimator or a frontier benchmark result.

## Executed mathematical result

The [frozen question](QUESTION.md) tests the general-K optimum asserted in
Hara, Matsuura, Honda and Ito, *Active model selection: A variance minimization
approach*, Machine Learning113,8327-8345, published21November2024.
Its Eq9 sums pairwise conditional variances; Theorem2/Eq10 uses the sum of
absolute pair differences as query weights. Primary source:
[the complete publisher article](https://link.springer.com/article/10.1007/s10994-024-06603-1).

Take two test points, four fixed binary predictions and true labels0. Their
zero-one loss rows are [0,0,0,1] and [0,0,1,1]. Query exactly one point.
Enumerating both possible query outcomes gives:

| Query rule | Probabilities | Sum of six pairwise variances |
| --- | --- | --- |
| Published ideal rule | (3/7,4/7) | 3/4 |
| Fixed rational challenger | (7/15,8/15) | 41/56 |
| Uniform | (1/2,1/2) | 3/4 |
| Published source's default0.01 smoothing, rational reference | (301/702,401/702) | 362003/482804 |

The challenger strictly improves the stated objective by **1/56**. Thus the
published general-K formula is not a universal minimizer of that objective.
This is a finite mathematical counterexample, not an estimate from simulation.
[The method](METHOD.md) derives the ordinary importance-sampling optimum:
q_i proportional to the Euclidean norm of the pair-difference vector. This is
standard constrained-variance mathematics, not an algorithmic novelty claim.

The mental derivation and proposed challenger were already known when the
question froze. This is an authored, exposed example, not a blind benchmark.
It does not establish improved model-selection accuracy, fewer human labels,
a flaw in the paper's empirical results, or any Reiyah competitive advantage.
It does not refute the paper's two-model formula. No publisher correction,
external scientific review or independent replication is claimed.

## Source mechanism and verification

Pinned author code is at
[33f6fab5f50d470bc2957a3ed1c4e86d94d82f5d](https://github.com/sato9hara/active-model-selection/tree/33f6fab5f50d470bc2957a3ed1c4e86d94d82f5d).
Only the two selected query function bodies run, with their JIT decorators
removed and prange mapped to serial range. Numba is absent. On oracle point-mass
label probabilities, all nine defined query calls agree with their rational
references. The all-equal unsmoothed call is explicitly unexecuted because its
normalization is undefined. No original compiled program, model training,
inference, paper experiment or surrogate-quality evaluation ran.

The closed-form calculation agrees with separate finite-probability enumeration
for all20distributions across five authored cases. The record checker passes
16controls, including two permutations, invalid distributions, cases where the
published rule is appropriate, and mutations of the actual saved result.
Both implementations share an author; these are separate calculations, not
independent authorship. The nonzero controls also retain worse challenger
variances, rather than reporting only its favorable case.

[Results](results.json), [checker record](check.json), [freeze](freeze.json),
[source identities](sources.json), [later source supplement](source-supplement.json)
and [costs](costs.json) are retained. Whole supervised audit process:
0.220885209s; checker:0.108728041s. Internal audit workflow:0.064224667s.
These scopes overlap and must not be added. They are not speed comparisons.

## What changes for Reiyah

[The comparison design review](COMPARISON_DESIGN.md) distinguishes statistical
model selection from universal finite-model certification. Compare methods
under the same guarantee, information and stopping rule. A statistical
estimator's smaller label count does not certify every admitted world; a
worst-case certificate does not establish better statistical efficiency.
Use the corrected classical objective when that is the chosen baseline,
retaining the published rule separately for faithful reproduction.

The next proposed check targets a real implementation limit: the finite-world
kernel falls back to loose bounds beyond4096assignments or2million estimated
work units. For fixed eligibility and positively conditioned object presence,
a two-endpoint matching calculation may avoid enumeration. Test and prove the
restriction, inspect current consumers, and retain counterexamples outside it
before modifying the evaluator. General Boolean dependencies, conditional
edges, missing references and inconsistent assumptions must keep their current
semantics. No scalability or novelty result for that proposal is claimed here.

This engineering study cannot substitute for a future decision-relevant,
equal-information value experiment on separately selected qualified material.
The earlier mapping and encoded-grid parity, navigation disadvantage and
unresolved physical claims remain unchanged. All1,433reserved images stay closed.

## Reproduction and custody

The public checker uses the standard library:

```sh
python -B research/comparison-design/0.1.0/check.py \
  research/comparison-design/0.1.0/results.json \
  /tmp/reiyah-comparison-check-FRESH.json
```

Use a nonexistent output filename. This verifies the saved authored result.
Full query-mechanism reproduction additionally needs existing NumPy and the
exact pinned private query source recorded in sources.json:

```sh
python -B research/comparison-design/0.1.0/audit.py \
  /path/to/qualified-owner /path/to/FRESH-result.json
```

The owner layout contains private/sources/hara-code-src--query.py. The archived
execution used a byte-bound existing runtime and supervisor, denied network
before the child started, and verified the frozen files. The examples above
are development replay, not the locked historical Gate A release procedure.

Complete publisher HTML is retained privately. Hara PDF capture stopped at
1,500,001bytes; its render failed. A second, distinct Dürr2024 PDF capture stopped
at450,001bytes. Both prefixes and failures remain; neither is complete PDF
evidence. No payload is redownloaded to evade the caps. Source HTML, author
code and tool-rendered research bodies stay private; public files contain
authored analysis, authored numbers and source metadata only.

Private owner: ~/.codex/reports/reiyah/comparison-design-2026-09-21-l8umtwg0/.
Read CLOSEOUT, FINAL_COSTS, PUBLISH_FINAL and FINAL_CONFIRMATION after
integration. Publisher readback is an integrity observation by the publisher,
not independent transport or scientific evidence. Gate A remains
operator-unaccepted. Full effort, charges, energy, network overhead and peak
memory remain unknown. The completed historical ten-hour assignment is not
restarted or padded.

The [validation record](validation.json) retains two initial lint/format launch
failures: Ruff was passed directly where the frozen wrapper requires Python.
Both failed before child execution. Corrected launches through the pinned
Python runtime pass without changing the frozen wrapper or audited code.

The [validation supplement](validation-supplement.json) retains a failed optional
Git whitespace check: one extra blank line ends the frozen question. Its bytes
remain unchanged. This formatting check is not represented as passing.
