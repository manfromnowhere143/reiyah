REIYAH RESEARCH LANE: CONTINUATION PROMPT FOR THE NEXT FABLE 5 SESSION
Prepared 17 September 2026 by the session that executed the research-lane work from 16 to
17 September (Opus 5, standing in for the Fable lane). Execute the work; do not produce another
strategy document. Daniel authorizes bounded offline work. No cloud, no inference campaign, no
human audit, no post, no outreach.

IDENTITY, OWNERSHIP, RULES THAT DO NOT BEND

Canonical repository: /Users/danielwahnich/workspace/reiyah (read AGENTS.md and
docs/SESSION_HANDOFF.md first; the identity gate and the continuation resolver are binding).
Remote: https://github.com/manfromnowhere143/reiyah.git (distribution channel, never authority).
Your branch: research/2026-09-16-audit-sufficiency. Latest commit: b3125c4a97c0029a1f70aba7d0ab5105a9b3d233
(pushed; readback observed; not independent transport verification).
Your report directory: /Users/danielwahnich/.codex/reports/reiyah/opus-audit-sufficiency-2026-09-16-d38b4f32/
  candidate/   git worktree of your branch (the only place you edit code)
  inputs/      sealed inputs with SHA256SUMS (six case files, Fable census index, Engine source list)
  private/     identity-bearing outputs (nuScenes annotation tokens): census units with
               coordinates, per-unit results, displacement vectors, query histories, controls
  OUTBOX/      audit-sufficiency-0.1.0 (consumed by Engine), 0.2.0 and 0.2.1 (sealed; 0.2.1 is current)
Engine (Codex/Astra) owns: source qualification, comparison semantics, common proof checking,
main integration, tools/perception_decision and tools/perception_revision. You own: query
selection, stronger optimization, conventional comparators, counterexample searches, complete-cost
experiments, and research/audit-sufficiency/0.1.0 on your branch. Do not edit main, the Engine's
worktrees, frozen Gate A files or closed Engine reports. Never push main.
Commits: configured human identity (Daniel Wahnich), no AI, co-author, generated-by or session
trailers, ever. Repository documents contain no em dash. Identity-bearing bytes (annotation
tokens, record indices) never enter Git; every committed JSON is scanned for 32-hex tokens first.
Runtime: /Users/danielwahnich/.codex/reports/reiyah/engine-discovery-custody-2026-09-13/private/runtime/bin/python
with -B and env -u PYTHONPATH. Reiyah custody for data: /Users/danielwahnich/workspace/reiyah-gate-b
(predictions/, meta.tgz); never read sibling repositories (sentinel, telos, inbar, odeya, aweb).

WHAT EXISTS ON THE BRANCH (research/audit-sufficiency/0.1.0), WITH THE NUMBERS THAT ARE CHECKED

