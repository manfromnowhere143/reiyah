# Gate A 1.1.2 Adversarial Review

## Status and authority

This record freezes an internal adversarial review of the exact public Gate A 1.1.2 repository
state at commit `656d826cfe6938fd628c0ede7ea15929fe11d90e`. The reviewed packet commit is
`ad1a8cae6ad17f26f5a07f43fb60b6c9f55b4b1b` and the reviewed evidence index digest is
`sha256:17f3a2e601e9cb4e1c0cd0f97561b1da9ffdc7d5893ed4af4eaccbaf8a67989f`.

The review is advisory. It was performed with model assistance and verified through local
counterexample construction. It is not independent external evidence, operator acceptance,
scientific support, a safety assessment, a standards opinion, or runtime authorization.

The canonical Gate A 1.1.2 validator reproduced its retained report byte for byte and returned
zero diagnostics. The counterexamples below nevertheless passed that validator. This distinction
is the reason for a new protocol and packet successor rather than an in-place repair.

## Review method

The review traced each normative statement through four layers:

1. the mathematical specification;
2. the protocol and definition registries;
3. the application schema that claims to encode the statement;
4. the validator rule and a minimally changed synthetic counterexample.

A control was treated as executable only when a counterexample violating the stated invariant
was rejected for a stable, reason-specific diagnostic. Schema shape, prose, a declared boolean,
and a passing fixture were not treated as proof of semantic enforcement.

## Scientific contract findings

| ID | Severity | Gate A 1.1.2 defect | Counterexample accepted by 1.1.2 | Gate A 1.2.0 disposition |
|---|---|---|---|---|
| AR-001 | Critical | Sequential off-policy evaluation computed effective sample size across step ratios instead of cumulative trajectory weights and lacked complete action distributions. | A two-step trajectory with zero cumulative target-policy weight still reported an effective sample size of one. A one-action policy also assigned probability below one. | Require normalized behavior and target distributions for every frozen history, exact logged-action reconciliation, support cells, cumulative weights by horizon, declared transformations, and trajectory-level effective sample size. |
| AR-002 | Critical | Causal adjustment validity was declared rather than derived. The validator checked graph references and acyclicity but not temporal role, observability, forbidden mediators or colliders, or the selected identification criterion. | A post-treatment mediator marked as prohibited was accepted in the selected adjustment set. | Require typed treatment, outcome, estimand, graph, temporal and observability evidence, a machine-derived identification disposition, and strategy-specific validity checks. |
| AR-003 | High | A confident aggregate readiness value could coexist with an unknown required capability. | A required capability changed to `unmeasured` while the aggregate remained observed at `0.99`. | Bind every aggregate to an executable capability rule. Any required unknown propagates to an explicit unknown aggregate unless a preregistered partial estimand is used and labeled. |
| AR-004 | High | Recoverability summaries were not reconciled with event history or the observation window. | A ten-second record reported `time_to_recovery` as 999 seconds and terminal recovery without a qualifying recovery event. | Derive event time, censoring, competing-event, and invalid dispositions from the earliest qualifying event and the frozen observation window. |
| AR-005 | High | The transfer contract omitted metric direction, harmonization, overlap, invariance, adaptation, tuning, access chronology, and coverage needed by the mathematical specification. | A transfer result could be schema-valid without enough information to interpret its sign or eligibility. | Require exact metric and domain identities, direction, population, harmonization, overlap, invariance, adaptation and tuning disclosure, access chronology, uncertainty, and an explicit eligibility disposition. |
| AR-006 | High | A conformal guarantee could remain unqualified after an assumption was recorded as false. | `exchangeability=false` was accepted beside an unqualified finite-sample guarantee statement. | Separate a structured guarantee claim from empirical coverage. A failed or unknown required assumption forces the guarantee disposition to unsupported or not applicable. |
| AR-007 | Medium | Out-of-distribution and selective-prediction counts and rates were not bound to an exhaustive denominator partition. | Counts totaling 24,000 and arbitrary rates were accepted for a population of 100. | Require disjoint and exhaustive counts, exact rate arithmetic, threshold chronology, unresolved-state accounting, and coverage-performance reconciliation. |
| AR-008 | Medium | Worst-group minimum-information eligibility was asserted through prose and a boolean. | A group with sample size one was marked sufficient and accepted. | Require typed count, coverage, effective-sample-size, and interval-width rules. Derive eligibility and preserve an unknown overall result when a required group is ineligible. |

## Validation and custody findings

| ID | Severity | Gate A 1.1.2 defect | Demonstration | Gate A 1.2.0 disposition |
|---|---|---|---|---|
| AR-009 | High | The installed JSON Schema format checker did not implement every format used by indexed schemas. | Invalid `date-time` and `uri` strings passed because the optional checker entries were absent. | Register deterministic local checkers for the exact permitted format set, scan all schemas for undeclared formats, and run positive and negative canaries. |
| AR-010 | High | Validation read the live worktree repeatedly and index construction performed a later independent read. | A concurrent change could present one byte sequence to an early semantic check and another to the index builder. | Validate one immutable byte snapshot. Release mode reads a resolved regular-blob Git tree. Development mode snapshots the selected worktree bytes and rejects any pre-to-post fingerprint drift. |
| AR-011 | Medium | Offline and read-only guards began after Python imports and ordinary invocation allowed user-site and path shadowing. | Third-party or shadow modules could execute before the validator established its claimed boundary. | Use a standard-library bootstrap, isolated Python, dependency byte verification, and a digest-bound macOS sandbox that denies network access and repository writes before third-party import. Report the platform-conditional boundary exactly. |
| AR-012 | Medium | The offline validator treated a locally authored receipt as if it independently proved current GitHub state. | Receipt fields and assertions could be internally consistent without a trusted remote observation. | Classify repository receipts as retained transport assertions. Offline validation reports transport as `not_evaluated`. A separately retained observation record is required for any scoped remote-verification claim. |

## Correction boundary

Gate A 1.2.0 may correct only static architecture, schemas, synthetic fixtures, deterministic
validation, custody semantics, and documentation needed to make the controls executable. The
mission remains `reiyah.mission@1.1.0`. The corrected scientific contract requires the new
protocol release `reiyah.protocol.harbor-gate-a@1.2.0`.

The correction does not authorize data collection, model execution, policy execution, cloud
infrastructure, private-data ingestion, live vehicle integration, deployment, publication of an
empirical result, Gate B, or physical control. It also does not establish that the proposed
constructs are valid or useful. Those questions remain open until eligible evidence and explicit
operator decisions exist.

## Closure criterion

A finding is closed only when all of the following are true for the same immutable candidate:

1. the normative definition is machine-readable and version-bound;
2. the schema requires the information needed to evaluate the invariant;
3. the validator derives the result rather than trusting a self-asserted conclusion;
4. a known-good fixture passes;
5. a minimally changed known-bad fixture fails for the declared diagnostic;
6. the full report and evidence index are deterministic and byte-bound;
7. an adversarial replay cannot reproduce the original accepted counterexample.

Until all seven conditions hold, the finding remains open and Gate A 1.2.0 must not be described
as architecture complete.
