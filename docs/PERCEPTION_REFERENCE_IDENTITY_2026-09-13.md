# Reference names without losing joint interpretations

Document ID: `reiyah.perception-reference-identity.checkpoint`

Version: `0.1.0`

Lifecycle status: `exploratory`; comparison date: 2026-09-13.

Interpretation-local object names no longer prevent a bounded, exact sharing opportunity.
In the selected synthetic example, changing only those names and their faithful source digests
previously changed a finite `[1,1]` result into an open `[-1,1]`. The compiler now recovers `[1,1]`
while retaining all 64 joint worlds and all 192 original source mappings. This is a representation
improvement, not a correction to the reference schema or evidence of a physically true object.

Two attempted implementations lost stronger results under resource limits. Both failures are
retained; the integrated design falls back to the previous sharing plan when broader sharing
cannot fit either evaluator work or geometry. No limits, common interface versions or frozen
protocols changed. Fable's comparator, planner, checkers and research ref were not edited.

## Decision and comparator

The selected previous compiler is `tools/perception_reference.py` at
`61d290bb77dca41b9af0198b3254d2d359e32942`, SHA-256
`acb2fe1e87e08aeb0c448ffab55322f233786e20a4810422bc209be434649e69`.
Every other production dependency is unchanged. Each before/after comparison uses the same
input bytes; the separate stable/renamed comparison changes only local IDs and their
corresponding synthetic source/world digests. Original coordinates independently supply tiny
exhaustive partial-injection matchings and full loss calculations.

The alternative was to require callers to coordinate stable names across worlds. The selected
admission and reference interfaces require uniqueness within an interpretation; they do not give
local object IDs that additional cross-world meaning. Broad partial-subset Boolean sharing was
deferred: it would add conditional representation machinery beyond this demonstrated gap.
The retained [Bryant source review](../research/perception-reference-sharing/0.1.0/sources.json)
provides conventional Boolean-representation context, not a theorem proving this compiler or a
dated state-of-the-art comparison. No novelty or superiority claim is made.

## Why this sharing is exact

For each anchor, an eligible group has the same **ordered, nonempty proposal members**, class,
canonical rational coordinates and timestamp in every declared world. All worlds are validated
first. Within any world, member groups are disjoint, so two distinct objects cannot have that
same member tuple. There is therefore exactly one eligible object per world for this group.

Replace those world-conditional graph nodes with one unconditional node. In each admitted world,
mapping that node back to that world's original object is a bijection. Equal class and coordinates
give exactly the same strict-distance detection edges. This preserves the entire same-class
bipartite graph, hence both maximum one-to-one matchings, object counts and full losses. It also
preserves matching competition. Coincident objects with distinct members remain distinct.
An equal loss or equal edge set alone is insufficient to qualify for sharing.

The joint choice variables, unused-code exclusions, anchor weights, penalties and tolerance are
unchanged. An object that is absent, unresolved, differently grouped, differently classified or
differently positioned in a later world cannot silently become unconditional. Unknown coverage,
timing and inspection states retain their existing open behavior.

Every original local ID, member tuple and record digest remains in the compilation mapping.
Its interpretation requires **world + anchor + object**, as established by the
[matching-source trace](PERCEPTION_MATCHING_TRACE_2026-09-13.md). A reused local name or shared
graph ID alone is not a source identity. The checked common-operand path retains the admission
bytes, world encodings and mapping rows. The retained two-world synthetic example still encloses
`[-1,1]`, with no assistance released and no human judgment claimed.

## Resource behavior and retained failures

For a proposed plan let `n_a` be its distinct graph-node count, `s_a` its shared count,
`d_a` its prediction count and `k` the number of joint choice bits. The existing evaluator bound
adds, for each potentially finite anchor,

```text
k*(n_a-s_a) + 4*(d_a+1)*(n_a + min(2048, d_a*n_a) + 1).
```

Together with the model/clause term and `2^k` assignments, this must fit the declared core work
limit. Compiled edges have empty conditions; object guards carry their activation. This is a
bound on that evaluator estimate, not on measured wall time or memory.

