# External review request, 2026-09-06

Document ID: `reiyah.gate-b.external-review-request-2026-09-06`

Version: `0.1.0`

Lifecycle status: `proposed`

No result in this repository has been independently reviewed. That is the honest ceiling on every
claim here and the one thing the authors cannot supply themselves. This document is what a reviewer
needs to start without asking: the exact subject, the claims ranked by how much would fall if each
were wrong, the reproduction commands, the known threats, and what counts as a finding. A review
that returns nothing but "reproduces" is worth less than one that breaks a claim; the register is
built to record breakage.

## Subject

Review the exact commit named in the closeout section of
[`GATE_B_SESSION_HANDOFF.md`](GATE_B_SESSION_HANDOFF.md) on branch `gate-b-measurement` of
`https://github.com/manfromnowhere143/reiyah`. Resolve every claim from
[`evidence/claim-status-register-2026-09-06.json`](../evidence/claim-status-register-2026-09-06.json),
never from prose; the register lists each claim's status, unit, source custody, retained transcript,
and what would move it. `tools/measure/check_claim_reconciliation.py` must pass on the commit.

## Claims ranked by what falls if each is wrong

1. **The conditional camera-lidar coefficient exceeds 1 on a common support** (Results L, M, N, O,
   Q; register `conditional-coincident-miss-convergence`). If the matcher, the stratification or
   the common support is wrong, the sensor spine falls. Attack the matcher first: it reimplements
   the devkit accumulation and is gated only by reproducing published mAP.
2. **Same-kind pairings couple more than cross-kind pairings** (Q, T, W, Y; H3, H5, H6). The
   sensor cell rests on one lidar-lidar and one camera-camera pair; the LLM cell rests on three
   Llama sizes; the human-machine cell rests on in-lab gaze from an engaged observer. The conditional
   same-minus-cross margin is 0.01 on HellaSwag (Y). Any of these can narrow the law's second arm.
3. **The evidence-cost direction** (register `evidence-cost-direction`) is qualitative only. Every
   figure derived from it is withdrawn as stated with five unmet conditions; confirm none is asserted.
4. **The LLM monitor transfers across juries and not across benchmarks** (V, X). Gold for the
   2024-format leaderboard files is recovered at join time; verify the per-row check.
5. **The two-sensor monitor conjecture is unsupported** (Z, AA). A reviewer who builds a sensor
   monitor that beats the density and own-feature baselines outside the fold spread overturns this.

## Reproduction

Sensor spine, human channel and LLM threads each reproduce from their own README commands
(`README.md` section "Reproduce the static checks" points to the Gate A launcher, which is separate;
the measurement commands are in `GATE_B_SESSION_HANDOFF.md` section 9, `human-channel/README.md`
and `llm-generalization/README.md`). Every tool is seeded and must re-run byte-identically against
its retained transcript; a reviewer who observes a byte difference has found a finding, not a
nuisance. Large intermediates are regenerated, never trusted from the repository. Detector match
sets must pass their `--validate` mAP gate or nothing downstream is believed.

Data access a reviewer needs: nuScenes trainval metadata (terms of use, SHA-256 pinned), the four
detectors' released predictions, 100-Car (CC0), DCPT (CC BY 4.0, three files in the repository),
BDD-A (research use, from the Berkeley portal), and the Open LLM Leaderboard v1 archive on Hugging
Face. Custody for each is in
[`PUBLIC_DATA_CUSTODY_2026-09-06.md`](PUBLIC_DATA_CUSTODY_2026-09-06.md).

## Known threats, already on record

[`MEASUREMENT_THREATS_TO_VALIDITY.md`](MEASUREMENT_THREATS_TO_VALIDITY.md) lists nine, of which
shared training data, one benchmark and one split, detection as a proxy for the RSS subsystem, and
the absence of external audit remain open. The LLM threads add: benchmark-dependence of the lineage
mechanism (Y), the leaderboard's prompt-format non-joins, and question-level rather than
subject-level resampling for intervals (AC).

## What a review returns

A review is retained as a dated record naming the reviewer, the exact commit reviewed, each claim
examined with its verdict (`reproduced`, `narrowed`, `contradicted`, `not_examined`), and the
evidence. It is advisory until the register is updated from it; a reviewer's signature is not
acceptance and reproduction is not scientific support. Shared authorship, code or compute with the
authors disqualifies a review as independent and must be declared.

## Non-claims

A request and a map, not a review. It creates no acceptance, authority, or claim, and it modifies no
released `1.2` byte.
