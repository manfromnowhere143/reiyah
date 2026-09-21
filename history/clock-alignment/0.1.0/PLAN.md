# Preserve recorded clock associations

Document ID: `reiyah.clock-alignment.plan`. Version: `0.1.0`.
Status: exploratory development. Date: 21 September 2026.

## Decision and consequence

May one constant offset replace the selected ViF-GTAD ego GPS-to-written-ROS
mapping while preserving the neighboring ego record identities for every target
timestamp in its recorded support? If supported, that constant is admissible for
this exact association contract. If contradicted, retain the recorded mapping
and reject this shortcut. This is an adapter decision, not vehicle safety,
physical simultaneity, interpolation accuracy or product value.

Use scenario 3, BME Honda, already selected in compact-motion 0.1.1. All 7,761 ego
and 4,437 target rows were exposed in its serialization/clock audit. Its summaries
motivated this question. This is a development comparison, not a held-out study.
No previous source is altered and no new motion population is selected.

The dataset README calls the first ego CSV column ROS time, supplies GPS week
and seconds in the same row, and describes the target timestamps as GPS time.
Use those written calendar labels literally: GPS epoch plus week/seconds for
ego GPS, target MAT Time as GPS calendar labels, and the ego first-column calendar
as its written ROS labels. Do not silently convert UTC, time zones or leap seconds.
This nominal interpretation is explicit; physical clock calibration remains
unqualified. Do not substitute the message header for the documented first column.

## Complete allocation before new association results

- Require strictly increasing nonempty ego GPS and written-ROS sequences and
  strictly increasing target times. Reject malformed/missing/sub-nanosecond
  fields instead of sorting, rounding or imputing them.
- Retain every target disposition: before support, after support, bracketed,
  or exactly at the terminal ego knot. Unsupported rows are input-blocked for
  association and are never silently removed from the reported population.
- For each supported target, preserve its original GPS bracket. The candidate
  constant must give the identical bracket in written ROS time. Ties select the
  right-hand bracket. The terminal endpoint must remain that exact endpoint.
- Test existence over **all real constants**, using exact integer-nanosecond
  interval endpoints. There is no chosen clearance threshold, fitted correction,
  finite candidate grid, smoothing, trajectory extrapolation or favorable window.
- Reveal mapping constraints in target source-row order. Reiyah intersects the
  surviving interval and stops when it is empty, or accepts after all supported
  constraints. A competent conventional extremum scan has the same inputs,
  ordering, refusal rules and early-stop permission. Retain parity and overhead.
- A separate full-source reference uses independently parsed rational clocks,
  a monotone merge for association and extrema over every constraint. Check the
  full result and every prefix, including the infeasibility certificate.

These are logical reveals of already captured/decoded records. They measure
neither new sensor acquisitions nor saved downloads or human effort. Both arms
are authored in this session and share custody/MAT decoding, not arithmetic.
Report source preparation, complete verification and all failed work separately
from nested arm timers. No independent baseline authorship or replication claim.

## Verification and bounds

Before execution, freeze plans, sources, both calculations, controls, runtime
and supervisor. Exercise endpoint openness, exact ties, unsupported/empty
coverage, common versus per-row offset, non-monotone/missing inputs and large
epoch precision. After execution reject mutations of decisions, source identities,
counts, interval endpoints, witnesses and reveal traces. Any required frozen-code
correction gets a new version and retains the original failure.

Use pinned Python/NumPy/SciPy without installation; deny network before execution
and checking runtimes. Cumulative execution and checking each stay below 600 s,
including failures. New bodies and derived text stay below 8 MiB; new artifacts
and owned temporaries below 128 MiB; checkout counted separately; free disk above
5 GiB. Prior numeric bodies are hash-bound by reference and charged historically,
not redownloaded. Keep all 1,433 reserved images closed. No media, inference,
training, paid compute, outreach, delegation, deployment or physical control.

Complete the bounded decision, verification, costs, concise handoff/roadmap,
reviewed integration and normal push/readback. Preserve the historical controller
and all closed studies. Gate A remains operator-unaccepted. Publication and
internal agreement confer no scientific or transport independence.
