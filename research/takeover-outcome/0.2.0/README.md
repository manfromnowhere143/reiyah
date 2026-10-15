# Complete takeover census and outcome timing qualification

Document ID: `reiyah.takeover-outcome`. Version: `0.2.0`.
Lifecycle status: `exploratory`. 15 October 2026.

**All 500 TD2D v2 trial summaries are captured and their five required fields are
qualified for this descriptive audit. Outcome timing is not qualified for a
recovery target or readiness model.** The complete census reproduces the
published task totals and reaction-time means. It still lacks the evidence that
would turn scenario end into a known failure time or common monitored horizon.

This completes the source coverage left open in [0.1.0](../0.1.0/README.md).
The [decision](DECISION.md) keeps modeling unadmitted and specifies the evidence
needed to reopen temporal qualification. Gate A remains operator-unaccepted.

## Complete coverage and comparison

| Observation | Essential-field admission | Original strict-header admission |
| --- | ---: | ---: |
| Captured summaries | 500 | 500 |
| Usable trials | 500 | 499 |
| Unacquired summaries | 0 | 0 |
| Rejected full-header anomaly | 0 | 1 |
| Recorded successes / failures | 320 / 180 | 320 / 179 |
| Within-driver/event cross-outcome pairs | 242 | 242 |
| Failed trial strictly faster | 19 | 19 |
| Successful trial strictly faster | 223 | 223 |
| Equal latency | 0 | 0 |
| Drivers with a faster failed trial | 11 | 11 |

The 19 witnesses contradict deterministic monotone substitution of initiation
latency for recorded outcome on this cohort. They do not make latency useless as
a predictor or show that faster response causes failure. These are dependent
pairs with different secondary tasks and other trial conditions, not 242
independent experiments or a population failure rate. Forty-five drivers have
eligible cross-outcome pairs; all 150 driver/event cells remain in the result.

[Exact results](result.json), [strict-header sensitivity](legacy-result.json)
and [SQL verification](verification.json) retain all witnesses and 193 strata.
The conventional SQL self-join and sorted-list producer use the same complete
observations and exact rational arithmetic. They agree on every pair, witness,
stratum and aggregate. This is a separate arithmetic check within one assisted
investigation, not independent scientific replication or work-saving evidence.

## The source defect remains visible

D11/gaming has 20 cells, including a trailing unnamed workload header. Its first
five headers and values are unique, correctly ordered and aligned. The
[adapter](prepare_records.py) reads only those required fields; it does not
repair or consume the workload suffix. Required-field duplicates, absent values,
unequal row widths, unknown labels and invalid times are rejected. The
[admission ledger](admission.json) preserves the full-header anomaly.

The author's pinned notebook selects named outcome and reaction-time columns.
This supports a task-specific field projection without guessing workload data.
The [protocol](protocol.json) froze that rule before the 339 new summaries were
parsed; the previously captured 161 summaries and five discordant pairs were
already exposed. The original 0.1.0 packet and its integer-to-decimal correction
remain unchanged. This is an exploratory continuation, not a fresh blinded study.

All ten task success counts and mean reaction times exactly match the retained
descriptor's Table 4, with **zero mean difference**, under the five-field
projection. [Reconciliation](source-reconciliation.json) also reports the original
strict contract: gaming has 49 trials and a mean difference of 131/1225 ms;
its other nine tasks match. Agreement with an aggregate table supports source
consistency, not the validity of a physical recovery construct.

## Timing: supported arithmetic, unresolved outcome horizon

For every admitted trial, `event + reaction <= end`. The derived first-action
time is the sum of recorded event onset and reaction latency. It is post-event
information and cannot be used as an available pre-event readiness feature.

| Recorded difference, milliseconds | Minimum | Median | Maximum |
| --- | ---: | ---: | ---: |
| Critical event to scenario end | 2,717 | 5,798 | 23,404 |
| Derived first action to scenario end | 1,735 | 4,788 | 22,015 |

All 500 differences are positive. The [timing report](timing.json) preserves every
row and six event/outcome groups; its per-row quantities also agree with a Decimal
reconstruction. These are timestamp differences, not independently verified
continuous monitoring durations. Neither the minimum nor the median is an
admitted recovery cutoff.

The [source findings](timing-evidence.json), [commit bindings](source-bindings.json)
and [custody](source-custody.json) distinguish what was observed from what remains
unknown:

- The descriptor defines the released millisecond fields and binary outcome.
  The summaries contain no per-trial collision or sidewalk-event timestamp.
