# Shared training and transfer: the next discriminating experiment

Document ID: `reiyah.training-overlap-next-experiment.2026-09-07`

Version: `0.1.0`

Lifecycle status: `proposed`

The preceding metadata census establishes a feasible log partition, not a
training intervention. Moving to a second dataset and disjoint training at
the same time would confound two changes. Keep the shared-training contrast
within a dataset, then replicate that contrast on a second dataset.

## Four fits provide the within-dataset contrast

For fixed camera and lidar architectures, train each architecture on training
partition U and on disjoint partition V. The four resulting channels permit
four pairings on the exact same test opportunities: camera-U/lidar-U,
camera-V/lidar-V, camera-U/lidar-V and camera-V/lidar-U. Every trained channel
appears in a shared-data pair and a disjoint-data pair. No test item, failed
producer, empty output, invalid sensor or unresolved reference may be dropped
because its pair is inconvenient.

Let aU, aV, bU, bV be their reference-relative binary miss indicators. A useful
paired contrast in joint miss probability is

```text
D_joint = (E[aU*bU] + E[aV*bV] - E[aU*bV] - E[aV*bU]) / 2
        = E[(aU-aV)*(bU-bV)] / 2.
```

This is an algebraic identity, not an observed result or an identified causal
effect. Shared pairing can change joint risk simply because marginal error
rates differ. Its independent-product contrast is

```text
D_marginal = (E[aU]-E[aV]) * (E[bU]-E[bV]) / 2
D_covariance = D_joint - D_marginal
             = Cov(aU-aV, bU-bV) / 2.
```

Retain all four marginal rates, joint rates and defined coincidence ratios,
alongside these two contrasts. Do not interpret an average of coefficients
as a common marginal-matched risk difference. Complete-case values require
an explicit coverage denominator and separate unknown bounds. Averaging
these paired test rows cannot supply training-randomization uncertainty.

## Resolve the actual training comparison before execution

The three existing seed proposals remain unchanged. They balance log counts
within location, not sample budgets. Before selecting a candidate protocol,
retain exact sensor-file availability, training and pretraining lineage,
configuration and weight identities, a common training-step budget within
each architecture, and independent calibration logs. Split identities must
be fixed without reference to detector failures. All three partitions, rather
than whichever later produces the strongest coefficient, belong in the
intended robustness check. Initialization seeds and the uncertainty procedure
over training repetitions remain to be specified prospectively.

A budget-matched subset is a new metadata-only selection that must preserve
whole collection groups and record unused examples. Equal epochs on unequal
partitions do not equalize optimization work. A recall-matched secondary
comparison needs training/calibration-only thresholds with a fixed rule for
unattainable recall. Test labels cannot choose operating thresholds, strata
or the test population. Common pretraining must be disclosed; disjoint
fine-tuning alone does not establish independent training histories.

The primary endpoint, pairing contrast, minimum useful effect, complete
opportunity population and interval method must be frozen before any new
fits. A passing synthetic test or four completed training processes does not
fill those presently unresolved design choices.

## Second-dataset and current-method preflight

The [source record](../evidence/predictive-monitor/research-source-ledger-0.1.0.json)
binds privately retained public documentation retrieved on 2026-09-07. It
does not admit a dataset payload or constitute permission to redistribute one.

The official [perception documentation](https://waymo.com/intl/fil/open/data/perception/)
describes separate camera and lidar labels, correspondence and no-label zones.
These offer useful audits of label visibility and common opportunities;
separate annotation channels do not by themselves establish independent
physical truth. The [download history](https://waymo.com/intl/es/open/download/)
identifies modular perception 2.0.1 and perception 1.4.3, dated March 2024.
The [March 2025 terms](https://waymo.com/open/terms/) state non-commercial
use and restrict dataset/model distribution and production use. No account
registration, terms acceptance, protected payload or matched pair of detector
predictions was obtained. Exact compatible predictions and training provenance
remain unresolved; this is an access and design preflight, not a replication.

[Knowledge-Guided Failure Prediction v1](https://arxiv.org/abs/2603.25499v1),
submitted 2026-03-26, compares internal detector features with visual-foundation
embeddings to predict detector failures. It is a relevant future comparator
for richer observation channels. Its image-level selective prediction question
differs from paired future joint-miss counts; the published result does not
establish Reiyah's performance or novelty. Comparison would require the same
target, inputs, split and alert costs. The original private source set also
retains the 2016 introspective-perception predecessor and exact library docs.

The existing [standards crosswalk](STANDARDS_CROSSWALK.md) remains a mapping
of retained metadata and gaps. A reference-relative detector benchmark cannot
be represented as a standards assessment, even if a regulation motivates the
question. The [research-board review](RESEARCH_BOARD_2026-09-07.md) and
[RSS transfer correction](RSS_TRANSFER_AND_RARE_EVENT_LIMITS_2026-09-07.md)
remain necessary reading before making an external safety inference.

The next bounded action is a sensor-file and model-provenance inventory that
can turn this design into an executable, budgeted protocol. Independent human
reference adjudication remains the separate highest-value scientific need.
No further tuning of the stopped spatial-summary attempt is planned.
