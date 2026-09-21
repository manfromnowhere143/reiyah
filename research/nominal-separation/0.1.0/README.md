# A checked nominal separation counterexample

Document: reiyah.nominal-separation.report, version 0.1.0. Status: exploratory.
21 September 2026. One already exposed ViF-GTAD encounter; development evidence.

**Nondecreasing navigation-reference separation is not a valid premise
for this declared reconstruction.** Over 25.039 seconds, distance grows from
151.730 m to 307.317 m overall, but the largest local reversal is **0.026854 m**,
about 2.7 cm. This small nominal reversal does not refute the authors' physical
scenario description or establish a driving, sensor or clearance failure.

The useful adapter decision is to preserve the observed reversal and its scale,
rather than assume exact monotonicity or silently repair the trace. The
[frozen plan](PLAN.md) defines that decision before new joint geometry. The
[method](METHOD.md) states reference points, clock labels, spherical projection,
affine interpolation and exact arithmetic. The [source record](SOURCES.md)
distinguishes published descriptions from this explicit interpretation.

| Complete nominal calculation | Result |
| --- | --- |
| Input records loaded by each arm | 7,761 ego; 4,437 target |
| Prior clock constraints independently reproduced | 2,504 |
| Common support | GPS-label 09:01:29.790 to 09:01:54.829 on 25 June 2020 |
| Continuous intervals checked | 5,007 |
| Nondecreasing / decreasing / interior reversal / constant | 4,652 / 355 / 0 / 0 |
| First counterexample | Interval 4,555, zero-based; 22.779 s after common start |
| Maximum earlier-to-later decrease | [0.026853869291, 0.026853869293] m |
| Maximum-decrease witness | Peak at 22.779 s, minimum at 25.039 s |
| Minimum uniform scalar repair admitting a nondecreasing trace | About 0.013427 m, or 1.34 cm |
| Physical maneuver, clearance, synchronization and error bounds | Unresolved; zero physical cases |

The fine decimal enclosure certifies arithmetic for the model; it says nothing
about picometre measurement accuracy. The scalar repair bound is the standard
L-infinity monotone-feasibility quantity derived in METHOD.md. It is not an
estimated sensor error and does not prove physical realizability of a repair.

The 1,933 target timestamps before ego support remain explicit. There are 5,257
ego timestamps after target support. To interpolate the common boundaries, the
calculation uses target row 1,932 and ego row 2,504 as brackets: 2,505 records
from each actor contribute, even though only 2,504 timestamps per actor lie
within the common horizon. No observation is extrapolated. No out-of-support
timestamp is relabeled as an in-support measurement.

## Verification and comparison

The union-knot Reiyah calculation and a separately implemented conventional
segment-pair calculation agree on every interval, rational coefficient,
extremum, source index, numerical enclosure and result. Each parses clocks and
compiles coordinates from the bound source bytes. Both share the declared model,
MAT container decoder, numerical libraries and this session's author. This is
implementation cross-checking, not independent authorship or external replication.

Both could reject after 4,556 logical interval reveals in chronological order;
both actually evaluate all 5,007 intervals and load all 12,198 source records.
No query advantage or physical acquisition saving is established. The reference
has no disagreements with the producer on this one case; this is not an estimate
of real-world false acceptance/refusal rates. Twenty-eight directed controls and
eleven result mutations pass. In particular, a constructed increasing-endpoint
case correctly reveals an interior decrease. That control is not an observed
property of this encounter.

Single-run calculation timers are 0.367380 s for union knots and 0.405599 s for
segment pairs. Their full supervised processes take 1.396194 s and 1.117016 s,
respectively; the latter also checks the producer's outputs. Sequential loading,
preparation and differing output obligations prevent a controlled speed claim.
See [timings](timings.json) and [costs](costs.json) for scope. Existing source
acquisition and unknown engineering effort must not disappear from economics.

