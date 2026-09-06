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
git log --oneline -1           # 21c533b (baton) or later
git status --short             # clean
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
decision say otherwise. **Model execution is bounded and named, never hidden.** No LLM is executed
anywhere. Pretrained detectors are executed only to produce channel outputs on public frames: FCOS3D
on nuScenes (section 8, on the GPU box) and torchvision Faster R-CNN and SSDLite on BDD-A frames for
H5 and H6, locally. Result V fits and calibrates a logistic-regression monitor on leaderboard outputs.
Each execution is recorded in the result it serves and none is a Reiyah product model.

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
   **Do not tidy them away.** The machine-readable reconciliation point is the newest dated
   register under `evidence/claim-status-register-*.json` (currently
   [`claim-status-register-2026-09-06.json`](../evidence/claim-status-register-2026-09-06.json),
   which names its predecessor by digest and carries every prior claim forward), and
   `tools/measure/check_claim_reconciliation.py` fails closed if any live prose states a figure the
   register forbids. The register, not any prose, is the truth. Every human-channel and LLM result
   is registered there; a result that is not registered is not a claim.
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
| HEAD | resolve with `git rev-parse HEAD`; the closeout in section 14 names the exact commit it describes |
| Pushed | all commits pushed to `origin/gate-b-measurement`; `origin/main` state is a recorded governance event (section 14) |
| Uncommitted | none at closeout |
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
looking and acting, fail together at `c = 1.46`, band [1.04, 1.90] over all events and including 1 in
each severity subgroup (H3, H7), the same shape the sensors show at far lower precision. In Level 3
automation a visual-manual distraction slows takeover by about a quarter (H4). The cross-agent
question no prior work had measured, a validated detector against the driver gaze heatmap taken to
the automation's total blindness with a clip-clustered interval, gives `c = 0.98`, approximately
independent (H5, H6). This is where the law's other arm shows: a human and a machine are genuinely
different kinds, and their redundancy holds. Files `human-channel/H1..H6_*.md`.

**Domain three: AI juries (Open LLM Leaderboard v1, MMLU and ARC-Challenge).** Seven models fail
together; same-lineage more than cross-lineage; the residual survives difficulty conditioning; a
seven-model jury has the effective diversity of 3.6 (T). Agreement is over-trusted: two agreeing are
correct 64.8% of the time, all seven agreeing are still wrong 10.4% (U). It replicates on
ARC-Challenge, where a six-model jury carries the diversity of 1.6 and unanimity is wrong 37.2% (W),
and on HellaSwag, where the jury's diversity is 1.28 and the conditional residual is only 1.03, so the
lineage mechanism is benchmark-dependent while the marginal law is not (Y, 2026-09-06). Every
quantity carries a question-resampled interval (AC): the same-family excess beyond difficulty is
0.058 [0.050, 0.066] on MMLU and includes zero on the other two, so Result T's lineage statement is
narrowed to MMLU. A label-free margin normalization does not repair the monitor's task transfer and
costs its channel transfer (X2); fitting on two benchmarks does not transfer to a third and on
HellaSwag the transferred monitor is worse than chance (AE): fit per task, read across channels.
No LLM inference: this reads public per-question outputs and joins by example hash. Files
`llm-generalization/RESULT_T..W_*.md`.

**The correction (S), re-scoped 2026-09-06.** Under RSS Corollary 3 the admissible per-channel
error rate shrinks as `1/sqrt(c)`, so a campaign sized under independence is undersized wherever
`c > 1`. The evidence-budget percentages and counts Result S derived are withdrawn as stated: the
register's five conditions (estimand document section 6.4) are unmet, and the reconciliation check
caught the figures on 2026-09-06. The direction survives as conditional; no percentage is claimed.
The human-machine layer at `c` about 1 adds essentially no correction. File
[`RESULT_S_CORRECTED_SAFETY_CALCULUS.md`](RESULT_S_CORRECTED_SAFETY_CALCULUS.md), correction first.

