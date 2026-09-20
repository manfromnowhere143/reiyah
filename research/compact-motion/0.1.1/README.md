# A vehicle-coordinate export changes the recorded positions

Packet version: `0.1.1`. Status: exploratory development, 20 September 2026.

**The selected ViF-GTAD target CSV is not a lossless substitute for its MATLAB
companion.** All 4,437 identity-matched records differ in both latitude and
longitude. The maximum nominal spherical displacement between representations
is **6.631331 m**, with mean **3.747876 m**. This is a serialization comparison;
neither file has been validated as physical ground truth here.

The practical input decision is to preserve the original numeric representation
or explicitly account for serialization error before applying a finer-scale
measurement contract. This result does not justify a physical clearance claim,
and it does not say that CSV as a format is inherently unsuitable.

## An executed decision, with parity

The [frozen decision plan](DECISION_PLAN.md) asks whether every selected coordinate
pair remains numerically equal across the two exports. It was frozen before
the full comparison; prior first-row/schema exposure and the outcome-informed
MAT companion selection are disclosed. One complete target file is allocated.

| Evidence available | Possible mismatching-record count | Whole-file decision |
| --- | --- | --- |
| CSV and identity metadata; no MAT coordinate reveal | 0 to 4,437 | Unresolved |
| First corresponding MAT coordinate pair revealed | 1 to 4,437 | Lossless substitution contradicted |
| Separate complete-file reference | Exactly 4,437 | Lossless substitution contradicted |

Reiyah and a competent conventional early-exit scan both reject after **one
logical record reveal**. The checker recomputes every prefix bound and traverses
the complete file. Each method resolves the one allocated decision, with zero
false acceptance, zero false refusal and zero unresolved decisions against this
recorded-data reference. These are single-case counts, not error-rate estimates.

**No query advantage is demonstrated.** Both methods were authored in this
session and share source decoding. Their answers are computed separately, not
constants copied from one another. The source file was already downloaded and
decoded; one logical reveal does not mean one row of actual acquisition work.
The universal bounds here cover all completions under the export contract. This
does not expand the older continuous-clearance method's pair-distinguishing
measurement into a guarantee of physical decision resolution.

## Source and numeric findings

The [selection](selection.json) chose scenario 3 from metadata: the smallest
ego GPS CSV, then the alphabetically first target CSV, BME Honda. The
[companion selection](companion-selection.json) later chose that exact target's
MAT file to investigate its coordinate precision. No favorable time window was
selected. These dependent observations are not independent drives.

Supported public HTTP Range requests retrieved the ZIP directory and six small
members, including the 7,761-record ego stream, 4,437-record target stream and
target MAT companion. Captured source and derived inventory/cell files occupy
4,323,197 bytes, counting compressed ranges and extracted members separately.
Additional source transcriptions and schema-exposure records are charged in
[costs.json](costs.json). The complete 6.7 GB archive, sensor bags,
images and videos were not downloaded. Its publisher MD5 remains unverified.
Member CRCs and local SHA-256 digests are retained. See [sources](SOURCES.md),
[byte ledger](sources.json) and [distribution terms](DISTRIBUTION.md).

Both numeric streams are finite in their inspected measurement columns, with
no repeated or non-increasing timestamps. CSV/MAT target timestamp strings agree
on every row. The CSV uses three or four fractional coordinate digits. The
largest latitude/longitude discrepancies are approximately 0.00005 degrees;
the standard-deviation columns remain numerically identical. A fine-looking
standard-deviation field therefore does not describe the export discrepancy.
The target's heading also differs in 4,436 records; one integer-valued MAT
heading caused the retained initial decoder failure.

The ego GPS field advances exactly 0.01 seconds per record, while header increments
range from 0.000296246 to 0.232434092 seconds. The target's written-time increments
range from 0.009 to 0.370 seconds. Nominal ego calendar text minus header epoch
ranges from 7,200.000027808 to 7,200.010880092 seconds. GPS-epoch-plus-week minus
header epoch ranges from 79.734742154 to 80.004643902 seconds. These are explicitly
defined field differences, not measured UTC clock error, latency or synchronization
bounds. No fitted offset or silent timezone/GPS correction is applied.

Dimensions and GPS offsets for both vehicles are documented. Output reference
point/lever-arm interpretation, target time semantics, clock residuals, applicable
joint pose/geometry error, intersample motion and whole-trajectory coverage remain
unqualified. **Zero physical clearance cases ran.** No actor-time join, inference,
training, simulator or vehicle control was performed. All 1,433 reserved images
remain closed; prior NGSIM, authored and perception studies are unchanged.

