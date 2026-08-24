# HARBOR Gate A Mathematical Specification

Document ID: `reiyah.mathematical-specification`

Version: `1.2.0`

Lifecycle status: `proposed`

Program name: HARBOR, Human-Automation Readiness, Belief & Operational Risk (`proposed`)

## 1. Scope and non-claim

This document specifies candidate estimands, typed scientific objects, identification
requirements, unknown handling, and validation boundaries for Gate A. It does not implement
an estimator, run an experiment, ingest private data, control a vehicle, or establish that
any measure is safe, valid, compliant, or supported.

The keywords **MUST**, **MUST NOT**, **REQUIRED**, **SHOULD**, and **MAY** are normative.
Symbols define a protocol language; they are not empirical results.

## 2. Indexed units and time

Let:

- \(i \in \mathcal I\) identify a person-vehicle-automation encounter, never a person alone;
- \(o \in \mathcal O_i\) identify a physical or operational object relevant to encounter
  \(i\), such as a road actor, control affordance, hazard, or automation state;
- \(t \in \mathcal T_i\) identify event time on a declared clock;
- \(e \in \mathcal E\) identify an environment or domain;
- \(g \in \mathcal G\) identify a preregistered validation group; and
- \(\pi \in \Pi\) identify a candidate policy.

Every protocol MUST define clocks, temporal tolerance, encounter construction, object identity
rules, and whether repeated encounters are dependent. Record time and event time MUST remain
separate. Unknown object correspondence MUST not be resolved by assuming identity.

For an information item \(r_j\), retain event, measurement, availability, and recorded times
\((t_j^e,t_j^m,t_j^a,t_j^r)\). The eligible information set for actor \(a\) at decision time
\(t\) is

\[
\mathcal I_{a,t}=\{r_j: t_j^a\le t,\;r_j\text{ is disclosed to }a,\;
r_j\text{ satisfies the frozen eligibility rule}\}.
\]

An item that arrived later, was withheld, or failed its validity rule is not a member, even when
its event occurred earlier. Membership, non-membership, withholding, and unavailable state MUST
be reconciled against the complete candidate-item set.

## 3. Six disjoint scientific object types

The persistent object namespaces and payloads are disjoint. Cross-layer relationships are by
typed identifiers, not by embedding one layer as if it were another.

### 3.1 Observation \(O\)

\[
O_{i,o,t} = (X_{i,o,t}, q^O_{i,o,t}, p^O_{i,o,t})
\]

\(X\) is a vector of acquired measurements, \(q^O\) is a vector of epistemic states, and
\(p^O\) is acquisition provenance. An observation states what the acquisition process
returned; it is not a latent cognitive state, ground truth, or outcome. Each component is a
discriminated measurement with exactly one state from `docs/STATUS_MODEL.md`.

### 3.2 Latent belief \(B\)

\[
B^{h\rightarrow x}_{i,o,t}\!\left(\,\cdot\mid\mathcal I_{h,t}\right)
\in \mathcal P(\mathcal S_o) \cup
\{\bot_{m},\bot_{u},\bot_{d},\bot_{s},\bot_{a}\}
\]

\(B\) is a proposed distribution held by typed actor \(h\), concerning typed target \(x\), over
an explicitly defined state space \(\mathcal S_o\), conditional on one frozen information set.
The bottom symbols respectively denote missing, unmeasured, out-of-distribution,
sensor-invalid, and abstained. They are not probability zero. A belief record MUST reference
its observation inputs, calibration target, reference process, inference specification,
applicability domain, scoring or decision-loss rule, and abstention policy; it MUST NOT be stored
as an observation or asserted as a person's true mental state.

For an observed categorical belief, components MUST satisfy, within a protocol-declared
numeric tolerance,

\[
b_k \in [0,1], \qquad \sum_{k=1}^{K} b_k = 1.
\]

For Gate A, the exact protocol release fixes the absolute tolerance
\(\epsilon_B=10^{-6}\), and both the protocol policy and record bind that same value:
\(\left|\sum_k b_k-1\right|\leq\epsilon_B\). A record cannot select a looser tolerance.
The record carries the complete `belief.normalization_policy_binding`, not an unowned numeric
literal. The schema closes its shape, while deterministic semantic validation is REQUIRED to
check the sum, field-for-field equality with the exact protocol policy, and a one-to-one
correspondence between the unique component labels and the exact declared state-space members.
Missing, duplicate, or extra states are invalid even when the numeric sum is one.
When the distribution envelope is non-observed, there are no component probabilities to
normalize or silently reconstruct. The validator preserves its exact epistemic state and reason,
continues to resolve the object, state-space, actor, information-set, temporal, and estimand
bindings, and does not run observed-only coverage or sum rules. A separately observed human
decision may coexist because it records an action, not a recovered latent belief.

Observation validity and measurement state also reconcile. A sensor-invalid observation cannot
contain a value whose state is `observed`, and an observed value cannot bypass an invalid
observation wrapper. Observation, belief, and decision records for one assessment MUST agree on
encounter, object, actor, clock, and frozen information-set membership. Each referenced
observation MUST be available no later than the belief or decision boundary that consumes it.