**The instrument (V).** A monitor that sees only the channels' outputs, with no ground truth,
returns a calibrated probability the ensemble is wrong, having learned the coupling from a labeled
calibration set. On held-out data it beats the naive agreement heuristic on every metric (AUC 0.845
against 0.719, ECE 0.015 against 0.045); on unanimous items where the naive assumption assigns 0%
risk it assigns the 11.6% the data carries against a true 9.5%. Its features are channel-agnostic, so
the same form applies to two sensors or a human and a machine. File
`llm-generalization/RESULT_V_DEPLOYED_MONITOR.md`. **The transfer test (X, 2026-09-06):** fitted
once on jury A and never refitted, the monitor reads seven models from seven unseen families at AUC
0.853 against an in-domain ceiling of 0.856; read on ARC-Challenge it falls to or below the naive
baseline and its calibration breaks. Channel transfer holds, task transfer does not. File
`llm-generalization/RESULT_X_MONITOR_TRANSFER.md`. **The sensor test (Z, 2026-09-06):** as a
scene-level estimator of jointly missed objects on the camera and lidar channels, the coupling-aware
form does not beat a density baseline (Spearman 0.60 against 0.61 across scene folds), so the claim
that the same form applies to two sensors is a conjecture with one failed test, `inconclusive`. File
[`RESULT_Z_SCENE_BLINDNESS_MONITOR.md`](RESULT_Z_SCENE_BLINDNESS_MONITOR.md). **The per-object test
(AA, 2026-09-06):** on detections only one channel reports, the detection's own attributes predict
realness at AUC 0.79 against 0.68 for its score alone, and six cross-channel context features add
0.003, inside the fold spread. Two estimands, no support. File
[`RESULT_AA_DISAGREEMENT_MONITOR.md`](RESULT_AA_DISAGREEMENT_MONITOR.md). Replicated on a second
camera, a second lidar and a second operating point with the same verdict
([`RESULT_AB_SENSOR_MONITOR_REPLICATION.md`](RESULT_AB_SENSOR_MONITOR_REPLICATION.md)). **The
non-linear test (AD):** with a boosted model the object-level context increment is 0.022 to 0.026
AUC outside the fold spread on three of four configurations and inside it on one; the scene-level
null stands. The conjecture is restated: readable at the object level with a non-linear monitor,
not at the scene level ([`RESULT_AD_NONLINEAR_SENSOR_MONITOR.md`](RESULT_AD_NONLINEAR_SENSOR_MONITOR.md)).
In the jury quantity, four sensors give 2.10 [2.08, 2.13] independent channels
([`RESULT_AF_SENSOR_JURY.md`](RESULT_AF_SENSOR_JURY.md)).

## 5. The law, and the headline coefficients

| domain | same-kind pairing | cross-kind pairing |
|---|---|---|
| sensors | two lidars, c = 1.29 | camera x lidar, c = 1.10 to 1.15; human x machine, c ~ 0.98 |
| the human | eyes x hands, c = 1.46 [1.04, 1.90], event-resampled (H7) | (the human x machine cell above) |
| LLM juries | same family c = 1.52 (MMLU), 1.87 (ARC), 2.43 (HellaSwag) | cross family c = 1.29 (MMLU), 1.73 (ARC), 2.30 (HellaSwag) |

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
figures were withdrawn as stated and remain withdrawn (Result S reasserted them, the reconciliation
check caught it on 2026-09-06, and S now carries the correction first);
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

1. **Operator decisions, taken 2026-09-06.** Daniel instructed the session to go public with
   whatever is needed and to take the decisions; `origin/main` is fast-forwarded to the reconciled
   branch tip (governance event, decision section), and the DCPT payload stays in public history
   under its retained CC BY 4.0 record and NOTICE attribution.
2. **Retain an independent external review.** Operator action; cannot be self-performed. This is the
   real frontier.
3. Retain the BDD-A terms once the portal is reachable; DCPT and 100-Car custody is retained and
   verified (section 14), the leaderboard archive states no licence.
4. Done this session: X, X2, Y, Z, AA, AB, AC, AD, AE, AF, H7, the Gate B check. Open and
   scoped: a monitor on real driving channel outputs beyond the public benchmark; the H5 cross-agent
   coefficient with a clustered band (H6 has one); a second dataset for the shared-training-data
   threat.

Continue only the smallest unresolved step. Engineering pressure raises the burden of proof; it
never raises confidence by itself.

## 12. What is blocked, and by what

