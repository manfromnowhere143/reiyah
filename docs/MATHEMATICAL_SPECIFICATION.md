# HARBOR Gate A Mathematical Specification

Document ID: `reiyah.mathematical-specification`

Version: `1.1.0`

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

For an information item (r_j), retain event, measurement, availability, and recorded times
((t_j^e,t_j^m,t_j^a,t_j^r)). The eligible information set for actor (a) at decision time
(t) is

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
The schema bounds components and tolerance, while deterministic semantic validation is
REQUIRED to check the sum, exact policy equality, and state-space correspondence.

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

For a correction or retraction, the prior reference has the same logical record ID, kind,
and schema as the successor, but an older version and distinct artifact ID, path, and digest.
The successor's own digest is external in the Gate A index, so no record hashes bytes that
contain that same hash.

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
that hides a safety-critical unknown, state whether automation state is included, and avoid
interpreting a score as authorization to control a vehicle.

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

If any required assumption is unsupported or contradicted, the effect is not identified under
that design and MUST be reported as `inconclusive`, `invalid`, or an explicit bound as dictated
by the protocol, not as an unqualified causal estimate.

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
policy, intersection construction, and minimum-information criterion. A group below the
criterion remains an explicit unknown or inconclusive group and MUST NOT be omitted from the
minimum. The typed worst-group disposition records every group ID in the direction-aware
extremum set \(g^*\), including all ties, plus the protocol-owned selection rule; free prose
cannot select or relabel the worst group. Post-hoc group discovery is `exploratory` and must
be labeled separately.

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

For episode (i), let the logged history through step (t) be

\[
H_{i,t}=(S_{i,0},A_{i,0},R_{i,0},C_{i,0},\ldots,S_{i,t}),
\]

where (R) is the preregistered reward and (C) is a separately defined safety cost. Let
(mu_v(a\mid H)) be the exact behavior-policy version and (pi_v(a\mid H)) the exact target
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
Failed support or information criteria force the preregistered invalid, inconclusive, or bounded
disposition. Gate A specifies these records but executes no policy or estimator.

### 5.10 Selective, OOD, and conformal evaluation

Let (s_\tau(x)\in\{0,1\}) denote acceptance under a frozen selective threshold. Report both
coverage (kappa_\tau=\Pr(s_\tau(X)=1)) and conditional risk
(R_\tau=\mathbb E[\ell(Y,f(X))\mid s_\tau(X)=1]), with all rejected cases partitioned into
novelty, ambiguity, missing, sensor-invalid, and protocol-abstention states. The threshold and
its selection data MUST be frozen before evaluation outcomes are accessed.

For a conformal set (C_\alpha(X)), a statement such as

\[
\Pr\{Y\in C_\alpha(X)\}\ge 1-\alpha
\]

is admissible only under the exact declared finite-sample, exchangeability, calibration-set,
weighting, and source-to-target shift conditions. Group-conditional and target-domain coverage
must be reported where declared. When the guarantee assumptions are unsupported or contradicted,
the guarantee disposition is invalid or inconclusive, never silently inherited from the source
domain.

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

For preregistration record (G), typed analysis specification (A), and declared observation
opening time (t_{open}), eligibility for `preregistered` requires

\[
\operatorname{idver}(G.experiment)=\operatorname{idver}(X),\quad
G.analysis=A,\quad
G.protocol=X.protocol,\quad
t_{freeze}(G)<t_{open}(G).
\]

The hash-bound (A) repeats the experiment-frozen target population, unit, sampling frame,
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
2. the scientific profile classifies every reference-bearing JSON path by ownership domain,
   expected kind, version rule, and cardinality; every resulting local, protocol-owned, or exact
   external reference resolves under that rule;
3. all referenced files are relative, retained, and match their SHA-256 digest;
4. categorical belief vectors correspond to their state spaces and sum to one within the
   exact protocol-owned tolerance, with the record tolerance equal to that policy;
5. observed numeric probabilities lie in \([0,1]\);
6. non-observed measurements contain no `value` and include a reason;
7. event-time intervals are ordered and clock identifiers resolve;
8. intervention assignment, delivery, receipt, and adherence are not conflated;
9. every metric binds an estimand, comparator, population, validity conditions, abstention
   rule, and uncertainty method;
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
    current-status parity, and byte-valid immediate-predecessor lineage;
16. every corrected or retracted successor preserves its logical record ID and kind/schema
    while binding a distinct existing older predecessor artifact, path, version, and digest;
17. every preregistration resolves a typed analysis specification, matches its experiment and
    protocol exactly, and freezes strictly before its declared observation boundary;
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
    and
21. every experiment and its typed analysis specification contain exactly the seven declared
    population, object, time, sensor, reference, support, and protocol boundaries;
22. observation availability, actor-bound information-set membership, belief holder and target,
    readiness capability windows, recovery histories, and censoring dispositions reconcile;
23. sequential evaluation reconciles horizon, trajectory steps, propensities, cumulative weights,
    effective sample size, estimator bindings, reward, cost, support, and no-extrapolation state;
24. joint-event arithmetic, transfer gaps, coverage denominators, and every direction-aware tied
    worst group equal the values implied by their complete operands;
25. the research-function registry has unique contiguous order, an exact acyclic dependency DAG,
    locally resolvable Gate A schemas, and compatible producer-consumer contract handoffs;
26. the public profile reconciles exactly four retained ISO payloads and four pointer-only records;
    the distribution inventory, rights observation, attributions, receipt chronology, repository,
    ref, reachable commit, exact index, payload tree, readback, and receipt lineage agree; and
27. every recovered historical byte, expected class, digest, size, archived-index membership,
    sidecar, report, and recovery disclosure agrees without editing the recovered artifacts.

Fixtures MUST prove each critical rejection path. Validators MUST fail closed on unknown
properties, unresolved references, digest mismatch, and unknown schema identifiers.

## 10. Gate A decision boundary

These definitions are architecture candidates. Passing their schemas demonstrates internal
structural consistency only. Advancing beyond Gate A requires an explicit, hash-bound operator
acceptance record and any independent scientific review required by the accepted protocol.
