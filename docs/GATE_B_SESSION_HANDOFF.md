# Gate B Session Handoff

Read `AGENTS.md` first, then this. Resolve every state from the exact artifacts named here, never
from this prose. This file is a continuation contract, not authority. It is the mission baton: a
fresh session should be able to inherit the whole program, its standards, and its exact state from
this one file plus the records it names.

## 0. Where you are, and where this work is

**This work is not on the branch you are probably sitting on.** It lives in a dedicated worktree,
on its own branch, cut from a released commit so no `1.2.0` byte is ever touched.

| Worktree | Branch | Contents |
|---|---|---|
| `~/workspace/reiyah` | a Gate A continuity branch, **another owner** | leave its worktree and its uncommitted paths alone; never switch branches inside it |
| `~/workspace/reiyah-gate-b` | `gate-b-measurement` | everything described below |

```sh
cd ~/workspace/reiyah-gate-b
git remote get-url origin      # https://github.com/manfromnowhere143/reiyah.git
git branch --show-current      # gate-b-measurement
git log --oneline -1           # 3450415 (Result W) or later
git status --short             # clean, or only docs/GENERAL_SYNTHESIS.md until committed
```

Branch cut from a released commit, so no `1.2.x` byte is touched and the Gate A continuity
workstream is undisturbed. Published at
`https://github.com/manfromnowhere143/reiyah/tree/gate-b-measurement`.

## 1. The mission, in one paragraph

Every safety and ensemble argument for autonomous and AI systems rests on one load-bearing
assumption: that redundant channels fail independently. It is almost never measured. This program
measures it, with a single estimand, across three domains: two automation sensors, the human, and
AI juries. The finding, stated to its evidence and no further, is a law: **redundancy across
genuinely different kinds buys independence; redundancy across similar kinds does not.** The program
also corrects the safety calculus that the assumption feeds, and builds a live monitor that reads
the coupling from channel outputs alone. HARBOR (Human-Automation Readiness, Belief & Operational
Risk) is the proposed working research program; every scientific, benchmark, standards, safety, and
comparative claim stays `proposed` until eligible retained evidence and an authorized external
decision say otherwise. **No model is executed in the analysis lane.** The one place inference ran is
recorded in section 8, on a separate GPU box, to produce a second camera detector's predictions.

The single reading of the whole program is [`GENERAL_SYNTHESIS.md`](GENERAL_SYNTHESIS.md). The
contract authorizing the measurement lane is
[`GATE_B_MEASUREMENT_CONTRACT.md`](GATE_B_MEASUREMENT_CONTRACT.md), lifecycle `proposed`.

## 2. The standards (read this before you touch anything)

These are absolute and they are the reason the work is credible. A fresh session that keeps only
these has the mission.

1. **Honesty above all.** Every claim carries the epistemic state of its evidence. A computed number
   is not a measurement, a passing validator is not acceptance, a checksum is not truth, and
   generated prose is not evidence. State results forward as information the work bought, never
   soften a null and never inflate a finding. The mission is to earn the trust of the best
   engineering minds in the world by being more honest than they expect, not louder.
2. **Everything stays `proposed`.** No scientific support, safety finding, compliance determination,
   comparative claim about any vendor, operator acceptance, or runtime authorization is asserted by
   any artifact here. The lifecycle states are distinct values with distinct histories; missing,
   unmeasured, out-of-distribution, and abstained never collapse into zero, false, or a confident
   label.
3. **Corrections are permanent and additive.** Eighteen-plus claims have been withdrawn or narrowed;
   every correction made the result smaller. All remain in place with their refutations attached.
   **Do not tidy them away.** The machine-readable reconciliation point is
   [`claim-status-register-2026-08-29.json`](../evidence/claim-status-register-2026-08-29.json), and
   `tools/measure/check_claim_reconciliation.py` fails closed if any live prose states a figure the
   register forbids. The register, not any prose, is the truth.
4. **Marginal and conditional are never conflated.** The marginal coefficient includes shared
   difficulty; the conditional removes the measurable part and reports what is left. Always report
   both, and name which one a sentence means.
5. **No released byte is modified.** No `1.2` architecture byte is touched by any of this work. New
   schema and contract successors are `proposed` against the release, never applied in place. Never
   weaken a substitution guard, a validator, or a check to make a run pass; a validator that refuses
   real data because its frozen contract names a fixture is working as designed.
6. **Reproducible and seeded.** Every tool re-runs byte-identically. If one does not, stop and find
   out why before trusting anything it produced. Large intermediates are gitignored and regenerated;
   never admit a detector match set that fails its `--validate` accuracy gate.
