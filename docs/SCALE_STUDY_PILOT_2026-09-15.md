# Scale study pilot: the method agrees, and my own measure is close to tautological

Document ID: `reiyah.scale-study.pilot.2026-09-15`

Version: `0.1.0`

Lifecycle status: `proposed`

Date: 2026-09-15. Lane: independent research.

Protocol frozen before any outcome at
`4c601ca94bc1e34e155fda0b16a7e45d660c5084e913f5630938224b74686368`, including the pilot selection
rule. Artifacts: [`research/scale-study/0.1.0/PROTOCOL.json`](../research/scale-study/0.1.0/PROTOCOL.json),
[`pilot.json`](../research/scale-study/0.1.0/pilot.json),
[`ratio-limit.json`](../research/scale-study/0.1.0/ratio-limit.json),
[`independent-rematching-check.txt`](../research/scale-study/0.1.0/independent-rematching-check.txt)

## The census, rebuilt here

| quantity | value |
|---|---:|
| frames, from the tokens all submissions share, joined to the original tables | 6,019 |
| scenes | 150 |
| tokens failing to join | 0 |
| census annotations | 192,041 |
| included under the common 50 m rule | 148,440 |
| excluded beyond 50 m | 39,088 |
| excluded, category not in the detection map | 4,513 |
| frames with zero qualifying annotations, retained as declared empty | 47 |

The 148,440 figure is not the 134,565 row cache. That cache uses a class dependent range and this
study uses the common 50 m rule, exactly as the protocol required them to be kept apart.

## The first falsifier did not fire

The declared first falsifier was that the pilot disagrees with complete ordinary rematching. A
second implementation was written from the protocol with its own qualification, its own edge
construction and its own matcher, importing nothing from the study module.

**20 of 20 units agree exactly**, as rationals, including the ten adverse ones.

## The pilot

Five scenes at census index 0, 30, 60, 90 and 120, and four ordered pairs at index 0, 5, 10 and 15,
all fixed by the published rule before running. 20 units, 22 seconds.

| status | units |
|---|---:|
| unsupported baseline | 10 |
| certified at the arithmetic floor | 10 |
| certified above the floor | 0 |
| unresolved or budget exhausted | 0 |

**Half the comparisons do not clear the tolerance at all.** Those ten are adverse results for the
addition and are retained as first class outcomes, not filtered out.

One pilot scene, `scene-0096`, contains frames already exposed in the first two case studies. The
selection rule was published before the scenes were known and has not been adjusted to avoid the
overlap; the overlap is recorded instead.

## The finding that matters, and it is against my own measure

Every resolved unit sits at its floor. Twelve of twelve now, counting the two earlier cases. I
presented that replication as a result. The algebra says it is close to a tautology.

With unit penalties and equal frame weights over `F` frames, writing `g_f` for the gain, `r_f` for
the retained additions, `G = sum g_f` and `R = sum r_f`:

```text
D * F   = 2G - R
k_floor = ceil( (D - t) * F / 2 ) = ceil( (2G - R - tF) / 2 )
```

so `k_floor <= G` whenever `R + tF >= 0`, which is always. Each deletion removes at most one unit
of gain, and there is always at least as much removable gain as the floor requires. **The floor is
therefore always reachable in principle on this family.** A ratio above one needs reassignment to
block every remaining single unit removal before the chain reaches the floor, which is a structural
accident rather than the normal case.

So observing a ratio of one, twelve times, restates the arithmetic more than it reports on the
annotations. The headline is qualified in the register rather than withdrawn: the replication is
real, and it is close to constant by construction.

**What carries information instead is the absolute count.**

| scene | pair | k | annotations | k / annotations |
|---|---|---:|---:|---:|
| scene-0558 | fcos3d + mapillary | 3 | 910 | 0.0033 |
| scene-0558 | mapillary + megvii | 3 | 910 | 0.0033 |
| scene-0555 | megvii + pointpillars | 18 | 1,665 | 0.0108 |
| scene-0101 | mapillary + megvii | 49 | 2,299 | 0.0213 |
| scene-0966 | mapillary + megvii | 54 | 1,859 | 0.0290 |
| scene-0555 | mapillary + megvii | 56 | 1,665 | 0.0336 |
| scene-0096 | mapillary + megvii | 69 | 1,688 | 0.0409 |
| scene-0966 | fcos3d + mapillary | 76 | 1,859 | 0.0409 |
| scene-0555 | fcos3d + mapillary | 139 | 1,665 | 0.0835 |
| scene-0096 | fcos3d + mapillary | 150 | 1,688 | 0.0889 |

Two decisions with the same ratio need 3 corrections or 150. That is a factor of fifty in what a
validation lead would have to check, and the ratio hides all of it. The earlier two case studies,
at 1 and 2 deletions, sit at the extreme fragile end of this spread and were presented without it.

## A defect in my own search, found and repaired here

The first pilot run returned five units as `bounded_only`. The cause was mine: the witness was
built by summing single deletion gain losses, and losses inside one frame are not additive, because
the second deletion can be absorbed by a reassignment the first opened. Deletions in *different*
frames are exactly independent, since the matching is per frame, but that does not license the sum
within a frame.

The witness is now grown one deletion at a time with the gain reverified after each, never summed.
All five resolved, and every witness is checked by full recomputation before it is reported.

## What is not claimed

No annotation is asserted to be wrong. A count of hypothetical deletions is not an error rate. Five
scenes and four pairs are not a sample of anything: the units share scenes, objects and detectors,
and the 20 ordered pairs reuse five submissions. This is the Engine additive loss, not official mAP
or NDS. Nothing here speaks to human effort, deployment practice, customer value or novelty.

## Next

The declared census of up to 3,000 units, with every stopping outcome retained and the absolute and
normalised counts reported beside the ratio. The open question the pilot sharpens: does any unit in
the full census reach a ratio above one? A census with none is a negative result and will be
reported as one.