### 3.3 Decision \(D\)

\[
D_{i,t}^{\pi} = (a_{i,t}, \mathcal A_{i,t}, r^D_{i,t}, q^D_{i,t})
\]

\(a\) is a selected analytic action or abstention, \(\mathcal A\) is the declared choice set,
and \(r^D\) references the rule or policy. Gate A decisions are research records only. They
MUST NOT be wired to physical control. A decision references beliefs and any permitted
observations through one actor-bound \(\mathcal I_{a,t}\); it does not rewrite them. The decision
information-set members MUST equal the eligible candidate items after applying the frozen
availability, disclosure, withholding, and exclusion rules.

### 3.4 Intervention \(A\)

\[
A_{i,t} = (z_{i,t}, \alpha_{i,t}, q^A_{i,t})
\]

\(z\) is the assigned intervention level and \(\alpha\) is the assignment mechanism. At Gate
A this is a protocol-level variable, not an operational actuator. Assignment, delivery,
receipt, and adherence are distinct fields. Non-delivery MUST NOT be relabeled as assignment
to control.

### 3.5 Outcome \(Y\)

\[
Y_{i,o,[t,t+h]} = (y_{i,o,[t,t+h]}, q^Y_{i,o,[t,t+h]}, p^Y_{i,o,[t,t+h]})
\]

An outcome is measured after a declared index time over a declared horizon \(h\). Outcome
definitions and censoring rules MUST be fixed before analysis. An outcome is neither a
decision nor evidence for its own interpretation.

### 3.6 Evidence \(E\)

\[
E_j = (T_j, S_j, M_j, P_j, V_j, L_j, H_j)
\]

Evidence object \(j\) binds target claims or results \(T\), retained source records \(S\), a
method \(M\), provenance \(P\), a validity assessment \(V\), lifecycle status \(L\), and
nonempty lifecycle history \(H\). The history ends in \(L\), uses versioned evidence
references, and binds each non-root event to its immediate predecessor artifact.
Checksums and signatures support integrity or attribution; they do not independently make
\(E_j\) scientific evidence. A source URL without retained bytes and digest is an evidence
gap.

### 3.7 Immutable lifecycle history

For any versioned scientific record \(R^{(v)}\), let

\[
H(R^{(v)}) = (h_1,\ldots,h_m), \qquad m \ge 1.
\]

\(h_1\) is the unique proposed root with null prior status and prior artifact. For \(k>1\),
\(h_k\) contains the prior status \(L_{k-1}\), new status \(L_k\), a strictly later UTC time,
actor, rationale, versioned evidence references, and an exact reference to the immutable
artifact carrying \(h_{k-1}\). The semantic invariants are

\[
\operatorname{seq}(h_k)=k,\quad
\operatorname{priorStatus}(h_k)=L_{k-1},\quad
L_m=L(R^{(v)}).
\]

The record `created_at` is the logical-record inception time and equals
`h_1.recorded_at` exactly. Every later lifecycle event is strictly later. A successor preserves
that inception time together with the exact predecessor history prefix; it does not relabel the
successor artifact's later construction time as a new logical-record creation.

For a correction or retraction, the predecessor has the same schema-specific logical record ID,
record kind, and compatible schema as the successor, but a distinct immutable artifact ID, a
strictly older semantic record version, and distinct path and digest. The prior reference carries
the predecessor byte size as well as its digest. The
predecessor's complete lifecycle history MUST equal the successor history with the final event
removed. Matching only the predecessor's terminal status is insufficient because it permits
earlier events to be rewritten. The successor's own digest is external in the Gate A index, so
no record hashes bytes that contain that same hash.

The Gate A 1.2 application envelope exposes only an explicit evidence-gap binding. It has no
eligible scientific-evidence or experiment-binding resolver. Consequently a status that the
protocol marks as evidence requiring, including `supported`, `contradicted`, or `replicated`,
cannot pass merely because its lifecycle transition is structurally allowed. Non-support
successors can exercise append-only lineage; favorable scientific dispositions remain
schema-representable only as rejection targets until a later authorized protocol defines and
validates their complete evidence dependencies.

## 4. Epistemic partiality

For any typed quantity \(Z\), define

\[
\widetilde Z = (q_Z, v_Z), \quad
q_Z \in \mathcal Q = \{observed, missing, unmeasured,
out\_of\_distribution, sensor\_invalid, abstained\}.
\]

The value function is partial:

\[
v_Z \text{ is defined if and only if } q_Z = observed.
\]

There is no map \(c: \mathcal Q \setminus \{observed\} \rightarrow \{0,false,negative,normal\}\)
in the Reiyah data model. Any analysis transformation must operate on the pair, preserve the
original, and declare its effect on the target population and denominator.

Define an eligibility indicator only when its inputs are observed:

\[
I_i^P = \begin{cases}
1 & \text{all preregistered inclusion and validity rules for protocol } P \text{ pass},\\
0 & \text{an observed fact triggers a preregistered exclusion},\\
\bot & \text{eligibility is not knowable from valid observed inputs}.
\end{cases}
\]

\(\bot\) MUST NOT be coerced to zero. Protocols MUST report its count and possible impact.

