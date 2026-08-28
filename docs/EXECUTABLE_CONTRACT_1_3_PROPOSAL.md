# Executable contract 1.3: separating the policy from the subject

Document ID: `reiyah.executable-contract-1-3-proposal`

Version: `0.1.0`

Lifecycle status: `proposed`

## The finding

`schemas/v1.3` fixes three representational limits and lets a real 134,565-row joint-miss record
pass JSON Schema validation with zero errors. That is structural conformance only.
`docs/MATHEMATICAL_SPECIFICATION.md` section 9 is explicit that schema validation is necessary and
not sufficient, and that the offline validator must additionally perform deterministic semantic
checks. Those live in `tools/gate_a_1_2_0_science.py`.

The semantic layer will not accept the record, and the reason is not arithmetic. In
`joint_violations`, before any cell reconciliation runs, the executable contract drawn from the
scientific profile is compared against a fixed expectation. That expectation pins, by exact
equality:

| Operand | Pinned value |
|---|---|
| `object_ref` | `reiyah.object.synthetic_vehicle` |
| `human_channel_ref` | `reiyah.channel.synthetic_human_observation` |
| `automation_channel_ref` | `reiyah.channel.synthetic_automation_observation` |
| `clock_id` | `reiyah.clock.synthetic-utc` |
| `window_id` | `reiyah.window.joint-opportunity-001` |
| `opportunity_set_ids` | the three synthetic sets |
| `common_opportunity_cells` | the four v1.2 role-named cells, in order |

Any deviation raises `ScienceContractError: joint silent-miss executable contract has an
unrecognized operand`.

## What this is, correctly characterised

This is **not** a bug, and it is important to say so precisely rather than score a point.

It is a substitution guard. Its purpose is to prevent the contract being weakened by editing the
profile: a validator that enforced whatever contract it was handed could be neutered by rewriting
the contract. The guard makes the validator refuse to run against a contract it was not written
for. That instinct is correct and `AGENTS.md` requires it: never weaken a validator to make
validation pass.

The Gate A `1.2` envelope is also openly synthetic. `docs/SESSION_HANDOFF.md` states that
scientific fixtures are deterministic synthetic counterexamples and never empirical evidence, and
that the `1.2` application envelope exposes only an explicit evidence-gap binding. The contract is
doing what it says it does.

**The finding is narrower and more useful: extending to real data requires a new executable
contract release, not merely a schema successor.** A schema successor alone gets you a
structurally valid record that the semantic layer will still refuse. That is the correct outcome
and it is what happened.

## The design defect underneath

The guard conflates two different things.

**Policies** are the contract. `marginal_derivation`, `identifiability_policy`,
`joint_unknown_propagation`, `row_derivation_policy`, `silent_joint_miss_policy`,
`opportunity_manifest_resolution_policy`. These are the semantic commitments. If any of them
changes, the contract has changed and the validator must refuse.

**Identifiers** are the subject. `object_ref`, `clock_id`, `window_id`, the channel references, the
opportunity set identifiers. These say *which data* the contract is being applied to. They carry no
semantic commitment at all.

Pinning both by exact equality means the contract cannot be pointed at a second dataset without a
new release, and the guard cannot distinguish a weakened policy from a different subject. A
validator should refuse the first absolutely and permit the second under a declared binding.

## The 1.3 proposal

Split the guard.

1. **Policy operands remain pinned by exact equality.** No relaxation. A changed policy is a
   changed contract and the validator must refuse to run.

2. **Subject identifiers move into a declared `subject_binding` block** carrying the object kind,
   clock, window, channel references, and opportunity set references for the dataset under
   analysis. The guard checks the binding's *shape* and required kinds, not its literal values.

3. **The channel references become an ordered pair with explicit roles**, matching the
   `channel_contract` introduced in `schemas/v1.3`, so a machine-versus-machine comparison is
   expressible in the executable contract as it now is in the schema.

4. **Cell names follow the schema**, moving from `human_only_miss` and `automation_only_miss` to
   `first_only_miss` and `second_only_miss`.

5. **A subject binding is itself versioned and digest-bound**, so pointing the contract at a new
   dataset is a recorded, reviewable act rather than a silent edit. The protection the current
   guard provides is preserved; what changes is that it protects the right thing.

## What must not happen

The guard must not be removed, loosened to a subset check, or made advisory. The failure mode it
prevents is real: a validator that accepts any contract handed to it validates nothing. If the
choice is between a validator that refuses real data and a validator that can be talked into
anything, the current design is the correct one and should be kept until a proper successor exists.

This proposal is not that successor. It is the specification of what the successor must do.

## Status

`proposed`. No released byte is modified. No contract is issued. `schemas/v1.3` remains a
structural successor whose semantic counterpart does not yet exist, and the real record therefore
remains **structurally valid and semantically unvalidated**, which is the honest description of its
state.
