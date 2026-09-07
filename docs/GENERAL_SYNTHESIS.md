# What the measurement program currently supports

Document ID: `reiyah.general-synthesis`

Version: `0.2.0`

Lifecycle status: `corrected`

Reiyah measures coincident errors on declared public-data populations and tests whether observable
outputs can predict some of those errors. The program supports descriptive findings, not a
universal law of independence, a vehicle safety bound, or a validated human-belief estimator.
The [research-board report](RESEARCH_BOARD_2026-09-07.md) reconstructs the implementation,
compares relevant primary research through the review date, and defines the next experiments.
The [claim register](../evidence/claim-status-register-2026-09-07.json) is the current reconciliation
point. Prior transcripts and the previous synthesis remain discoverable in Git history.

## Sensors

On the existing nuScenes camera/lidar pair, excess joint misses survive the declared conditioning.
The new [reference audit](RESULT_AO_REFERENCE_POPULATION_AUDIT.md) reproduces the conditional
ratio and uses whole scenes for resampling. It also demonstrates that the filtered reference
creates many of the original ghost flags: those predictions are near annotations that the cache
excluded. Complete annotations still do not establish exhaustive physical truth.

The temporal coincidence analysis shows an association among unmatched detections. Its magnitude
and meaning depend on reference coverage, donor selection and whether the null preserves
world-fixed or ego-relative geometry. It is not the Bernoulli safety-critic coefficient in RSS.
The descriptive sensor result is useful. Its cause and safety consequence remain unestablished.

The operating-point studies show why marginals and absolute joint loss must accompany a normalized
coefficient. Preregistered same-kind ordering forecasts were partly falsified. A channel that is
nearly blind can force the coefficient toward one. Different sensing modalities do not guarantee
independent failures, and similar architectures do not determine a universal dependence ordering.

## Humans

The human thread measures looking, responding, takeover latency and gaze allocation in different
public datasets. These are different variables. They do not establish object-specific belief or
recoverability. The BDD-A detector/gaze construction uses detector-selected opportunities and
aggregate laboratory attention. Its near-one coefficient cannot certify complementary human and
machine detection, particularly when one channel is nearly always labeled as missing.

## Language-model juries and monitors

Archived question outputs show coincident errors and benchmark-specific lineage associations.
Correlated errors and difficulty mixtures have substantial prior literature. The homogeneous
independent-equivalent summary is an arithmetic convention, not a literal identified count of
independent models. The same formula in two domains does not make their latent constructs equal.

A calibrated logistic monitor predicts jury correctness within some tested settings. Other results
record failed benchmark transfer. Sensor monitors similarly use conventional fitted models and
reference-defined labels. They have not shown a general ability to identify jointly unseen objects,
robust risk control under shift, or superiority over all relevant calibrated baselines.

## Evidence and limits

The repository preserves rejected predictions, corrections and reproducible operands. That
practice should continue. Internal consistency and passing checks are not independent scientific
verification. The research-board probes found that the original matcher could fail its accuracy
gate yet emit an output, and the replay consumer could accept a failed process as replicated.
The isolated research revision repairs both and retains regression tests.

Result O's claim that each confounding arm must individually exceed the E-value is corrected in
its [current document](RESULT_O_SENSITIVITY_EVALUE.md). The historical generator and transcript
remain an exact record of what was printed, including the overinterpretation. Historical numerical
reproduction does not endorse that prose.

## Next scientific choice

Complete one reference-validity study before expanding the model roster: define the opportunity
population independently of detector outputs, compare justified references and temporal nulls,
and independently adjudicate uncertain cases. If a residual physical effect survives, test whether
causally available temporal evidence improves a decision beyond equally calibrated baselines.
If it does not, retain the narrower auditing result and change the thesis.

Gate A remains operator-unaccepted. This research branch is not a release-mode Gate A validation,
a repaired readiness implementation, an independently reviewed safety case or a product runtime.