7. **Red-team your own work.** Every result names the objection a reviewer would raise and answers
   it or records it as open. Two defects found in this program's own scripts were recorded rather
   than quietly fixed.
8. **No em dash in any repository document.** Plain reviewable Markdown, JSON, and deterministic
   scripts. Match the README's voice: precise, honest, real numbers, no ornament.
9. **Commits are Daniel-authored only.** Plain messages, no `Co-Authored-By` trailer, no Claude
   attribution. Daniel's authorship alone.
10. **No company names in any public or outward-facing artifact.** A LinkedIn post or comment, or
    anything shared outside the repo, carries the science only: the coefficient, the law, the
    numbers. Never name a vendor. Inside the repo, vendor pointers exist only as bounded,
    evidence-ineligible comparator references that establish no claim.
11. **Separation by law.** Reiyah is independent of Aweb and Odeya. Never couple their code, claims,
    or infrastructure. The engine repo `~/workspace/reiyah` forbids runtime and network inside it;
    enter it only through its own baton and never drag its worktree.
12. **Host stewardship is narrow and recoverable.** Disk cleanup removes only exact inactive,
    re-downloadable, cloud-backed targets after checking ownership and process use; never delete
    personal files, credentials, active runtimes, or unrelated repositories to make a run succeed.
13. **Do the plain work yourself.** A file move, an unzip, a small script: do it, do not delegate a
    trivial operation back to the operator.

## 3. Exact current state

| Item | State |
|---|---|
| Worktree / branch | `~/workspace/reiyah-gate-b`, `gate-b-measurement` |
| HEAD | `3450415` (Result W) |
| Pushed | all commits pushed to `origin/gate-b-measurement` |
| Uncommitted | `docs/GENERAL_SYNTHESIS.md` until committed with this handoff |
| Schema successor | `schemas/v1.3/`, **proposed**, not applied to any released byte |
| Executable contract successor | `1.3.0` joint-silent-miss contract, **proposed, not registrable from this lane** (section 12) |
| Record validation | `port` or `spec_reimplementation` only; the shipped module can validate only its frozen synthetic fixture |
| Operator acceptance | none |
| Scientific support | none |
| External independent review | **none: this is the one open item that would raise confidence** |
| Released `1.2` bytes modified | none |

## 4. The complete arc, by domain

Transcripts in `evidence/` and the per-thread `evidence/` folders; tooling in `tools/measure/`,
`human-channel/tools/`, and `llm-generalization/tools/`. The three READMEs
(`README.md`, `human-channel/README.md`, `llm-generalization/README.md`) narrate each thread.

**Domain one: two automation channels (nuScenes).** A camera detector and a lidar detector miss the
same objects more than independence predicts. Conditional `c = 1.151`, 95% CI [1.138, 1.160], after
stratifying on class, range and visibility on a common support, with the marginal at `1.587`. It
survives four independent robustness axes: a second lidar (M), every operating threshold (N),
unmeasured confounding with an E-value of 2 to 3 (O), and a second camera, FCOS3D, run for this
program (Q, and Q-depth). Two sharpening results keep it honest: the coefficient is smallest exactly
where the sensors jointly miss most, so `c` alone cannot certify redundancy (P); and an inviting
accuracy trend is mostly the marginal arithmetic of the miss rate, not coupling (R). The 2x2 modality
grid: two lidars couple most (1.29), a camera and a lidar less (1.10 to 1.15). The worst eligible
group is a close-range car at lift 6.946, band [2.221, 11.671] on 34 instances (I, J); never quote
it without the band. Results L, M, N, O, P, Q, R; red-team in
[`MEASUREMENT_THREATS_TO_VALIDITY.md`](MEASUREMENT_THREATS_TO_VALIDITY.md).

**Domain two: the human (100-Car NDS, DCPT, BDD-A).** In real conflicts the driver was looking
forward two thirds of the time: observation is not detection (H2). The human's own two channels,
looking and acting, fail together at `c = 1.46`, the same shape the sensors show (H3). In Level 3
automation a visual-manual distraction slows takeover by about a quarter (H4). The cross-agent
question no prior work had measured, a validated detector against the driver gaze heatmap taken to
the automation's total blindness with a clip-clustered interval, gives `c = 0.98`, approximately
independent (H5, H6). This is where the law's other arm shows: a human and a machine are genuinely
different kinds, and their redundancy holds. Files `human-channel/H1..H6_*.md`.

**Domain three: AI juries (Open LLM Leaderboard v1, MMLU and ARC-Challenge).** Seven models fail
together; same-lineage more than cross-lineage; the residual survives difficulty conditioning; a
seven-model jury has the effective diversity of 3.6 (T). Agreement is over-trusted: two agreeing are
correct 64.8% of the time, all seven agreeing are still wrong 10.4% (U). It replicates on
ARC-Challenge, where a six-model jury carries the diversity of 1.6 and unanimity is wrong 37.2% (W).
No LLM inference: this reads public per-question outputs and joins by example hash. Files
`llm-generalization/RESULT_T..W_*.md`.

