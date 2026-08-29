# Monitor interface contract, and the exact conditions under which "silent" becomes measurable

Document ID: `reiyah.gate-b.monitor-interface-contract`

Version: `0.1.0`

Lifecycle status: `proposed`, contract design only

No empirical record may use the word `silent` under this document. It specifies what an adapter
must supply before that word becomes available. Until an audited adapter supplies every required
operand, Reiyah reports **joint observed miss** only.

## 1. Why the word was withdrawn

`docs/CONTRACT_CAUGHT_AN_ERROR.md` records the correction: a source that observes no warning and
no fallback cannot establish silence. Silence is a property of the **downstream response path**,
not of the detection channels. Two channels missing an object says nothing about whether anything
downstream announced it.

## 2. Admissibility gate

For an opportunity `w`, the disposition `silent_to_system` is admissible only when **all** hold.
Any failure yields `unknown`, never `not_silent`.

1. every evaluated channel records an **observed** miss on `w`, with no `unknown` operand;
2. a versioned monitor is **applicable** to `w`: `w` is inside the declared ODD and inside the
   declared object scope;
3. the monitor is **healthy** for the entire window: no fault, no out-of-distribution flag, no
   abstention;
4. logging is **complete** across every named dependency for the entire window;
5. no qualifying indication and no qualifying fallback occurred before the prespecified deadline.

## 3. Four dispositions, never merged

| Disposition | Definition |
|---|---|
| `silent_to_system` | No channel produced a qualifying detection **and** no monitor produced a qualifying indication before the deadline |
| `not_communicated` | A qualifying indication existed internally, but no delivery event to the human occurred before the deadline |
| `communicated_unacknowledged` | Delivery occurred, and no acknowledgment or qualifying response evidence exists before the deadline |
| `unknown` | Any required operand non-observed: incomplete logs, unhealthy monitor, out of ODD, out of object scope, clock unresolved |

Collapsing these is prohibited. They have different causes, different remedies, and different
safety meanings. `not_communicated` is a delivery defect; `communicated_unacknowledged` is a human
factors result and is **not** evidence of unawareness, because acknowledgment is not awareness
under the same argument as `docs/HUMAN_CHANNEL_FEASIBILITY_2026-08-29.md` section 1.

## 4. Required fields

| Group | Fields |
|---|---|
| Monitor identity | `monitor_id`, `version`, `build_digest`, `config_digest` |
| Dependencies | `input_dependency_set[]`, each with `dependency_id`, `version`, `health`, `observed_at` |
| Applicability | `odd_declaration_ref`, `odd_state` in `{in, out, unknown}`, `object_scope_ref`, `object_in_scope` in `{true, false, unknown}` |
| Thresholds | `threshold_set_id`, exact values, `frozen_at`, freeze evidence reference |
| Alert taxonomy | `alert_class`, `severity`, `modality` in `{visual, auditory, haptic, multi}`, `qualifying` in `{true, false}` under a declared rule |
| Indication lifecycle | `generated_at`, `delivered_at`, `perceptible_at`, `acknowledged_at`, each with state `observed`, `not_observed`, or `unknown` |
| Timing | `window_onset`, `deadline`, `latency_budget`, `clock_source`, `clock_offset`, `max_clock_skew`, `sync_method` |
| Fallback lifecycle | `fallback_requested`, `fallback_initiated`, `fallback_completed`, `fallback_outcome`, each stated separately |
| Health | `monitor_health`, `ood_flag`, `abstention_flag`, `degraded_mode` |
| Log completeness | `expected_record_count`, `observed_record_count`, `gap_intervals[]`, `completeness` in `{complete, incomplete, unknown}` |
| Provenance | `source`, `retrieved_at`, `sha256`, `byte_size`, `rights`, `redistribution_state` |
| Propagation | `unknown_operands[]`, `disposition` |

A field that is absent is `unknown`. A field that is absent MUST NOT default to a favourable
value. There is no default that means "no alert was needed".

## 5. Clock discipline

Indication timing is the whole content of the estimand, so an unresolved clock invalidates the
record. `clock_source` and `max_clock_skew` are required. If `max_clock_skew` exceeds the
`latency_budget`, the ordering of `generated_at`, `delivered_at`, and the `deadline` is not
established and the disposition is `unknown`.

## 6. Adapter authority

The monitor is an **untrusted evidence adapter**, exactly like a dataset. It supplies bytes and
its own provenance. It holds no Reiyah scientific, safety, acceptance, publication, or transport
authority.

**Disclosed dependence is mandatory.** If the adapter shares compute, code, authorship, evaluation
harness, or operator with Reiyah, that MUST be recorded in the record's provenance block. Such an
adapter can supply an observation. It can never supply independent validation, and a result built
on it MUST NOT be described as independently replicated.

## 7. Known-bad cases required before any adapter is admitted

1. an indication generated after the deadline, which must not be counted as communicated;
2. a monitor healthy at window start and faulted mid-window, which must yield `unknown`;
3. a log gap covering the indication interval, which must yield `unknown` rather than
   `silent_to_system`;
4. an object outside the declared object scope, which must be excluded rather than counted silent;
5. clock skew exceeding the latency budget;
6. an acknowledgment recorded with no preceding delivery, which is a log-integrity failure;
7. a synthetic adapter fixture, which must be provably unable to escape into an evidence path.

## 8. Non-claims

This document creates no empirical record, no scientific support, no operator acceptance, and no
safety finding. It authorizes no adapter. It defines the conditions under which one word becomes
usable.
