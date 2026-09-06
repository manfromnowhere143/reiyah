# Threats to validity for the human-channel, LLM-jury and monitor results

Document ID: `reiyah.gate-b.threats-human-and-llm-threads`

Version: `0.1.0`

Lifecycle status: `proposed`

The sensor spine has [`MEASUREMENT_THREATS_TO_VALIDITY.md`](MEASUREMENT_THREATS_TO_VALIDITY.md).
The threads added since (H1 to H7, T through AF) carry their threats inside the register and their
own non-claims; this consolidates them where a reviewer expects them, in the same form: the
strongest version of each attack, what answers it, and what is left open. Nothing here is talked
down.

## Human channel

### 1. Events cluster within drivers and the 100-Car intervals ignore it (open)

The public 100-Car files carry no driver identifier. H7's bands are event-resampled and understate
uncertainty if events cluster within drivers, which they do (about 100 drivers, 828 events). The
eyes-by-hands coefficient's band [1.04, 1.90] would widen; its lower bound is already close to 1.
Answered only by the full-data driver mapping, which is not public.

### 2. The eyes-by-hands coefficient contains a causal component (stated, not removed)

Not looking impairs reacting; part of `c = 1.46` is that mechanism, not latent dependence. H3 says
so. The cell that does not depend on it, looked forward yet did not react, is reported separately
(4.3 percent of events, 23 percent of crashes [12, 36]).

### 3. Forward gaze is not detection (stated)

`Forward` is a glance through the windshield, not fixation on the hazard. H2's two thirds is an
upper bound on attention to the hazard, which strengthens rather than weakens the reading that
observation is not sufficiency.

### 4. The human-machine independence rests on in-lab gaze from an engaged observer (open)

H5 and H6 use BDD-A's aggregate attention heatmap from attentive observers in a laboratory, not a
naturalistic driver, and H3 and H4 show a distracted human's channels collapse. The cross-agent
`c` near 1 is conditional on attention and is a floor on dependence, since objects both channels
miss entirely are unobservable without ground truth. Only a synchronized naturalistic pilot with
human-subjects review answers it; not authorized.

### 5. H5 has no band; H6 does (answered)

H5b re-executed the detector with the clip id recorded per object: c = 0.962 with a
clip-clustered band [0.927, 0.993] on 117 clips. The sample differs from H5's retained run (519
against 651 frames; H5's arguments were not recorded), and the three cross-agent estimates agree
within the band.

### 6. BDD-A terms are not retained (open)

Three retrieval attempts failed on 2026-09-06 and are recorded. The data are not redistributed;
the results may be described as research-use public data and no further until the terms are held.

## LLM juries

### 7. Model selection was not preregistered (open)

The seven candidate models were chosen for family diversity and availability on the archived
leaderboard, before any coefficient was computed, but the choice is not preregistered and a
different seven could give different coefficients. Jury B (seven other families) gives the monitor
transfer result on an independent selection, and the marginal law appears on every jury and
benchmark tried; the specific coefficients are jury-specific.

### 8. Prompt-format non-joins drop models unevenly (stated)

On ARC-Challenge Falcon and two jury B models use a prompt format whose example text differs, so
their questions do not join and they are dropped by a rule stated in advance (Result W). The ARC
juries are therefore six and five models. Every table names the jury actually used.

### 9. The 2024-format files carry no gold answer (answered)

Gold is recovered at join time from a 2023-format model on the same question and checked against
every row's own correctness flag; the check held on 100 percent of rows for every model and
benchmark (Results X, AE). A reviewer can re-run that check.

### 10. Shared difficulty is only partly measured (stated)

The conditional coefficient removes difficulty as measured by the other models, leave-the-pair-out,
in five quantiles. Difficulty the other models do not see remains in the residual. Result AC's
intervals show the residual is above 1 on every benchmark and that its same-lineage part is a MMLU
finding; a finer difficulty measure could shrink the residual further, and the marginal statements
do not depend on it.

### 11. Questions are the resampling unit, not subjects (stated)

AC's intervals resample questions. MMLU questions cluster within 57 subjects; subject-level
resampling would widen the MMLU bands. The bands on the other benchmarks and the sign of every
finding do not depend on it.

### 12. Base models only (open)

Every model is a pretrained base model. Instruction-tuned and RLHF models may couple differently;
the archived leaderboard's chat variants did not carry per-question files for this benchmark set.

## Monitors

### 13. The features were chosen once and not tuned (stated)

The seven LLM-monitor features and the fourteen sensor features were fixed in advance and never
tuned to a held-out result; the boosted model in AD is one class with fixed hyperparameters. This
protects the negative results (Z, AB, X2, AE) from the charge that a better model was not tried,
but it also means the positive results (V, X, AD) are lower bounds on what the form can do.

### 14. The realness label is a labeling matcher, not the validated one (answered)

AA, AB, AD and AG label a detection real by a same-class annotated object within 2 m, one-to-one by
score. The labeler is checked against the validated per-object matcher on every run: every object
the validated matcher scored at or above threshold is marked real, 100 percent on both channels in
every configuration, or the run refuses.

### 15. Transfer across detector pairs shares one channel and one training split (stated)

The second camera and second lidar configurations each share one channel with the primary pair,
and all four detectors were trained on the nuScenes training split. Sensor monitor transfer (AG)
is therefore transfer within one benchmark's detector ecosystem, not across deployments.

### 16. Proposed, not externally audited (the meta-threat, unchanged)

No result in any thread has been independently reviewed. The request is in
[`EXTERNAL_REVIEW_REQUEST_2026-09-06.md`](EXTERNAL_REVIEW_REQUEST_2026-09-06.md).

## Non-claims

An adversarial self-review, retained as `proposed`. It is advisory, not independent review, and
creates no acceptance, authority, or claim. No released `1.2` byte is involved.
