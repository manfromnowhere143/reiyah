# Technical review guide

Document ID: `reiyah.technical-review`. Version: `0.1.0`.
Lifecycle status: `exploratory`. Updated 16 October 2026.

Reiyah implements offline conditional comparisons and evidence checks. The
research question is whether those capabilities can improve a consequential
engineering decision under imperfect observations. The broader HARBOR program
includes belief, readiness, recovery, joint silent misses, causal effects,
transfer and worst-group validation. Those ambitions have different measurement
requirements and are not all implemented.

The [README](../README.md) explains the complete research progression. This guide
provides a direct path from its claims to contracts, code, checks and limitations.
The [dated review record](reviews/technical-review-2026-10-16.json) records what
was checked in this presentation pass. It is not a scientific acceptance record,
security certification or claim of state-of-the-art performance.

## Read in this order

1. **Decision and evidence.** Read the README's [implemented scope](../README.md#implemented-scope),
   [current evidence](../README.md#current-evidence) and
   [next decision](../README.md#next-research-decision). Conventional parity,
   corrections and unresolved physical measurements are part of the result.
2. **Computational contract.** Read the
   [perception architecture](PERCEPTION_DECISION_ARCHITECTURE_2026-09-09.md) for the
   shared-world loss calculation and the
   [replacement contract](../research/perception-revision/0.1.0/README.md) for
   independently declared A/B outputs. The architecture's original study plan is
   historical; the current [handoff](SESSION_HANDOFF.md) controls continuation.
3. **Producer and checker.** Inspect the
   [strict contract](../tools/perception_revision/contract.py),
   [proof producer](../tools/perception_revision/kernel.py),
   [comparison checker](../tools/perception_revision/checker.py), and
   [matching/cover verifier](../tools/perception_decision/checker.py).
   Then inspect [adversarial and direct-calculation tests](../tests/test_perception_revision.py).
4. **Measurement obligations.** Read the
   [reference-population audit](RESULT_AO_REFERENCE_POPULATION_AUDIT.md),
   [complete takeover census](../research/takeover-outcome/0.2.0/DECISION.md),
   [manD source closure](../research/mand-semantics/0.1.0/DECISION.md), and
   [nuPlan source contract](../research/nuplan-outcome-source/0.1.0/CONTRACT.md).
   Stored data, executable semantics and physical measurement are separate evidence.
5. **Authority and reproducibility.** Read the [repository contract](../AGENTS.md),
   [static Gate A architecture](ARCHITECTURE.md) and [validation procedure](VALIDATION.md).
   Gate A remains operator-unaccepted. Research test execution does not accept it.

## Architecture boundaries

| Boundary | What crosses it | Required qualification |
| --- | --- | --- |
| Source to normalized input | Exact source identities, selected membership, availability and transformation records | Terms, complete accounting and the source-to-operand transformation. A supplied digest alone does not authenticate the source. |
| Input to reference model | Shared alternatives, constraints, object identity, matching and time assumptions | The finite model must represent the declared uncertainty. Enumeration cannot establish physical coverage of omitted alternatives. |
| Model to proof | Rational loss bounds, worlds and matching/cover witnesses | The implementation must respect common references and work limits. Resource exhaustion cannot become evidence of consistency or support. |
| Proof to checked decision | A result entailed by the certificate and the exact submitted input | Check every admitted world where required, witness validity, bounds and strict decision thresholds. Invalid or unavailable inputs remain distinct. |
| Research result to empirical or product claim | Retained findings, failures, comparator and complete costs | Qualified observations and a fair comparison. Passing tests does not supply physical truth, independent replication or measured work savings. |

The replacement checker reconstructs admitted worlds and validates matching and
vertex-cover certificates without invoking the producer's matching algorithm.
The parser, rational representation, domain semantics and some certificate helpers
are shared trusted code. The conditional-audit producer also uses the audit
checker's conclusion function. This is a specific separation of responsibilities,
not two independent implementations of the entire pipeline.

CLI inputs are bound to expected file hashes before parsing. The
[writer](../tools/perception_decision/cli.py) checks a complete packet and uses an
atomic non-overwriting filesystem operation. Callable internal APIs have their
own input-validation preconditions; not every helper is a public trust boundary.
The ordinary research CLI does not provide the Gate A locked-launcher isolation.

## Reproduce the reviewed surface

The smallest example uses the Python standard library only:

```sh
python3 -B research/perception-decision-review/0.1.0/reproduce.py
```

Compare its stdout byte-for-byte with
[expected.json](../research/perception-decision-review/0.1.0/expected.json).
It exercises authored matching and uncertainty examples; it does not run a model.

The complete perception unit-test pattern requires **jsonschema and Pillow** in
addition to Python. The repository consistency check also requires **NumPy and
SciPy**. The dated record reports the versions actually used; it is a tested
environment record, not a portable environment lock for every historical study.
Use an isolated environment and keep these research dependencies separate from
[Gate A's validator lock](../validation/requirements.lock).

```sh
python3 -B -m unittest discover -s tests -p 'test_perception*.py' -v
python3 -B tools/measure/gate_b_check.py --json /tmp/reiyah-gate-b-check.json
```

The test pattern covers the perception modules and authored fixtures, including
input admission, unknown states, matching proofs, replacement/audit calculations,
source identity and CLI failure paths. It does not cover every tool in this
repository. The default consistency check verifies historical transcript hashes;
it does not replay those experiments. Optional attack suites, upstream nuPlan
execution, full simulator runs and model campaigns are separate operations.

The first run of this review failed because Pillow was absent from the chosen
Python environment. That attempt is retained. The corrected run used an isolated
local environment with the existing Pillow installation; no packages, datasets or
models were downloaded. No assertion, expected failure or scientific artifact was
changed to obtain a pass.

## Current evidence and open obligations

- **Perception:** conditional mathematics and selected comparisons are inspectable.
  Broad superiority, physical truth and complete-work savings remain unestablished.
- **TD2D and manD:** the inspected source routes are closed. Complete summary coverage
  or aligned recorded coordinates do not establish a recovery horizon.
- **nuPlan:** v1.2 source inspection qualifies sampled event rules, software timestamps
  and the selected termination path. Native controls and complete observed windows
  remain prerequisites for interpreting future simulator trials.
- **Human readiness and physical recovery:** neither is admitted by the current evidence.
  A simulator contact metric does not replace a human or physical measurement model.
- **Engineering scope:** current checks establish only their declared properties.
  Production readiness, whole-repository security and external scientific replication
  have not been established by this review.

The next scientific action remains the bounded authored nuPlan native-control
protocol in the [current decision](../research/nuplan-outcome-source/0.1.0/DECISION.md).
A polished presentation does not change that dependency, reopen closed cohorts or
supply Gate A acceptance. Cite the exact packet and commit whose evidence supports
a statement; the stable release tag and later main-branch work have distinct scopes.
