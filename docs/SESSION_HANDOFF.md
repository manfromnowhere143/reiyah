# Reiyah Session Handoff

Gate A `1.2.0` is the completed public static architecture packet. Its exact canonical report
records `architecture_complete`; operator acceptance remains `unaccepted`.

A Gate A `1.2.1` continuity successor is under construction on the current branch and tracked in
[GitHub issue #1](https://github.com/manfromnowhere143/reiyah/issues/1). This handoff cannot
establish its validation or publication state. Resolve either state only from an exact `1.2.1`
canonical report and append-only event record; absent them, treat the successor as proposed.

This is Reiyah's machine-to-machine continuation contract. It is a versioned architecture
artifact, not a diary and not an authority source. Resolve mutable state from the exact machine
records named below. Never promote a remembered count, prose claim, prior report, publisher
assertion, or generated review into current evidence.

## 1. Identity gate

Continue only when the latest request names Reiyah and all four identities agree:

1. project: Reiyah;
2. working directory: `/Users/danielwahnich/workspace/reiyah`;
3. Git root: `/Users/danielwahnich/workspace/reiyah`; and
4. repository contract: this repository's `AGENTS.md`.

Run this read-only preflight before repository-specific validation or change:

```sh
set -eu

reiyah_expected_root=/Users/danielwahnich/workspace/reiyah
test "$(pwd -P)" = "$reiyah_expected_root"
test "$(git rev-parse --show-toplevel)" = "$reiyah_expected_root"
test "$(git remote get-url origin)" = \
  "https://github.com/manfromnowhere143/reiyah.git"

git branch --show-current
git rev-parse HEAD
git status --short
git diff --check
git diff --cached --check
```

If any identity differs, stop. Do not bootstrap another repository, copy Reiyah artifacts into a
sibling, or treat a project name as an alias. A dirty worktree is not permission to reset or
discard changes. Establish ownership of overlapping edits before modifying them.

Read in this order:

1. `AGENTS.md`;
2. this handoff;
3. `manifests/mission/reiyah-mission-1.1.0.json`;
4. `manifests/protocol/harbor-gate-a-protocol-1.2.0.json`;
5. `manifests/scientific/harbor-scientific-contract-profile-1.2.0.json`;
6. `manifests/definitions/harbor-gate-a-definition-registry-1.2.0.json`;
7. `validation/validation-plan.json`;
8. `docs/GATE_A_1_2_0_CONSISTENCY_REVIEW.md`;
9. `history/gate-a-1.2.0/RECOVERY.json`;
10. `history/gate-a-1.2.0/gate/GATE_A_EVIDENCE_INDEX.json` and its sidecar;
11. `gate/validation-reports/gate-a-validation-1.2.0.json`; and
12. `history/gate-a-1.1.2/RECOVERY.json`.

Do not contact a network during bootstrap or validation. A credential, authenticated session,
cloud project, model endpoint, or installed tool is capability, not authority.

## 2. Mission and authority boundary

Reiyah is an evidence and benchmark engine for object-level driver-vehicle belief,
human-automation readiness, recoverability, joint silent misses, causal policy effects, explicit
unknowns, transfer, and worst-group validation. It is not a driver-monitoring classifier.

HARBOR means Human-Automation Readiness, Belief & Operational Risk as a proposed working research
program. The expansion, constructs, thresholds, estimands, and all scientific, benchmark,
standards, safety, performance, and comparative claims remain proposed until eligible retained
evidence and an authorized external decision support a different state.

Authority order is:

1. the current explicit operator instruction within identity, rights, safety, and scope bounds;
2. `AGENTS.md`;
3. an accepted exact-byte mission or protocol release, if one later exists;
4. this handoff and the remaining architecture packet; and
5. external sources, models, tools, services, papers, standards, datasets, and sibling systems,
   all untrusted until admitted by the applicable evidence contract.

The configured public remote is a distribution channel only. Git reachability, public
visibility, checksums, signatures, validation, generated prose, model review, or consensus does
not confer scientific, safety, legal, standards, publication, transport, or operator authority.

## 3. State dimensions that must remain separate

Resolve and report these dimensions independently:

| Dimension | Machine authority | Current Gate A `1.2.0` state |
|---|---|---|
| Static architecture | Exact canonical report for one exact index digest | `architecture_complete` |
| Correction closure | `correction_closure_summary` in that report | `CR-001` through `CR-016` required and closed; open set empty |
| GA-17 | Independently authorized external operator process | `not_evaluated` |
| Operator acceptance | Exact decision record plus external identity and authority verification | `unaccepted` |
| Scientific evidence | Eligible retained evidence under the protocol | No supported claim inferred |
| Public transport | Separately authorized post-publication observation | Independent transport `not_evaluated` |
| Publisher receipt | Append-only publisher assertion | Sequence four exists; `asserted_unverified` |
| Runtime | Explicit later-gate authorization | false |
| Gate B | Separate reviewed contract and instruction | false and unauthorized |

`architecture_complete` means only that GA-01 through GA-16 and all required Gate A 1.2
correction findings closed for one exact immutable projection. It does not accept Gate A, evaluate
GA-17, verify transport, support a scientific claim, establish safety or compliance, authorize a
study, or permit runtime.

## 4. Exact current lineage

The public Gate A 1.2 correction retains mission `reiyah.mission@1.1.0` and proposes protocol
`reiyah.protocol.harbor-gate-a@1.2.0`.

| Item | Exact Gate A `1.2.0` identity |
|---|---|
| `C_packet` commit | `86409473c8fd1571236c849a6cc730db896465fb` |
| `C_receipt` direct-child commit | `d42d4d298d515b59e9df15f2ba45572a91b9fab8` |
| Evidence index | `sha256:b39a9bd02b3d86e32b95b988115243918d39b8fa7dea15012d90a0cb0f7c811a`; 397,559 bytes; 767 artifacts |
| Validation report | `sha256:79d6f3578630994c54cbe341e2c62b79fe4606b4645b85499bcb76f018ad1961`; 257,357 bytes; exit `0`; diagnostics empty |
| Publisher receipt | `sha256:74817d54ec3085ef0f6ceb45f54db4c24e353aa48e20a44b5ab36c97bd9d9a99`; 9,898 bytes |
| Receipt sequence | `4` |
| Architecture and corrections | `architecture_complete`; `CR-001` through `CR-016` closed; zero diagnostics |
| Release replay | Two fresh evaluations; candidate, index, S01 through S19, nested-contract, and selector equality passed |
| Authority boundary | operator `unaccepted`; GA-17 `not_evaluated`; runtime `false`; Gate B `false` |
| Transport boundary | publisher `asserted_unverified`; independent transport `not_evaluated` |

The current index's internal `candidate_pending_canonical_report` value is an intentional acyclic
pre-report state. Resolve architecture completion from the exact report whose index binding is the
digest above. The receipt binds the public `C_packet`; it cannot independently verify transport or
claim readback of the later commit that contains the receipt itself.

The immediate immutable predecessor is Gate A 1.1.2:

| Item | Exact predecessor identity |
|---|---|
| Packet commit | `ad1a8cae6ad17f26f5a07f43fb60b6c9f55b4b1b` |
| Receipt-bearing commit | `656d826cfe6938fd628c0ede7ea15929fe11d90e` |
| Evidence-index digest | `sha256:17f3a2e601e9cb4e1c0cd0f97561b1da9ffdc7d5893ed4af4eaccbaf8a67989f` |
| Validation-report digest | `sha256:06fc3114522c16625da337fe25c71b1fd53abeeaf9c31a11748afc06eb5d66d8` |
| Publisher-receipt digest | `sha256:e7f3bedac49423d4ba042419056896c507d26ee2bd9a706981abf2131dcda19d` |
| Recovery record | `history/gate-a-1.1.2/RECOVERY.json` |

The predecessor report covered 68 schemas, 241 normative instances, 196 fixtures, 1,010
required-property mutations, and 347 indexed artifacts with zero diagnostics. Those counts and
its `architecture_complete` result apply only to the exact predecessor bytes. They are not Gate A
1.2 expectations and cannot close a successor finding.

Gate A 1.0.0, 1.1.0, and 1.1.1 remain earlier immutable history. Never regenerate, overwrite,
relabel, or retarget their indexes, reports, receipts, templates, or identifiers.

## 5. Scientific contract boundary

Keep observation, latent belief, decision, intervention, outcome, and evidence separate in kind,
identity, provenance, and time. Missing, unmeasured, out-of-distribution, sensor-invalid, and
abstained states are distinct and never become zero, false, normal, negative, or a confident
label.

Preserve these lifecycle statuses as distinct values and histories: `proposed`, `exploratory`,
`preregistered`, `running`, `blocked`, `invalid`, `null`, `inconclusive`, `failed`, `supported`,
`contradicted`, `replicated`, `corrected`, and `retracted`.

The Gate A 1.2 application envelope exposes only an explicit evidence-gap binding. It has no
eligible scientific-evidence or experiment-binding resolver. Favorable or terminal
evidence-requiring scientific dispositions remain schema-representable rejection targets, not
attainable claims. Non-support lifecycle successors may exercise append-only lineage.

The machine profile maps ten application estimand paths to exact protocol and definition-registry
contracts. Eleven executable contracts cover estimand resolution, derived values, cross-cutting
references and identifiers, lifecycle lineage, evidence eligibility, OPE reconciliation, and
governance boundaries. Do not trust the count or an identifier alone: every handler must consume
the contract's exact application role, measure, direction, unit, population, outcome, comparator,
aggregation, evidence policy, required operands, tolerances, thresholds, and freeze semantics.

Scientific fixtures are deterministic synthetic counterexamples, never empirical evidence. Gate A
contains no product runtime, model training or inference, real policy evaluation, study execution,
private-data ingestion, deployment, live service, alert path, vehicle connection, or physical
control interface.

## 6. Gate A 1.2 correction contract

`docs/GATE_A_1_2_0_CONSISTENCY_REVIEW.md` defines `CR-001` through `CR-016` as immutable
pre-replay findings. The canonical report derives closure from the same immutable snapshot used for
all other checks. It contains:

- ordered `required_finding_ids`, exactly `CR-001` through `CR-016`;
- ordered `closed_finding_ids`;
- ordered `open_finding_ids`; and
- exactly one ordered `finding_results` row per finding, with its production check and fixture
  evidence.

Closed and open IDs must be a disjoint exact partition of required IDs. The report may state
`architecture_complete` only when required equals closed, open is empty, every mapped check and
fixture passed, GA-01 through GA-16 passed, all counts reconcile, exit code is zero, and diagnostics
are empty. Review prose, a hardcoded list, schema validity alone, or a prior run cannot close a
finding.

For the exact public `C_packet`, the retained canonical report records all sixteen required
findings as closed and records no open finding. That bounded result applies only to the exact index
and report identities in section 4. It creates no scientific support, acceptance, transport
verification, or runtime authority.

The correction covers belief and observation reconciliation, causal identification and exact
split manifests, readiness and recoverability, sequential off-policy support and weight
reconciliation, member-complete joint opportunities, atomic OOD and selective partitions,
versioned conformal and worst-group universes, transfer and assumption boundaries, exhaustive
typed references, append-only lifecycle lineage, launcher and toolchain binding, public-rights
interfaces, transport separation, canonical-report implications, fixture-catalog integrity,
release chronology, and truthful documentation.

## 7. Canonical validation entry point

Use only the byte-bound launcher. Direct execution of either Python module is unsupported.

For an intentionally dirty development tree:

```sh
tools/gate_a_1_2_0.sh --snapshot-mode development --output human
tools/gate_a_1_2_0.sh --snapshot-mode development --output json \
  > /tmp/reiyah-gate-a-validation-1.2.0.json
```

Development output is diagnostic only. It is never release evidence, even when its exit code is
zero.

The following bootstrap procedure is retained to explain how the immutable `1.2.0` packet was
created. Do not rerun its emit modes against the populated current paths or rewrite the release.

Bootstrap the cycle-breaking outputs only through these three committed states. `C0` is clean and
contains every candidate artifact, including both fresh capture manifests, except the current
index, sidecar, and report. `C_index` adds the exact index and sidecar. `C_packet` adds the exact
report. Always send bootstrap output to `/tmp`: shell redirection to a repository path creates or
truncates that path before the validator captures its snapshot and therefore makes the release
tree dirty.

```sh
set -eu

index_tmp=/tmp/reiyah-gate-a-index-1.2.0.json
report_tmp=/tmp/reiyah-gate-a-validation-1.2.0.json

test -z "$(git status --porcelain=v1 --untracked-files=all)"
test ! -e gate/GATE_A_EVIDENCE_INDEX.json
test ! -e gate/GATE_A_EVIDENCE_INDEX.sha256
test ! -e gate/validation-reports/gate-a-validation-1.2.0.json

tools/gate_a_1_2_0.sh --snapshot-mode release --output json --emit-index \
  > "$index_tmp"
cp "$index_tmp" gate/GATE_A_EVIDENCE_INDEX.json
index_digest=$(shasum -a 256 "$index_tmp" | awk '{print $1}')
printf 'sha256:%s  gate/GATE_A_EVIDENCE_INDEX.json\n' "$index_digest" \
  > gate/GATE_A_EVIDENCE_INDEX.sha256
git add gate/GATE_A_EVIDENCE_INDEX.json gate/GATE_A_EVIDENCE_INDEX.sha256
git commit --amend --no-edit

tools/gate_a_1_2_0.sh --snapshot-mode release --output json --emit-report \
  > "$report_tmp"
cp "$report_tmp" gate/validation-reports/gate-a-validation-1.2.0.json
git add gate/validation-reports/gate-a-validation-1.2.0.json
git commit --amend --no-edit
```

The first amend establishes `C_index`; the second establishes `C_packet`. `--emit-index` requires
all three output paths to be absent. `--emit-report` requires exact committed index and sidecar
readback and an absent report path. Neither flag is valid in development mode.

In both report-emitting release modes, two fresh isolated children execute S01 through S19. The
parent also performs a complete production replay over its independently retained immutable
snapshot and requires each child's full token, nested, selector, index, publication-state, and
report-input bundle to equal that outer result before comparing the two children and emitting
S20. The parent replay is a substitution guard, not a third independent evaluator.

For a clean committed candidate whose canonical index, sidecar, and report already exist:

```sh
set -eu

tools/gate_a_1_2_0.sh --snapshot-mode release --output json \
  > /tmp/reiyah-gate-a-validation-1.2.0-a.json
tools/gate_a_1_2_0.sh --snapshot-mode release --output json \
  > /tmp/reiyah-gate-a-validation-1.2.0-b.json

cmp /tmp/reiyah-gate-a-validation-1.2.0-a.json \
  /tmp/reiyah-gate-a-validation-1.2.0-b.json
cmp /tmp/reiyah-gate-a-validation-1.2.0-a.json \
  gate/validation-reports/gate-a-validation-1.2.0.json

expected_index_digest=$(awk '{sub(/^sha256:/, "", $1); print $1}' \
  gate/GATE_A_EVIDENCE_INDEX.sha256)
actual_index_digest=$(shasum -a 256 gate/GATE_A_EVIDENCE_INDEX.json | \
  awk '{print $1}')
test "$actual_index_digest" = "$expected_index_digest"

jq '{result, exit_code, architecture_status, operator_acceptance_state,
  correction_closure_summary, control_summary, transport_summary,
  runtime_authorized, gate_b_authorized, diagnostics}' \
  gate/validation-reports/gate-a-validation-1.2.0.json
```

The launcher enters the locked macOS Seatbelt policy before CPython starts, uses isolated
`-I -S -B` execution, denies network and filesystem writes, and exact-checks the declared
toolchain. A release invocation starts two fresh child interpreters, each reloads the same clean
committed projection without shared mutable evaluation state, and the parent exact-compares their
S01 through S19, nested, selector, and index bytes before emitting S20. This is state separation,
not independent external verification. Development uses one observational snapshot and cannot
emit a canonical completion result.

Release exit `0` means the two internal pre-report evaluations matched and the one rendered report
passed. A retained release is usable only after two complete launcher invocations are also
byte-identical to that canonical report while the tree remains unchanged. Exit `1` is a
deterministic contract failure. Exit `2` means the required execution boundary could not be
established. No exit code evaluates GA-17 or authorizes runtime.

## 8. Two-evaluation verification order

The release path must preserve this order:

1. verify repository identity and a clean immutable Git tree;
2. verify launcher, primary validator, science module, platform, and toolchain-lock bytes;
3. capture release evaluation one, read its complete candidate projection, and reject drift,
   symlinks, special files, and undeclared exclusions;
4. for that snapshot, verify Gate A 1.1.2 recovery and inheritance, schemas, normative instances,
   reference ownership, scientific documents, fixtures, catalog, plan, rules, manifests, ledger,
   correction delta, and canonical index bytes;
5. independently capture release evaluation two and repeat the complete pre-report pipeline;
6. canonicalize S01 through S19, all nested contract rows, and the index for each evaluation, then
   require byte equality without reusing either evaluation record;
7. emit S20 only for the observed two-evaluation match;
8. derive controls and correction closure from those observed rows;
9. render and schema-check the canonical report once;
10. in ordinary release mode, require exact committed-report readback as a non-emitted guard; and
11. after report creation, repeat the complete launcher invocation and compare both outputs with
    the committed report as external release and publication evidence.

Counts are always recomputed from the exact snapshot. Do not hand-edit or copy counts, digests,
byte sizes, closure sets, index rows, or report results.

## 9. Index and report resolver

The index is the canonical inventory of the exact candidate projection. It intentionally excludes
itself, its sidecar, the canonical report, operator decision records, publisher receipts, and
explicitly constrained transient caches to avoid digest cycles. Exclusion never creates a general
hiding place.

Resolve the immutable public `1.2.0` baseline from:

```sh
jq '{version, architecture_status, mission_release_id, protocol_release_id,
  operator_acceptance_state, runtime_authorized, artifact_count:
  (.artifacts | length)}' \
  history/gate-a-1.2.0/gate/GATE_A_EVIDENCE_INDEX.json

jq '{result, exit_code, architecture_status, candidate_projection,
  fixture_summary, correction_closure_summary, control_summary,
  security_toolchain_summary, transport_summary, operator_acceptance_state,
  runtime_authorized, gate_b_authorized}' \
  gate/validation-reports/gate-a-validation-1.2.0.json
```

The Gate A `1.2.0` identities in section 4 are immutable historical bindings. Recompute them from
the archived bytes and sidecar before relying on them. A future `1.2.1` current-path index and
report, if later generated, must resolve independently under their own versioned plan. This prose
does not establish a `1.2.1` release or validation state.

## 10. Research and evidence state

The source ledger and public distribution inventory define retained custody. A URL is not retained
evidence. Third-party payloads may enter public Git history only when exact bytes, identity,
version, date, scope, access and redistribution terms, attribution, limitations, and digest are
recorded. Otherwise retain a pointer-only, evidence-ineligible discovery record.

The 2026 frontier baseline is `evidence/frontier-discovery-register-1.1.0.json`. The successor
`evidence/frontier-discovery-register-1.2.0.json` exact-preserves its 38 records as an unchanged
prefix and appends 16 records, for 54 total. Every record is pointer-only and evidence-ineligible.
The additions cover official Tesla, Mobileye, MOIA, NHTSA, Waymo, and Google material plus primary
research pointers, but establish no safety, performance, causality, or superiority claim. Later
browsing or model-assisted research remains discovery input until the evidence admission process
retains exact eligible bytes and independent review.

Standards crosswalks are dated relevance and gap analyses. They do not establish applicability,
conformity, certification, legal interpretation, or compliance.

## 11. Public release sequence

Public distribution is separate from architecture validation and operator acceptance. When the
operator explicitly authorizes publication of one frozen candidate, preserve this sequence:

The Gate A `1.2.0` event completed this sequence. `C_packet` is
`86409473c8fd1571236c849a6cc730db896465fb`; its sequence-four rights and receipt records were
added together at direct-child `C_receipt`
`d42d4d298d515b59e9df15f2ba45572a91b9fab8`. The receipt binds the exact packet, index, report,
rights record, and publisher readback assertion. Its transport state is `asserted_unverified`;
independent transport remains `not_evaluated`. The procedure below is retained as release history
and must not be treated as authority to repeat or mutate the event.

1. preselect event ID `reiyah.distribution-event.gate-a-1.2.0-static-correction`, future rights
   path `evidence/public-rights-revalidation-2026-08-25-gate-a-static-correction-1.2.0.json`, and
   receipt path
   `gate/public-distribution-receipts/reiyah.public-distribution-receipt-1.2.0.json`;
2. require that one exact path as a cycle-breaking projection exclusion while rejecting any broad
   rights-prefix exclusion; historical rights records remain indexed;
3. predeclare
   `evidence/rights-observations/2026-08-25-iso-open-data-gate-a-static-correction-1.2.0.json`
   and
   `evidence/rights-observations/2026-08-25-nist-technical-series-gate-a-static-correction-1.2.0.json`,
   include them as ordinary indexed packet artifacts, and never exclude those paths;
4. complete all other architecture bytes, then observe both official pages and freeze two typed
   capture manifests in their predeclared modes: direct HTTP response metadata when exposed, or a
   bounded adapter observation plus the recorded blocked direct attempt when response bytes are
   unavailable; never invent status, digest, size, or cookie state, and preserve the explicit
   no-response-body/no-redistribution boundary;
5. generate the index, sidecar, and report and commit the packet as `C_packet`, with neither the
   future rights record nor a sequence-four
   receipt present, and perform two byte-identical clean release replays;
6. create a fresh event-specific rights observation for the exact `C_packet`, index, report, and
   distributed payload set, without implying legal review, publication acceptance, safety,
   compliance, science, or runtime authority;
7. keep that record uncommitted while pushing exactly `C_packet` to the configured public `main`
   ref, then read back the exact repository, ref, commit, index, report, and payload bytes as
   publisher observations only;
8. append a sequence-four publisher receipt whose transport state is exactly
   `asserted_unverified` and whose rights binding names the fresh record;
9. commit the rights observation and receipt together as direct child `C_receipt` of `C_packet`,
   rerun ordinary release validation so its non-emitted post-event guard proves the production
   schemas, joins, chronology, direct-parent topology, event-only delta, and unchanged packet
   projection, index, and report, then push `C_receipt`; any later publisher readback of
   `C_receipt` requires a distinct append-only observation and is not part of the receipt; and
10. retain `C_packet` and `C_receipt` as distinct immutable identities.

Generate the two postpacket records from the nested `record` shapes in
`fixtures/v1.2/governance-good/public-rights-revalidation.json` and
`fixtures/v1.2/governance-good/public-distribution-receipt.json`; those files are synthetic
shape witnesses, never event evidence and never a source for copying placeholder digests, times,
commits, or observer identities.

For the rights record, preserve the predeclared artifact, event, repository, ref, mission,
protocol, schema, and prior-record identities. Recompute `intended_distribution.candidate_git_commit`
from `C_packet`; recompute the index and report reference digests and byte sizes from the exact
committed files; bind both capture manifests by exact path, artifact ID, schema, digest, byte size,
role, URL, mode, and their real `observation_completed_at`; record the actual observation time and
truthful observer basis; derive the covered payload and excluded pointer source-ID sets from the
validated source ledger and packet inventory. Distribution is eligible only when
`all_included_payloads_covered` is `true` and `preflight_outcome` is exactly
`eligible_payload_basis_observed_pointer_payloads_excluded`. Keep every legal, acceptance,
science, compliance, GA-17, and runtime authority field at its nonclaim value.

For the sequence-four receipt, recompute every custody, source-ledger, frontier-register,
distribution-inventory, rights, index, report, and distributed-payload reference from actual
bytes. Set repository, ref, and `published_git_commit` to the pushed `C_packet`; set
`published_at` to the real publication event; derive `oldest_capture_age_seconds` as publication
time minus the oldest capture `observation_completed_at`; retain the actual bounded operator
authorization; and populate `remote_readback_assertion` only from the publisher's subsequent
readback of that same `C_packet`. Enforce capture completion at or before rights observation,
rights observation at or before authorization, authorization at or before publication,
publication before readback, and readback at or before receipt recording. Keep transport exactly
`asserted_unverified`, the independent record reference `null`, the prior receipt exact, and
`receipt_bearing_commit_self_readback_claimed` `false`. Do not put either real record on disk
before the event that supplies these values.

A rights observation must be fresh for the actual distribution event and exact packet. Do not
reuse a stale observation after candidate bytes or timing changes. A publisher receipt cannot
verify its own transport. Independent transport requires a distinct, separately authorized
observer, authentication basis, authorization record, retained observation evidence, and valid
post-publication chronology. Without that process, publisher transport remains
`asserted_unverified` and independent transport remains `not_evaluated`.

This exact exclusion is necessary because the rights record binds `C_packet`, the index, and the
report. Including it in `C_packet` would make the Git commit hash contain a record that names that
same commit and would make the index and rights record hash one another. No ordinary digest fixed
point exists. The exclusion is exact, schema-constrained, and absent during packet replay; it is
not permission to hide another rights record or candidate artifact.

The two capture manifests are different: they do not bind `C_packet`, so they remain ordinary
indexed packet artifacts. They retain locally authored retrieval metadata and the digest and size
of an unretained response only when the direct mode exposes those values, not the raw ISO or NIST
HTML. A predeclared adapter mode records unavailable transport fields as unobserved and cannot
serve as a silent fallback. Reiyah supplies no credential material; unexposed adapter cookie state
remains unobserved. The validator must resolve every `capture_manifest_ref` byte, enforce ordered
capture, manifest, rights, and publication timestamps, and derive freshness against both
completion times. If either capture
will be more than 3,600 seconds old at first publication, abort and rebuild both captures, the
report, and `C_packet`; never refresh bytes under a committed capture path.

No tool may create an operator decision, choose `accepted`, invent a reviewer, infer authority,
or treat publication instructions as Gate A acceptance. The decision template remains invalid
until an authorized human independently completes and verifies it.

## 12. Hard-problem doctrine

Engineering pressure increases the burden of proof. It never increases confidence by itself.

| Trigger | Required response | Forbidden shortcut |
|---|---|---|
| Unexplained failure | Freeze the observed bytes, reproduce, minimize, identify the violated invariant, and retain a reason-specific counterexample. | Retry until green or delete the observation. |
| Validator and specification disagree | Treat both as hypotheses, trace the production path, repair the contract, and add a minimally changed fixture. | Weaken the rule or expected diagnostic merely to pass. |
| Evidence is absent or ineligible | Preserve the exact unknown, gap, blocked, invalid, or inconclusive state. | Convert fluent prose, consensus, a checksum, or self-review into evidence. |
| Source or result conflicts | Preserve both identities, scopes, versions, provenance, and limitations. | Average away or silently choose the favorable record. |
| Support, coverage, or subgroup failure | Expose denominators, unknowns, censoring, intervals, and worst-group limits; abstain where required. | Hide the failure in an aggregate. |
| Post-freeze byte changes | Preserve the old target and create a versioned successor with exact lineage. | Regenerate or relabel an immutable release. |
| Rights or authority is uncertain | Keep payload pointer-only or stop at the current gate. | Treat public reachability, credentials, or urgency as permission. |

Failures are information. Preserve them as diagnostics, known-bad fixtures, open findings,
blocked states, contradictions, corrections, or retractions.

## 13. Stop conditions

Stop closeout or publication when any of these holds:

1. project, directory, Git root, repository contract, or remote identity differs;
2. overlapping worktree changes cannot be attributed safely;
3. a released identifier or historical byte would be overwritten, relabeled, or retargeted;
4. predecessor recovery, schema, profile, plan, catalog, ledger, index, sidecar, or report does not
   reconcile;
5. any known-good fails, any known-bad misses its exact primary diagnostic, any required finding
   remains open, any GA-01 through GA-16 control fails, or diagnostics are nonempty;
6. repeated clean release report bytes differ;
7. an epistemic state, lifecycle state, denominator, group, opportunity, reference, or lineage
   event would be coerced, omitted, duplicated, or self-attested;
8. public payload identity, redistribution terms, attribution, rights observation, or freshness is
   unresolved;
9. acceptance, transport, scientific support, safety, compliance, causality, or superiority would
   be inferred without its independent authority and evidence; or
10. the task would introduce runtime, cloud execution, deployment, private data, empirical study
    execution, publication machinery, physical control, or Gate B work.

Report the exact condition, affected paths or records, and the smallest in-scope recovery. Do not
broaden scope to escape a stop condition.

## 14. Host and repository stewardship

The repository is small; host storage pressure is not caused by Gate A artifacts. Disk cleanup
must be narrow, inspected, and recoverable where practical. Never delete active update staging,
active Codex runtimes, credentials, unrelated repositories, user documents, or broad cache roots
to make validation appear successful. Remove only exact inactive targets after checking process
use and ownership. Repository-generated `__pycache__` is transient and forbidden in the candidate
projection; the launcher uses `-B` to avoid creating it.

## 15. Continuation resolver

At the start of the next session:

1. run the identity and worktree preflight;
2. inspect the exact `1.2.0` report, closed correction set, rights record, and sequence-four
   receipt;
3. run development validation only for an intentionally dirty candidate;
4. run the repeated release sequence only for a clean committed candidate;
5. compare local and remote commit identities without treating reachability as independent
   transport verification;
6. inspect append-only rights, receipt, transport, and decision records separately; and
7. continue only the smallest unresolved Gate A architecture or release step.

The complete public Gate A `1.2.0` packet and publisher receipt now exist. The next bounded work is
the `1.2.1` continuity successor tracked in
[GitHub issue #1](https://github.com/manfromnowhere143/reiyah/issues/1), followed only by separately
requested architecture review or governance. Describe `1.2.1` as released, validated, or
publication-authorized only when a distinct exact machine record establishes that state. Gate B,
runtime, cloud execution, deployment, private-data ingestion, physical control, and empirical
publication remain unauthorized until a new explicit instruction and reviewed contract say
otherwise.

## 16. Required closeout statement

Every handoff must state, separately and from exact machine records:

- repository root, branch, local commit, configured remote, and remote ref identity;
- worktree cleanliness and every uncommitted path;
- index path, digest, byte size, and artifact count;
- report path, digest, byte size, exit code, diagnostics, and replay equality;
- required, closed, and open correction finding sets;
- GA-01 through GA-16 result and GA-17 state;
- operator acceptance state;
- publisher-receipt state and independent transport state;
- scientific evidence and claim state;
- runtime and Gate B authority; and
- unresolved risks and the next smallest authorized action.

A successful architecture closeout is an exact-byte integrity result. It is never, by itself,
scientific support, safety validation, standards compliance, product readiness, competitive
superiority, publication acceptance, independent transport proof, operator acceptance, or runtime
authority.

## 17. Proposed 1.2.1 continuity authoring checkpoint

This checkpoint describes an uncommitted documentation proposal, not a release record. The branch
is `gate-a-1.2.1-continuity`, based on public receipt commit
`d42d4d298d515b59e9df15f2ba45572a91b9fab8`. The documentation scope is `README.md`,
`gate/README.md`, `evidence/README.md`, `docs/STATUS_MODEL.md`,
`docs/RESEARCH_GAP_REGISTER.md`, `docs/SESSION_HANDOFF.md`,
`docs/RESEARCH_OPERATING_MODEL.md`, and `CITATION.cff`. `docs/SOURCE_POLICY.md` required no
current-state correction and remains unchanged.

The documentation self-review established all of the following:

- `C_receipt` is the direct child of `C_packet`;
- Git-object recomputation matched the exact index, report, and sequence-four receipt digests in
  section 4;
- the report machine fields matched `architecture_complete`, closed `CR-001` through `CR-016`,
  GA-17 `not_evaluated`, operator `unaccepted`, runtime `false`, Gate B `false`, and zero
  diagnostics;
- the receipt machine fields matched sequence four, `asserted_unverified`, null independent
  transport record, GA-17 `not_evaluated`, no acceptance, and no runtime authority;
- `CITATION.cff` parsed as YAML, all local Markdown links resolved, the scoped diff passed
  `git diff --check`, and the edited files contained no em dash.

The locked `1.2.0` launcher was also run in development mode against the shared, intentionally
dirty successor worktree. It returned `GA12-PLAN-SCHEMA` because the concurrently developing
`1.2.1` validation plan contains successor properties outside the frozen `1.2.0` plan schema.
That diagnostic is not release evidence, does not validate this documentation proposal, and must
not be weakened. The validator and frontier workstreams own concurrent non-document changes; do
not discard, stage, or attribute those paths to this documentation correction.

### 17.1 Continuity defect closure observed on 2026-08-28

The proposed `1.2.1` launcher `tools/gate_a_1_2_1.sh` was run in development mode against the
shared successor worktree. The first observation returned five control diagnostics. Each was
traced to an exact cause and closed without weakening a control, a tolerance, or an expected
diagnostic.

| Observed diagnostic | Exact cause | Bounded closure |
|---|---|---|
| `GA121-SUCCESSOR-DELTA-SCOPE` | A transient `.ruff_cache/` lint cache entered the candidate projection. It is outside the closed `__pycache__` and `.pytest_cache` boundary, so the validator refused it rather than ignoring an unknown directory. | The transient cache was moved out of the worktree. The closed cache boundary was not widened. |
| `GA121-DOCUMENTATION-LINKS` | Downstream of the delta failure. | Closed by the same removal. |
| `GA121-FIXTURE-COVERAGE` | Downstream of the delta failure through the known-good continuity replay. | Closed by the same removal. |
| `GA121-DISCOVERY-NONAUTHORITY` | `EXPECTED_FRONTIER_FIXTURE_CASE_MAP_SHA256` still held an authoring placeholder. Every one of the eleven frontier fixtures had already matched its own declared diagnostic before the frozen digest was compared. | The diagnostic was first made self reporting, then the freeze was sealed for the first time on an unreleased successor. |
| `GA121-TOOLCHAIN-BINDING` | `validation/toolchain-lock-1.2.1.json` was stale. It bound a nonexistent `schemas/operator-decision-record-1.2.1.schema.json`, omitted both frontier schemas, and pinned an earlier validator byte size. | The lock was regenerated from actual bytes and cross checked against the validator's own declared schema path tuple. |

### 17.2 Retained host toolchain drift diagnostic

After the schema binding was repaired, `GA121-TOOLCHAIN-BINDING` reported that the host Python
stdlib no longer matched the frozen `1.2.0` toolchain lock. The cause was identified exactly and
is retained here as a diagnostic rather than resolved by re-sealing an immutable predecessor.

Three CPython bytecode caches had been written into the locked stdlib tree on 2026-08-27 at
15:18 local time by a process other than the Reiyah launcher, which always uses `-B`:

- `__pycache__/smtplib.cpython-314.pyc`;
- `multiprocessing/__pycache__/heap.cpython-314.pyc`; and
- `multiprocessing/__pycache__/sharedctypes.cpython-314.pyc`.

The observed tree carried 2,892 files and digest
`sha256:f5a1435faa67b572755cafa1924f2264f8af67a496d294790466e33a500e59e5`. Excluding exactly those
three derived caches restored 2,889 files and digest
`sha256:6c16d67e7b053e4a26cf18c518b5d726ac7031bc4688208320daf57c41c2f491`, which equals the value
recorded in `validation/toolchain-lock-1.2.0.json`. The Python framework binary was byte identical
throughout. The three derived caches were therefore quarantined outside the interpreter tree so
the locked byte closure holds. The frozen `1.2.0` lock was not retargeted.

This drift is a host reproducibility signal, not a Reiyah artifact defect. The validated runtime
byte closure is not guaranteed immutable on a shared developer host. Any future release evaluation
must re-verify it rather than assume it.

### 17.3 Current observed continuity state

The `1.2.1` launcher then returned a development observation of `pass` with exit code zero, empty
diagnostics, and byte identical repeated output. The observed candidate projection was 821
artifacts at
`sha256:1d16d333d20846244554993ee301dd2fcb7a51bc3f10b7441364367b661ce619`. Fourteen controls
passed and `GA121-DUAL-EVALUATION` remained `not_evaluated` because it is reachable only in
release mode. The continuity catalog exercised 24 fixtures, of which one known good passed and 23
known bad were rejected for their declared diagnostic, alongside 11 frontier fixtures and 54
pointer only discovery records.

Development output is diagnostic only. It is never release evidence, even at exit code zero. It
does not validate, release, publish, or accept the successor, and it creates no scientific
evidence.

The next action is to commit the successor scope on this branch and then run the `1.2.1` release
path under its own locked plan. Until a distinct exact machine record establishes otherwise,
`1.2.1` remains proposed, unvalidated, unreleased, and without publication authorization.