## 5. Target constructs and estimands

The following are candidate definitions. Each protocol release MUST instantiate the target
population, time horizon, comparator, measurement procedure, validity boundary, aggregation,
uncertainty method, and abstention handling. No value is meaningful without that binding.

### 5.1 Object-level belief quality

For a proper scoring rule \(s\), observed reference state \(S_{i,o,t}\), and valid belief
\(B_{i,o,t}\), define scoped belief loss

\[
L_B(P) = \mathbb E_P\!\left[s(B_{i,o,t},S_{i,o,t})
\mid I_i^P=1, q_B=observed, q_S=observed\right].
\]

The protocol MUST report coverage of the conditioning set and each excluded epistemic state.
A lower loss among a selectively non-abstaining subset is not evidence of better overall
belief quality without a coverage-sensitive analysis.

### 5.2 Human-automation readiness

Readiness is not a classifier label. Let \(C_i(h)\) denote the preregistered set of required
capabilities over horizon \(h\), with capability-specific validity \(V_{ic}\) and criterion
\(K_c\). Define

\[
R_i(h) = \bigwedge_{c\in C_i(h)} K_c(O_i,B_i,D_i;h)
\quad \text{only when } \bigwedge_c V_{ic}=1.
\]

Otherwise \(R_i(h)=\bot_q\) for the applicable epistemic state. A protocol MAY define a
continuous readiness functional, but MUST retain component measurements, forbid compensation
that hides a required, safety-critical, or positively weighted unknown, state whether automation
state is included, and avoid interpreting a score as authorization to control a vehicle. Weight
normalization is checked over the complete configured capability set regardless of which values
are observed.

Population readiness at threshold \(r\) is

\[
\theta_R(P,r,h)=\Pr_P(R_i(h)\ge r \mid I_i^P=1,q_R=observed),
\]

reported with coverage \(\kappa_R=\Pr_P(q_R=observed\mid I_i^P=1)\) and a sensitivity bound
for non-observed cases. A protocol MUST NOT report \(\theta_R\) alone.

### 5.3 Recoverability

Let \(H_i\) be a preregistered challenge event, \(\tau_i\) its onset, \(W_i\) the feasible
recovery window derived independently of the observed response, and \(G_i(t)\) a declared safe
recovery condition. Define time to recovery

\[
T_i^{rec}=\inf\{t\in[0,W_i]:G_i(\tau_i+t)=1\}.
\]

If no qualifying recovery is observed within a valid, fully observed window, record a
right-censored outcome, not zero and not missing. If the window or sensors are invalid, use
the corresponding epistemic state.

For horizon \(h\),

\[
\theta_{rec}(P,h)=\Pr_P(T_i^{rec}\le h \mid H_i=1,I_i^P=1),
\]

with a declared censoring estimator, competing-event policy, observation coverage, and
uncertainty interval. Assignment to an intervention and actual receipt MUST remain separate.

### 5.4 Joint silent miss

Let \(Z_{i,o,t}=1\) denote a preregistered relevant condition established by an independent
reference process. Let \(M^H=1\) mean the human-side process misses that condition, and
\(M^A=1\) mean the automation-side process misses it. Let \(W=1\) mean that neither side nor
a declared fallback produces a qualifying indication inside the window. Then

\[
J_{i,o,t}=\mathbf 1[Z=1\land M^H=1\land M^A=1\land W=1]
\]

is defined only when all four operands are valid and observed. The scoped rate is

\[
\theta_{JSM}(P)=\Pr_P(J=1\mid Z=1,I_i^P=1).
\]

Unknown human state, unknown automation state, or an invalid reference process makes \(J\)
unknown. It MUST NOT be counted as no miss. Protocols MUST specify object correspondence,
relevance, indication modality, temporal alignment, fallback behavior, and clustered
uncertainty.

### 5.5 Causal policy effects

For policy \(\pi\), let \(Y_i(\pi)\) be the potential outcome under a well-defined intervention
regime. For policies \(\pi_1,\pi_0\), the average policy effect is

\[
\tau(P;\pi_1,\pi_0)=\mathbb E_P[Y_i(\pi_1)-Y_i(\pi_0)].
\]

Identification requires, as applicable:

1. consistency and no hidden versions of each policy;
2. positivity over the target population;
3. exchangeability conditional on preregistered covariates or a valid randomization process;
4. declared interference assumptions;
5. valid outcome measurement and censoring assumptions;
6. assignment, delivery, receipt, adherence, and contamination records; and
7. no conditioning on post-treatment variables unless the estimand requires and identifies it.

When every graph, role, observability, temporal, and selected-set operand is observed and the
declared back-door criterion fails, the machine disposition is `not_identified`. When a required
endpoint or eligibility operand is non-observed or unresolved, the disposition is `unknown`.
Neither state permits an unqualified causal estimate. A protocol may separately map the resulting
scientific record to `inconclusive`, `invalid`, or an explicit bound, but it may not relabel an
unresolved input as a completed negative identification result.

### 5.6 Transfer

Let \(P_s\) be a source domain and \(P_t\) a declared target domain. For metric loss
\(L(\cdot)\), define transfer gap

