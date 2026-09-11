# Which uncertainty changes the comparison?

Document ID: `reiyah.perception-decision-review.examples`

Version: `0.1.0`

Lifecycle status: `exploratory`

These synthetic examples distinguish uncertainty that cancels from uncertainty that changes
maximum matching. They expose a failure of reasoning, not a newly discovered physical effect.
The [calculation](reproduce.py) uses only the Python standard library and imports no Engine
code. Its exhaustive reachable-object-subset search is deliberately different from the
Engine's augmenting-path producer and matching/vertex-cover checker.

Run from the repository root:

```sh
python3 -B research/perception-decision-review/0.1.0/reproduce.py
```

The single JSON line should match [expected.json](expected.json). Its SHA-256 is
`62d159ba5255046fcb5d04b21abfbd64fe96550acda747e7be3aafce51a0594f`.
All objects have the same class. Eligibility is strict center distance <2 m; loss is
miss count plus false-detection count. Positive delta favors the augmented configuration.

| Constructed question | Exact answer | Why it matters |
|---|---|---|
| Base at 0, addition at 3, known object at 1.5, disputed object at -1 | Delta is -1 if disputed object absent, +1 if present | A real object near the candidate does not settle the candidate's incremental value |
| Eight disjoint copies at each of two half-weight anchors; all sixteen candidate objects confirmed | [-8,8] remains possible | Counting candidate confirmations alone gives no guaranteed review budget |
| Base at 0, addition at 3, known objects at 0 and 3, disputed object at 10 | Paired delta [1,1]; subtracting separate loss ranges gives [0,2] | An unreachable object's contribution cancels only when the comparison keeps the same world |
| Two half-weight copies of the first example, with disputed presence constrained to be opposite | Joint delta [0,0]; separate anchor relaxation [-1,1] | Cross-anchor constraints must survive aggregation |

In the first example, both detections can match the known object. When the disputed object
exists, only the base can match it. Maximum matching then reallocates the base and lets the
addition supply an extra match. The candidate-to-object edges are identical in both worlds.
The uncertainty lies near the base, yet it changes the value of the addition.

The sixteen-object case repeats this geometry at offsets 0, 6, ..., 42 m. All coordinates
remain within the declared 50 m range and every addition survives the strict suppression rule.
The two supplied joint worlds make every disputed base neighbor absent or present. These two
worlds are enough to attain both count-bound endpoints. They are not reference interpretations
admitted for the actual development data, which have 9 and 7 additions rather than 8 and 8.

The script also checks all 512 labelled graphs with two base detections, one addition and three
objects, using six nonnegative penalty pairs including zero-penalty boundaries. It computes
absolute losses and the paired identity separately in 3,072 comparisons. This finite control
does not replace the general proof in the [architecture](../../../docs/PERCEPTION_DECISION_ARCHITECTURE_2026-09-09.md).
The exhaustive implementation is suitable only for these bounded small examples.

The current Engine and separate certificate checker were also exercised on the matching trap,
sixteen-object extension and unreachable-object case during the
[bounded review](../../../docs/ENGINE_CREDIBILITY_REVIEW_2026-09-11.md). Agreement is an internal
computational check. It does not establish physical truth, external review, general solver
scalability or novelty over conventional matching and paired analysis.

For a normal Engine packet, use the original
[matching-ambiguity input](../../perception-decision/0.1.0/matching-ambiguity.json) and
[run/verify commands](../../perception-decision/0.1.0/README.md). The standalone reference
calculation above deliberately has no detector input loader, review-record writer or admission
authority. It cannot turn this illustration into human evidence.
