# What Reiyah should learn from Sentinel, Telos, and Inbar

Document ID: `reiyah.sibling-research-transfer.2026-09-07`

Version: `0.1.0`

Lifecycle status: `exploratory`

The operator expressly requested this cross-repository investigation on September 7, 2026.
The decision is to carry over specific experimental controls, while keeping the projects and
their evidence authorities separate. No repository merge is justified by this review.

This is a bounded, source-level examination of selected result-bearing paths, not a complete
new audit of every historical experiment in the three repositories. It supplements the
[Reiyah research board](RESEARCH_BOARD_2026-09-07.md) and does not displace the
[reference adjudication study](REFERENCE_ADJUDICATION_STUDY_2026-09-07.md).

## Sources and inspection boundary

| Project | Exact inspected Git commit | What was examined |
| --- | --- | --- |
| Sentinel | `20fefa9b9a5ce031db021909404867bc0fa58de4` | Frozen research question, full-benchmark and transfer results, iteration 134 protocol, analyzer, actuator patches, execution and decision logs |
| Telos | `7551466ff777bd638ec7fda8cedc64ea52d3b409` | Current mission pointer, corrected property-oracle pipeline, natural-rate and execution-oracle results, issue-derived tests, transfer reconstruction, adjudication code and rows |
| Inbar | `65bec5634c5ca83de3955d7f377b997f5a48734f` | Repository contract, handoff, susceptibility freeze and correction, retrospective atomic cells, plant/forward-model implementation, masking computation and replay tests |

The Inbar checkout is physically named `fieldtrue`; its own `AGENTS.md` identifies it as
Inbar and its configured remote is `manfromnowhere143/inbar`. This observation does not
rename Reiyah or import Inbar's bootstrap. Sentinel had existing uncommitted work, which was
excluded from the scientific snapshot and left untouched. Telos and Inbar were clean when
observed. No sibling bootstrap, validator, model, provider, container, simulator or actuator
was executed. Thirty-two selected Git blobs were retained privately, with source paths,
commit identities, byte sizes and digests in the
[source pointer ledger](../evidence/developer-value/sibling-source-ledger-0.1.0.json).

The new [independent aggregator](../tools/measure/audit_sibling_evidence.py) reads those
retained bytes without importing sibling code. Its
[output](../evidence/developer-value/sibling-audit-0.1.0.json) distinguishes execution-log
aggregation, adjudicator-row aggregation, and retrospective simulator-cell aggregation.
These are different evidence levels. None is a fresh physical experiment or independent
semantic adjudication.

## Sentinel: a monitor's benefit does not identify its mechanism

Sentinel wraps a frozen driving planner with an intervention rule. Its iteration 134 control
uses a donor schedule of brake times and the same trajectory actuator, withholding the
planner's risk-related inputs from the placebo decision. The code actually implements that
separation: the placebo receives a frame counter and schedule, while its actuator returns
the frozen zero trajectory. This is a useful negative control for an introspective monitor.

Independent aggregation of the retained execution log reproduces 400 episodes per arm and
class-weighted NCAP means of 2.1350, 2.9058 and 2.5376 for off, union and placebo. The union
minus placebo difference is 0.3683, with the registered pair-bootstrap interval
[-0.1901, 0.8866]. It remains inconclusive. This review did not rerun the simulator, recover
safe-progress trajectories, or independently check the upstream environment-drift comparison.

The placebo decision log contains 859 brake records and 6,219 frame records. All frame
records lack the `pair` key required by the historical counter, reproducing the mechanism
behind the already disclosed zero-frame report. The report's frame value is incorrect; the
registered score comparison is not changed by that defect.

The retained result reports 1,205 scheduled placebo brake frames, but only 859 realized.
Its interpretation correctly leaves the semantic mechanism unresolved. A further source-level
observation is that the analyzer's positive semantic-verdict branch checks the score interval,
but does not gate that verdict on realized-dose comparability. That branch did not produce
the current result; it must not be mistaken for a demonstrated false positive in this run.

Two inference details deserve prospective attention. The 20 resampled scenario-class pairs
contain only 14 distinct scene identifiers, so scene reuse needs explicit treatment in any
claim requiring independence across environments. In the exact registered random sequence,
69 of 10,000 bootstrap draws omit at least one scenario class; the analyzer assigns that
absent class a zero component. This convention is reproducible, but a new protocol should
define its stratified estimand and resampling behavior before running. No replacement
interval was selected after seeing whether it would favor the monitor.

**Carry into Reiyah:** interventions need a placebo and a progress constraint. Frozen rules
must distinguish overall policy benefit from evidence that the perception semantics caused
the benefit. A future causal monitor study must retain intended actions, realized actions,
termination, censoring and outcomes as separate observations.

**Do not carry over:** a reported simulator improvement as evidence for Reiyah, a universal
benefit of introspection, or the inference that matching realized brake counts would itself
isolate semantics. Realized dose is affected by the policy and by early termination. Matching
or conditioning on it after execution can create selection bias.

