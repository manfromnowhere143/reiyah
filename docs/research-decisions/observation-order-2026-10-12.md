# Does selecting responses by recorded time preserve their evidence?

Document ID: `reiyah.observation-order-decision`. Version: `0.1.0`.
12 October 2026. Exploratory decision packet, written before the new contrast.

**Run one finite-record observation test. Keep product expansion stopped.**
The important gap is still a consequential paired engineering decision with a
qualified review process and complete work records. Reiyah already contains
human-response studies; the missing piece is not simply more human data.
Neither the exact-choice solver nor the research-intake helper fills that gap.

A new public source permits a narrower useful step: determine whether choosing
three responses by lower recorded response-time values changes the observed
answer distribution more than equal-count uniform selection. This qualifies
one assumption a future timing-aware adapter might otherwise inherit. Current
Reiyah already permits dependent observations; this is not a claimed engine bug.

## Evidence and alternatives

| Alternative | Evidence and decision |
| --- | --- |
| Build another selector or autonomous research platform | Does not supply a decision owner, qualified observations or complete work. Defer. |
| Reopen the existing detector, Cityscapes, WOD, EgoDyn or small AUGRC studies | No new packet changes their closed status. Do not repeat. |
| Use CIFAR-10H trial responses | Pinned release includes trial response times but declares CC BY-NC-SA4.0. Intended commercial reuse is unresolved; no raw ingestion. |
| Use CIFAR-N times | Pinned release declares CC BY-NC4.0 and records annotation-batch time. Dividing that time invents per-trial costs. No raw ingestion. |
| Use new 2026 cognitive-labeling studies | Relevant to how elicitation, prevalence and calibration change judgments; inspected OSF metadata does not complete the present source/rights/timing contract. Do not invent missing fields. |
| MVT released response records | Source describes individual category answers and recorded choice times. Exact annotation member is acquired without images; structure audit finds 200,382 rows, 28,626 seven-response cells, six exposure levels and one negative time. Admit only ordinal selection of the released field. |

The [source ledger](../../evidence/observation-feasibility-2026-10-12.json)
binds versions, access and failures. Current primary research includes
[Epping et al., arXiv:2603.11511v1](https://arxiv.org/abs/2603.11511v1)
and the [September 2026 cognitive-labeling paper](https://doi.org/10.3758/s13428-026-03160-4).
Their recruitment, prevalence and elicitation procedures matter; publication
recency does not establish transfer to Reiyah's review process.

[Lim et al., arXiv:2412.00260v1](https://arxiv.org/html/2412.00260v1)
already study viewing limits and retrospective response times. Recorded time is
not the intervention of imposing a deadline. The
[MVT paper](https://objectnet.dev/mvt/how_hard_are_computer_vision_datasets_Calibrating_dataset_difficulty_to_viewing_time_neurips2023.pdf)
already reports time–correctness association. We do not claim that phenomenon
as new. The [crossed-effects literature](https://artowen.su.domains/reports/pbs2.pdf)
also cautions against treating every worker–image response as independent.
This finite-cohort test needs neither an iid assumption nor a population interval.

## Milestone, falsifier and acceptance

The [frozen protocol](../../research/response-order-sensitivity/0.1.0/protocol.json)
fixes k=3 and groups by image and assigned exposure. Both arms use the identical
positive finite recorded-time pool. The one negative value remains in the source
and missing-timing accounting; it is not converted to zero or ranked first.
Compare squared distribution distance to the full timed pool. Enumerate every
three-response subset, and independently check its expected distance against
the finite-population formula. Keep modal ties unresolved and quantify boundary
time-tie sensitivity. Report all exposure and dataset strata.

A positive equal-cell mean difference falsifies the narrow assertion that the
recorded-time selection is no more distorting on this release. A nonpositive
result does not establish independence. No practical tolerance was supplied,
so neither sign alone demonstrates engineering value. The full recorded answer
distribution is a reference for this calculation, not physical truth. Greater
departure could remove mistaken answers and improve correctness. Neither sign
therefore establishes observation quality or review harm. See the
[pre-execution clarification](../../research/response-order-sensitivity/0.1.0/pre-execution-clarification.json);
the frozen estimand remains unchanged.

Acceptance requires exact source membership, two identical producer executions,
a separately authored raw-input arithmetic checker, declared coverage, and
negative controls rejecting changed source bytes and altered results. These
checks are within one investigation, not independent scientific replication.
The protocol is locally frozen after source and structural exposure, before
new outcome inspection; it is exploratory, not blinded or preregistered.

## Resources and stopping

CPU and standard library only; no new dependency, inference campaign, paid
service, outreach or sibling change. Owner wall cap 60minutes; each analysis
run 120seconds; 33direct capture attempts used for this review, within 40;
retained-source cap48MiB and private-owner cap128MiB excluding the candidate.
The 142.8MB CSV is streamed from its 6.2MB compressed member, never written whole.
Historical engineering effort is unknown and is not reset by this study.

Stop after this fixed comparison and checks, regardless of sign. No k sweep,
metric switch or wider benchmark hunt. Recorded-time ranking is retrospective:
one generally learns these times only after acquiring the responses. It proves
no online acquisition strategy, saved labor, causal deadline effect, physical
truth, automotive transfer, safety or scientific superiority.

The next value milestone remains one owner-defined paired decision, with the
observation procedure qualified separately and correctness plus complete-work
measurement frozen before fresh outcomes. A favorable descriptive result does
not authorize broader product expansion.