## Verification, correction and cost

The separate diagnostic reference agrees on 210 reported scalar leaves. It uses
rational clock arithmetic and unit-vector chord distance, while the producer
uses decimal clocks and haversine distance. They share the SciPy MAT container
decoder and byte custody, not the reported arithmetic. The decision checker
independently traverses all 4,437 coordinate pairs and checks both methods' stops
and the complete bound trace. This is internal verification, not independent
replication, calibration or evidence of frontier performance.

Current controls pass: 23 diagnostic pre-controls, five diagnostic result
mutations, seven decision control families and six decision result mutations.
The initial 0.1.0 actual audit failed on a legitimate uint8 heading cell. Its
code, freezes and failure remain, and its time is counted. The
[correction](CORRECTION.md) accepts exactly representable numeric integer cells,
keeps text and unsafe integer rejection, and changes no decision or arithmetic.
[Failures](failures.json) also retains setup, network and read-only command errors.

The corrected audit took 0.545859 outer-process seconds; its separate check took
0.708086 seconds. The decision execution took 0.353718 seconds and its complete
check 0.365151 seconds. Shared binding and decoding inside the decision execution
took 0.178421 seconds. The one-shot method timers were approximately 18 microseconds
for Reiyah and 5 microseconds for the conventional scan. They are nested costs,
not added again to the process envelope, and are not a performance benchmark.
No time or acquisition saving is established. Full known workflow costs and
cutoffs are retained separately; human effort, charges, energy and peak workflow
memory remain unknown.

## Reproduce the recorded decision

Use the existing pinned Python 3.14.2 environment, NumPy 2.4.2 and SciPy 1.17.1.
The installed package versions are recorded; a reproducible rebuild of every
environment binary is not claimed. The [analysis freeze](freeze.json) binds the
offline code and exact source bytes; the [decision freeze](decision-freeze.json)
adds the decision protocol. Source artifacts and the bounded acquisition receipts
are private under the owner path below. The public source member names and
digests permit a separately authorized reconstruction; do not substitute changed
downloads or another dataset version silently.

From the owned candidate, with task-specific variables assigned:

```sh
reiyah_owner=/Users/danielwahnich/.codex/reports/reiyah/compact-motion-2026-09-20-ee6goaua
reiyah_py=/Users/danielwahnich/.codex/reports/reiyah/engine-discovery-custody-2026-09-13/private/runtime/bin/python
reiyah_packet=research/compact-motion/0.1.1
"$reiyah_py" -B "$reiyah_owner/private/supervise.py" decision-recheck checking \
  "$reiyah_py" -B "$reiyah_packet/decision_check.py" \
  --sources "$reiyah_owner/private/sources" \
  --freeze 2afdec93b04fec556d05c6815e8da8e6f1d8fff7d4ac5e6e7c20bde37c4cee5a \
  --decision-freeze df366904343acf6157efe7971990310a686cc07663505bf252e081d8d940f190 \
  --result "$reiyah_owner/private/decision-run-01.json" \
  --output "$reiyah_owner/private/decision-recheck.json"
```

The supervisor denies network before the child runtime, enforces the cumulative
owner budget, uses an owned temporary root and refuses an existing command name.
Choose a new output/name for an intentional replay; do not modify retained evidence.
Public result files are [diagnostics](audit-result.json), [diagnostic check](check-result.json),
[decision](decision-result.json), [decision check](decision-check.json), and
[repository validation](validation.json). A passing check or publisher readback
does not constitute Gate A operator acceptance.

## Next decision

Reject this CSV as an exact coordinate replacement. Preserve the MAT representation
for any next recorded-data study and carry the clock differences explicitly.
Before a relational physical experiment, obtain and verify the source's clock/
reference-point mapping and applicable uncertainty evidence. For example, a record
explaining which physical instant the target time names must also explain how it
aligns with the ego GPS field; subtracting an observed average offset is insufficient.
Daniel need not possess private team records or grant general permission again.

The next substantive study should freeze a meaningful relational decision and
test whether an obtainable observation resolves the full remaining decision
bounds against an equally informed conventional method. If only recorded-data
semantics qualify, state that narrower claim before outcomes. Do not count this
serialization result as a driving-safety result, another source inventory as
comparative value, or expand the monitor to compensate for missing calibration.
