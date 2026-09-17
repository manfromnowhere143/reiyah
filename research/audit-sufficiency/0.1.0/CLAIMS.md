# Claim-by-claim status, research lane, 17 September 2026

Status vocabulary: `checked` (independently recomputed by the Engine or by a separate
implementation), `conditional` (holds under a stated premise), `unresolved`, `contradicted`,
`superseded`. Scope is stated per row. Nothing here is a physical claim or a human measurement.

| # | Claim | Status | Scope and evidence |
|---|---|---|---|
| 1 | A minimum deletion witness is not a sufficient audit; two disjoint 49-witnesses exist on the forty-frame case | checked | Engine review 15 Sep; reproduced by the MILP here |
| 2 | Exact minimum sufficient audits: 9 of 106 (first case), 53 of 737 (second case) | conditional | implicit hitting set with solver-tier certificates; deletion family, one world; not Engine-replayed |
| 3 | Forty-frame minimum sufficient audit | superseded | this lane's [306, 373] is superseded by the Engine's exact 372 (main `0d6f116`) for the unrestricted-deletion confirmed-present count problem |
| 4 | Every one of the 1,125 supported census verdicts is overturned by exactly `floor` deletions | checked | additive pool meets the floor in every unit; Engine replay of all 3,000 decisions: 2,981 exact, 19 containing bounds, 0 disagreements |
| 5 | Random deletion at the floor never crossed in 200 trials for 1,048 of 1,125 verdicts | conditional | Monte Carlo with digest-derived seeds (repaired from process hash); not Engine-replayed |
| 6 | Audit lower bound (pool cut) median 11.5% of labels; certified upper bound median 17.7% | conditional | deletion family; upper bounds from one policy, local; lower bound proven per unit |
| 7 | Split-level deletion margins for nine supported pairs | checked | six exact minima and three intervals agree with the Engine's weighted composition (main `b41963e`); universal lower and attained upper bounds kept apart |
| 8 | Split-level 260-label witness overturns PointPillars + Mapillary | checked | Engine recomputation |
| 9 | Localization 0.1.0 census statuses | superseded | 0.1.0 had two defects (inner boundary; residual freeze) and 0.2.0 a radius convention defect at 0.1 m (binary float); replaced by 0.2.1 results in `localization-summary.json` |
| 10 | Localization 0.2.0: inner-boundary and residual controls | checked | both retained controls now yield exhibited shifts; the residual shift (13/250, -21/250) verified by the Engine's `localization` command as `refuted_by_displacement` |
| 11 | Forty-frame verdict robust to 0.1 and 0.25 m | checked | Engine conventional bound (lower improvement 1/2 at 0.25 m) and this lane's solver tier agree |
| 12 | Forty-frame verdict robust to 0.5 m | checked (certificate) | solver-free rational certificate `forty-frame-dual-certificate-0.5m.json`, verified by `verify_dual_certificate.py` without a solver: certified max drop 21/10 against margin 49/20; the Engine's conventional bound stays unresolved at 0.5 m |
| 13 | Exhibited geometric counterexamples in the census (44 under 10 cm, 97 under 25 cm, 128 under 50 cm, 107 under 1 m) | checked | displacement vectors retained privately; 375 of 376 accepted by the Engine's `localization` command as `refuted_by_displacement`, one Engine work-limit |
| 14 | Insertion monotonicity theorem | checked | proof in README; exhaustive 1,236,958-case check; randomized test |
| 15 | Cost to a checked decision (frozen plan) | conditional | `cost-experiment.json`: deletion family, hitting set online wins 12 of 12 certified cases against the strongest conventional selector and fails to certify 3 within 200 rounds; counterexample-guided 2 wins, 5 draws, 8 losses; 3 to 6 times the computation; localization at 0.5 m mostly needs no query; 0.25 m residual leaves the fragile case uncertifiable |
| 16 | Reuse of observations on a distinct comparison | conditional | `reuse-experiment.json`: 20 pairs, same base and scene, different addition; second-comparison deletion queries 39% of fresh with per-record applicability; localization reuse negligible; not A-to-B replacement |
| 17 | Retained census index reproduces under an unrotated global-XY range rule; preparation gate now rejects mismatches and passes its negative control | contradicted in part | detections reproduce; 660 units differ by 1 to 2 annotations near 50 m; the index's generating driver was not committed |
| 18 | Any human-time or money saving | not claimed | |
| 19 | Solver-free certificates across the localization census | checked (certificate) | `dual-summary.json`: 100% of solver-robust verdicts certified at 10 cm, 99.4% at 25 cm, 96.4% at 50 cm, 84% at 1 m, plus 17 verdicts at 1 m certified where the solver timed out; certificates reproducible by `verify_dual_certificate.py --emit`; deletion program's LP relaxation too loose to certify (reported) |
