# Executable metric contract: successor design

Document ID: `reiyah.gate-b.executable-metric-contract-successor-design`

Version: `0.1.0`

Lifecycle status: `proposed`

Extends [`EXECUTABLE_CONTRACT_1_3_PROPOSAL.md`](EXECUTABLE_CONTRACT_1_3_PROPOSAL.md). That
document specified the policy-versus-subject split correctly and remains the core of the design.
This one adds what the 2026-08-29 audit established, and separates what can be built in the Gate B
lane from what cannot.

## 1. What the audit added

The `1.3` proposal said extending to real data "requires a new executable contract release". The
audit established that it requires more than that, and the reason is now bound to bytes rather
than inferred. See [`CLAIM_AUDIT_2026-08-29.md`](CLAIM_AUDIT_2026-08-29.md) section 4.

`tools/gate_a_1_2_0_science.py` is Git blob `a32c6cfa948ee1005a99937e54670991999db253`, identical
to the frozen Gate A `C_packet` copy. Its guard `executable_contract_binding_violations` compares
the registry entry against `FROZEN_EXECUTABLE_CONTRACT_DEFINITIONS`, **a constant inside that
released module**, by exact dictionary equality, together with exact `version` and
`owner_protocol_release_id`. So a corrected contract in a new registry is not enough: the module
itself carries the expectation, and changing it means a Gate A science-module successor.

**Two lanes, and only one of them is here.**

| Component | Lane | Status |
|---|---|---|
| Metric record schema, semantic rules, fixtures, port validator | Gate B | **built**, this packet |
| Executable contract release with the policy/subject split | Gate A | designed, not buildable here |
| Science-module successor carrying the new frozen expectation | Gate A | **required**, not buildable here |
| Definition-registry successor binding the contract | Gate A | required, not buildable here |

Nothing in this document licenses touching a frozen Gate A byte, and nothing relaxes the
substitution guard. The guard is not the defect; it is refusing real data because the contract it
was frozen against names a fixture, which is exactly what a substitution guard should do.

## 2. What the record must carry

Beyond the `1.3` proposal's operands, the audit makes the following mandatory. Schema:
`schemas/v1.4/coincident-miss-metric-record.schema.json`, closed properties throughout.

1. **The complete estimand vector, never a bare `c`.** `p_first`, `p_second`, `p_joint`, `c`, the
   four cell counts, the unknown-operand count, the eligible denominator, and the universe
   definition that produced it. Rationale in
   [`ESTIMAND_RSS_DEFINITION_32.md`](ESTIMAND_RSS_DEFINITION_32.md) section 5.
2. **An explicit `c_state`.** `defined`, `undefined_zero_denominator`, or
   `unknown_operand_present`. Counterexample CE-6 shows a stratum where a marginal vanishes;
   coercion to zero, one, or `independent` is prohibited.
3. **Operating-point comparability.** `matched_marginal_miss_rate`, `declared_grid_point`, or
   `convenience_threshold`, plus both thresholds and the matcher identity. CE-4 shows `c` moving
   from 1.8186 to 1.2262 when one operating point moves with the coupling structure untouched, so
   a `c` without its operating point is not interpretable.
4. **Whether the matcher uses channel-specific geometry**, which is prohibited because it
   privileges one modality.
5. **Whether the universe filter is defined on an evaluated channel**, which is prohibited as a
   primary denominator because it induces dependence by construction.
6. **Whether the reference process is independent of every evaluated channel.** Fixture F-04 of
   the M4 work shows channel-dependent contamination moving `c` from 1.0 to 5.0 by construction.
   That yields `invalid`, not a wider interval, and no bound repairs it.
7. **Channel provenance**, including the prediction digest, whether the published headline metric
   was reproduced within a declared tolerance, and **training-corpus overlap with the peer
   channel**, since a shared corpus is a coupling mechanism and must be a declared covariate
   rather than background.
8. **The clustering hierarchy and the primary unit**, with a design effect required whenever the
   primary unit is the detection box. Frame count is not a sample size.
9. **The reference-error identification block, with `delta` rather than an overall error rate.**
   Proposition M4-1 in [`M4_IDENTIFICATION_FINDINGS.md`](M4_IDENTIFICATION_FINDINGS.md) proves `c`
   is scale invariant, so uniform reference error does not bias it and the overall annotation
   error rate is irrelevant. The required parameter is the bound on how much the error rate varies
   across cells. The block also carries the ladder level and the outer set.
10. **`validated_by`**, one of `artifact_of_record`, `port`, `spec_reimplementation`,
    `not_validated`. **Never promotable upward.** No record validated by a port may be described
    as validated by the artifact of record.
11. **Explicit non-claims** as required constants: causal, safety, compliance, vendor comparison,
    and operator acceptance are all `false`; independent replication is `false` or
    `disclosed_dependence`.

## 3. Semantic rules and their coverage requirement

Schema validity is necessary and nowhere near sufficient. Thirteen rules are implemented in
`tools/measure/validate_metric_record_1_4.py`, each with at least one known-bad fixture under
`fixtures/v1.4/known-bad/`. Transcript:
[`metric_record_1_4_validation.txt`](../evidence/measurement/metric_record_1_4_validation.txt).

| Rule | Rejects |
|---|---|
| SR-01 | cells that do not sum to the eligible denominator |
| SR-02 | a reported `c` that is not recomputable from the cells |
| SR-03 | a zero marginal coerced to a number instead of the undefined state |
| SR-04 | an unknown operand that does not propagate into `c_state` |
| SR-05 | a universe filtered by an evaluated channel |
| SR-06 | a reference process not independent of every evaluated channel |
| SR-07 | a matcher using channel-specific geometry |
| SR-08 | a channel that failed its headline reproduction gate |
| SR-09 | a box-unit record with no design effect |
| SR-10 | an `L3` identification claim not resting on blinded reannotation |
| SR-11 | an outer identification set that does not contain the inner sampling interval |
| SR-12 | a port-validated record claiming `supported` |
| SR-13 | a non-sufficient stratum claiming `supported` |

**The run fails unless every rule is rejected by at least one applicable fixture.** A rule with no
counterexample is untested, and an untested rule is not a rule. Current state: 13 declared, 13
covered, good fixture clean, `RESULT: PASS`, byte-identical across runs.

A fixture may trip more than one rule. That is acceptable provided it trips its declared rule;
pretending a cell-sum mutation leaves `c` recomputable would mean weakening one of the two checks.

## 4. What this design deliberately does not do

It does not issue a contract. It does not register anything. It does not modify a released byte.
It does not relax, subset, or make advisory any substitution guard. It does not permit a
`port`-validated record to claim `artifact_of_record`. It emits no empirical record: every fixture
here is synthetic.

## 5. Non-claims

No scientific support, no operator acceptance, no safety or compliance finding, no comparative
claim about any detector or vendor. No released `1.2` byte is modified.
