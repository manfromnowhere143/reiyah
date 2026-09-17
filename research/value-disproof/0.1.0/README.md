# Current-bound development comparison

Artifact: `reiyah.value-disproof`, version `0.1.0`, exploratory, 17 September 2026.

**Decision: inconclusive for product value. Stop the selection-superiority claim on
this all-present development family and keep platform expansion stopped.**

The direct matching baseline needs 2,534 hypothetical presence queries across the
15 previously exposed addition cases. Their necessary confirmation counts sum to
2,244. Even a selector attaining every floor could improve this baseline by only
**1.1292x**, below the 3x investment gate. The direct construction already attains
the floor on 13 cases, including the 372-confirmation forty-frame case.

A conventional implicit hitting-set fallback reduces the aggregate to 2,255
queries. The same selector with conventional stopping produces **identical ordered
queries, answers, bounds and outcomes**. The observed reduction is available to
both sides; it is not a Reiyah-specific stopping or selection advantage.

Both actual independent-output replacement directions remain unresolved after
512 queries each. These are archived detector substitutions, not chronological
modern model revisions. The forty-frame position case and small public example
are zero-query draws under shared linear bounds. A stricter-threshold control
remains unresolved with its explicitly zero-query budget. Every assigned row is
retained. Human work and full economic cost remain unmeasured.

## Runnable artifacts and scope

[results.json](results.json) retains aggregate results, every case, source-result
digests, cost gaps and the decision. [compare.py](compare.py) implements the common
observation interface, selectors and stopping. [interaction.py](interaction.py)
adds the fourth cell of the ablation. [replay.py](replay.py) checks every recorded
query and scheduled stopping point. [test_compare.py](test_compare.py) provides
targeted soundness and refusal controls. [prepare.py](prepare.py) records exact
source membership; [summarize.py](summarize.py) derives the public aggregate without
publishing per-record identifiers.

The private local experiment root is
`~/.codex/reports/reiyah/value-disproof-2026-09-17-93iqbzbr/`.
It contains `SESSION.json`, `PLAN.json`, `FREEZE.json`, `INTERACTION_PLAN.json`,
`SOURCE_VERIFICATION.json`, `PUBLIC_REPLAY.json`, all inputs, ordered histories,
native proof payloads, stdout/stderr and replay reports. Identity-bearing data stay
outside Git. Closed predecessor reports and the controller checkout are unchanged.

Selected Engine: `38a50ec014cc83e86ea6f247df803ded2971b386`.
Selected research implementation: `b3125c4a97c0029a1f70aba7d0ab5105a9b3d233`.
The fresh candidate shares the canonical controller's Git common directory and
verified Reiyah remote. Engine production code is unchanged.

From this candidate, replay into **new** output directories using the existing
runtime. Retained private inputs and their access conditions are required for the
benchmark rows; the tests need no third-party dataset.

```sh
reiyah_python=/Users/danielwahnich/.codex/reports/reiyah/engine-discovery-custody-2026-09-13/private/runtime/bin/python
reiyah_experiment=/Users/danielwahnich/.codex/reports/reiyah/value-disproof-2026-09-17-93iqbzbr
env -u PYTHONPATH "$reiyah_python" -B research/value-disproof/0.1.0/test_compare.py
env -u PYTHONPATH "$reiyah_python" -B research/value-disproof/0.1.0/compare.py \
  "$reiyah_experiment" "$reiyah_experiment/runs/reproduction-new"
env -u PYTHONPATH "$reiyah_python" -B research/value-disproof/0.1.0/replay.py \
  "$reiyah_experiment" "$reiyah_experiment/runs/reproduction-new"
env -u PYTHONPATH "$reiyah_python" -B research/value-disproof/0.1.0/interaction.py \
  "$reiyah_experiment" "$reiyah_experiment/runs/interaction-new"
```

## Comparison and information contract