| Blocked | Blocker | Lane |
|---|---|---|
| Registering the `1.3.0` contract so the shipped module runs these checks | the frozen expectation lives inside a released Gate A module and is compared by exact equality; changing it would edit a released byte | Gate A successor |
| Any evidence-budget figure, percentage, count, or multiplier | five conditions in `ESTIMAND_RSS_DEFINITION_32.md` section 6.4, none yet met | Gate B, open |
| Bounding `c` on a measured stratum by reference-error rate | no blinded reannotation performed | Gate B, needs authorization |
| Any use of the word `silent` | no audited monitor adapter | contract design done, adapter absent |
| Object-level human miss on real data at scale | no audited public dataset identifies it; a pilot needs human-subjects review | outside current authority |
| A scientific, safety, or comparative claim | eligible retained evidence and an authorized external decision | outside this lane |

## 12a. The Gate B check

`python3 tools/measure/gate_b_check.py` is the lane's discipline as one fail-closed command. It
verifies every retained transcript against the SHA-256 recorded in
`validation/gate-b-replay-manifest.json`, replays the transcripts of the classes named by
`--replay` and requires byte identity, runs the register and reconciliation check, verifies the
custody digests, and enforces the style rules (no em dash, document headers, resolving links). It
writes a machine-readable report with `--json`. Without `--replay` every transcript is reported as
`not_replayed_here`, a distinct state never counted as replicated; rows of class
`argv_unrecorded_historical` are digest-checked and never replayed. Run it before every closeout
and retain its report under `evidence/`.

## 13. Required closeout

Run the Gate B check (section 12a) and retain its report. State, separately and from exact records: worktree, branch, commit, and cleanliness; which schemas
and contracts are `proposed` against released; how many records validate and against which validator
(the port, the spec reimplementation, or the shipped module); every claim withdrawn since the last
handoff and that `check_claim_reconciliation.py` passes; every reproduction that a corrected prose
depends on re-run with its byte-identity stated; source custody per source; that no result is
independently replicated and shared compute or authorship is never independent validation; operator
acceptance, scientific support, external-review, runtime, and Gate B authority states; and the next
smallest authorized action.

## 14. Session of 2026-09-06: the baton audited against its own bytes

A fresh session took the baton at `21c533b` and ran the closeout it requires before trusting it.
The tree failed its own rules in six places. Every correction below is additive; nothing withdrawn
was deleted and no check was weakened.

1. **The reconciliation check failed at `21c533b`** with six live assertions of register-forbidden
   evidence-cost figures, in `README.md`, this handoff, `GENERAL_SYNTHESIS.md`, and Result S. The
   prior closing statement that reconciliation was intact was wrong. Result S now carries a
   correction first, its figures are marked withdrawn as stated, and the three summaries state the
   `1/sqrt(c)` direction with no percentage. The check's live-prose coverage was widened to the
   `human-channel/` and `llm-generalization/` documents; it was not loosened. Later the same day
   the register gained an append-only successor (`0.2.0`, schema `v1.4`) that registers every
   human-channel and LLM claim with its unit, source custody, and reconsideration requirements, and
   the check now reads the newest register; the widened register caught two more unmarked Result S
   lines, which were marked.
7. **Result X added**, the monitor transfer test, with transcript `llm-generalization/evidence/result_x.txt`
   byte-identical across three runs and registered as `llm-monitor-transfer` (register `0.2.1`).
8. **Result Y added**, the third benchmark (HellaSwag), transcript `llm-generalization/evidence/result_y_hellaswag.txt`
   byte-identical across two runs, registered as `llm-jury-coincidence-hellaswag-replication`
   (register `0.2.2`), with the near-zero conditional residual stated as the headline nuance.
9. **Result Z added**, the scene-level sensor monitor, verdict `inconclusive`: the coupling-aware
   form does not beat density on the driving channels. Transcript `evidence/measurement/result_z.txt`
   byte-identical across three runs; registered as `sensor-scene-blindness-monitor` (register
   `0.2.3`); the untested sentence in Result V is annotated. The pinned `meta.tgz` was re-fetched
   and its SHA-256 matched the handoff's value.
10. **Result AA added**, the per-object disagreement monitor: realness of a single-channel
   detection is predictable from its own attributes (measured), and cross-channel context adds
   nothing inside the fold spread (inconclusive). The two-sensor conjecture now has two failed
   tests. Transcript `evidence/measurement/result_aa.txt` byte-identical across three runs;
   registered as `sensor-disagreement-realness` and `sensor-disagreement-context-increment`
   (register `0.2.4`).
