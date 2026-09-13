# The conventional baseline reaches the same conclusion

Document ID: `reiyah.overlap-parity.2026-09-13`

Version: `0.1.0`

Lifecycle status: `proposed`

Lane: independent research and conventional comparator. Changes no Engine file, no Gate B file, no
shared handoff and no owner checkout. Gate A remains unaccepted.

## The result, stated first

**For the ordering claim this lane has been making, the dependence coefficient earns nothing over
ordinary set overlap.** An Engine consumer checked the selected tables without importing this lane's
code and found that Jaccard reproduces the ordering everywhere. That is the competent conventional
analyst this lane exists to be measured against. It was given a fair opportunity to succeed, and it
succeeded.

## The identity, derived here rather than accepted

Take an exactly matched universe: `N` observed objects, a common unseen count `m`, each channel
capturing `k`, pair intersection `w`, and `d = N - k`. Each channel misses `(N + m) - k = d + m`, and
both miss `(N + m) - (2k - w) = N - 2k + w + m`. So

```
c(m) = (N + m) * (N - 2k + w + m) / (d + m)^2
```

and for two pairs at the same `k`,

```
c_1(m) - c_2(m) = (N + m) * (w_1 - w_2) / (d + m)^2.
```

The factor is strictly positive, so `sign(c_1 - c_2) = sign(w_1 - w_2)`. **Ordering by the coefficient
is ordering by intersection size, for every common unseen count.** Jaccard `w / (2k - w)` has
derivative `2k / (2k - w)^2 > 0` in `w`, so it induces the same ordering. Checked on 4,000 random
configurations with no disagreement.

The real tables do not have exactly matched marginals, so the identity is a comparator under its
premise rather than a proof about them. Tested directly instead: across the **270** pairwise
comparisons available in this lane's own retained counts, Jaccard agrees with the coefficient **270
times out of 270**.

## What this means, and does not

It does not make the coefficient wrong, and it does not make the prospective instrument useless. It
identifies precisely where value must now be earned, and it is not here:

- faithful source preparation from raw detector submissions rather than annotation matched caches
- useful abstention where the evidence does not support a conclusion
- sensitivity to association error, which this lane has bounded in theory and never measured
- a cheaper review procedure, measured against an analyst given the same overlap
- a better integration choice under the additive detector loss

Until one of those is demonstrated, an analyst with ordinary overlap gets the same answer at lower
cost, and this lane should say so rather than let the coefficient carry an implied advantage.

## Withdrawn: the wider margin claim

This lane reported that the label free view separated with a **wider** margin than the annotated
view, and treated that as stronger evidence. It is not, because the two views were never at matched
marginals.

| view | nominal target | actual miss fraction | population |
|---|---|---|---|
| annotated | 0.30, 0.40, 0.50 | **0.300, 0.400, 0.500** | 134,565 |
| label free | 0.30, 0.40, 0.50 | **0.238, 0.299, 0.363** | 119,496 / 111,425 / 102,118 |

The threshold was chosen against the union of what any channel captured, and the coefficient was then
evaluated against a smaller per pair universe. **A wider margin across different marginals and
populations establishes nothing.** The claim is withdrawn. An Engine consumer found it; this lane did
not.

The stage a target refers to, the initial and final populations and the threshold selection are now
recorded alongside every row.

## What still stands, with its caveat in the sentence

The label free view reaches the same ordering as the annotated view at two of three operating points.
That remains true. The credit belongs to channel agreement, which ordinary overlap also captures, not
to the coefficient.

And the caveat belongs in the result sentence rather than a later paragraph: **the retained caches
contain only detections matched to annotated objects, so annotation based membership, correspondence
and unmatched detection filtering remain in the inputs. This is a useful ablation conditional on that
association, not an end to end annotation free measurement.**

## Reproduce

```sh
python3 -B tools/measure/overlap_parity.py
python3 -B -m unittest discover -s tools/measure -p 'test_overlap_parity.py'
```

Sixteen tests, exact rational arithmetic, standard library only. The overlap counts are derived from
this lane's own retained recovery counts, whose digest is recorded in the artifact.

## Non-claims

An internal research artifact, retained as `proposed`. Not independent external scientific review,
not an operator acceptance, not a safety, compliance or vendor claim.
