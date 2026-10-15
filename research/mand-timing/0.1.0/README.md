# Qualify a recorded takeover timeline before defining recovery

Document ID: `reiyah.mand-timing`. Version: `0.1.0`.
Lifecycle status: `exploratory`. 15 October 2026.

**The selected manD vehicle and environment files share an exact recorded time
axis. Their event labels do not establish a recovery outcome.** All 134,373 rows
in each file have identical time values, on a grid of 1/256 source-time units.
Two takeover-request episodes align between the scenario-event and system-message
channels. The inspected scenario contains no accident code, so it supplies no
positive check of accident timing. Readiness modeling remains unadmitted, and
Gate A remains operator-unaccepted.

This is a new bounded source qualification after the closed
[TD2D census](../../takeover-outcome/0.2.0/README.md) and
[simulator-history check](../../takeover-source-lineage/0.1.0/README.md).
Those results and all exposed comparisons remain unchanged. The question here
concerns the observation channel, not a new model, causal effect or road-safety claim.

## The selected records

The source is **manD 1.0, Harvard Dataverse release 2.0**, DOI
[10.7910/DVN/SG9TMD](https://doi.org/10.7910/DVN/SG9TMD), by Khazar Dargahi Nobari
and Torsten Bertram, under CC BY 4.0. The release is dated 24 January 2024; the
[primary descriptor](https://www.nature.com/articles/s41597-024-03137-y) was published
30 March 2024. Dataset title and repository release version are distinct identifiers.
See [attribution and terms](SOURCE_LICENSE.md) and [custody](source-custody.json).

The coverage workbook provides 300 participant/scenario slots, including one
familiarization slot per participant. It marks both vehicle and environment data
available in 235 slots: 50 familiarization, 29 no-emotion, 41 anger, 39 surprise,
38 sadness and 38 fear. These are metadata slots, not 235 verified complete trials;
a familiarization slot can cover more than one drive. The scenario-order sheet
also uses font color to distinguish driven from undriven scenarios. The reader
preserves that distinction rather than treating every listed name as a recording.
[Coverage and cell references](coverage.json) retain the complete scoped projection.

Before opening trial contents, the [protocol](protocol.json) selected the lowest
participant ID and then the first ordered driven scenario with both channels
available: **P1, anger**. The scenario name is an experimental condition, not a
measured emotional state. Selection used neither outcomes nor archive size.
Availability did not prequalify completeness. No replacement scenario was allowed.

The 681,745,151-byte P1 archive matches the release's advertised MD5. Its selected
inner `Anger.7z` is 224,555,377 bytes. Only the two permitted state text files were
extracted: 40,024,788 bytes of environment data and 16,169,660 bytes of vehicle data.
The published description calls them `EnvironmentState.txt` and `VehicleState.txt`;
the release instead uses `Environment.txt` and `Vehicle.txt` inside the corresponding
state directories. [The field map](field-map.json) binds those exact files and headers.
No driver media, physiology or activity streams were written as extracted files
or analyzed. Archive parsing may decompress unselected solid blocks internally;
that internal byte work was not instrumented.

## What the clock and events establish

The time fields range from 0 to 524.890625, with every adjacent difference exactly
0.00390625. Both files have the same number of rows, identical time tokens and
identical numeric coordinates. This establishes alignment of the supplied records.
The dictionary documents native acquisition at 20 Hz and delivery at 256 Hz, but
its time-unit cells and the released `time` headers do not name a unit. The grid
is consistent with the documented delivery rate. Physical seconds, absolute origin,
sensor/annotation latency and an error bound are not independently established.
Upsampling does not establish finer native precision.

| Recorded observation | First request | Second request |
| --- | ---: | ---: |
| Request starts, source-time coordinate | 253.375 | 465.5234375 |
| First following non-request record | 254.42578125 | 467.5234375 |
| First subsequent manual-mode record | 254.4765625 | 468.625 |
| Request to first manual-mode record, source-time difference | 1.1015625 | 3.1015625 |
| Request to last recorded row, source-time difference | 271.515625 | 59.3671875 |

These are exact recorded differences, not driver first-action latency or recovery
time. The request marker ends before the first manual-mode record in both episodes.
Intermediate automation states remain explicit. Shared request markers may derive
from the same simulation or annotation process; agreement is not independent event
confirmation. [The result](result.json) includes every categorical run and boundary.

The end-of-ride parking message starts at 495.57421875; recording continues for
another 29.31640625 source-time units. Its final segment has no observed next-record
boundary. A message onset and file termination therefore cannot be interchanged.
Neither establishes a common monitored recovery horizon or explains censoring.
The descriptor describes environment code 6 as an ego-vehicle accident; vehicle
message 13 is a separate accident-detected prompt. Neither appears in these records.
That absence is not a successful-recovery label or evidence about detector sensitivity.

The first 33 rows have missing vehicle measurements and automation state, while
the event/message columns are already populated. Missing automation is not manual
mode. Every field's missing, nonfinite, invalid and finite-value counts are reported;
source-specific unavailable-distance sentinel 99000 remains explicit. No gaps were
imputed and no categorical values were rounded.

## Verification and limits

[The Decimal auditor](audit.py) checks stored arithmetic, all field states and all
categorical runs. A [separate Fraction/SQLite calculation](verify.py) checks all
268,746 source rows, 134,373 aligned row pairs, 57 field summaries, 53 categorical
runs, both request onsets and all 600 required coverage cells. This is a calculation
and integrity check within one investigation, not independent scientific replication.

[18 timing controls](controls.json) cover missing versus zero, nonfinite and invalid
values, fractional/out-of-range codes, malformed records, clock order/alignment and
unobserved endpoints. [Seven coverage controls](coverage_controls.json) reject
header, identity, availability, color-legend and cached-total corruption for their
specified reasons. Network-denied execution with write-denied input copies
reproduces the three scientific outputs and both control reports byte for byte.
No historical empirical or Gate A release replay is counted as new evidence.

The inspected [upstream extraction source](extraction-source-review.json) expands
all streams and deletes archives, including after a caught extraction error. It
was read but not imported or executed. System `bsdtar` inspected/extracted exact
members under network/write restrictions, while a parent process bounded output
bytes and elapsed time. A full inner listing hit its 2 MiB output cap because of
media filenames. That incomplete listing and a failed descriptor-name lookup are
retained. Narrowing the listing to the two authorized directories resolved the
release names without increasing limits or reacquiring data. No full inner
inventory claim is made.

## Reproduce on retained or separately acquired eligible files

Use Python 3.10 or newer, a fresh output directory and the original coverage
workbook plus the two selected state files. Do not run the upstream extractor.
Original source payload is retained privately; the public packet includes authored
code and attributed derived metadata/results, not the compressed archives or raw
streams. The following calculations are offline:

```sh
reiyah_study=research/mand-timing/0.1.0
reiyah_sources=/absolute/path/to/qualified-inputs
reiyah_run=/absolute/path/to/new-run
mkdir "$reiyah_run"
python3 -B "$reiyah_study/coverage.py" --workbook "$reiyah_sources/AvailableData.xlsx" --output "$reiyah_run/coverage.json"
python3 -B "$reiyah_study/audit.py" --environment "$reiyah_sources/Environment.txt" --vehicle "$reiyah_sources/Vehicle.txt" --output "$reiyah_run/result.json"
python3 -B "$reiyah_study/verify.py" --environment "$reiyah_sources/Environment.txt" --vehicle "$reiyah_sources/Vehicle.txt" --workbook "$reiyah_sources/AvailableData.xlsx" --coverage "$reiyah_run/coverage.json" --result "$reiyah_run/result.json" --output "$reiyah_run/verification.json"
python3 -B "$reiyah_study/coverage_controls.py" --workbook "$reiyah_sources/AvailableData.xlsx" > "$reiyah_run/coverage_controls.json"
python3 -B "$reiyah_study/controls.py" > "$reiyah_run/controls.json"
```

[The decision](DECISION.md) admits only the demonstrated recorded-axis findings.
A recovery endpoint still needs a release-linked accident-detection/annotation
rule, physical clock interpretation, a positive accident check and termination/
censoring evidence. Preserve this exposed scenario; do not expand it into a
readiness benchmark or silently treat the absent accident code as success.
