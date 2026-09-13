# Check original worlds before trusting a shared reference graph

Document ID: `reiyah.engine.partition-conformance`

Version: `0.1.0`

Lifecycle status: `exploratory`

The current reference compiler preserves the declared source identities, complete active graphs,
maximum matching and joint loss in **5,400 bounded synthetic cases**. The final audit checks
**42,000 active original edges** and **53,280 original source mappings**. Two complete runs
produce identical output. No compiler repair is justified by this result.

The changed engineering decision is what a conformance check must establish. A valid core
certificate and an unchanged loss are insufficient: the audit must also preserve original
weights, tolerance, prediction roles, source context, ordered member records and the invariant
identity of a shared node. Deliberate faults exposed two weaknesses in the new audit before
those premises were enforced. Neither weakness was a defect in the selected compiler or a
newly discovered Fable defect.

## Bounded question and conventional comparison

The [member-equivalence compiler](PERCEPTION_REFERENCE_EQUIVALENCE_2026-09-13.md) shares an
object across worlds when its proposal-member set, class, timestamp and exact point agree.
Local object names and original list order remain in provenance. Individual tests cover
selected splits, merges and budget fallbacks. This audit asks whether their interactions
preserve the complete declared matching problem over all pairs of four-proposal partitions
within a small, explicit geometry and encoding grid.

Each case has two anchors and two jointly coupled worlds. World one uses partition A at the
first anchor and B at the second; world two uses B then A. Both anchors retain the same base
detection at x=0 and the added detection at x=3. The existing normalizer keeps the addition.
All points have y=0, nominal ego is (0,0), and reference timestamps equal their anchor times.

| Dimension | Declared choices |
|---|---|
| Partitions A and B | Each of the 15 set partitions of proposals 0,1,2,3; all 225 ordered pairs |
| Geometry of a block S | x=3/2; x=3*(min(S) mod 2); or x=4*min(S)-2 |
| Class rule | All car; or truck when sum(S) is odd, car otherwise |
| Source encoding | Member-derived names and ordered members; or reused local object indices with reversed members in the second world |
| Anchor weights | (1/2,1/2) or (1/3,2/3) |

The product is 15*15*3*2*2*2 = 5,400 cases. Both miss and false-detection penalties are 1,
tolerance is 1/10, and the Engine's existing same-class strict squared-distance threshold is 4.
The boundary geometry includes exact distance-2 exclusions. All generated objects are within
the declared 50 m range and have explicit point geometry. This grid is exhaustive only over
these choices. It is not exhaustive over coordinates, class assignments, timestamps, all world
counts, resource boundaries, physical ambiguities or pipeline error operations.

The serious conventional comparison constructs each original world's ordinary bipartite graph
directly from its source coordinates and enumerates partial injections to find both maximum
matching sizes. It uses no shared nodes or compiler edge construction. Source equality and
the matching problem are checked; no advantage over a competent analyst doing the same exact
calculation is claimed. These partitions do not assign a cost, likelihood or physical validity
to splits, merges or correspondence repairs. Fable retains that separate research work.

## What is checked and why it suffices within the grid

For each world and anchor, the original source body must match its digest, local object,
world and anchor. Every original object has exactly one active graph node through its mapping,
and every active node has one original object. Original member lists and record digests are
compared exactly. Whenever the same graph node appears in multiple worlds, its member set,
class, timestamp and exact coordinate signature must agree.

Every active edge is then compared with the original same-class distance calculation, including
its absence where the distance is exactly 2. A bijection preserving all edges transports every
matching in either direction without changing its size. Direct partial-injection enumeration
checks those sizes against the produced proof for both base and augmented predictions.
Original prediction roles, weights, loss, tolerance and other unchanged operands are checked
explicitly, and expected loss is calculated from the original operands.