\[
\Delta_{tr}(s,t)=L_{P_t}-L_{P_s}.
\]

The target-domain loss MUST be computed on retained target-domain evidence; similarity of
metadata alone is not validation. A transfer claim MUST name the source and target versions,
support-overlap diagnostics, covariate and label definitions, measurement invariance
assumptions, adaptation data, and any target-domain tuning. Where required overlap is absent,
the result is `out_of_distribution`, not extrapolated performance.

A protocol SHOULD report both \(\Delta_{tr}\) and target performance with uncertainty and
coverage. A small aggregate gap does not establish subgroup transfer.

### 5.7 Worst-group validation

For preregistered groups \(\mathcal G_P\) and a utility metric where larger is better,

\[
\theta_{WG}(P)=\min_{g\in\mathcal G_P} \theta_g,
\qquad
g^*=\arg\min_{g\in\mathcal G_P}\theta_g.
\]

For a loss metric, replace the minimum with a maximum. The protocol MUST declare direction.
It MUST retain every preregistered group, group sample size, coverage, uncertainty, multiplicity
policy, intersection construction, and minimum-information criterion. The complete universe is
partitioned exactly into sufficient, observed-insufficient, and unknown groups. Known
insufficient groups remain visible but are not eligible for the extremum. Any unknown group makes
the overall result unknown. When there are no unknown groups and no sufficient groups, the exact
disposition is `no_eligible_groups`. Otherwise the typed result records every sufficient group ID
in the direction-aware extremum set \(g^*\), including all ties, plus the protocol-owned selection
rule; free prose cannot select or relabel the worst group. Post-hoc group discovery is
`exploratory` and must be labeled separately.

### 5.8 Coverage-performance pair

All selective metrics, including abstaining methods, MUST report

\[
\kappa(P)=\Pr_P(q_Z=observed), \qquad
\theta(P)=\mathbb E_P[\ell(Z)\mid q_Z=observed],
\]

plus counts by every non-observed epistemic state. Comparisons MUST use a preregistered
coverage alignment, risk-coverage curve, or sensitivity analysis. A metric improvement caused
only by increased abstention is not a supported improvement claim.

### 5.9 Sequential off-policy evaluation

For episode \(i\), let the logged history through step \(t\) be

\[
H_{i,t}=(S_{i,0},A_{i,0},R_{i,0},C_{i,0},\ldots,S_{i,t}),
\]

where \(R\) is the preregistered reward and \(C\) is a separately defined safety cost. Let
\(\mu_v(a\mid H)\) be the exact behavior-policy version and \(\pi_v(a\mid H)\) the exact target
policy version. For every target-supported action, positivity requires

\[
\pi_v(a\mid H)>0\Longrightarrow\mu_v(a\mid H)>0.
\]

The cumulative importance ratio is

\[
w_{i,t}=\prod_{k=0}^{t}
\frac{\pi_v(A_{i,k}\mid H_{i,k})}{\mu_v(A_{i,k}\mid H_{i,k})}.
\]

Any zero or unknown required behavior propensity makes that target-policy contribution
unsupported. It MUST NOT be replaced by a small constant. The effective sample size for a
declared weight set is

\[
n_{eff}=\frac{(\sum_i w_i)^2}{\sum_i w_i^2}.
\]

The static contract MUST bind horizon, discount, terminal and censoring rules, propensity
provenance, support diagnostics, weight-tail and clipping rules, estimator candidates, estimator
selection boundary, reward and safety-cost estimands, uncertainty, and estimator disagreement.
Each history identity and each required history-action support cell is unambiguous and occurs
exactly once. Effective-sample-size sufficiency is derived from the recomputed value and the exact
registry-owned threshold. Failed support or information criteria force the preregistered invalid,
inconclusive, or bounded disposition. Gate A specifies these records but executes no policy or
estimator; estimator values and interval bounds therefore remain explicitly non-observed. The
discount factor is retained as a future estimator operand and does not alter static weight
arithmetic.

### 5.10 Selective, OOD, and conformal evaluation

Let \(s_\tau(x)\in\{0,1\}\) denote acceptance under a frozen selective threshold. Report both
coverage \(\kappa_\tau=\Pr(s_\tau(X)=1)\) and conditional risk
\(R_\tau=\mathbb E[\ell(Y,f(X))\mid s_\tau(X)=1]\), with all rejected cases partitioned into
novelty, ambiguity, missing, sensor-invalid, and protocol-abstention states. The threshold and
its selection data MUST be frozen before evaluation outcomes are accessed.

For a conformal set \(C_\alpha(X)\), a statement such as

\[
\Pr\{Y\in C_\alpha(X)\}\ge 1-\alpha
\]

is admissible only under the exact declared finite-sample, exchangeability, calibration-set,
weighting, and source-to-target shift conditions. Group-conditional and target-domain coverage
must be reported where declared. When the guarantee assumptions are unsupported or contradicted,
the guarantee disposition is invalid or inconclusive, never silently inherited from the source
domain. Gate A 1.2 has no retained assumption-evidence resolver, so its conformal guarantee is
exactly `none`, `not_asserted`, and scope `none`. Empirical coverage remains separate and is
derived from explicit covered and evaluated counts. A zero or non-observed denominator produces
non-observed coverage. The group-scope mode states whether group denominators are disjoint and
exhaustive or overlapping; only a disjoint exhaustive declaration permits summing them to the
aggregate denominator.

