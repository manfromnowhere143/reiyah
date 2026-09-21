# Reject a constant clock-offset shortcut

Document ID: `reiyah.clock-alignment.report`. Version: `0.1.0`.
Status: exploratory development. Date: 21 September 2026.

**No single constant offset preserves all recorded target-to-ego associations
in the selected ViF-GTAD streams.** Keep the recorded clock mapping when choosing
neighboring source rows. Reiyah and the competent conventional scan both reject
the shortcut after three logical constraint reveals. There is no query advantage.

The [frozen plan](PLAN.md) asks a consequential adapter question: whether the
paired GPS/written-ROS mapping may be replaced by one constant without changing
which ego records bracket each supported target timestamp. It tests all real
constants, with exact endpoints and source-row ties, rather than selecting a
convenient fitted correction. [The method](METHOD.md) is standard interval
feasibility, not a new mathematical primitive.

## Complete population and decision

| Retained scope | Result |
| --- | ---: |
| Ego records | 7,761 |
| Target records | 4,437 |
| Targets before ego GPS support | 1,933, input-blocked for association |
| Targets after support | 0 |
| Bracketed target timestamps | 2,504 |
| Exact terminal endpoints | 0 |
| Allocated adapter decisions | 1 |
| Reiyah / conventional decision | contradicted / contradicted |
| Logical reveals, each method | 3 |
| Distinct ego mapping rows touched by those reveals | 4 |
| Full reference constraints checked | 2,504 |
| Incorrect acceptance / refusal against this exact reference | 0 / 0, each method |
| Physical clearance cases | 0; physical claim unresolved |

All records keep their dispositions. The decision concerns supported associations;
it does not silently extrapolate the earlier 1,933 target records. There is one
dependent development case, not 2,504 independent tests of scientific performance.
Both full numeric streams were exposed in the earlier compact-motion audit.

The early certificate is particularly small. Zero-based target row 1,933 requires
the offset c, in seconds, to lie in **[7119.988637, 7120.004873)**. Row 1,935
requires **[7120.045459, 7120.046866)**. These intervals do not intersect. The
three-row prefix already excludes **every** constant in the declared family;
unrevealed rows cannot restore feasibility. This is stronger than showing that
two selected candidate offsets disagree, while remaining specific to this family.

The full reference independently obtains lower endpoint 7120.114120 s and upper
endpoint 7119.996738 s, an empty intersection, with extrema at target rows 3,955
and 4,072. These offsets relate written clock labels. They are not measured
hardware latency, a time-zone correction or a physical synchronization bound.

## Evidence, verification and costs

[Sources](SOURCES.md) records the author paper and scenario description plus
read-only reuse of the prior numeric sources. The README identifies the ego's
first column as ROS time and the target timestamps as GPS time. We use those
labels literally. The message-header epoch is not substituted for the first
column; no UTC, leap-second or time-zone conversion is inferred.

The producer uses Decimal clocks and binary-search brackets. The separate
reference uses Fraction clocks and a monotone merge, verifies all constraints
and all three prefixes, and checks the two-row infeasibility certificate.
The conventional scan computes extrema through another code path. Both arms
and the checker were authored in this session and share custody/MAT decoding.
This is internal verification, not independently authored comparison or replication.

The [result](result.json), [reference check](check.json),
[26 boundary/refusal controls](controls-pre.json),
[11 actual-result mutations](controls-post.json), [freeze](freeze.json),
[source identities](sources.json), [validation](validation.json),
[failures](failures.json) and [cutoff costs](costs.json) retain the exact scope.
The full per-row constraint and reveal trace remains private, digest-bound by
both result and check. No frozen implementation correction was required.

New source bodies and derived text total **5,209,042 bytes**; 3,229,533 bytes of
earlier retained sources are bound without another download. The complete decision
command took 0.645523 s and full reference command 0.459070 s. Nested shared
binding/decoding/allocation took 0.494982 s. One-shot arm timers were about
12.04 microseconds for Reiyah and 6.17 for the conventional scan. These tiny nested
measurements are not a speed benchmark and are not added to outer command costs.
The source was already fully captured and the constraints allocated before the
logical reveal comparison. No actual acquisition or human-effort saving follows.

Costs include failed work and distinguish process durations, overlapping UTC
envelopes, elapsed time and unmeasured active effort. Provider charges, energy,
peak workflow memory and complete economics remain unknown. Final integration,
publication/readback and later costs are in the owned closeout, after this public
cutoff. The completed original ten-hour mission is not restarted or padded.

## Reproduction and next decision

Owned report: `~/.codex/reports/reiyah/clock-alignment-2026-09-21-6a8ofcly/`.
Use its CLOSEOUT, FINAL_COSTS, PUBLISH_FINAL and FINAL_CONFIRMATION records.
The following command creates a fresh checker result under the owned, bounded,
network-denied supervisor. It needs the retained private source bodies and trace;
the public aggregate alone does not reproduce source decoding.

```sh
reiyah_owner=/Users/danielwahnich/.codex/reports/reiyah/clock-alignment-2026-09-21-6a8ofcly
reiyah_python=/Users/danielwahnich/.codex/reports/reiyah/engine-discovery-custody-2026-09-13/private/runtime/bin/python
reiyah_sources=/Users/danielwahnich/.codex/reports/reiyah/compact-motion-2026-09-20-ee6goaua/private/sources
cd "$reiyah_owner/candidate"
"$reiyah_python" -B "$reiyah_owner/private/supervise.py" reproduce-check checking \
  "$reiyah_python" -B research/clock-alignment/0.1.0/reference.py \
  --retained-sources "$reiyah_sources" --sources "$reiyah_owner/private/sources" \
  --freeze-sha256 2e22a6e6dce30a242f0b61a4574ff7aeec68a28840b8d8579482392ebf91a43d \
  --result "$reiyah_owner/private/result-01.json" \
  --trace "$reiyah_owner/private/trace-01.json" \
  --out "$reiyah_owner/private/reproduce-check.json"
```

Do not rerun this closed decision to accumulate passes. The next bounded question
should use the preserved MAT coordinates and recorded associations to test one
declared nominal two-vehicle relation, such as the scenario description's increasing
separation. Freeze its projection, geometry, interpolation and unknown rules before
new relational outcomes. Label the result as recorded-data conditional unless
applicable physical pose, clock and between-sample uncertainty are qualified.
This negative shortcut result does not justify a wider monitor or platform.

All 1,433 reserved images stay closed. Perception source remains 38a50ec014cc83e86ea6f247df803ded2971b386.
The historical controller and prior failures remain unchanged; Gate A is
operator-unaccepted. [Distribution](DISTRIBUTION.md) separates public derived
summaries from private source bodies. Normal push/readback gives publisher
integrity observations, not scientific or independent transport acceptance.