**The correction (S).** Required validation evidence in the redundancy argument scales as `sqrt(c)`,
reproduced against RSS's own worked example. With the measured coefficient, a same-kind redundancy
needs at least 26% more validation evidence than the argument claims (a lower bound); the
human-machine layer needs almost none. Two coupled sensors give the joint-failure protection of one
and a half independent channels. File [`RESULT_S_CORRECTED_SAFETY_CALCULUS.md`](RESULT_S_CORRECTED_SAFETY_CALCULUS.md).

**The instrument (V).** A monitor that sees only the channels' outputs, with no ground truth,
returns a calibrated probability the ensemble is wrong, having learned the coupling from a labeled
calibration set. On held-out data it beats the naive agreement heuristic on every metric (AUC 0.845
against 0.719, ECE 0.015 against 0.045); on unanimous items where the naive assumption assigns 0%
risk it assigns the 11.6% the data carries against a true 9.5%. Its features are channel-agnostic, so
the same form applies to two sensors or a human and a machine. File
`llm-generalization/RESULT_V_DEPLOYED_MONITOR.md`.

## 5. The law, and the headline coefficients

| domain | same-kind pairing | cross-kind pairing |
|---|---|---|
| sensors | two lidars, c = 1.29 | camera x lidar, c = 1.10 to 1.15; human x machine, c ~ 0.98 |
| the human | eyes x hands, c = 1.46 | (the human x machine cell above) |
| LLM juries | same family c = 1.52 (MMLU), 1.87 (ARC) | cross family c = 1.29 (MMLU), 1.73 (ARC) |

Similar channels share a substrate and share their blind spots; genuinely different ones do not. The
independence assumption is a load-bearing fiction wherever redundancy is claimed, and it fails most
for the systems that share the most.

## 6. The unit and the estimand

The estimand is the RSS Definition 32 coincidence coefficient
`c = P(A fails and B fails) / [P(A fails) P(B fails)]`; `c = 1` is independence. It is not specific
to sensors, which is why the finding travels across domains unchanged. See
[`ESTIMAND_RSS_DEFINITION_32.md`](ESTIMAND_RSS_DEFINITION_32.md).

The statistical unit matters more than it looks. An opportunity set is one common object over a time
series; nuScenes objects are tracked, so 8,976 instances at a mean of 15 observations are the correct
unit, and treating the boxes as independent is a clustering error the program's own traps table
catches. Any future analysis clusters on `instance_token`; the LLM and human threads carry their own
clustered intervals (clip-clustered for BDD-A, example-joined for the juries).

## 7. Corrections already on the record

Every withdrawn or narrowed claim stays with its refutation attached; the register is the
reconciliation point. A non-exhaustive reminder of the shape of them: censoring inflates dependence
rather than deflating it; dependence is worst up close, not at long range; the evidence-budget
figures were withdrawn and only the `sqrt(c)` correction (S) returned them under stated conditions;
the word `silent` is wrong for a both-channel miss without an audited monitor adapter and must not
be used; Result H's cross-modality separation is `inconclusive` by construction because neither arm
has internal replication. Full tables in
[`CLAIM_AUDIT_2026-08-29.md`](CLAIM_AUDIT_2026-08-29.md) and the register.

## 8. Compute, data, and the one inference run

`sentinel-gpu` in `us-west1-a`: `g2-standard-8`, NVIDIA L4 24 GB, normally TERMINATED, about one
dollar an hour running and near zero stopped. **Stop it when not computing.** It belongs to
Sentinel; do not downgrade its torch. It holds the full nuScenes trainval set. The camera axis
(Result Q, FCOS3D) is the one place inference ran: in a container (`uniad:latest`, torch 1.9/cu111,
mmdet3d 0.17.1), with `--ipc=host` for the DataLoader and a CPU-side patch of `torch.inverse` for
the L4. The predictions were validated by mAP reproduction before use, like every other detector.

Local analysis venv: `~/bdda-venv` (torch 2.14/torchvision 0.29 with MPS, `datasets`,
`huggingface_hub`, `sklearn`, `scipy`; ffmpeg present). The human and LLM threads run from it, for
example `bdda-venv/bin/python llm-generalization/tools/result_t_llm_independence.py`.

