# Normative Glossary

Terms in this file constrain Gate A documents and schemas. Metric symbols and full estimands
are defined in the mathematical specification.

| Term | Normative meaning | Must not be collapsed into |
|---|---|---|
| Observation | A time-indexed, provenance-bound measurement or explicit measurement-state record from an object or context. | Ground truth or latent belief |
| Latent belief | A distribution or set-valued epistemic representation over hypotheses, conditional on declared evidence. | Observation, decision, or confident class label |
| Decision | A recorded choice or abstention produced under a declared policy and information set. | Intervention actually delivered |
| Intervention | A time-indexed action, non-action, or delivery failure with assignment and exposure provenance. | Intended decision or outcome |
| Outcome | A post-intervention or naturally observed endpoint with a measurement protocol and validity state. | Label, decision, or evidence of causality |
| Evidence | Retained bytes plus provenance that may bear on a claim. | Truth, authority, consensus, or acceptance |
| Object-level | A stable, scoped driver, vehicle, subsystem, road user, event, or context entity with explicit linkage and time. | Frame-wide anonymous feature or person-only classification |
| Driver-vehicle belief | A joint epistemic state over relevant human, automation, vehicle, and context hypotheses. | Driver state alone |
| Readiness | A protocol-bound estimand of ability to satisfy a declared transition or fallback demand within a declared horizon and loss model. | Alertness, gaze, or one classifier score |
| Recoverability | A protocol-bound estimand of whether a safe-enough reachable response set remains under declared dynamics, horizon, uncertainty, and constraints. | Readiness or eventual outcome alone |
| Joint silent miss | A declared hazard-relevant condition in which specified human and automation channels both fail to expose or act on the condition within the evaluation window. | Union of independent errors or missing data |
| Causal policy effect | A contrast between potential outcomes under specified policies for a target population, identification strategy, and assumptions. | Correlation or before/after difference |
| Transfer | Performance or validity evaluated across a predeclared source-to-target shift. | Random split generalization |
| Worst-group validation | Evaluation over every preregistered eligible group, reporting the least favorable group under coverage and uncertainty rules. | Overall average or a post-hoc subgroup search |
| Comparator | The exact baseline, policy, protocol, or system against which an estimand is contrasted. | A vague “state of the art” label |
| Validity domain | The population, context, sensors, policy, time, and measurement conditions under which a value may be interpreted. | Deployment scope |
| Abstention | An explicit decision not to emit a substantive estimate or action because a declared validity or uncertainty rule fired. | Negative, zero, missing, or failure |
| Missing | Expected data are absent for a known reason or an explicitly unknown reason. | Zero or normal |
| Unmeasured | The protocol did not attempt or was unable to define the measurement. | Missing-at-random or negative |
| Sensor-invalid | Bytes exist but fail declared sensor or acquisition validity criteria. | Observed value |
| Out-of-distribution (OOD) | A declared shift detector or domain rule places the case outside the validated domain. | Error, anomaly, or negative |
| Null result | A valid protocol result that does not reject or distinguish the declared null under its decision rule. | Missing, invalid, or proof of no effect |
| Inconclusive | Evidence is insufficient for the declared decision rule while the analysis may remain valid. | Null, failed, or supported |

The canonical lifecycle status definitions and allowed transitions live in
[`STATUS_MODEL.md`](STATUS_MODEL.md). Where ordinary language conflicts with a schema or
accepted manifest, the accepted hash-bound artifact controls within its declared scope.
