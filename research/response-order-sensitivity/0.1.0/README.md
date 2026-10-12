# Selecting responses by recorded time changes two measures differently

Study ID: `reiyah.response-order-sensitivity`. Version: `0.1.0`.
12 October 2026. Exploratory, finite released-cohort analysis.

**Choosing the three lowest recorded response-time values increases departure
from the full valid-time answer distribution, while improving unique-modal agreement.**
The two measurements answer different questions. Neither establishes physical
truth, better reviewers, less work or a Reiyah advantage.

Across all 28,626 MVT image × assigned-exposure cells, the mean squared
response-distribution distance is **0.113094** for the recorded-time selection
and **0.110682** for the exact expected uniform three-response subset. The
primary difference is **+0.00241244**. The frozen assertion that this selection
is no more departing from the timed-pool distribution is contradicted on this
finite cohort. No practical importance threshold or population significance
claim was specified.

At the same time, a unique selected mode agrees with the unique full-pool mode
in **59.89%** of cells, compared with **58.33%** under the uniform expectation.
The full valid-time answer distribution is the calculation's reference, not truth:
selecting away mistaken answers could increase distribution departure and
improve correctness. We did not measure that physical or reference-label
correctness endpoint.

## What was fixed before results

The [decision packet](../../../docs/research-decisions/observation-order-2026-10-12.md)
selects this narrow observation question without reopening the stopped product
expansion or older closed studies. The [protocol](protocol.json) froze at
14:28:05 UTC after methods and a structure-only audit. The
[interpretation clarification](pre-execution-clarification.json) preserves the
original protocol bytes and narrows two phrases before execution. Both
[implementations](code-freeze.json) froze at 14:33:08 UTC, before the new comparison.
These are local chronological records, not external preregistration or blinded
validation. The authors' published time–correctness association was already known.

