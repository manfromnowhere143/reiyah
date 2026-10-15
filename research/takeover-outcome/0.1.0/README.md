# Takeover response and recorded outcome

Document ID: `reiyah.takeover-outcome`. Version: `0.1.0`.
Lifecycle status: `exploratory`. 15 October 2026.

**Five recorded pairs contain a faster failed takeover and a slower successful
takeover by the same driver in the same critical-event category.** They come from
three drivers. Reaction time cannot serve as a deterministic substitute for the
recorded outcome on these observations. It may still be informative; this audit
does not estimate a causal effect or evaluate a predictive model.

The planned 500-trial audit is **incomplete**. Acquisition stopped after a DNS
failure and one bounded continuation that received HTTP429. All missing
opportunities remain in the released [record projection](records.json).
There was no replacement sample or attempt to evade the rate limit.

| Coverage or comparison | Result |
| --- | ---: |
| Expected trials, 50 drivers × 10 conditions | 500 |
| Captured and source-bound summaries | 161 |
| Usable under the corrected numeric contract | 160 |
| Rejected for an inconsistent header | 1 |
| Not acquired | 339 |
| Comparable success/failure pairs within driver and event type | 70 |
| Failed trial strictly faster | 5 |
| Successful trial strictly faster | 65 |
| Equal recorded latency | 0 |

These are dependent pairs from an incomplete, filename-ordered capture. They are
not 70 independent experiments, a representative sample, a failure probability
or an estimate of an intervention's effect. Different tasks and other trial
conditions remain different even when driver and event category match.

## The observation being qualified