The new expanded plan also requires

```text
sum_a d_a * min(128, n_a) <= 2,000,000.
```

This sum includes ultimately open anchors and anchors with unavailable prediction roles: they
can still consume geometry during emission. Anchors with already established open reasons consume
none and are omitted. At most 128 nodes per anchor reach geometry evaluation; early edge
exhaustion only reduces this cost. Thus the sum conservatively bounds actual geometry work.

If either preflight fails, try the previous same-name sharing plan with its original evaluator
guard, then ordinary world nodes. Geometry is materialized once. This deliberately preserves
legacy fallback behavior, including its limits; it does not promise complete name invariance or
finite evaluation of every sparse model that might theoretically fit.

| Selected synthetic control | Previous compiler | Failed candidate | Final compiler |
|---|---|---|---|
| 64 worlds, three invariant objects, stable names | `[1,1]`, 3 nodes, 6 geometry pairs | No failed result | Same compiled input, compilation receipt and decision packet bytes |
| Same operands, local names differ by world | `[-1,1]`, open, 256 pairs | No failed result | `[1,1]`, 3 nodes, 6 pairs; 192 original mappings |
| Heavy newly shared anchor plus small stable anchor | `[0,1]`, 2,199 pairs | Discarding all sharing after work failure gave `[-1,1]` | Exact previous output bytes |
| 31 heavy open anchors plus a small final anchor | `[-15/16,1]`, 747,445 pairs | Work-only guard used 1,999,678 pairs but retained the result | Exact previous compiled/decision bytes; receipt differs only in compiler source digest |
| Same heavy anchors, larger valid final graph | `[-15/16,1]`, 748,575 pairs | Work-only guard used 1,999,998 pairs and lost the final anchor: `[-1,1]` | Exact previous compiled/decision bytes; receipt differs only in compiler source digest |

The first geometry control was an honest negative result, not a reproduced loss of the final
anchor. The second established that failure within all four compiler file caps. Its three worlds
and 4,311 mapping rows remain present. Directly, each heavy anchor has three maximum matches for
both configurations and delta `-1`; the last has eight/nine matches and delta `+1`. Equal weights
give `(-31+1)/32 = -15/16`. The open compiler enclosure is appropriately wider. Hundreds of
coincident synthetic predictions stress computation; they do not model plausible traffic.

## Validation, cost and next falsifier

The final production source passed **399 repository tests**, eight added here. Tests retain
adverse late worlds, coincident distinct objects, reused local names, joint-anchor constraints,
common provenance and both actual resource failures. The original 125 tiny world-pattern controls
and earlier failures remain. The old “different local ID prevents sharing” assertion was a
conservative representation policy and was deliberately replaced by stronger graph/provenance
checks; no input rejection or physical-evidence requirement was weakened.

The full suite took 59.222 seconds under the retained Python 3.14.2 runtime, with macOS child
maximum RSS 289,505,280 bytes. Four existing SQLite `ResourceWarning`s remain in the transcript;
passing tests do not establish absence of resource leaks. The **93 measurement tests** are retained
from their previous run with 107 source bindings rechecked, not replayed or added to 399.

Separate one-run captures put the final small renamed replay at 0.187 seconds / 39,043,072 bytes
RSS, and the final large geometry control at 3.819 seconds / 148,815,872 bytes. These include
parsing, compilation and checking; concurrent execution and single observations do not establish
a latency ranking. Preparation, failed prototypes, repairs and verification are retained in the
private checkpoint. No participant effort, total human-effort advantage or physical accuracy
has been measured. [Verification identities](../research/perception-reference-identity/0.1.0/verification.json)
and the [offline reproduction](../research/perception-reference-identity/0.1.0/README.md) make the
bounded engineering result reviewable.

The next compiler falsifier is an admitted model whose per-world graph or source join changes
under eligible local renaming, or a budget-valid counterexample that loses an earlier usable
anchor. An actual supported viewing/selection return takes priority over further representation
work. The real comparison remains **[-8,8]**, human references and participant usability remain
missing, external scientific review remains missing, and Gate A remains unaccepted.
