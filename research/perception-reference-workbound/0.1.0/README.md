# Reference work-bound audit, 0.1.0

The suspected missing edge-literal cost is not a defect in the selected compiler. Its edges
have empty conditions; their objects' guards control whether they participate. The existing
preflight bounds the unchanged evaluator estimate. No production correction is warranted.

Let `b` be the number of choice variables, `V = 2^b` the enumerated Boolean assignments,
`O` the proposed shared representation's object count, `S` its all-world objects, and `D`
the retained detection count for one anchor. The existing preflight uses

```text
V * [1 + b + sum(clause lengths)
     + sum_over_potentially_finite_anchors(
         b*(O-S) + 4*(D+1)*(O + min(2048,D*O) + 1))].
```

Every nonshared object's condition has `b` literals; each shared object's condition is empty.
Every emitted edge's condition is empty. A finite graph has at most `min(2048,D*O)` edges.
Substituting that edge bound into the evaluator's exact work formula gives the preflight term.
An anchor already known to be open contributes no finite matching work. An anchor that later
hits the geometry or graph limit also becomes open and removes a nonnegative term. Skipping
proposed object counts above 128 is sound because those anchors cannot be emitted finite.
Unused Boolean encodings remain in the same clauses and are charged by the same header term.

This proves a bound on the selected evaluator's **declared work estimate**, not on wall time,
memory or all implementation costs. It depends on the compiler emitting unconditional edges.
If a future representation adds edge literals, the estimate must account for them; that is a
change obligation, not evidence of a current bug. Source and evaluator identities are retained.

The adversarial example has 64 joint worlds and two equally weighted anchors. On the first,
six base predictions and one addition connect to every active reference object. `S` objects
are invariant; one further object's exact position varies by world. On the second, one
addition has no edge. Direct coordinate checks establish a complete bipartite graph and an
empty graph, respectively. Distinct-object injections attain the detection-count upper bounds:
base/augmented matches are 6/7 and 0/0, so unit FN/FP penalties give deltas +1/-1 and a joint
weighted value of zero in every world. This dense construction is a computational fixture,
not a claim about physically plausible traffic or independently observed reference objects.

| Invariant objects S | Preflight for sharing | Actual selected work | Result |
| --- | ---: | ---: | --- |
| 46 | 1,830,848 | 1,830,336 | finite [0,0] |
| 56 | 1,994,688 | 1,994,176 | finite [0,0] |
| 57 | 2,011,072 | 58,304 | sharing declined; mixed [-1,0] |

The limit stays 2,000,000. At 57 objects, current compiled input, compilation receipt and
checked packet equal the pre-sharing compiler's artifacts byte for byte on the same inputs.
All 64 worlds and per-world source mappings remain. The lost precision at this declared
resource boundary is computational; it does not imply that learning correct information
weakens a universally valid claim under a fixed uncertainty model.

One new regression runs the adjacent 56/57 cases through compilation and the separate core
checker. It verifies finite matching counts, exact bounds, retained world/mapping populations
and the mixed fallback. Run it without changing limits:

```text
python -B -m unittest tests.test_perception_reference_sharing.ReferenceSharingTests.test_dense_graph_at_adjacent_sharing_budget_boundary -v
```

The private immutable checkpoint retains the initial failed suspicion, source selections,
all original inputs, direct coordinate checks, current/baseline outputs and measured process
costs. The rejected hypothesis remains discoverable. The [verification record](verification.json)
and [checkpoint](../../../docs/PERCEPTION_REFERENCE_WORKBOUND_2026-09-13.md) distinguish fresh
391-test execution from the retained 93 measurement tests. No human review occurred.

Real bounds remain [-8,8]. Human references, actual participant usability and external
scientific review are missing. Gate A is unaccepted. This audit establishes no state-of-the-art,
physical-safety, human-effort or performance claim.