11. **Results X2, AB and AC added.** X2: a label-free margin normalization, stated in advance, does
   not repair task transfer and costs channel transfer. AB: Z and AA replicate on a second camera,
   a second lidar and a second operating point with the same inconclusive verdict. AC: bootstrap
   intervals on every LLM quantity; Result T's lineage-beyond-difficulty statement is narrowed to
   MMLU. Transcripts byte-identical across repeated runs; register `0.2.5`. An external review
   request is drafted in [`EXTERNAL_REVIEW_REQUEST_2026-09-06.md`](EXTERNAL_REVIEW_REQUEST_2026-09-06.md).
12. **H7 added**, bands on every human-channel headline; the eyes x hands cell is narrowed to
   1.46 [1.04, 1.90] (register `0.2.6`), and the DCPT delay survives participant clustering.
13. **Results AD, AE, AF added** (register `0.2.7`). AD: with a boosted model the object-level
   context increment is measurable on three of four configurations; the scene-level null stands.
   AE: multi-benchmark calibration does not transfer, and on HellaSwag the transferred monitor is
   worse than chance. AF: the four-sensor jury has 2.10 [2.08, 2.13] effective independent
   channels; a bootstrap defect in its first draft is recorded and corrected. Four background jobs
   were stopped externally at 15:25 and rerun serially; nothing was lost.
14. **Full replay retained.** `gate_b_check.py --replay local_deterministic,network_cached` on the
   tree at `35add31`: 19 of 19 replayable transcripts byte-identical (T, U, V, W, X, X2, Y, AC, AE;
   H1 to H4, H7; Z, AA, AB, AD, AF), 17 historical sensor-spine rows digest-checked and never
   replayed, 2 BDD-A inference transcripts not replayed here. Report
   `evidence/gate-b-check-2026-09-06-replay-mode.json`.
2. **The statement that no model is executed in the analysis lane was false.** H5 and H6 execute
   pretrained torchvision detectors on BDD-A frames; Result V fits a logistic-regression monitor.
   Section 1 and the thread READMEs now say exactly what runs.
3. **The word silent** appeared in H5, H6, and the human-channel README for a both-channel miss
   while section 12 blocks it. Replaced with joint total miss; the register's reservation is now
   stated in H6.
4. **Em dashes** in five result documents (M, P, Q, R, findings synthesis) were replaced.
5. **Source custody** for the four new public sources was unrecorded, and the DCPT payload sits in
   public history without retained licence bytes or attribution. Recorded in
   [`PUBLIC_DATA_CUSTODY_2026-09-06.md`](PUBLIC_DATA_CUSTODY_2026-09-06.md) as open findings, then
   closed the same day for DCPT and 100-Car: the Zenodo and Dataverse publisher records are retained
   under `evidence/sources/`, every committed and local payload matches the publisher's checksum,
   and `NOTICE` carries the CC BY 4.0 attribution. BDD-A terms remain unretrieved after three
   recorded attempts; the leaderboard archive states no licence on its card.
6. **The public `main` ref was moved to the Gate B tip** by earlier pushes, unrecorded. Recorded in
   [`GOVERNANCE_EVENT_2026-09-06_MAIN_REF_MOVED.md`](GOVERNANCE_EVENT_2026-09-06_MAIN_REF_MOVED.md);
   the ref's correct target is an operator decision.

Closeout, from exact records: worktree `~/workspace/reiyah-gate-b`, branch `gate-b-measurement`,
the commit that retains this section is the one whose message names it, tree clean after commit;
schemas `v1.3` and the `1.3.0` contract remain `proposed` against released `1.2`; record validation
unchanged, `port` or `spec_reimplementation`; `check_claim_reconciliation.py` returns PASS on this
tree with 64 live artifacts scanned; no transcript or tool that produced a retained result was
edited, so every reproduction dependency is byte-identical to its commit; custody per source is in
the custody record; no result is independently replicated and shared authorship is never independent
validation; operator acceptance, scientific support, external review, runtime, and Gate B authority
all remain none or false. Numbers quoted in the synthesis were checked line by line against their
transcripts and match, except the withdrawn evidence-cost figures.

A successful measurement is an honest descriptive result on public data. It is never, by itself,
scientific support, safety validation, standards compliance, product readiness, competitive
superiority, operator acceptance, or runtime authority. Say only what the evidence says, and say the
open item every time.