### 5.11 Executable reconciliation rules

Gate A 1.2.0 distinguishes a reported value from the operands and rule that derive it. A record
MUST carry enough typed information for the offline validator to recompute each derived value.
A self-asserted `valid`, `sufficient`, `supported`, or `verified` field is never a substitute.

For a finite action space \(\mathcal A(H)\), each behavior and target policy row MUST be a
complete distribution:

\[
\sum_{a\in\mathcal A(H)}\mu_v(a\mid H)=1,\qquad
\sum_{a\in\mathcal A(H)}\pi_v(a\mid H)=1.
\]

Behavior and target policy identities have distinct fixed application roles and each resolves to
its complete, frozen per-history table. A role swap, policy-reference swap, table outside its
declared freeze, or row whose history or information set differs from the owning step is invalid.
The ordered `trajectories[].trajectory_id` array MUST equal the exact ordered `member_ids` of the
registry-resolved, artifact-bound external trajectory-set manifest; the synthetic manifest and
trajectory records used at Gate A are evidence-ineligible contract witnesses and establish no
empirical result.
Each noninitial `history_prefix` is the exact ordered sequence of prior logged actions, and each
information set contains the protocol-declared prior-action members for that same history; neither
is a free label.

The logged-action propensity MUST equal the corresponding member of each distribution. Positivity
is evaluated for every target-supported action, not only the logged action. For one declared
horizon, the validator derives one cumulative \(w_i\) per trajectory and computes effective
sample size across those trajectory weights. Step ratios are not independent trajectories.
Clipping, truncation, normalization, or stabilization changes the estimand-facing weight set and
MUST be declared, parameterized, and reconciled separately from the raw weights.
Trajectory steps MUST form one contiguous sequence from the declared origin through the observed
horizon. Terminal flags, stopping rule, maximum horizon, and observed horizon MUST agree. ESS rows
MUST cover exactly every declared evaluation horizon and use the weight set selected for the
bound estimator; a transformed set cannot be presented as raw or silently normalized.
History IDs are globally unique across steps in the Gate A 1.2 static contract. Required and
unsupported support rows contain unique history-action pairs, never overlap, and reconcile to the
one owning step distribution before any map reduction. ESS disposition is a biconditional over
the recomputed ESS, the all-zero state, and the exact registry threshold. It is not a free label.

For a covariate-adjusted causal design, every selected adjustment variable MUST be observed at the
declared decision boundary, temporally prior to treatment, and neither a prohibited collider nor a
post-treatment descendant. The selected set MUST satisfy the declared graphical identification
criterion on the exact directed acyclic graph. Acyclicity alone does not establish identification.
A different identification strategy MUST provide its own typed criterion and cannot inherit a
back-door disposition.
The causal query's treatment and outcome identifiers MUST resolve to graph nodes with those exact
roles, and its estimand MUST equal the preregistered estimand. The selected adjustment-set IDs in
the control strategy MUST equal the declared selected set exactly; an unselected eligible set or
free-standing `valid` label cannot satisfy the query.
Gate A 1.2 executes only the typed back-door strategy. Its graph has exactly one treatment-role
node and one outcome-role node. Both endpoints must be observed for an identified query; a
non-observed endpoint makes the identification disposition unknown. The design freeze is
identical wherever repeated and strictly precedes feature and outcome access. Every adjustment
set is frozen no later than the design. Train, calibration, and test splits bind exact frozen
member manifests: their member IDs are unique, their sets are pairwise disjoint, their union is
the complete declared split population, and every stratification input is typed, observed before
the freeze, and not an outcome or post-outcome proxy. Distinct split references alone do not prove
any of those properties. The estimand identifier resolves an exact registry contract for
population rule, treatment, comparator, outcome, outcome window, risk-difference effect measure,
and intercurrent-event rule.

For readiness, let \(U_i\) be the set of capabilities whose measurement or criterion disposition
is unknown and that are required, safety critical, or assigned positive weight. The aggregate is
defined only when \(U_i=\varnothing\). If \(U_i\ne\varnothing\), the aggregate MUST carry the
applicable non-observed state and the record MUST list exactly the unresolved capability
identifiers. Its non-observed basis IDs equal that same canonical set. A weighted aggregate MUST
reconcile every configured weight to one even when some inputs are non-observed. Belief holder,
decision actor, and readiness subject identify the same human; an observed selected action is a
member of the exact declared action space. The readiness as-of time lies inside its ordered
window and follows the reconciled observation, belief, and decision inputs. Window ID, clock, and
planned UTC boundaries equal the exact registry window contract; coherent boundary drift is a new
window definition, not the same frozen window.

