# Exact acquisition-objective audit, 0.1.0

Status: exploratory authored mathematical counterexample. This is a baseline
qualification step, not a Reiyah statistical estimator or empirical benchmark.

Let d_i be the vector of all unordered pairwise model-loss differences at test
point i. At the first query of a finite pool of size N, a sampled point J with
positive probability q_J produces the unbiased pair-vector estimate d_J/(Nq_J).
Its sum of component variances is

V(q) = [sum_i ||d_i||_2^2/q_i - ||sum_i d_i||_2^2] / N^2.

The second term does not depend on the query distribution. Cauchy-Schwarz gives
sum_i a_i/q_i >= (sum_i sqrt(a_i))^2 for a_i=||d_i||_2^2 and sum q_i=1.
For positive a_i equality requires q_i proportional to sqrt(a_i). If every
a_i is zero the objective is zero for every distribution. This is a standard
constrained-variance calculation, not a novel algorithm claimed for Reiyah.

Replacing ||d_i||_2 by ||d_i||_1 changes the objective in general. The frozen
question uses two test points and four fixed candidate models with zero-one
loss rows [0,0,0,1] and [0,0,1,1]. Both rows are realizable by binary predictions
with true label0. Directly enumerate J=0 and J=1 and calculate each of the six
pair estimates, its exact mean and its exact variance. No Monte Carlo estimate,
uncertainty threshold or fitted observation is involved.

The challenger distribution (7/15,8/15) was fixed before execution. A strictly
lower exact V than the published rule disproves that universal optimum claim
for the stated objective. It does not prove better model-selection accuracy,
fewer human labels, robust deployment performance or a defect in reported
empirical results. Two-model and equal-spread controls retain cases where the
published ideal rule and the classical optimum agree.

The author query source is pinned and kept private. Numba is absent. Only two
named function bodies are extracted with Python AST; JIT decorators are removed
and prange executes serially. Original function bodies, including the default
0.01 query smoothing, are unchanged. This is explicitly an uncompiled mechanism
reproduction on authored arrays. It is not the original native program or any
published experiment. The paper's ideal formula is the exact mathematical
reference; the source estimator's1e-8 guard is not silently substituted for it.

The separate reference enumerates the finite probability space without calling
the closed-form objective. The checker validates the actual records, expected
means, variance sums, source-policy values, classical stationarity, control
equalities and mutations. Same author and Fraction/NumPy dependencies are shared;
this is not independent replication. No claim of new Reiyah advantage follows.

Source qualification relies on the complete retained publisher HTML. Local
PDF capture and rendering failed under the body limit and remain discoverable.
No complete or visually inspected PDF is claimed. Third-party payloads stay
private. The original question, code, source and runtime freeze must remain
unchanged after execution. Failures count against the same resource budget.
