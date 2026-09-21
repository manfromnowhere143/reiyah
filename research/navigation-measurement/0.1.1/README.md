# Navigation measurement attempt: no eligible source case

Document: reiyah.navigation-measurement.report, version 0.1.1.
Status: blocked recorded-data experiment; authored mathematical development only.

The first 72,000 bytes of the pinned Oxford Technical Solutions NCOM example
contain 1,000 packets, all reporting navigation mode 2 (initialization). The
frozen selection requires mode 4 and a registered clock. It selects zero samples,
so neither decision arm acquires a reply or executes a fidelity decision. The
manufacturer's separately authored decoder confirms the 1,000 packet outputs
and empty eligible set. Empty error lists have denominator zero; they establish
no decision accuracy, parity, uncertainty reduction or acquisition saving.

The [question](QUESTION.md) was frozen before obtaining the numeric prefix:
could a 10 Hz linear reconstruction replace a 100 Hz recorded north-velocity
trace within an authored uniform tolerance of 0.05 m/s, conditional on a
5 m/s² recorded-rate premise? This is a numerical fidelity requirement, with
no demonstrated customer or safety significance. No alternative window was
substituted into this failed attempt. Physical qualification remains unresolved.

The [method](METHOD.md) implements a two-sided residual-margin decision and
complete continuous response sets. Its scalar residual-rate family is a
conservative relaxation. The strong conventional alternative retains the
original velocity-rate constraint and the coarse reconstruction, so it may
resolve more with fewer samples. The directed linear-trace control demonstrates
that representational disadvantage. Decision methods, wrappers and controls
share one author; the vendor decoder supplies an independently authored input
check, not independent experiment replication.

Twenty-five authored pre-controls pass, including strict response endpoints,
an isolated supporting response, consistency, clock/status/sentinel distinctions
and source binding. They are development checks, not 25 empirical cases. No
recorded response partition, witness stage or full-reference fidelity case ran.
The eight conditional post-result mutations were not run and are not counted.

The initial frozen 0.1.0 controls failed on a missed unit-bearing output key.
All original bytes and its [correction](correction.json) remain; 0.1.1 fixes
field names without changing the mathematics or pre-outcome question. A failed
hardcoded tool-path lookup and a packaging-only dictionary/list mismatch are
also retained in [failures](failures.json). The latter failed before file edits.

The preceding bounded 7V-Scanario access investigation received supported byte
ranges and decoded a partial archive prefix. It did not qualify a numeric
trajectory: no complete NCOM packet was identified in the selected RD prefix.
The complete archive and each complete compressed block exceed the source cap.
This does not prove all partial-access strategies impossible, and metadata
checksums do not authenticate a partially decoded payload. No physical case ran.

Read [results](results.json), [input check](check.json), [unexecuted baseline
record](baseline.json), [controls](controls-pre.json), [validation](validation.json)
and [costs](costs.json). All source-derived row tables and decoder output stay
private; [identities](private-output-identities.json) bind them. Source bytes,
access terms, exact versions and partial-digest limits are in [the ledger](sources.json)
and [source notes](SOURCES.md). See [distribution scope](DISTRIBUTION.md).

Reproduction requires the exact privately retained sources listed in the ledger,
the declared compiler and pinned Python, and the byte-bound supervisor used by
the owner. Build the original vendor decoder with the public authored wrapper,
then run controls, run.py and check.py with the frozen digest and fresh output
paths; [the plan](PLAN.md) fixes order, caps and isolation. Executing these
scripts directly is a development replay and does not recreate the retained
launcher provenance or any historical Gate A release. The live source host is
not a runtime dependency. No third-party body, source row or vendor binary is
redistributed by this packet.

This checkpoint does not end the mission. A separate follow-up may freeze one
disjoint end-of-file sample before its values are inspected, retaining this
failed initial-prefix attempt. Eligibility follows declared status and clock
fields, never favorable fidelity outcomes. If that fixed sample is also
unusable, close this source route rather than sweeping it. Keep the same
threshold, rate premise, demanding baseline and complete-cost obligations.
Such a follow-up would be explicitly exploratory after this qualification
failure. All 1,433 reserved images remain closed; Gate A is operator-unaccepted.