For recoverability, the validator orders all valid events on the declared clock and selects the
earliest qualifying recovery, censoring, or competing event inside the frozen window. Elapsed time
is the difference from the index event and MUST lie within that window. A `recovered` disposition
requires a qualifying recovery event. The index role is exactly `none`, and its event ID and every
candidate event ID are pairwise unique. Absence of such an event in a fully observed window yields
right censoring. Invalid or non-observed windows retain their explicit state.
The planned window boundaries and clock equal the exact registry contract. When the index time is
non-observed, elapsed-time arithmetic is undefined and the validator MUST not parse or synthesize
a timestamp. An incomplete observation window cannot yield a confident terminal outcome without
the rule-specific evidence that permits it. A no-event right-censored record has no selected event
ID and derives its elapsed time only from the exact complete window endpoint; every other no-event
summary remains explicitly unknown, invalid, or inconclusive as applicable.
The absent-event reason is derived exactly: an unresolved index or qualifying-event time is
`input_nonobserved`; an explicitly incomplete window is `window_incomplete`; a registry-invalid
window is `invalid_window`; a tied earliest recovery and competing event is
`ambiguous_event_tie`; and a valid complete window with no qualifying event is
`no_qualifying_event`. These reasons cannot be interchanged while retaining the same outcome.

For transfer, source and target values MUST bind the same metric identity, direction, unit, and
harmonized population definition. The reported gap is recomputed using the declared direction.
Eligibility additionally requires typed dispositions for support overlap, measurement invariance,
access chronology, adaptation, and target-domain tuning. Failure or absence of a required condition
prevents an unqualified transfer result.
An assumption disposition is not established merely because its own field says so. Required
overlap, invariance, harmonization, exchangeability, or weighting conditions MUST bind eligible
retained evidence or remain proposed, unmeasured, contradicted, or otherwise non-establishing.
Empty or self-referential evidence references cannot authorize a comparable transfer result.
Gate A 1.2 contains no resolver that can establish transfer assumptions. Population
harmonization, overlap, and invariance therefore remain explicitly non-establishing, and the
favorable comparable disposition is unavailable in this release. Metric direction and source and
target domain identities still resolve exactly so a known structural failure can remain distinct
from an unresolved condition. An observed domain estimate requires at least one observed record;
without it, the domain estimate, uncertainty, and transfer gap remain non-observed. Analysis freeze
strictly precedes first target access. Use of target labels requires a retained label-access
timestamp, but a later evaluation timestamp does not by itself imply that labels were used for
adaptation.

For selective and out-of-distribution evaluation, the declared population is partitioned into
disjoint and exhaustive observed, missing, unmeasured, out-of-distribution, sensor-invalid, and
abstained counts. Counts MUST sum to the population denominator. Rates, coverage, conditional risk,
and confusion-table totals MUST equal the values implied by those counts and the frozen threshold.
Every opportunity belongs to exactly one atomic partition cell. Overlapping axes such as
`reference_unknown` and `detector_unknown` cannot be summed as though they were disjoint; their
intersection and complements MUST be represented explicitly or the aggregate is unidentified.

A conformal statement has a separate structured guarantee disposition and empirical coverage
result. An unqualified finite-sample guarantee is eligible only when every required assumption,
calibration-set condition, weighting condition, and declared group or target scope is established.
A contradicted or unmeasured required assumption forces an unsupported, inconclusive, or
not-applicable guarantee disposition even when empirical coverage happens to be high.
An `established` exchangeability or calibration condition requires an eligible external binding
under the evidence policy; self-attestation and an empty evidence set force a non-establishing
disposition.
Aggregate and per-group empirical coverage each carry an integer covered numerator and evaluated
denominator. For an observed positive denominator, the reported value is exactly their ratio
within the registry-owned absolute tolerance. A zero or non-observed operand yields non-observed
coverage and disposition `unknown`. Calibration and test set references are distinct. Under a
`disjoint_exhaustive` group scope, group evaluated counts sum exactly to the aggregate denominator;
under `overlapping`, they do not establish an aggregate by summation.
Every per-group row also resolves to one member of the exact external versioned group set. The
declared row universe and the external member set are equal, so coordinated deletion of both a
local universe entry and its result row remains detectable.

Joint silent misses are intersections over common object-level opportunities. Marginal human
miss, automation miss, and total counts identify only bounds on the intersection, not its exact
value. An exact joint count therefore requires one exact versioned opportunity set and one
member-complete row per set member. Every row binds the common object, clock, evaluation window,
reference state, human indication, automation indication, warning availability, and fallback
availability. All aggregate cells and marginals are derived from those rows; a self-declared or
marginal-only contingency table is insufficient. Any required non-observed row operand propagates
an explicit nonidentifiable result unless a separately specified partial-identification contract
derives a bound.

Worst-group eligibility is derived from typed minimum count, coverage, effective-sample-size, and
interval-width criteria. A group is unknown when membership or a required information operand is
non-observed; it is insufficient only when every operand is observed and at least one threshold
fails; otherwise it is sufficient. The universe is partitioned exactly into sufficient,
insufficient, and unknown ID sets. Any unknown group makes the overall result unknown. With no
unknown and no sufficient group, the result is `no_eligible_groups`. With at least one sufficient
group and no unknown, the extremum is identified over sufficient groups only, while every known
insufficient group remains visible.
The complete universe is the exact member list of one external versioned group set. Every result
row resolves to exactly one member, all members occur once, and the metric identity, unit, and
direction are shared before eligibility or the extremum is evaluated.