All deletion arms use the same fixed, finite reference graph, loss, strict
threshold, unrestricted deletion family, hypothetical all-present answers,
512-query ceiling and 120-second budget checked between atomic calls. Each IHS
solver call has a 10-second limit. A batch contains at most ten queries, shortened
to end exactly at a known necessary floor. Reported stopping is the first justified
decision at these scheduled checkpoints, not an unobserved earlier point.

| Arm | Selector | Stopping |
|---|---|---|
| A | Direct matching construction, then addition adjacency; disagreement ranking for replacements | Independent conventional exact endpoint matcher on additions |
| B | Exactly A | Native checked endpoints on additions |
| C | Same direct construction when it attains the floor; otherwise pinned conventional IHS with an exact monotone adversary | Exactly B |
| D | Exactly C | Exactly A |

For replacements all arms receive native legacy and component bounds, which are
publicly usable by the conventional arm. No addition-only theorem is applied to
them. For position rows every arm receives the ordinary and shared-edge linear
proofs. Their interval intersection is a research-level combination of two
separately checked calls, each under the unchanged native work ceiling; it is not
a new single Engine proof with a raised work limit. The threshold control has a
zero-query ceiling and is not an observation-policy evaluation.

The direct selector matches B to references with no A eligibility edge, then
queries those reference endpoints. Where enough such endpoints exist, the
confirmed subgraph has A rank zero and B rank equal to the confirmation count.
For uniform weight w, unrestricted deletions and all-present answers, sufficiency
requires `(fn+fp)*w*q - fp*sum(w*(D_B-D_A)) > tolerance`. A separately checked
sufficient request attaining this floor proves the minimum under that contract.
This does not optimize reviewer time or cover contradictory, missing-object,
class, localization or correlated corrections.

`select_next` receives original operands and revealed history. It has no oracle
argument. The observation service reveals one answer after a request and records
native anchor/object/context bindings, a subject digest, requested precision,
answer, residual uncertainty, timestamp, method and cost. This is an API boundary,
not a process sandbox or a claim of independent blinding. No corrected-label
container or outcome-reserved label was opened. A hypothetical adverse world
means the positive decision is not yet justified; it does not by itself justify
excluding improvement in the actual unknown world.

All arms begin with cold observation caches and equal access to retained inputs
and coefficients. Repeated queries reject. Distinct prefixes are checked; no
cross-arm answer transfer or free historical optimizer cost is claimed. The first
three-arm plan was frozen after exposed development preparation. D was explicitly
added after those results as a development interaction check. It is not a
prospectively unseen evaluation. Standard IHS is the remaining strong comparator,
not a proprietary candidate method.

## Every assigned case

Counts are **hypothetical query events**, not people or actual measurements.
All four arms resolve the same 17 of 20 rows. Model/scene combinations, the reverse
comparison and threshold variant are dependent; 20 is not an independent sample size.

| Case | A | B | C | D | Outcome in all arms |
|---|---:|---:|---:|---:|---|
| First exposed addition | 9 | 9 | 9 | 9 | Supported |
| Second exposed addition | 328 | 328 | 55 | 55 | Supported |
| Forty-frame addition | 372 | 372 | 372 | 372 | Supported |
| FCOS3D + PointPillars, 0910 | 164 | 164 | 164 | 164 | Supported |
| Mapillary + Megvii, 0915 | 178 | 178 | 178 | 178 | Supported |
| FCOS3D + Megvii, 0554 | 182 | 182 | 182 | 182 | Supported |
| FCOS3D + Megvii, 0269 | 82 | 82 | 82 | 82 | Supported |
| FCOS3D + PointPillars, 0557 | 99 | 99 | 99 | 99 | Supported |
| PointPillars + Mapillary, 0963 | 177 | 177 | 177 | 177 | Supported |
| FCOS3D + Mapillary, 0636 | 116 | 116 | 116 | 116 | Supported |
| FCOS3D + CenterPoint, 0782 | 222 | 222 | 222 | 222 | Supported |
| PointPillars + Mapillary, 0928 | 125 | 125 | 119 | 119 | Supported |
| FCOS3D + PointPillars, 0636 | 128 | 128 | 128 | 128 | Supported |
| FCOS3D + CenterPoint, 0638 | 281 | 281 | 281 | 281 | Supported |
| FCOS3D + Megvii, 0802 | 71 | 71 | 71 | 71 | Supported |
| Standalone Mapillary to Megvii | 512 | 512 | 512 | 512 | Query limit; unresolved |
| Reverse of that replacement | 512 | 512 | 512 | 512 | Query limit; unresolved |
| Forty-frame position, 0.5 m | 0 | 0 | 0 | 0 | Supported; draw |
| Same positions, tolerance 0.5 | 0 | 0 | 0 | 0 | Unresolved zero-query control |
| Public position example | 0 | 0 | 0 | 0 | Supported; draw |
| **All assigned rows** | **3,558** | **3,558** | **3,279** | **3,279** | No omissions |