For a prospective randomized policy comparison, let A assign the semantic or blind policy,
D be realized brake dose, T termination, and Y the outcome. The policy can affect both D and
T, while T limits D. The intention-to-treat contrast E[Y | A=semantic] minus
E[Y | A=blind] compares those complete policies. A contrast conditional on observed D answers
a different question and requires additional identification assumptions. A preregistered
family of blind policies can test whether semantic selection improves the measured
safety/progress tradeoff over that family. It cannot establish superiority over every
possible blind policy.

## Telos: reference-free generation can still have reference-dependent evaluation

Telos examines completion that satisfies a visible grader while violating a task's intended
behavior. Its corrected iteration 197 is directly relevant to Reiyah's independence thesis.
Source inspection confirms that the property generator obtains a function/file locator from
the candidate diff. Its later soundness rule keeps properties that pass on the gold patch.
Withholding the gold patch from the prompt therefore does not make the complete pipeline
reference-free. Zero failures on the gold executions used for selection cannot independently
estimate a false-positive rate.

For iteration 231, a separate aggregation of the 67 retained adjudicator rows reproduces
4 flags among 13 positive-labeled opportunities with 4 missing outcomes, and 10 flags among
54 negative-labeled opportunities with 12 missing. Thus the observed-lower, missing-upper
and complete-case recall counts are 4/13, 8/13 and 4/9. The corresponding false-positive
counts are 10/54, 22/54 and 10/42. Retaining the adjudicator's four instrument-failure labels
reduces the diagnostic counts to 2/13 and 8/54. Those labels were not independently
adjudicated here, and this operation does not revalidate the underlying semantic ground truth.

The history also cautions against universal impossibility claims. Iteration 231 described
plausible wrong values as an oracle ceiling. Iteration 234 subsequently retained an
issue-derived consequence test that distinguished one such candidate from its gold control.
The latter record narrows the former interpretation. Even the revised claim that a detector
reasoning from code faces an absolute ceiling is too strong without an information model:
specifications, relational properties and independent consequences can supply additional
constraints. A failure by a finite collection of instruments is not an impossibility theorem.

**Carry into Reiyah:** trace every input to generation, selection and adjudication; measure
instrument failures separately from subject failures; retain explicit missingness; compare
ensembles at a matched false-alarm or review budget. A shared reference can make apparently
different judges fail together.

**Do not carry over:** a gold-selected zero-FP figure, an unverified semantic label, or a
universal ceiling inferred from a small selected cohort. Telos's cross-solver recurrence
and transfer results are not perception results.

## Inbar: probe observability before celebrating inference

Inbar's research formulation is relevant: maintain competing mechanism hypotheses, choose a
discriminating intervention, separate the proposer from the outcome authority, and represent
unknowns. Its current implementation and retained corrections sharply limit what is established.

The plant and forward-model code share `_graded_transform`. The simulated plant additionally
contains lag, noise and an initial-state nuisance; the forward calculation omits them.
That does introduce controlled mismatch, but it is not an independent model of an unknown
physical system. The `unknown` mechanism maps to nominal parameters at every severity.
An unknown identifier therefore does not establish open-set fault coverage.

Independent joining of the 75 retained predictions and 1,125 retrospective measurements
reproduces the informative 746/750 agreement and confusion counts TP=60, FP=0, FN=4, TN=686.
The always-negative comparator scores 686/750, which already exceeds the frozen 0.90
agreement threshold. The stronger sensitivity and balanced-accuracy diagnostics remain
retrospective. This aggregation does not recreate the contemporaneous evidence missing
from the original run or repair its source-binding and approval defects.

**Carry into Reiyah:** test whether the claimed effect follows algebraically from the data
generator; include an observation-free baseline; retain competing hypotheses until evidence
separates them; test genuinely omitted mechanisms rather than labeling nominal behavior
`unknown`. Calibration must include reference and model misspecification, not only noise
around a shared forward model.

**Do not carry over:** the toy plant, a collection of signatures as independent human intent,
or an accuracy threshold that a trivial predictor can pass. A large validation apparatus is
useful only to the extent that its controls reach the scientific failure it claims to constrain.

## Architecture decision

There is a common scientific problem: the observed success signal may not identify the
claimed property. That supports shared research concepts, not a monolithic code merge.
Sentinel's unit is a closed-loop episode, Telos's a task/candidate/exercise, and Reiyah's
current study unit a sampled detection with sensor evidence. Inbar's simulator cell has
another observation and intervention model. Collapsing them into one generic `success`
record would erase precisely the distinctions that matter.

Reiyah should keep first-class opportunity populations, reference scope, evaluator input
lineage, instrument validity, unknown states and explicit counterexamples. Domain adapters
may later emit those fields, with domain-specific semantics and independent admission.
No sibling code or restricted payload is incorporated by this review.

The immediate implementation is the [portable reference audit](REFERENCE_AUDIT_DEMO_2026-09-07.md).
The next scientific observation remains the independent human review of the already prepared
240 cases. No amount of software consolidation supplies those missing observations.