For each anchor, the audit computes both full losses and separately checks
`delta = (a+b)*(TP_augmented-TP_base) - b*r`. The weighted total uses the same joint world across
both anchors. Its minimum and maximum must equal the checked packet's enclosure. The canonical
input digest must remain unchanged, and physical coverage remains unestablished.
The separate core checker runs with the producer's matching-certificate function disabled.
That check validates the compiled packet; the original-world audit supplies the additional
source-equivalence obligations. Neither validates physical reference truth.

The partition enumeration itself is checked through a different construction: all 256 label
words on four positions, normalized to sets of nonempty blocks, produce the same 15 partitions.
No new matching method, benchmark performance, novelty or state-of-the-art claim is proposed;
this is a finite check of the existing Engine contract and its elementary graph-bijection
argument. Shared trusted code is named in the reproduction README and verification record.

## Failed controls and corrections

The first auditor used the compiled weights to calculate expected loss. A forged packet changed
the original equal weights to (1/3,2/3), retained a valid core certificate and passed that audit.
The control's enclosure remained [1,1], so comparing that number alone could not detect the
changed estimand. The correction checks all original non-reference anchor operands and uses
the original weights and prediction roles for its independent calculation. Tolerance rewriting
is rejected even when the loss is unchanged.

The next control forcibly shared nodes across different member partitions that happened to
have identical matching graphs. The core certificate, full edge comparison and loss all passed.
The strengthened audit now rejects that representation because a shared node's declared member
identity changes across worlds. Equal edges do not establish the selected sharing premise.

A new joint-coupling test also initially assumed that the last partition in lexical order was
the fully merged group. It was a two-block partition. The failed transcript is retained, and
the corrected test selects the explicit partition by its member content. The partition generator
and compiler were unchanged. All three first failures and their exact source versions remain
in the private checkpoint and sealed exchange.

The final eight targeted checks also reject a missing edge that leaves matching size and loss
unchanged, and a rewritten member order. An unknown joint-coverage control remains open with
[-1,1]; it does not become an empty reference or a finite observation. All 5,400 current cases
then pass the strengthened audit twice, with the same 3,753,153-byte output, SHA-256
`43029aaf31d9184923df9b01ff42977885959fd8cb376891bd7167813841a542`.

## Reproduction, costs and next falsifier

The [reproduction](../research/perception-partition-conformance/0.1.0/README.md) emits a recipe and
exact input, source-body, compiled-graph, compilation-receipt, checked-packet and original-graph
digest for every case. Any indexed case can be expanded into its full original operands and
outputs. Eight complete examples are additionally retained for inspection; the complete grid
is not replaced by those examples. Their selection is a synthetic audit convenience, not a
physical-study cohort or seed selection.

The initial 48-case cost pilot took 0.382 reported seconds. The two final runs took 18.163 and
18.200 reported seconds, with maximum reported child RSS of 43,024,384 and 42,500,096 bytes.
The final eight controls took 0.186 seconds. These are local supervisor observations, not
human effort or a controlled algorithm-performance comparison. The earlier incomplete auditors,
failed controls, first complete run and preparation costs remain in
[verification](../research/perception-partition-conformance/0.1.0/verification.json).

No Engine runtime, compiler, common interface, admission, viewer, Fable source or frozen protocol
changed. The 404 repository and 93 measurement tests remain retained against unchanged source;
the prior eight command-accounting checks are also retained. No broad suite is counted as a
fresh replay here. Gate A remains unaccepted.

The next falsifier is a valid original-world mapping that this audit accepts despite a changed
active edge, shared-node signature, source record, prediction role, tolerance, weight or joint
loss. Passing this bounded grid cannot rule out failures outside it. A real reviewer return
still takes priority: the actual comparison remains **[-8,8]**, with no admitted human
references, actual participant usability or external scientific review. A read-only browser
discovery at 15:16:35 UTC still returned no available browser. No interactive observation was
created. P005 is operator-reported published; no further post or outreach is authorized.
