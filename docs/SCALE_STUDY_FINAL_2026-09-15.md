# The census, finished: every supported decision sits exactly at its floor, and that is not a tautology

Document ID: `reiyah.scale-study.final.2026-09-15`

Version: `0.1.0`

Lifecycle status: `proposed`

Date: 2026-09-15. Lane: independent research.

Supersedes the conclusions of [`SCALE_STUDY_CENSUS_2026-09-15.md`](SCALE_STUDY_CENSUS_2026-09-15.md)
version `0.2.0` and of `research/scale-study/0.3.0/CORRECTION.json`. Both are retained. Protocol
`4c601ca94bc1e34e155fda0b16a7e45d660c5084e913f5630938224b74686368`.
Artifacts: [`FINAL_POSITION.json`](../research/scale-study/0.4.0/FINAL_POSITION.json),
[`unresolved-closed.json`](../research/scale-study/0.4.0/unresolved-closed.json).

## The result

> Among **3,000** declared annotation conditional decisions under the Engine additive loss and the
> single record deletion family, **1,127** were supported and **all 1,127 have an exact minimum
> equal to their arithmetic floor**. **0** exceeded it and **0** remained unresolved. **1,873** had
> an unsupported baseline.

The three units that exhausted the old growing budget were rerun under the repaired module with a
raised budget. All three certified at their floors, at 137, 283 and 256 deletions, in 7.1, 8.1 and
10.5 seconds. The census now has no unresolved unit.

## I said this three times and only the third is right

| version | claim | verdict |
|---|---|---|
| `0.2.0` | the ratio is near tautological; the census proves the measure empty | **wrong**: the derivation confused the gain to remove with the deletions needed to remove it |
| `0.3.0` | whether any real unit exceeds its floor is unknown | **over withdrawn**: unknown only where the search stalls, and the census had no stalls |
| `0.4.0` | every supported unit has minimum exactly at its floor, proved, while a larger minimum is possible in principle | stands |

The middle one was my own over correction, written an hour after the consumer showed me the first
was wrong. Retracting too far is its own error and it is recorded as one.

## Why the census does establish this, by the stall argument

The growing search takes only deletions that remove exactly one unit of gain. So the loss removed
equals the number taken, and it halts at `ceil(need/step) = k_floor` exactly.

- **If it succeeds**, `k` deletions remove `k` units of gain and the decision crosses, so the
  minimum is at most `k`. The floor is a proved lower bound, so the minimum **is** `k`.
- **Contrapositive**: a unit whose minimum exceeds its floor cannot let the search succeed, so it
  must stall, and version `0.1.0` reported every stall as `no_admissible_crossing`.

The census reported `no_admissible_crossing` **0 times**, and **0** certified units had
`k_observed` different from `k_floor`. So every supported unit that completed has a minimum exactly
equal to its floor, and that conclusion does not pass through the defective branch.

## Why it is a finding rather than arithmetic

The consumer's counterexample has floor 1 and minimum 2: one base at `x=0`, one addition at `x=3`,
three objects between them, where no single deletion changes the gain and every pair does. The
general family with `m` objects between one base and one addition has floor 1 and minimum `m - 1`.

**A minimum above the floor is possible under this very loss.** That it never occurs across 1,127
real supported decisions is a property of this data, not of the arithmetic. That is precisely why
the tautology claim was wrong, and it is also what makes zero a measurement rather than a
definition.

## The distribution, with its denominators

Over all 1,127 supported units, every one of which is now resolved:

| quantity | value |
|---|---:|
| minimum deletions | 1 |
| median | 26 |
| maximum | 575 |
| normalised, median | 0.0239 |

- 37 of 1,127 are overturned by deleting a single annotation.
- 169 of 1,127 need five deletions or fewer.
- 271 of 1,127 need one percent or less of their scene's annotations.

## What is not claimed

No annotation has been checked, so there is no label error rate and no probability. The 3,000 units
share 150 scenes and 5 submissions and are not independent experiments. This is the Engine additive
loss at a common 50 m range, not official mAP or NDS. Label errors destabilising benchmark rankings
is prior art from Northcutt, Athalye and Mueller, NeurIPS 2021. Whether the floor is a useful
quantity for a validation lead is still unmeasured, and no comparison with any company's practice is
made or implied.

## Next falsifier

A second dataset. If some supported decision there has a minimum above its floor, then the uniform
result here is a property of nuScenes rather than of this loss, and the floor stops being a
sufficient answer. If none does, the floor is the answer on two datasets and the search that finds
it can be replaced by the arithmetic, which would make the instrument cheaper rather than smarter.