[TD2D v2](https://zenodo.org/records/14185964), by Jiwoo Hwang, Woohyeok Choi,
Jungmin Lee, Woojoo Kim, Jungwook Rhim and Auk Kim, supplies simulator trial
summaries. The [2025 descriptor](https://doi.org/10.1038/s41597-025-04781-8)
defines reaction time from critical-event onset to the first maneuver. Its
outcome records collision or sidewalk failure separately. These are different
observations. A first maneuver occurs after event onset and is unavailable as
a pre-event readiness feature.

The retained author-hosted descriptor PDF has a publication-date placeholder;
it is not asserted to be byte-identical to the final publisher article. The
Zenodo record is v2, published 20 November 2024, updated 2 April 2025. The author
notebook and inspected simulator files inform source interpretation; no pinned
capture-runtime linkage or replay of the original simulator is established.
A purported PMC capture was a CAPTCHA page and is evidence-ineligible.

For the 160 usable records, reported event-to-end windows range from 2.896 to
23.404 seconds, and time after the first maneuver ranges from 1.735 to 22.015
seconds. Those are differences between recorded fields. The summaries do not
independently verify collision detection, event timing, outcome censoring or a
common sustained-recovery horizon. They do not measure latent belief or establish
recoverability in road driving.

## Exact contrast and witnesses

For each driver and event category, compare every failure to every success.
Count `failure_latency < success_latency`, its reverse, and equality separately.
The [producer](analyze.py) counts with sorted lists and exact rational arithmetic.
The [conventional checker](verify.py) performs a SQL self-join using exact rational
ordering and checks every witness, all 193 strata and all summary values. It
imports no producer code. Both use the same observations and corrections.

| Driver | Event category | Failed task / latency | Successful task / latency |
| --- | --- | --- | --- |
| D05 | Leading vehicle stop | baseline / 1,325 ms | 0-back / 1,426 ms |
| D05 | Leading vehicle stop | baseline / 1,325 ms | 2-back / 1,336 ms |
| D06 | Pedestrian from right | audiobook listening / 652 ms | gaming / 670 ms |
| D11 | Pedestrian from right | baseline / 671 ms | 2back / 768 ms |
| D11 | Pedestrian from right | baseline / 671 ms | ebook reading / 817 ms |

The full [result](result.json) includes every driver/event cell, all ten task
summaries and all thirty task/event cells, including empty cells. Empty observed
cells have unavailable means, not zero risk. Missing trials have unknown event
assignment and outcome. The task means and success ratios cannot be reconciled
against the descriptor's complete Table 4 while 339 trials are absent.

## Corrections and verification

The [frozen protocol](protocol.json) preceded trial outcome inspection. The
[field mapping](field-mapping.json) records release spellings that differ from
the descriptor. One row was viewed before that mapping; this is disclosed.
The initial integer-time contract rejected two fractional-millisecond source
values. The [numeric correction](numeric-correction.json) retains those values
exactly, without rounding, and preserves the initial analysis in private custody.
Usable rows changed from 158 to 160; concordant pairs from 63 to 65. The five
counterexamples did not change. Neither pass is a fresh or preregistered study.

D11/gaming has a trailing unnamed header with a populated value. The adapter
refuses that record instead of guessing the intended column alignment. This is
an input-contract rejection, not a determination that its recorded outcome is
wrong. Missing and rejected records stay explicit.

[Verification](verification.json) checks the 161 raw source hashes and mappings,
70 pair rows, five witnesses and all strata. [Twenty-eight controls](controls.json)
check missingness, duplicate identities, invalid times, sub-binary64 distinctions,
ties, omitted witnesses and false claims. This is separately authored arithmetic
within one assisted investigation, not independent scientific replication.

## Reproduce offline

Python 3.10 or newer, standard library only. From the repository root, use a new
output directory. These commands reproduce the published projection; they do
not redownload missing trials or authenticate the original simulator.

```sh
reiyah_study=research/takeover-outcome/0.1.0
reiyah_run=/absolute/path/to/new-run
mkdir "$reiyah_run"
python3 -B "$reiyah_study/analyze.py" --records "$reiyah_study/records.json" \
  --output "$reiyah_run/result.json"
python3 -B "$reiyah_study/verify.py" --records "$reiyah_study/records.json" \
  --result "$reiyah_run/result.json" --output "$reiyah_run/verification.json"
python3 -B "$reiyah_study/controls.py" > "$reiyah_run/controls.json"
cmp "$reiyah_run/result.json" "$reiyah_study/result.json"
cmp "$reiyah_run/controls.json" "$reiyah_study/controls.json"
```

With the retained original summaries, `prepare_records.py INPUT_TD2D_ROOT OUTPUT`
rebuilds the projection, and `verify.py --raw-root INPUT_TD2D_ROOT` additionally
checks source mappings. Without that argument the checker reports zero raw
sources checked. The retained run denied network access before Python started;
[provenance](provenance.json) records runtime and execution scope.

## Rights, costs and next dependency

The derived data in `records.json`, source-derived result tables and witness
records are adapted from TD2D under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
Credit the six authors and the [versioned source](https://doi.org/10.5281/zenodo.14185964).
Changes: select essential fields, map documented names, preserve exact numeric
strings, add explicit unavailable states and calculate the described aggregates.
This data attribution is separate from Reiyah's authored code license. No paper,
upstream code, physiological streams, eye video or raw archive is redistributed.

[Source custody](source-custody.json) records 179 direct requests and 4,552,481
retained response bytes, including both failures and one duplicate member fetch.
The archive's full MD5 was not checked. Captured members passed exact range,
local header, size, CRC and SHA256 checks. Human work and provider billing remain
unknown; no complete-work advantage is claimed.

This acquisition owner is closed. A future continuation must respect the server's
rate limit, reuse exact captured bytes, and use a new bounded plan for the 339
missing summaries. Resolve the malformed row through source evidence before
calling the cohort complete. Completing this descriptive census would still not
supply outcome timestamps or qualify a shared recovery horizon. That observation
qualification is the dependency for a recovery benchmark, ahead of predictive
training or causal policy estimation. The prior microscopy cohort remains closed.
Gate A remains operator-unaccepted.