The fifteen-addition stratum is 2,534 versus 2,255 queries, a 1.124x ratio.
Including unresolved replacement queries gives 3,558 versus 3,279, a 1.085x ratio.
Against the equally equipped conventional D arm, C is **1.000x** on both scopes.
Both-zero-query cases are ties and have no ratio. Neither the 3x observation gate
nor the 2x full-cost gate is established.

## Costs, validation and limits

Recorded per-arm operation time totals were A 41.45 s, B 60.80 s, C 72.22 s and
D 50.26 s. These are single local runs; D overlapped correctness replay. Deletion
selection/stopping, preparation, public replay, repair and history verification
are recorded separately. The cost ledger explicitly leaves human preparation,
review, adjudication, engineering/integration, historical coefficient optimization,
imports and agreed monetary rates unmeasured where not captured. These operation
times do not establish a complete-cost ratio, cold-start saving or amortization.

Fresh verification:

- The four retained public reproduction commands pass, including separate linear
  verification and the independent synthetic examples.
- All 22 selected source bindings match prior checkpoint/index records. This is
  selected-byte custody, not a repeat of raw-source qualification.
- Ten targeted tests pass, including 144 independently enumerated graph/answer
  problems and wrong-context, unknown/duplicate query, unresolved-answer,
  forged-result, event-tamper, precision and fabricated-human-cost controls.
- Replay checks all **80 rows, 13,674 query events, 1,796 stopping points and 1,552
  proof payloads**. On 680 addition checkpoints with native payloads, separate
  conventional endpoints agree exactly. A/B and C/D ordered histories match.
- The documented research consistency check passes with zero findings. Its
  retained transcript bindings do not rerun historical experiments.

The initial preparation attempt failed on a relative-path resolution error before
experiments ran. Its stderr is retained; absolute-path resolution fixed it.
No Engine algorithm or limit changed. The 1,000-control future pilot target was
not run. No accepted invalid certificate in these checks is a finite test result,
not proof of zero future failure. No actual missed-regression rate, physical
truth, observation-reuse gain, customer demand or economic advantage is measured.
Gate A remains operator-unaccepted; this is an authorized offline research result.

## Next executable action

Demote selection planning for all-present fixed-eligibility additions. Preserve
the matching/checking kernels. Before touching the 1,433 outcome-reserved images,
use **already exposed** correction cases to define and challenge a replacement
uncertainty family without inserting the actual corrected alternatives into the
selector's inputs. Determine whether affordable observations can resolve that
family at all. Only then freeze a reserved-outcome protocol.

The [workflow interview brief](WORKFLOW_BRIEF.md) prepares the separate demand and
actual-cost check. Outreach still requires Daniel or a separately authorized
sender. If realistic corrections defeat useful resolution or competent methods
continue to erase the practical gain, stop this product bet and retain the math.
No Console, platform, new architecture release or public positioning is warranted
by this result.