Source: David Mayo, Jesse Cummings, Xinyu Lin, Dan Gutfreund, Boris Katz and
Andrei Barbu, *How hard are computer vision datasets? Calibrating dataset
difficulty to viewing time*, NeurIPS 2023. Read the
[official paper](https://objectnet.dev/mvt/how_hard_are_computer_vision_datasets_Calibrating_dataset_difficulty_to_viewing_time_neurips2023.pdf),
[release](https://objectnet.dev/mvt/download.html),
[version 1.0 datacard](https://objectnet.dev/mvt/datacard/index.html) and retained
[source descriptors](../../../evidence/observation-feasibility-2026-10-12.json).
The annotation notices specify CC BY-SA without an exact version. Raw responses,
worker identifiers, source images and paper payloads remain outside public Git.
The analysis code and conclusions are ours; comprehensive commercial-use clearance
is not asserted. Images were not acquired.

The [source audit](source-qualification.json) verifies 200,382 rows, 4,771 images,
2,647 recorded worker IDs and exactly seven distinct recorded IDs in every
image × exposure cell. One recorded time is negative. It stays explicit in
coverage: 200,381 positive finite times, 28,625 seven-response timed pools and
one six-response timed pool. All 28,626 cells are analyzed; none is dropped.
Recorded IDs do not authenticate humans or establish independence.

The field is used ordinally. A common change of units preserves ordering, but
worker/device-specific offsets or scales may not. Exact clock events, calibration
and response-time units are unverified. “Lowest recorded values” must not become
“fastest cognition.” Assigned exposure levels are also not verified physical
screen exposure for each online participant.

## Exact comparison

Within each cell, select k=3 records by positive recorded time, then original
row position for time ties. Let p be the categorical distribution of all valid-time
records in that cell and q the selected distribution. Use D=Σ(q−p)², with exact
fractions. The same timed pool supplies both arms and the reference.

For uniform selection without replacement from n records:

`E[D] = (n − 3) / (3(n − 1)) × (1 − Σ p²)`.

Both implementations enumerate all 35 subsets in a seven-response pool and all 20
in the six-response pool: **1,001,895 subset evaluations per implementation**.
Enumeration matches the finite-population formula exactly. Randomness belongs to
the declared selection of fixed records; no iid-worker assumption is required.

All cells receive equal weight. The six declared exposure strata are:

| Assigned exposure | Cells | Selected mean D | Uniform expected D | Difference |
| --- | ---: | ---: | ---: | ---: |
| 17ms | 4,771 | 0.182740 | 0.175881 | +0.00685928 |
| 50ms | 4,771 | 0.138198 | 0.134115 | +0.00408268 |
| 100ms | 4,771 | 0.118783 | 0.117752 | +0.00103041 |
| 150ms | 4,771 | 0.093568 | 0.092490 | +0.00107794 |
| 250ms | 4,771 | 0.098108 | 0.096669 | +0.00143954 |
| 10,000ms | 4,771 | 0.047169 | 0.047184 | −0.00001521 |
| **All** | **28,626** | **0.113094** | **0.110682** | **+0.00241244** |

Five exposure aggregates are positive; the 10,000ms aggregate is slightly negative.
Both source-origin aggregates are positive: `objectnet="False"` +0.00232224
and `objectnet="True"` +0.00250043. Every exposure × origin result, including the
mixed signs at 10,000ms, is retained in [result.json](result.json). No favorable
stratum is selected after seeing outcomes.

Nine cells have a time tie at the selection boundary. Across all choices allowed
by those ties, the aggregate difference ranges from **+0.00239580 to +0.00242353**.
This is a finite tie-choice sensitivity interval, not a confidence interval.
Separately, excluding the one invalid timing value changes that cell's response
reference by squared distance 11/882; the equal-cell mean effect is 11/25,248,132.
This missing-timing selection is not folded into the primary contrast.

## Modal outcomes remain separate

“Agree” requires unique modes in both selected and full timed pools, with the
same category. “Disagree” requires two different unique modes. A tie in either
pool remains “unresolved.” Denominators include every analyzed cell.

| Outcome | Recorded-time selection | Uniform expected count | Selection rate | Uniform expected rate |
| --- | ---: | ---: | ---: | ---: |
| Agree | 17,143 | 16,697.657 | 59.886% | 58.330% |
| Disagree | 351 | 402.914 | 1.226% | 1.408% |
| Unresolved | 11,132 | 11,525.429 | 38.888% | 40.262% |

Uniform counts are expectations, not an observed random run or fractional people.
Improved modal agreement and increased distribution departure can coexist. Which
one matters depends on the decision's evidence requirement; neither can replace
an owner-defined correctness obligation.

## Reproduction and checks

Standard-library Python only. [reproduce.py](reproduce.py) and
[checker.py](checker.py) independently parse the exact compressed source member;
the checker imports no producer code. They validate the member and decompressed
CSV SHA-256, CRC, length, header, roster, every per-cell result and all aggregates.
The 142,812,572-byte CSV is streamed and is not written in full.

After reviewing the source terms, retain only this annotation member from the
release, not its image archive. The exact HTTP range is
`bytes=206653537-212866900`, ETag `"cb01966-5fe3e1c2d233b"`, from the archive URL
in [protocol.json](protocol.json). The 6,213,364-byte response must hash to
`c4da8a042a1325e573ed932f6db5a3fc2a24b11b51854dcc8b3d7a69e905554c`.
A changed or whole-archive response is rejected by the analysis scripts.

From the repository root, with `MVT_MEMBER` naming that private file and
`MVT_OUTPUT` a new private directory:

```sh
sandbox-exec -p '(version 1)(allow default)(deny network*)' \
  python3 -B research/response-order-sensitivity/0.1.0/reproduce.py \
  --source "$MVT_MEMBER" --output "$MVT_OUTPUT"
sandbox-exec -p '(version 1)(allow default)(deny network*)' \
  python3 -B research/response-order-sensitivity/0.1.0/checker.py \
  --source "$MVT_MEMBER" --output "$MVT_OUTPUT"
python3 -B research/response-order-sensitivity/0.1.0/tests.py
```

`sandbox-exec` is the tested macOS network-denial launcher; another operating
system needs an equivalent policy before runtime. Enforce the 120second process
wall cap externally for both scripts. The output trace remains private.

Two producer runs match exact result and trace bytes. 14 authored tests pass,
including 252 cross-implementation cases. Three
[post-execution rejection controls](negative_controls.py) reject changed source
bytes in both readers and a changed aggregate. See [verification.json](verification.json),
[execution.json](execution.json) and [provenance.json](provenance.json).
All scientific runs start with network denied. This is one assisted investigation,
not independent scientific replication. No Gate A acceptance follows.

## Engineering consequence and stop

Preserve selection rule, displayed task, timing validity, response population,
aggregation and unresolved states in any proposed observation-channel identity.
Do not treat a retained response count as a complete-work estimate. Selecting by
observed completion values is retrospective and generally requires acquiring
all those answers first; it is not an online first-arrival policy.

This study is complete. Do not tune k, change the metric, enlarge the cohort or
repeat the same source hunt to obtain a more favorable headline. No production
adapter is admitted. The next value test still needs a consequential paired
decision, a separately qualified observation procedure, and a frozen comparison
with complete work against a competent conventional analyst.