Read README.md end to end, then CLAIMS.md (19 claims with status and scope), then WRITEUP.md.
- sufficiency.py: deletion-family audit sufficiency certificate with four tiers kept apart:
  sound (rational bound), dual (solver-free LP-duality bound; too loose for deletion, reported),
  solver (MILP via Konig duality, HiGHS), achieved (exact counterexample). ihs.py: implicit
  hitting set with the additive-pool cardinality cut (exact minimum sufficient audits 9 of 106 and
  53 of 737; forty-frame minimum superseded by the Engine's exact 372).
- census_units.py: rebuilds all 3,000 census units from custody under --range-rule global_xy; the
  preparation gate rejects mismatches and passes its negative control. census_run.py and
  census_summary.py: deletion census (1,125 supported verdicts; every one overturnable at its
  floor because the additive pool meets the floor; random deletion at the floor never crosses in
  200 trials for 1,048 of 1,125). engine_agreement.py: all 3,000 decisions through the Engine kernel
  and checker: 2,981 exact, 19 resource-limited containing bounds, 0 disagreements.
- localization.py 0.2.1: closed reference balls, exact rationals from source decimals (radius
  included), guaranteed iff e < R and s < (R - e)^2, possible iff s < (R + e)^2, returned centre
  and residual radius per confirmed position, displacement vectors retained. Both Engine controls
  that 0.1.0 reported falsely robust now yield exhibited shifts. localization_census.py: 1,125
  verdicts at 10 cm / 25 cm / 50 cm / 1 m: robust 1,077 / 986 / 813 / 495; exhibited geometric
  counterexamples 44 / 97 / 128 / 107. engine_localization_exchange.py: 375 of 376 exhibited
  counterexamples accepted by the Engine's `localization` command as refuted_by_displacement.
- dual_certificate.py, verify_dual_certificate.py, dual_census.py: solver-free certificates
  (Neumaier-Shcherbina with rational multipliers); forty-frame verdict certified robust at 0.5 m
  (certified max drop 21/10 against margin 49/20; the Engine's conventional bound is unresolved
  there); census-wide 100% / 99.4% / 96.4% / 84% of solver-robust verdicts certified at the four
  radii, plus 17 verdicts at 1 m certified where the MILP timed out.
- split_level.py: leaderboard margins for 20 ordered pairs; universal lower bound and attained
  upper bound kept apart; six exact minima and three intervals agree with the Engine.
- cost_experiment.py under PLAN_COST_EXPERIMENT.json (frozen before outcomes): deletion, hitting
  set online wins 12 of 12 certified cases against the strongest conventional selector and fails
  to certify 3 within 200 rounds at 3 to 6 times the computation; counterexample-guided 2 wins,
  5 draws, 8 losses. Localization at 0.5 m: 10 of 13 cases need no query; a 0.25 m residual against
  a 0.5 m question leaves the fragile case uncertifiable (precision limit, not selection).
- reuse_experiment.py: 20 pairs sharing base and scene, addition changed: second-comparison
  deletion queries 39% of fresh with per-record applicability; localization reuse negligible.
- Theorem (README, tested): adding a reference object never lowers TP_aug - TP_base. Hence a
  class change can overturn a verdict but never by more than deleting the same label; deletion is
  the worst case over presence and class errors for supported verdicts; insertion threatens
  excluded verdicts. Do not write "class errors cannot overturn a verdict"; that is false.

WHAT WE LEARNED THAT MUST SHAPE HOW YOU WORK

1. Tiers never merge. Sound, dual, solver, achieved, observed: separate fields, separate words.
   A solver optimum is a claim; a rational dual certificate is a proof; an exhibited displacement
   is a counterexample under the declared model, never a physical error.
2. Exactness is in the conventions, not only in the arithmetic. Two defects came from float
   handling: a boundary comparison on the wrong side of equality, and a radius built from the
   binary float 0.1 (5.5e-18 too large) that the Engine rejected 41 times. Every coordinate and
   radius goes through the decimal text of the source value; tests use rational strings.
3. A grid that finds no displacement is "not found", never "infeasible".
4. A measurement with residual error r cannot fix any edge within r of the matching boundary. The
   audit product needs precision at the boundary; more queries do not substitute.
5. Freeze plans before outcomes (PLAN_COST_EXPERIMENT.json is the template): cases, semantics,
   family, query unit, answer source, residual, budgets, digest-derived seeds, stopping obligation.
   Count every query until the first checked decision; never subtract because a certificate can
   later be shrunk; a run that does not certify is never a win.
6. Reproduce before you claim: the retained census index could not be exactly reproduced because
   its driver was never committed (660 units differ by one or two annotations near 50 m). Commit
   generators, gate rebuilds against sealed bytes, keep a negative control for the gate.
7. Process hygiene on this Mac: detach long jobs with nohup and < /dev/null (background pipes get
   stopped with exit 144); kill orphaned multiprocessing workers after any interrupted run (pkill
   -f spawn_main) or they silently eat CPU for an hour; use solver time limits (SIGALRM cannot
   interrupt HiGHS); never rebuild the unit directory while a census reads it; stdout to a pipe is
   block-buffered (use -u).
8. Empty families make hitting-set programs infeasible: when every moved object is already
   confirmed under residual answers, stop with no_candidates.
9. Every number in a document binds to a committed JSON; every commit message says what was
   proved, what is conditional, and what was superseded; first failures are retained, not erased.

NEXT STEP (do this first, in this order)

A. Consume the Engine's reply to OUTBOX/audit-sufficiency-0.2.1/REQUEST.md when it exists (verify
   its manifest and every payload; committed origins against Git blobs). Expected: replay of the
   376 witnesses (375 refuted_by_displacement, one work-limit) and of the forty-frame 0.5 m
   certificate (`certified max drop 21/10`, `robust certified`). Any witness rejected for a reason
   other than the Engine's work limit is the first falsifier; record it before anything else.
B. Close the deletion certificate gap. The LP relaxation of the deletion program is half-integral
   and useless. Two routes, both checkable: (1) add the additive-pool cardinality cuts and the
   Konig cover inequalities of the confirmed subgraph to the relaxation and re-derive the dual
   bound; (2) adopt the Engine's combinatorial confirmed-present construction (its 372 proof) as the
   certificate format for sufficiency and emit it from your policies. Measure on the three
   development cases and the twelve census-sample cases which route certifies which final sets.
   Falsifier: a certified-sufficient set with an adverse deletion that crosses.
C. Hitting set online on the three largest deletion cases: raise the round budget by declared
   amendment to the frozen plan (record it as an amendment, do not edit the plan in place), rerun
   those three cases, report queries and computation. If it still does not certify, report that.
D. Residual precision study: for the fragile localization cases, compute the minimal residual
   radius at which the guided audit can certify at all (bisection on r with the same stopping
   rule). That number, per verdict, is the measurement precision the audit requires; it is the
   physical specification a validation team would act on.

AFTER THAT

E. Replacement contract: when the Engine's A-to-B replacement inputs are available, run both
   censuses on replacement (the theorem's containment premise no longer holds, so insertion becomes
   a threat to supported verdicts too; both families must be run). Do not silently interpret B as
   the additions retained after suppression against A.
F. Structured adverse-set generator for the implicit hitting set at census scale (joint inert-label
   sets from the additive-pool complement), so exact minimum audits exist beyond the small cases.
G. Write-up revision (WRITEUP.md) with the certificate tier and the cost and reuse results, every
   number bound; then Daniel decides on the post. Post readiness in Daniel's voice: no vendor
   names, submissions called what they are, families and conditionality stated, the class-error
   sentence in its correct form.

DELIVERY

Fresh isolated candidate from your branch head; fresh output identity; new outbox version
(0.3.0), never overwriting a sealed manifest. Seal with MANIFEST.json (per-payload SHA-256 and
committed or generated origin), CLOSEOUT.json (delivered, first failures retained, unresolved),
REQUEST.md (one concrete consumer action for the Engine) and an updated CLAIMS.md with a status
for every claim: checked, checked (certificate), conditional, unresolved, contradicted, superseded.
Run test_controls.py (8 tests) before every commit; scan committed JSON for tokens. Finish with one
measured result, its limits, and one next falsifier. If a stronger method loses to the competent
baseline, say so and name the measured bottleneck.