Numeric comparison is protocol-owned and branch-specific. Integer counts and set cardinalities
are exact. Observed belief normalization uses absolute tolerance \(10^{-6}\). Other recomputed
scientific values, including policy weights, effective sample size, rates, coverage, and OPE
quantities, use absolute tolerance \(10^{-12}\) and zero relative tolerance. Recovery elapsed time
is computed as exact decimal seconds from normalized UTC instants and has zero numeric tolerance.
No record may choose a looser comparison policy.

The evaluation-assurance bundle is also executable as a non-claim boundary. Its dataset is
synthetic-only, so its license disposition is exactly `synthetic_original`; an evidence-gap record
cannot assert retained-permission verification. Scientific, safety, compliance, and deployment
authorization remain false regardless of test, hazard, argument, or checksum fields.

## 6. Comparator and denominator discipline

Every estimand MUST declare:

- target population and sampling frame;
- unit of analysis and dependence structure;
- exposure or policy and exact comparator;
- index time, horizon, and censoring rules;
- outcome definition and direction;
- denominator construction;
- epistemic-state handling and abstention rule;
- subgroup definitions fixed before analysis;
- identification assumptions and falsification checks;
- uncertainty, multiplicity, and decision criteria; and
- retained evidence references.

For preregistration record \(G\), typed analysis specification \(A\), and declared observation
opening time \(t_{open}\), eligibility for `preregistered` requires

\[
\operatorname{idver}(G.experiment)=\operatorname{idver}(X),\quad
G.analysis=A,\quad
G.protocol=X.protocol,\quad
t_{freeze}(G)<t_{open}(G).
\]

The hash-bound \(A\) repeats the experiment-frozen target population, unit, sampling frame,
observation window, exposure, comparator, estimands, outcomes, inclusion and exclusion rules,
assignment mechanism, identification assumptions, all seven validity boundaries, epistemic
and abstention policy, subgroup plan, uncertainty, multiplicity, decision rules, and the exact
metric-to-estimand-to-outcome/direction mapping. Each metric mapping also freezes its
decision-rule ID, abstention-rule ID, uncertainty-method ID, and confidence level. The
analysis names one primary metric. Result-level and group-level intervals must match the
frozen uncertainty fields, and every metric-derived result lifecycle status must equal the
primary metric's interpretation status. Semantic validation requires exact parity;
neither schema-valid prose nor a digest of untyped bytes establishes preregistration.

Changing any item after observing outcomes creates a new exploratory estimand or corrected
protocol release. It MUST NOT inherit preregistered status.

## 7. Validity boundary

No estimand is valid outside the intersection of its declared boundaries:

\[
\mathcal V_P = \mathcal V_{population}\cap\mathcal V_{objects}\cap
\mathcal V_{time}\cap\mathcal V_{sensors}\cap\mathcal V_{reference}\cap
\mathcal V_{support}\cap\mathcal V_{protocol}.
\]

An experiment records exactly one boundary for every factor in this intersection. A result
inherits those exact boundaries through its versioned `experiment_ref`; changing any boundary
requires a new experiment and analysis-specification version.

Failure to establish membership in an element produces an explicit unknown or invalid state,
depending on whether evidence is absent or a declared rule was violated. It does not produce
non-membership by default.

Known threats that a protocol MUST address include selection, label leakage, object matching
errors, temporal leakage, informative abstention, informative censoring, unmeasured
confounding, policy-version ambiguity, interference, calibration drift, subgroup multiplicity,
dataset duplication, and reference-process error.

## 8. Evidence and claim relation

Let \(C_k\) be a versioned claim and \(E(C_k)\) its retained evidence objects. A lifecycle
status function is constrained by preregistered criteria \(d_k\):

\[
L(C_k) = d_k(E(C_k),P_k).
\]

If the source bytes, exact protocol or document version, publication date, scope, comparator,
or provenance required by \(P_k\) are unavailable, \(d_k\) cannot yield `supported`,
`contradicted`, or `replicated`. Architecture prose, generated review, checksums, signatures,
and consensus do not fill those evidence fields.

Standards mappings are gap analyses. No mapping function in Gate A returns `compliant`.

## 9. Deterministic semantic checks

JSON Schema validation is necessary but not sufficient. The offline Gate A validator MUST also
check, without network access:

1. all identifiers are unique in their declared namespace;
2. the scientific profile classifies every reference-bearing JSON path exactly once across rule,
   versioned, actor, schema, artifact, document-local reference, explicit-evidence-gap,
   registry-bare identifier, and document-local identifier resolution; every expected kind,
   version, owner, member, and cardinality resolves; the independently derived bound-schema path
   inventory also marks every remaining stable identifier path as an identity declaration and
   rejects omissions, duplicates, or handler-only paths;
3. all referenced files are relative retained regular files and match their SHA-256 digest and
   byte size;
4. categorical belief vectors correspond to their state spaces and sum to one within the
   exact protocol-owned tolerance, with the record tolerance equal to that policy;