The [result](result.json), [baseline](baseline.json), [check](check.json),
[two certificate excerpts](certificates.json), [pre-controls](controls-pre.json),
[post-controls](controls-post.json), [validation](validation.json) and
[failure ledger](failures.json) retain the conclusions. The university paper-host
TLS failure is preserved; arXiv v2 capture succeeded with verification enabled.
No scientific execution failed or frozen byte required correction in this release.
The lint wrapper first rejected a direct non-Python executable before launch;
the pinned Python wrapper then passed lint and format checks without relaxing
the identity guard. That failed preflight and its unplaced tool cost are retained.
A later read-only helper lookup used the wrong directory after a successful
staged-diff inspection; the failure and corrected explicit-owner read are retained.
An unavailable plotting library was left uninstalled; no plot is claimed.

Freeze SHA-256: `1df60c2fee5556667763a95d464228d762fe185abe253be2ab9803757a29a890`.
New retained/derived source bodies total 337,736 bytes. Prior source/context and
clock records, 8,869,686 bytes, are reused without another download. Raw sources
and the full 5,007-interval trace remain private under the
[distribution scope](DISTRIBUTION.md). Costs distinguish command clocks, elapsed
time and unknown active effort; final integration/readback costs are retained
in the owner directory after the public pre-push accounting cutoff.

## Reproduce from retained inputs

Use the pinned environment and new output paths; scripts refuse overwrites.
The owner supervisor enforces the existing cumulative time/storage limits and
network denial before the language runtime. Direct invocation is development
replay only, not a replacement for retained supervision.

```sh
owner=/Users/danielwahnich/.codex/reports/reiyah/nominal-separation-2026-09-21-39yw1e1x
py=/Users/danielwahnich/.codex/reports/reiyah/engine-discovery-custody-2026-09-13/private/runtime/bin/python
numeric=/Users/danielwahnich/.codex/reports/reiyah/compact-motion-2026-09-20-ee6goaua/private/sources
clock_records=/Users/danielwahnich/.codex/reports/reiyah/clock-alignment-2026-09-21-6a8ofcly/private
packet="$owner/candidate/research/nominal-separation/0.1.0"
freeze=1df60c2fee5556667763a95d464228d762fe185abe253be2ab9803757a29a890
"$py" -B "$owner/private/supervise.py" replay-new execution \
  "$py" -B "$packet/separation.py" --numeric "$numeric" \
  --clock "$clock_records" --sources "$owner/private/sources" --freeze "$freeze" \
  --result "$owner/private/replay-result.json" --trace "$owner/private/replay-trace.json" \
  --timing "$owner/private/replay-timing.json"
"$py" -B "$owner/private/supervise.py" reference-new checking \
  "$py" -B "$packet/reference.py" --numeric "$numeric" \
  --clock "$clock_records" --sources "$owner/private/sources" --freeze "$freeze" \
  --result "$owner/private/replay-result.json" --trace "$owner/private/replay-trace.json" \
  --check "$owner/private/replay-check.json" --baseline "$owner/private/replay-baseline.json" \
  --timing "$owner/private/replay-reference-timing.json"
```

Do not rerun a closed owner merely to accumulate another passing count. A future
authorized reproduction must create its own ownership/accounting envelope and
retain new receipts. The commands show exact operands, not a request to reopen
historical work. Current retained outputs are `result-01.json`, `trace-01.json`,
`check-01.json`, `baseline-01.json` and both `timings-*-01.json` in owner/private.
Owner `CLOSEOUT`, `FINAL_COSTS`, `PUBLISH_FINAL` and `FINAL_CONFIRMATION` bind
the eventual final commit and publisher readback.

## Next scientific obligation

This closes the nominal question. A stronger physical conclusion needs applicable
joint reference-position, time-alignment and intersample uncertainty evidence,
or a separately justified statistical contract. For example, a source-bound
calibration record could show where both navigation references were at common
surveyed times and quantify the residual errors for this run. Daniel is not
expected to own a private team's records; current public descriptions do not
supply that record.

The next decision experiment should use such qualified uncertainty to test whether
an obtainable additional observation resolves the full remaining decision family,
compared with an equally informed conventional method. Do not treat distinguishing
one selected pair of explanations as universal resolution. Do not replay this
exposed encounter as independent validation or build a wider monitor to sidestep
the missing measurement contract. Research and product superiority remain unproven.

All 1,433 reserved images stay closed. Gate A remains operator-unaccepted.
Historical controller, perception engine and all closed studies are unchanged.