- Inspected simulator code maintains system and simulation clocks separately.
  A collision callback records `GameTime`, and criterion JSON recording is
  optional. No release-bound export configuration connects these values to the
  dataset's millisecond fields.
- The pinned T500RS wrapper imports a controller module whose matching path is
  absent from the inspected complete repository tree. The evidence therefore
  does not establish the original first-maneuver threshold or full capture path.
- The full archive directory identifies no simulator recorder log or criterion
  JSON. Original capture configuration, event-monitor termination, censoring and
  a common follow-up definition remain unestablished.

These are limits of the inspected evidence, not findings that the original
experiment was broken or that its labels are wrong. The
[authored counterexample](timing-counterexample.json) illustrates the ambiguity:
identical released fields can coexist with failure before or after first action.
It is not an observed crash. Scenario end must not be silently substituted for
outcome event time; absent failure timing must not be recoded as success.

## Reproduce offline

Python 3.10 or newer, standard library only. These commands reproduce the public
projection without downloading the archive or executing upstream simulator code.
Use a fresh output directory:

```sh
reiyah_study=research/takeover-outcome/0.2.0
reiyah_run=/absolute/path/to/new-run
mkdir "$reiyah_run"
python3 -B "$reiyah_study/analyze.py" --records "$reiyah_study/records.json" \
  --output "$reiyah_run/result.json"
python3 -B "$reiyah_study/verify.py" --records "$reiyah_study/records.json" \
  --result "$reiyah_run/result.json" --output "$reiyah_run/verification.json"
python3 -B "$reiyah_study/timing.py" --records "$reiyah_study/records.json" \
  --output "$reiyah_run/timing.json" --verification "$reiyah_run/timing-verification.json"
python3 -B "$reiyah_study/controls.py" > "$reiyah_run/controls.json"
cmp "$reiyah_run/result.json" "$reiyah_study/result.json"
cmp "$reiyah_run/timing.json" "$reiyah_study/timing.json"
cmp "$reiyah_run/controls.json" "$reiyah_study/controls.json"
```

Use `legacy-records.json` with the same producer/checker for the strict-header
comparison. With retained originals, run `prepare_records.py INPUT_TD2D_ROOT
OUTPUT_RECORDS OUTPUT_ADMISSION`; `verify.py --raw-root INPUT_TD2D_ROOT` also
checks all 500 source hashes and mappings. A public replay without originals
honestly reports zero raw sources checked.

[Thirty-nine controls](controls.json) cover identity, missingness, decimal
ordering, ties, source-field admission and forged timing/model claims. The
retained replay denied network before Python started and denied writes to its
input projection and raw summaries. Nine outputs reproduced byte-for-byte;
523 input files remained unchanged. [Provenance](provenance.json) records exact
scope, runtime and costs. It is not a full system-library attestation.

## Attribution, custody and next dependency

Derived records and source-derived result tables are adapted from TD2D v2 by
Jiwoo Hwang, Woohyeok Choi, Jungmin Lee, Woojoo Kim, Jungwook Rhim and Auk Kim,
under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), from the
[versioned release](https://doi.org/10.5281/zenodo.14185964).
Changes select five fields, map event names, preserve exact decimal strings,
expose header admission and derive the reported comparisons and durations.
This attribution is separate from Reiyah's authored code license. Raw CSVs,
article, notebook, simulator code, eye video and physiological streams are not
redistributed in this packet.

The [descriptor](https://doi.org/10.1038/s41597-025-04781-8) is represented by the
retained author-hosted manuscript with a publication-date placeholder, not an
asserted byte match to the final publisher PDF. Simulator inspection is pinned
to commit `115320f093f40650218f4312381680966ef27528`, supplement inspection to
`221070726063334915f521de90b6263a10abe22c`. The earlier CAPTCHA remains ineligible.

The current capture used 354 direct requests and retained 776,766 response bytes,
including one 404 from an incorrect source-code path. All 339 missing summaries
were obtained; 161 originals were reused by exact digest. Pacing was at least
2.5 seconds between request starts, sequentially. All current response headers
and error bodies are retained. The previous 179 requests, 4,552,481 retained bytes,
DNS failure and HTTP429 remain recorded. Full archive MD5, web transport overhead,
human active effort and billing remain unverified or unknown.

This source census is closed. The next useful dependency is a materially new
capture/export and outcome-monitoring packet that resolves the specified timing
gaps. Check its availability and qualify it before constructing recovery labels
or readiness models. No new modeling, inference, private ingestion, outreach or
Gate A acceptance is authorized by this result.