5. observed numeric probabilities lie in \([0,1]\);
6. non-observed measurements contain no `value` and include a reason;
7. event-time intervals are ordered and clock identifiers resolve;
8. intervention assignment, delivery, receipt, and adherence are not conflated;
9. every executable application section except assumption-evidence eligibility carries an exact
   typed estimand reference equal to its profile and protocol mapping; every metric additionally
   binds its comparator, population, validity conditions, abstention rule, and uncertainty method;
10. every preregistered group is represented in worst-group results, including explicit
    unknown or inconclusive groups;
11. every standards mapping includes exact version, publication date, scope, comparator, and
    retained evidence, or is explicitly marked as a gap;
12. decision records bind exact artifact digests and structurally valid reviewer metadata,
    while GA-17 remains `not_evaluated` without independent authority verification;
13. a candidate or changed manifest does not inherit acceptance from another digest; and
14. every claim, experiment, result, metric, and lifecycle-event evidence binding uses an
    exact evidence ID and version and resolves to an active, protocol-eligible evidence object
    with a retained, source-ledger-resolved basis, with valid evidence required for
    support-like dispositions, and at least one witness has the protocol-declared compatible
    evidence status (with corrected evidence prohibited as the sole support-like witness);
15. every lifecycle history is nonempty, has unique events and contiguous sequences,
    protocol-authorized transitions, increasing UTC times, exact prior-status parity, final
    current-status parity, and byte-valid immediate-predecessor lineage whose history is the exact
    append-only prefix;
16. every corrected or retracted successor preserves its logical record ID and compatible
    kind/schema while binding a distinct immutable artifact ID and existing path with a strictly
    older semantic record version, exact digest, and byte size; across the scientific inventory,
    artifact IDs and logical-ID/version tuples are unique and each logical record forms one
    fork-free chain with one current head;
17. every preregistration resolves a typed analysis specification, matches its experiment and
    protocol exactly, repeats one exact design freeze, freezes adjustment sets no later, precedes
    every declared data-access boundary, and keeps train, calibration, and test identities
    pairwise distinct when overlap is prohibited;
18. every protocol-governed definition resolves uniquely by ID, kind, version, and owning
    protocol; state-space and choice-set members resolve within the named composite;
19. every result metric matches the protocol estimand's unique metric class and direction and
    the typed analysis specification's metric, outcome, population, comparator, per-metric
    decision rule, abstention rule, uncertainty method, and confidence level; the result and
    analysis name the same unique primary metric and metric-derived lifecycle status equals
    its interpretation status;
20. every scientific-disposition result binds an exact eligible experiment version under the
    same protocol and analysis specification, whose history contains `preregistered` before
    `running` and whose retained preregistration passes binding, freeze-parity, and chronology;
21. every experiment and its typed analysis specification contain exactly the seven declared
    population, object, time, sensor, reference, support, and protocol boundaries;
22. observation availability, actor-bound information-set membership, belief holder and target,
    human subject identity, selected-action membership, readiness capability windows, exact
    unresolved-capability and basis sets, aggregate unknown propagation, recovery histories,
    earliest qualifying events, absent reasons, elapsed times, and censoring dispositions
    reconcile;
23. sequential evaluation reconciles unique trajectory and history identities, horizon and
    terminal state, complete normalized behavior and target action distributions, logged-action
    propensities, exact-once per-history support, cumulative raw and transformed trajectory
    weights, effective sample size and threshold disposition by horizon, estimator bindings,
    explicitly non-observed estimator outputs, reward, cost, support, estimator disagreement, and
    no-extrapolation state;
24. causal adjustment sets satisfy the declared identification criterion and temporal,
    observability, mediator, collider, and treatment-descendant restrictions on the exact graph;
25. joint-event arithmetic, transfer metric identity and direction, harmonization, overlap,
    invariance, adaptation and tuning disclosures, conformal covered and evaluated counts and
    group scope, OOD partitions, non-asserted guarantee disposition, the exact worst-group
    information partition, and every direction-aware tied worst group equal the values implied by
    their complete operands and typed rules;
26. the research-function registry has unique contiguous order, an exact acyclic dependency DAG,
    locally resolvable Gate A schemas, and compatible producer-consumer contract handoffs;
27. the public profile reconciles exactly four retained ISO payloads and four pointer-only records,
    while receipt assertions remain distinct from independently retained transport observations;
28. every recovered historical byte, expected class, digest, size, archived-index membership,
    sidecar, report, and recovery disclosure agrees without editing the recovered artifacts;
29. every schema format is in the closed local checker set and every checker passes deterministic
    positive and negative canaries;
30. validation consumes one immutable in-memory snapshot, binds its canonical projection digest,
    and rejects a changed release tree or development inventory before reporting success; and
31. the supported launcher verifies isolated Python, dependency and executable bytes, and the
    locked platform-specific sandbox before any third-party import or claimed network and
    repository-write denial.

Fixtures MUST prove each critical rejection path. Validators MUST fail closed on unknown
properties, unresolved references, digest mismatch, and unknown schema identifiers.

## 10. Gate A decision boundary

These definitions are architecture candidates. Passing their schemas demonstrates internal
structural consistency only. Advancing beyond Gate A requires an explicit, hash-bound operator
acceptance record and any independent scientific review required by the accepted protocol.
