# Recorded navigation fidelity: conventional method needs one fewer sample

Document: reiyah.navigation-measurement.report, version 0.2.0.
Status: exploratory recorded-data comparison; physical qualification unresolved.

Both methods support the fixed 0.05 m/s reconstruction-fidelity requirement in
all five dependent parts of one one-second recorded selection. Reiyah uses 90
extra logical samples; the original-velocity conventional method uses 89. The
full recorded reference's largest error is 0.0042 m/s. This is a small observed
disadvantage for the current residual formulation, not evidence of an advantage
or a general performance difference. No physical clearance or safety case ran.

| Part | Full recorded error, m/s | Reiyah queries | Conventional queries |
| --- | ---: | ---: | ---: |
| 0 | 0.0042 | 18 | 18 |
| 1 | 0.00192 | 18 | 17 |
| 2 | 0.0036 | 18 | 18 |
| 3 | 0.00376 | 18 | 18 |
| 4 | 0.00142 | 18 | 18 |

The [question](QUESTION.md) was frozen before capturing exactly the final
72,000 bytes of the pinned Oxford Technical Solutions example. All 1,000
packets report mode 4; 999 are eligible and the first lacks a preceding clock
registration. The fixed first-eligible rule selects 101 consecutive 10 ms
records. Five adjacent parts share endpoints and are not independent trials.
Both methods get the same eleven unique initial coarse samples, conditional
5 m/s² original-velocity rate premise and available native query times.

The preceding [initial-prefix attempt](../0.1.1/README.md) remains blocked with
zero cases. This disjoint fixed-tail follow-up was disclosed after that failure,
before viewing tail values; it is exploratory, not a held-out benchmark. No
favorable-window sweep occurred. No further slice from this source is planned.
The tolerance is an authored numerical fidelity requirement, with no established
customer or safety significance. The rate premise holds for the declared
piecewise-linear recorded reconstruction on all 100 selected native intervals;
it does not calibrate physical motion or establish future uncertainty coverage.

The [method](METHOD.md) exposes a useful engineering limitation. Reiyah replaces
the original constraint with a larger residual-rate family. The conventional
alternative retains the original velocity cones and baseline, and can resolve
with less information. Both families also allow bends between native grid
knots, so neither is the tightest model of the specified stored-data
interpolation. Preserving the original constraints and the known native grid is
the next correction to develop. A replay of this now-exposed trace must be
labeled development regression; it would not create new empirical evidence.

The independently authored manufacturer decoder agrees on all 1,000 packet
outputs, the complete 999-row eligible set and the selected values. Separate
geometry/LP calculations verify 190 one-sided model/witness stages and 270
response-partition checks: 90 joint two-sided partitions and their 180 one-sided
components. They represent 90 acquisitions, not 270 acquired observations.
The conventional arm has 94 checked bound stages. Twenty-five directed
pre-controls and eight actual-result mutations pass. The two methods agree
with the complete recorded reference in all five parts; that small dependent
development example does not estimate decision accuracy. Both decision
implementations, wrappers and experiment have one author. No external
scientific replication or novelty claim is made.

The complete slice was captured, loaded and decoded, including values later
counted as logical reveals. Query counts do not establish physical acquisition
savings. The reference process combines vendor decoding, Reiyah verification
and conventional calculation; comparing its total timer directly with the
producer timer would not be a fair speed comparison. Full costs retain source
preparation, reuse, execution, checking, controls, integration and readback.
Active effort, charges, energy, peak memory and full economics remain unknown.

Read [aggregate Reiyah results](results.json), [the conventional/reference
aggregates](baseline.json), [verification](check.json), [validation](validation.json),
[costs](costs.json), [failure history](failures.json) and [source ledger](sources.json).
Full row tables, source-derived proofs, vendor output and private trace values
are withheld from distribution; their [identities](private-output-identities.json)
bind the retained private records. Manufacturer sources, manuals and binaries
remain under their recorded terms; see [distribution](DISTRIBUTION.md).

For reproduction, use the exact source/runtime/binary identities in freeze.json
and fresh output paths. The [plan](PLAN.md) fixes controls, producer, independent
check, mutations, source caps and offline launcher order. Private owner command
receipts retain exact invocations. Direct script execution is a development
replay and does not recreate launcher provenance or any Gate A release.
The live source host is not a runtime dependency. The nine mathematical/decoder
Python kernels and original wrapper are byte-identical to 0.1.1; only source
binding, mapping and output-version metadata changed before the freeze.

The continuing mission remains active. Keep the initial failure and this
one-query disadvantage, develop the tighter recorded-data model, then seek
a separately frozen decision on unexposed eligible material. Preserve all
1,433 reserved images, the historical controller and closed studies. Gate A
remains operator-unaccepted. No deployment or physical claim is implied.
