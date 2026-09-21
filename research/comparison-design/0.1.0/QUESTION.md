# Frozen baseline question, 0.1.0

Status: exploratory mathematical audit selected after reading a published
derivation. This is authored counterexample research, not blinded empirical
model evaluation and not an advantage test won by Reiyah.

Decision: can the general-K acquisition rule in Hara et al. (Machine Learning
113, 2024, DOI10.1007/s10994-024-06603-1), equations9-11/Theorem2, be used as an
exact minimizer of its stated sum of pairwise conditional variances?

The retained publisher HTML explicitly uses the sum of absolute pairwise loss
differences. Its source is384,640bytes, SHA256
6f8ba20beb35046041670cc69449e26c808c503175f98eaca63a1f0c168fc5df.
The same expression appears in the web service's extracted PDF text. A complete
local PDF was not retained: the1,500,000byte per-body ceiling stopped capture
at1,500,001bytes. The failed prefix remains unchanged. Attempted local rendering
of page7 failed; no visual PDF inspection is claimed. Do not raise limits or
hide that failure. The full HTML remains the qualified source for this audit.

Pinned author repository:33f6fab5f50d470bc2957a3ed1c4e86d94d82f5d,
tree d8b08487dbe63ee29b24564795b4630b03915a28, commit3August2024.
Its query implementation also sums absolute pairwise differences, then adds
eps=0.01 before normalization. Distinguish that practical rule, its surrogate
label distribution, and the ideal oracle theorem. Retain the MIT license;
all original code can remain private. Do not train or run paper datasets/models.

## Frozen counterexample

N=2 test points, K=4 fixed candidate models, one queried label (m=M=1).
The complete authored zero-one loss rows, indexed by test point, are:

- [0,0,0,1]
- [0,0,1,1]

Both are realizable with binary labels0 and deterministic binary predictions
equal to the loss entries. All six unordered model pairs count equally.

For each sampled index J with positive probability q_J, compute the paper's
first-step estimator for every pair directly as Delta_J/(2*q_J).
Enumerate both possible J values, compute its exact expectation and variance,
then sum the six variances. This direct finite probability calculation must
not invoke the proposed acquisition objective as its reference.

Compare these fixed distributions:
- Paper ideal sum-absolute rule q=(3/7,4/7).
- Feasible rational challenger q=(7/15,8/15).
- Uniform q=(1/2,1/2).
- Classical constrained optimum q_i proportional to sqrt(sum_pairs Delta_i²);
  approximate square roots only for display; the rational challenger suffices
  to disprove universal optimality if its exactly computed variance is lower.
- Released query mechanism with eps=0 and its default eps=0.01 under a
  point-mass surrogate at the known authored label. Treat this as an oracle
  mechanism check, not a deployable acquisition policy with unavailable labels.

Pre-execution analytic reasoning predicts a discrepancy for K=4. Record that
prior reasoning; no pretense of outcome blinding. A contradictory computation,
source mismatch or objective mismatch invalidates the proposed diagnosis.

## Controls and scope

Use small authored controls for the K=2 equality case, K=3 binary disagreement,
K=4 equal disagreement counts, all-equal losses, invalid/zero query probability,
and invariance to a permutation of model identities and test-point identities.
Check the general objective using Cauchy-Schwarz/Lagrange reasoning separately
from finite enumeration. No large benchmark, random search or tuned sweep.

Verify the actual query code only if its current dependencies are available.
If Numba is absent, do not install it or claim native execution. An explicitly
labelled AST extraction without JIT decorators, with serial prange, can check
the unchanged function body on these tiny arrays. Keep that narrower execution
claim separate from the published compiled program. The LURE implementation's
denominator guard1e-8 is not the exact ideal formula and must not be silently
used as the mathematical reference.

No claims about the paper's empirical results, data quality, motives, overall
method usefulness or model-selection error follow from this finite audit.
No outreach, issue filing or author contact. No new Reiyah novelty or
comparative advantage follows from correcting a baseline's stated optimum.

## Broader Reiyah decision

Paired active comparison is established prior art; do not claim that idea as
new. Complete-world matching certificates remain conditional on admitted
reference models. Current perception implementation enumerates at most4096
assignments and otherwise uses a coarse enclosure; a small exhaustive reference
script is not a scalable solver or physical evidence.

Before a larger build, state a narrower candidate contribution and a competent
baseline with equal information and the same guarantee. Distinguish universal
finite-domain certificates from statistical estimators; neither may win by
receiving easier evidence or a weaker criterion. Preserve the completed-map
three-supported/one-blocked parity result and all previous negative findings.

No reserved images, inference, new dependencies, private records, deployment or
physical control. New source/derived cap3MiB, owned artifact cap128MiB, free floor
5GiB; failures count. The next implementation/source/runtime freeze must precede
executed mathematical outcomes. Continue Reiyah SOLO.