Public data sources, retained by custody state: nuScenes trainval metadata (SHA-256 pinned in
section 9), the four detectors' released prediction files, 100-Car NDS (CC0), the DCPT L3 takeover
set, BDD-A driver attention (research-use), and the Open LLM Leaderboard v1 per-question parquet
files (`open-llm-leaderboard-old` on Hugging Face). A URL is not retained evidence; a source held
only as a pointer may not be characterized as if retained.

## 9. Reproducing the sensor spine

```sh
cd ~/workspace/reiyah-gate-b
python3 tools/measure/fetch_predictions.py predictions        # ~250 MB, HTTP range requests
curl -o meta.tgz https://motional-nuscenes.s3.amazonaws.com/public/v1.0/v1.0-trainval_meta.tgz
shasum -a 256 meta.tgz    # db48746b10e3544d5ef619eaa3d687e3960626fe1b4422ed856711da5aa7325b
python3 tools/measure/build_gt_cache.py gt_val_cache.json < meta.tgz
python3 tools/measure/match.py gt_val_cache.json predictions/megvii_val.json matched_megvii.json --validate 51.9
python3 tools/measure/match.py gt_val_cache.json predictions/mapillary_val.json matched_mapillary.json --validate 29.8
python3 tools/measure/build_joint_records_per_instance.py gt_val_cache.json \
    first=matched_mapillary.json second=matched_megvii.json joint_records_per_instance.jsonl
python3 tools/measure/semantic_joint_1_3.py joint_records_per_instance.jsonl
```

No GPU for the spine. Never use a bare pipe over an unreliable connection; one silently corrupted
transfer was caught only because a checksummed copy verified CRC32C. The human and LLM threads
reproduce from their own README commands.

## 10. What is proven, and what is open

Proven and reproducible from this repository: the coefficient exceeds 1 for similar-kind redundancy
across three domains and two benchmarks; it is approximately 1 for a human and a machine; the
required evidence is understated by the measured amount; and a calibrated output-only monitor
corrects the over-confidence. Every result is `proposed`, self-checked against independent anchors,
robustness-tested, and red-teamed.

Open, and named plainly: **no independent external review has been retained.** That is the honest
ceiling on current confidence and the single most valuable next thing. It cannot be self-performed.
Beyond it: the driving results are association after declared conditioning on public benchmarks, not
a certificate about any deployed system; the human results are on naturalistic and simulator data
with an engaged human; the LLM monitor is validated on two benchmarks and one jury, not deployed.

## 11. The next smallest actions

1. **Commit `docs/GENERAL_SYNTHESIS.md`** with this handoff so the tree is clean and the fresh
   session inherits the single reading (Daniel-authored, no trailer). If this handoff already reads
   `clean` in section 3, that is done.
2. **Retain an independent external review.** Operator action; cannot be self-performed. This is the
   real frontier.
3. Optional hardening already scoped: a monitor cross-model transfer test (train the coupling
   estimator on one jury, test on a disjoint jury); the monitor validated on real driving outputs
   rather than benchmark outputs; a third benchmark for the LLM law.

Continue only the smallest unresolved step. Engineering pressure raises the burden of proof; it
never raises confidence by itself.

## 12. What is blocked, and by what

| Blocked | Blocker | Lane |
|---|---|---|
| Registering the `1.3.0` contract so the shipped module runs these checks | the frozen expectation lives inside a released Gate A module and is compared by exact equality; changing it would edit a released byte | Gate A successor |
| Any evidence-budget figure beyond the `sqrt(c)` correction | conditions in `ESTIMAND_RSS_DEFINITION_32.md` section 6.4 | Gate B, open |
| Bounding `c` on a measured stratum by reference-error rate | no blinded reannotation performed | Gate B, needs authorization |
| Any use of the word `silent` | no audited monitor adapter | contract design done, adapter absent |
| Object-level human miss on real data at scale | no audited public dataset identifies it; a pilot needs human-subjects review | outside current authority |
| A scientific, safety, or comparative claim | eligible retained evidence and an authorized external decision | outside this lane |

## 13. Required closeout

State, separately and from exact records: worktree, branch, commit, and cleanliness; which schemas
and contracts are `proposed` against released; how many records validate and against which validator
(the port, the spec reimplementation, or the shipped module); every claim withdrawn since the last
handoff and that `check_claim_reconciliation.py` passes; every reproduction that a corrected prose
depends on re-run with its byte-identity stated; source custody per source; that no result is
independently replicated and shared compute or authorship is never independent validation; operator
acceptance, scientific support, external-review, runtime, and Gate B authority states; and the next
smallest authorized action.

A successful measurement is an honest descriptive result on public data. It is never, by itself,
scientific support, safety validation, standards compliance, product readiness, competitive
superiority, operator acceptance, or runtime authority. Say only what the evidence says, and say the
open item every time.
