# Which measurements actually resolve a decision?

Document: reiyah.measurement-resolution.report, version 0.1.0.
Date: 21 September 2026. Status: exploratory authored mechanism experiment.

The additional-measurement calculation now checks **every feasible response and
the entire remaining signal family**. It then acquires a numeric oracle response,
updates the observations and recomputes complete bounds. This closes the earlier
limitation in which a proposed measurement distinguished only two selected
trajectories. It does not supply physical uncertainty calibration or prove an
advantage over competent conventional analysis.

The frozen nine-case experiment and its separate conventional calculation agree
on all ten continuous response partitions and 19 model/witness stages. Both
perform ten oracle calls. Twenty-five directed controls and ten result mutations
pass. All cases, including uncertainty, unavailable channels and an inconsistent
report, remain in [results](results.json). There are zero physical cases.

## A measurement can distinguish a pair and still leave uncertainty

Consider recorded observations of 6 m at times 0 and 2, a supplied 2 m/s scalar
rate bound, known clock and the authored obligation to stay at least 5 m over
[0,2]. A noiseless query at time 1 has feasible replies [4,8]. The complete
post-query decisions are:

| Reply y | Decision across the entire updated family |
| --- | --- |
| 4 <= y < 5 | Contradicted |
| 5 <= y < 6 | Unresolved |
| 6 <= y <= 8 | Supported |

The actual authored reply 5.5 leaves attainable minimum [4.75,5.5]. A second
query at time 0.5 returns 5.75 and still leaves uncertainty. A third query at
time 1.5 also returns 5.75 and gives [5.125,5.5], supporting the conditional
obligation. Each pre-query partition still had possible unresolved responses:
this actual resolving sequence is not a guarantee that every possible sequence
would resolve. The fixed query order is not claimed optimal.

## Complete retained outcomes

Intervals below bound the attainable minimum in the declared scalar model.
Metres, seconds and the five-metre threshold are authored development choices,
not a calibrated driving requirement. The single reporting fault is disclosed.

| Authored case | Final interval | Evidence result | Calls | Workflow |
| --- | --- | --- | ---: | --- |
| Noiseless point at equality | [5,5] | Supported | 1 | Resolved |
| Noisy point | [4.75,5.25] | Unresolved | 1 | Query opportunities exhausted |
| Midpoint then quarter queries | [5.125,5.5] | Supported | 3 | Resolved |
| Observed violation | [4,4] | Contradicted | 1 | Resolved |
| Common clock needs earlier/later data | [5,6] | Supported | 3 | Resolved |
| Report violates declared error bound | Not applicable | Inconsistent premises | 1 | Inconsistent |
| Unavailable measurement | [4,6] | Unresolved | 0 | Acquisition blocked |
| Unregistered measurement clock | [4,6] | Unresolved | 0 | Acquisition blocked |
| Initially supported | [5,7] | Supported | 0 | Resolved without acquisition |

The common-clock example retains one shared offset across the whole world.
Repeating a recording-time measurement alone does not establish a physical-time
value. Missing or unavailable replies are null, not zero. An inconsistent report
does not become an unsafe-world conclusion by vacuous reasoning.

## Method and comparison

[METHOD.md](METHOD.md) derives exact response thresholds from the lower-envelope
bad-time set and upper-envelope safe-window set. The [conventional checker](response_check.py)
instead projects strict and non-strict two-variable polyhedra, preserving open
and closed endpoints. Agreement concerns the entire feasible response interval,
not a grid of sampled replies. [Lineage](lineage.json) binds the reused envelope
kernel and separate LP witness checker to their unchanged earlier bytes.

The oracle interpolates explicitly authored scalar traces and reports numbers;
neither arm receives stored candidate verdicts. The conventional workflow also
reconstructs replies, interval merges and all post-acquisition models separately.
The arms share strict parsing/custody and one author. This is development evidence,
not blinded evaluation or independent external replication. Empty false-acceptance
and false-refusal lists in [check.json](check.json) refer to these nine cases only.

Active sensing to refine belief and satisfy temporal obligations is established
research. [Fu and Topcu's 2014 paper](https://arxiv.org/abs/1410.0083v1) is retained
privately and reviewed in [SOURCES.md](SOURCES.md), alongside the prior September
2026 review. No novelty, theorem transfer, contemporary superiority or customer
value follows from implementing this specific conditional calculation.

## Reproduction and costs

[PLAN.md](PLAN.md), the authored operands, implementations and source identities
were frozen before allocation execution. Freeze SHA-256:
`3715477e6a9d6b96542b2b58b32f6564ee664a81c62b6fded3d74430132fa97a`.
Full authored [proofs](proofs.json), [baseline](baseline.json),
[controls](controls-pre.json), [mutations](controls-post.json) and
[validation](validation.json) are public. Run in a fresh output directory with
the pinned runtime and exact locally retained sources required by binding.py:

```sh
python -B research/measurement-resolution/0.1.0/run.py \
  --freeze-sha256 3715477e6a9d6b96542b2b58b32f6564ee664a81c62b6fded3d74430132fa97a \
  --sources SOURCE_DIRECTORY --output results.json --proofs proofs.json \
  --timing producer-timing.json
python -B research/measurement-resolution/0.1.0/check.py \
  --freeze-sha256 3715477e6a9d6b96542b2b58b32f6564ee664a81c62b6fded3d74430132fa97a \
  --sources SOURCE_DIRECTORY --results results.json --proofs proofs.json \
  --output check.json --baseline baseline.json --timing reference-timing.json
```

The original isolated commands and complete receipts are in the owned private
record `~/.codex/reports/reiyah/measurement-resolution-2026-09-21-atj4fn36/`.
The source-body identity guard requires the private research PDF and derived text;
it does not make them public dependencies or permit their redistribution.

Nested producer/reference calculation timers were approximately 0.00839/0.01547 s,
with process CPU 0.01421/0.02737 s. Both load all nine oracle records and make ten
calls. These single-run timers are not a controlled speed benchmark, acquisition
saving or complete workflow economics. [Costs](costs.json) separate preparation,
commands, child CPU, storage, source capture and publisher readback cutoffs. Later
owned receipts retain the tail; nested timers are never added twice. Active
effort, charges, energy, peak memory and some tool overhead remain unknown.

Two read-only path mistakes during packaging are retained in [failures](failures.json)
with successful corrections. No scientific execution failed and no frozen byte
was corrected. The injected reporting fault is an experimental result, not a
lost or silently replaced execution. Earlier failed studies remain unchanged.

## Continuing mission

This is a substantive mathematical capability checkpoint. It does not qualify
the physical ViF-GTAD uncertainty contract, rerun its closed nominal question or
complete the continuing mission. The next experiment should bind an obtainable
public measurement to a consequential recorded-data or justified physical
question and measure actual resolution against a competent equal-information
workflow. Keep deterministic assumptions distinct from statistical coverage.
One useful missing physical record would give both navigation references at
common surveyed times and quantify the residual errors applicable to that run.
Daniel need not possess a private team's records or repeat general permission.

All 1,433 reserved images remain closed. Gate A remains operator-unaccepted.
No model, sensor, robot, simulator, inference, training or physical control ran.
The historical controller, perception kernel and six main README diagrams are
preserved. Normal guarded public distribution is publisher integrity only.
