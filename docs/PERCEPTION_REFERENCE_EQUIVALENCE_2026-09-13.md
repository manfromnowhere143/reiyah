# Preserve source order without paying for it in every world

Document ID: `reiyah.engine.reference-equivalence`

Version: `0.1.0`

Lifecycle status: `exploratory`

Permuting an object's proposal members no longer prevents otherwise identical all-world graph
nodes from being shared. In the bounded synthetic control, the previous compiler returned an
open **[-1,1]** result after this harmless ordering change; the candidate retains the finite
**[1,1]** result, all 64 joint worlds and all 192 original source mappings. Original member
order and record digests remain unchanged in each mapping and in the common admission packet.

This is an Engine representation improvement. The real comparison remains **[-8,8]**, with no
admitted human reference, participant usability result or external scientific review. Gate A
remains unaccepted. No Fable source, planner, checker, error model or interface was changed.

## Why the change is justified

[Admission](../tools/perception_admission.py) treats proposal members as a complete partition:
each member is accounted for once within each window and world. A member has no association role
defined by its list position. The reference compiler already rejects duplicate members and
overlapping groups, but its previous sharing key included member order. Six permutations of
the same three members therefore prevented sharing across 64 otherwise identical worlds.

The new [compiler](../tools/perception_reference.py) sorts only the internal group lookup key.
It leaves original objects, member arrays, record hashes and world encodings intact. It still
requires identical class, anchor time and canonical point coordinates in every admitted world.
Equal losses, coincident points with different members, or equal current edge sets are insufficient.

For each finite world, a nonempty member set occurs in at most one object because groups are
disjoint. A shared set therefore has exactly one corresponding original object in that world.
Class, time and point equality give identical same-class strict-distance edges to every retained
detection. Replacing that right-hand graph vertex is a bijection preserving the complete bipartite
graph, both maximum matching values, all unmatched detections and the additive loss. The shared
cohort-wide choice still selects the same complete joint world across all anchors. This argument
is conditional on the supplied interpretations; it does not establish their physical correctness.

Broader sharing can make a previously open graph fit and thereby increase evaluator work or the
geometry consumed before later anchors. The new plan uses the existing evaluator and geometry
guards. If it cannot fit, the compiler retains the previous ordered-member plan, then the older
ordered-member/same-name plan, before ordinary world-specific nodes. Geometry is materialized once.
No numerical, byte, world, matching, geometry or interface limit was raised.

## Dated controls and costs

The 13 September comparison selects previous main `2048e3e0dd10eaaed2849aace9e0039ddd654e09`,
compiler SHA-256 `5ad8b6e0e860fe514b04f76db8f11f7453eb63e5b9585b6b186407173eac7b55`.
Both methods receive the same normalized operands, source references, joint assumptions and budgets.

| Synthetic control | Previous compiler | Candidate |
|---|---|---|
| Identical source member order | Finite [1,1], three nodes, six geometry comparisons | Byte-identical compiled input, receipt and checked result |
| Permuted source member order | Open [-1,1], 256 geometry comparisons | Finite [1,1], three nodes, six comparisons; 192 source mappings retained |
| New sharing exceeds the evaluator budget | Mixed [0,1], with one finite anchor | Exact prior compiled, receipt and checked result bytes retained |
| Same budget case with the previous plan removed | Counterfactual [-1,1] loses that finite anchor | Counterfactual source and failure remain retained |

Tiny original-coordinate partial injections independently check every world, full graph edges,
matching competition, ordered source mappings and losses. An adverse last world remains adverse.
A split association changes the matching problem rather than being merged by coincident geometry.
The dense budget case uses a separate core checker and exact prior output identities; its
128-object anchor is not claimed to have an independently brute-forced matching calculation.

The complete repository suite passed **404 tests**, including five additions, in 62.136 seconds
with maximum child RSS 298,909,696 bytes and no resource warnings. The **93 measurement tests**
remain retained, with all 107 bound files rechecked; they were not replayed. The small baseline
and candidate probes took 0.258 and 0.270 seconds. This is no latency advantage claim. Sorting
at most 32 members adds bounded metadata work, and retaining the prior plan adds a second common
group map. The budget probe took 1.572 seconds while the repository suite was running.

A complete synthetic source-to-admission-to-common example retains four ordered source mappings
across two worlds and two anchors, with one shared node per anchor and direct losses [-1,-1].
Both common packets are byte-identical. Rehashing a rewritten source-member order is rejected
as `REVIEWED_PACKET`, even though the set geometry and loss are unchanged. No assistance is
released and no synthetic reviewer is presented as a human participant. This exercise took
1.414 seconds. The [standalone replay](../research/perception-reference-equivalence/0.1.0/README.md)
produced identical 4,145-byte output twice; the concurrent runs took 0.827 and 0.829 seconds.

## Preserved failures and next falsifier

The first proposal also considered unreduced rational spellings. The probe showed that the
shared parser already rejects them with `INVALID_RATIONAL`; numerical canonicalization was
withdrawn. That failure and an explicit rejection control remain retained. A new split-association
test initially placed the camera detection on the base detection, so established suppression
removed the addition and both losses were zero. The corrected fixture retains detections at 0
and 3 and reference point(s) at 3/2. The failed source and 39-test transcript remain; suppression
and the expected mathematical criterion were not weakened.

The old member-order non-sharing assertion described the previous conservative policy. Its exact
source is retained; the new tests replace that restriction with full original-world and source
preservation checks. All prior budget, unknown-state and malformed-source controls still pass.
[Verification](../research/perception-reference-equivalence/0.1.0/verification.json) binds sources,
outputs, failures and costs. The private packet is `~/.codex/reports/reiyah/engine-reference-equivalence-2026-09-13/`.

The next falsifier is a permitted member permutation that changes an active original-world graph,
drops or rewrites a source mapping, narrows away an adverse alternative, or loses a finite result
despite an available prior fallback. The finite resource scope still permits open outcomes; this
is not a promise that every finite reference input will fit. Actual reviewer effort and physical
reference validity remain missing. No new algorithmic, novelty or state-of-the-art claim is made.
