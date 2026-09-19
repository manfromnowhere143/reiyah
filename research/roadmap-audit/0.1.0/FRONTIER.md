# What current methods change for Reiyah

Document ID: `reiyah.roadmap-audit.frontier`. Version: `0.1.0`.
Lifecycle status: `exploratory`. Review cutoff: 19 September 2026.

Reiyah has a defensible architecture for conditional evidence, but no demonstrated
frontier advantage. The relevant competitive question is the cost of a justified
decision, under the same observation and error obligations. A dated method list
cannot answer that question without a comparison on qualified inputs.

The source IDs below resolve to exact versions, author lists, publication/revision
dates, review depth, private payload digests and rights records in
[sources.json](sources.json). All implications for Reiyah are this audit's
inferences. None of the external results were reproduced here. Abstract-only
records support a scoped candidate comparison, not an implementation guarantee.

## The closest comparators

| Source | What was inspected | Consequence for the roadmap |
| --- | --- | --- |
| **S01. [Active Testing, ICML 2021](https://proceedings.mlr.press/v139/kossen21a.html)** | Abstract: select evaluation labels and correct adaptive-selection bias. | Active evaluation is an established baseline, not a new category Reiyah can claim to invent. |
| **S02. [Weighted risk-limiting audits, UAI 2023](https://proceedings.mlr.press/v216/shekhar23a.html)** | Full arXiv v1: finite weighted populations, randomized sampling without replacement, confidence sequences and optional side information. | This is a particularly close comparator for spending fewer observations on a fixed population. Audit answers reveal the scoped values; Reiyah's residual reference uncertainty needs a separate argument. |
| **S03. [Active Statistical Inference, ICML 2024](https://proceedings.mlr.press/v235/zrnic24a.html)** | Abstract: model-guided label collection with inferential uncertainty. | Include acquisition and its correction costs. Model confidence alone is not an observation. |
| **S04. [Prediction-Powered E-Values, ICML 2025](https://proceedings.mlr.press/v267/csillag25a.html)** | Full arXiv v2: sequential construction with predictable bounded factors and constrained randomized label acquisition. | A relevant route to optional-stopping guarantees. Predictors and acquisition can adapt only within the stated information and nonnegativity requirements; it is not permission for arbitrary selective labels. |
| **S05. [Prediction-Powered Active Testing, 9 July 2026](https://arxiv.org/abs/2607.08347v1)** | Full v1: residualized finite-pool risk estimation and adaptive acquisition; asymptotic confidence intervals. | Current strong estimation comparator. Its unbiasedness and asymptotic interval result are different properties. Appendix E.5.5 requires overlap, moment and variance-stabilization conditions; finite-sample sequential validity does not follow automatically. |
| **S15. [Confidence sequences without replacement, NeurIPS 2020](https://arxiv.org/abs/2006.04347v4)** | Full v4: uniform sampling from a finite population with time-uniform uncertainty. | Use as a simple statistical baseline. The sampling randomness can support inference about that fixed population without asserting independent scene values; arbitrary preferential sampling needs the appropriate different construction. |

**Recommendation:** add a small statistical comparison beside the exact
conditional checker. Preserve the distinction between a probability of error
under a sampling design and excluding every allowed reference world. The original
studies compared exact stopping and selectors; they did not establish superiority
over all statistical evaluation methods. Conversely, the statistical papers do
not invalidate those exact results or magically identify an ambiguous reference.

## Where attractive guarantees need qualification

| Source | Actual scope | Reiyah decision |
| --- | --- | --- |
| **S06. [Anytime-valid, Bayes-assisted PPI, 24 October 2025 revision](https://arxiv.org/abs/2505.18000v2)** | Full v2 explicitly states asymptotic time-uniform validity for i.i.d. data; nonasymptotic extensions remain future work in its conclusion. | Do not classify it from the title alone as a finite-sample release guarantee. |
| **S17. [No Free Lunch for PPI, 24 June 2026 revision](https://arxiv.org/abs/2505.20178v2)** | Full v2 analyzes finite-sample mean-estimation error and shows that the studied PPI++ estimators can be worse than labels-only estimation when the correlation/sample-size conditions fail. | Retain a labels-only arm and small-sample or poor-proxy losses. This is not a universal condemnation of PPI or a measured Reiyah cost result. |
| **S19. [Calibeating PPI, 23 April 2026](https://arxiv.org/abs/2604.21260v1)** | Abstract: linear/isotonic calibration, semisupervised mean estimation and first-order efficiency relationships to established AIPW methods. | Watchlist for a later fixed-target comparison. Calibration time and data use count; the abstract supplies no general arbitrary-stopping guarantee. |
| **S20. [Stop Guessing When to Stop Testing, 9 July 2026](https://arxiv.org/abs/2607.08522v1)** | Full v1: group sequential evaluation with independence and approximately normal test-statistic conditions. | Useful recent task framing, not a theorem for dependent Reiyah image rows. No published cost-reduction percentage is transferred to Reiyah. |
| **S12. [Noisy-label conformal prediction, COPA 2025](https://proceedings.mlr.press/v266/penso25a.html)** | Abstract: finite-sample classification coverage under uniform label noise. | Arbitrary missing objects, correlated box errors and unknown timing do not become uniform class noise. Keep it a different contract. |
| **S13. [Automatically Adaptive Conformal Risk Control, AISTATS 2025](https://proceedings.mlr.press/v258/blot25a.html)** | Abstract: approximate conditional control of expected loss with data-adapted conditioning classes. | Consider for a later statistical risk target. It is not exact control for every joint interpretation or every subgroup. |
| **S18. [Multiple imperfect measurements without gold labels, 1 September 2026 revision](https://arxiv.org/abs/2608.18294v2)** | Full v2: three or more imperfect measurements, latent-variable identification and asymptotic inference under conditional independence and other identification/regularity conditions. | Adding another model is not a substitute for proving applicable assumptions. Shared detector errors are central to Reiyah; test dependence rather than declaring a consensus to be truth. |

These distinctions alter engineering priorities. First define the decision's
guarantee, population and measurement mechanism. Then select a method whose
theorem covers them. An asymptotic result, a marginal coverage result and an exact
conditional enclosure must not share an undifferentiated “certified” status.

## Exact proofs and downstream validation

| Source | Actual scope | Reiyah decision |
| --- | --- | --- |
| **S09. [SCIP Optimization Suite 10.0, 23 November 2025](https://arxiv.org/abs/2511.18580v1)** | Full section 3.1: rational MILP solving and VIPR-format proof logging, with declared certification and presolving limits. | Independent optimization checking already exists. Keep the domain-specific matching checker small; compare general proof systems when a real workload needs them. Do not claim rational certificates as unique technology. |
| **S08. [Sim2Val, 3 September 2025 revision](https://arxiv.org/abs/2506.20553v2)** | Full v2: paired target/auxiliary measurements and control variates for mean-performance estimation. The limitations specify i.i.d. target sampling and distinguish means from tail risk. | A strong future comparator if genuine expensive outcomes and correlated cheaper measurements exist. Include costs of both, selection bias and domain validity; no guaranteed saving follows from correlation alone in our unmeasured workflow. |
| **S10. [Pseudo-Simulation / NAVSIM, 20 March 2026 revision](https://arxiv.org/abs/2506.04218v3)** | Full v3: generated nearby observations, recovery-oriented evaluation and comparison to closed-loop simulation. Its limitations explicitly leave direct real-world deployment correlation unestablished. | It informs a later downstream evaluation. It does not validate this static detector-loss proxy or authorize buying/building a simulator now. |
| **S11. [BridgeSim, 12 April 2026](https://arxiv.org/abs/2604.10856v1)** | Full v1: observational shift and objective mismatch between open-loop policies and closed-loop simulation. | A stronger reason to qualify the intended action and outcome. Treat the authors' simulator results as scoped findings, not physical safety evidence. |
| **S16. [NAVSIM/Bench2Drive correlation study, 30 April 2026](https://arxiv.org/abs/2605.00066v1)** | Abstract: eight methods with complete paired published data and ranking inversions. | Keep as a limited diagnostic. This small cross-benchmark association cannot certify future systems or settle the operational target. |
| **S07. [Prediction-Powered Risk Monitoring, 10 June 2026 revision](https://arxiv.org/abs/2602.02229v2)** | Full v2: bounded loss, labeled and unlabeled data, nominal calibration and independent/i.i.d. sampling conditions within the stated setup. | Future monitoring comparator only. Its broad abstract wording must not erase the sampling or label requirements. It is distinct from Reiyah's closed, negative output-summary prediction experiment. |
| **S14. [No Free Lunch for Human-AI Collaboration, AAAI 2025](https://ojs.aaai.org/index.php/AAAI/article/view/33574)** | Abstract: limits on deterministic fusion of calibrated predictions for binary 0-1 accuracy. | Human/automation complementarity needs additional structure and evaluation. This does not prove human collaboration is useless; it prevents assuming benefit from two channels alone. |

**Recommendation:** retain evidence custody, common interpretations and a small
checker as useful infrastructure. Concentrate new work on the observation-to-decision
boundary and honest full-cost comparison. Delay broader runtime, simulation and
human-readiness extensions until each has an identified decision and qualified
inputs. A paper's sophistication or publication year is not a reason to add it.

The resulting [roadmap](../../../docs/ENGINE_ROADMAP_2026-09-19.md) is more current
and more falsifiable than the older navigation. Its proposed composition is not
claimed novel, optimal, independently reviewed or empirically superior.
