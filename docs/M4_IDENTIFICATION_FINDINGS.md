# M4: what reference error can and cannot do to the coincident-miss ratio

Document ID: `reiyah.gate-b.m4-identification-findings`

Version: `0.1.0`

Lifecycle status: `proposed`

Synthetic fixtures only. No measured data was read and no empirical record was emitted.
Generator: `tools/measure/m4_partial_identification.py`. Transcript:
[`m4_partial_identification.txt`](../evidence/measurement/m4_partial_identification.txt).
Deterministic: two runs are byte-identical, about six seconds, seed `20260829`.

## 1. Why a solver, and why it is not a linear program

Counterexample CE-5 in
[`estimand_counterexamples.txt`](../evidence/measurement/estimand_counterexamples.txt) shows a
0.50 percent reference error moving `c` from exactly 1.0000 to 0.5512 or to 1.3673. Reference
error is the dominant term, not a correction, which is why RGA-027 is P0 and why M4 is carried
inside the same contract as the estimate rather than appended to it.

The estimand is

```
c = a * n / [ (a + b) * (a + cc) ]      n = a + b + cc + d
```

with `a` both miss, `b` A only, `cc` B only, `d` neither. This is a ratio of two **quadratics**
in the cell counts, because the numerator carries `a * n`. Linear programming does not apply, so
no LP sharpness claim is made. The solver optimises by box-vertex enumeration plus a declared
grid plus a seeded random probe, and labels its own output

> NUMERICALLY VERIFIED OVER A DECLARED GRID, NOT PROVED SHARP

If the random probe ever beats the grid optimum the run reports a `SHARPNESS BREACH` rather than
quietly adopting the better value.

## 2. Proposition M4-1: `c` is invariant under proportional reference error

**Statement.** For any `lambda > 0`, `c(la, lb, lcc, ld) = c(a, b, cc, d)`.

**Proof.** `c` is a ratio of a degree-two form to a degree-two form:

```
c(la, lb, lcc, ld) = (la)(ln) / [ (l(a+b))(l(a+cc)) ]
                   = l^2 * a*n / [ l^2 * (a+b)(a+cc) ]
                   = c(a, b, cc, d)
```

A strictly proportional perturbation of all four cells is a scale by `(1 + t)`, so `c` does not
move. Verified numerically at `lambda` in `{0.90, 1.00, 1.15, 2.00}`: `c = 1.0549` at every value.

**Consequence, and it is the useful part.** Uniform reference error does not bias `c` at all.
Every unit of `c`'s identification exposure comes from **differential** reference error, error
whose rate depends on the cell and therefore on the channel outcomes.

This relocates the M4 problem. A blinded reannotation does **not** need to estimate the overall
annotation error rate, which is irrelevant to this estimand. It needs to bound how much the error
rate **varies across cells**. That is a different, smaller, and more achievable measurement
target, and it changes the reannotation design.

## 3. Two refuted L2 formulations, both retained

The `L2` rung is meant to add a non-differential-error restriction. Two encodings were tried and
both failed, in opposite directions. Both are kept in the transcript as refuted designs.

| Attempt | Encoding | Outcome |
|---|---|---|
| First | tie the perturbation of the two single-miss cells | **Vacuous.** Narrowed L1 by exactly 0.0000 |
| Second | error lands in each cell in proportion to that cell's share | **Null.** Width exactly 0.0000, no identifying content |

**Why the first is vacuous, structurally rather than by fixture accident.** `c` is monotonically
decreasing in `b` and in `cc`. Every maximiser therefore pushes both single-miss cells to their
lower bound, and every minimiser pushes both to their upper bound. The tie `b == cc` is satisfied
at both extrema for free, so it can never bind, on any stratum. It was first suspected to be a
symmetry artifact of the fixture; retrying on a stratum whose single-miss cells differ by nearly
a factor of four gave the identical width, which is what prompted the structural proof.

**Why the second is null.** It is exactly Proposition M4-1's invariance direction.

## 4. The formulation that binds: bounded differentiality

Each cell `j` is perturbed at rate `r_j` drawn from `[rbar - delta, rbar + delta]` for a free
common rate `rbar`, with total movement inside the L1 budget. `delta = 0` recovers the null
proportional case; large `delta` recovers L1. `delta` is the single reviewable number a blinded
reannotation must bound.

On the asymmetric fixture stratum, observed `c = 1.0549`:

| `delta` | Identification set | Width |
|---|---|---|
| 0.00 | [1.0549, 1.0549] | 0.0000 |
| 0.02 | [1.0057, 1.1063] | 0.1006 |
| 0.05 | [0.9620, 1.1547] | 0.1927 |
| 0.10 | [0.8935, 1.2375] | 0.3440 |

**At `delta = 0.05` the set already covers 1.0.** A five percentage point differential error rate
is enough to leave this stratum's dependence unidentified. That number is the precision target the
reannotation design must hit, and it is far more demanding than an overall-error-rate target would
have been.

## 5. Four adversarial cases

| Case | Attack | Result |
|---|---|---|
| F-02 | Relabel 40 both-miss rows as single misses on each channel and remove 40 neither-miss rows | **Both marginals preserved exactly**, `c` moves 1.0000 to 0.6000. Invisible to every marginal diagnostic; visible only to a bound |
| F-03 | Budget exceeds a thin stratum's A-miss marginal | Upper end **`UNBOUNDED`**, not a large finite number. Such a stratum is not eligible for a worst-group extremum |
| F-04 | Reference built using one evaluated channel's outputs | `c` moves 1.0000 to 5.0000 by construction. Verdict **`invalid`**, not a wider interval. No bound repairs it, and reference provenance must be established as independent before M4 runs |
| F-05 | Combining identification and sampling uncertainty | Reported as an **outer set containing an inner interval**, never collapsed, never summarised as one figure |

## 6. What this does not establish

It does not bound `c` on any measured stratum: no blinded reannotation has been performed, so no
`delta` is estimated and the measured reference-error identification state remains `unknown`, as
recorded in
[`claim-status-register-2026-08-29.json`](../evidence/claim-status-register-2026-08-29.json). It
does not prove sharpness. It does not license an L3 headline, which additionally requires
independent replication. Proposition M4-1 is a statement about the estimand's algebra, not about
any dataset.

## 7. Non-claims

No scientific support, no operator acceptance, no safety or compliance finding, no comparative
claim about any detector or vendor. No measured data was read. No released `1.2` byte is modified.
