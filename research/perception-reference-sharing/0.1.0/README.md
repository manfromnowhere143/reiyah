# Reference sharing, 0.1.0

Document ID: `reiyah.reference-sharing.guide`. Status: exploratory.

Identical objects across joint alternatives can exhaust the compiler's representation limit.
On the supplied synthetic 17-world comparison, the earlier compiler returns [-3/2,3/2],
unresolved. Direct per-world coordinate matching gives [1/2,3/2]. The revised compiler reaches
that finite bound without changing the reference assumptions or any world, detection, weight,
loss or tolerance. This supports the addition only inside this constructed model.

| Synthetic case | Earlier checked bound | Current checked bound | Edge-comparison work, earlier → current |
| --- | --- | --- | --- |
| Seventeen worlds, two anchors | [-3/2,3/2] | [1/2,3/2] | 434 → 74 |
| Original repeated-65 resource case | [-1,1] | [-1,-1] | 256 → 130 |
| Larger downstream-budget counterexample | [0,1] | [0,1] | 16640 → 16640 |

The larger case rejected an intermediate design: unconditional sharing produced [-1,1] because
its newly finite graph exceeded the evaluator's unchanged work budget. The final compiler
declines sharing there. Its compiled input, compilation receipt and checked packet match the
earlier baseline byte for byte. This is a computational fallback, not evidence that acquiring
correct information weakens a universal claim over a fixed uncertainty set.

## Exact scope

Sharing requires an in-scope point object with the same ID, ordered proposal members, class,
canonical rational XY and timestamp in every declared world of its anchor. Different record
digests remain separate in `object_mapping`. Equal edge sets or losses alone never establish
this equality. Different objects at the same coordinates stay distinct.

Every source world is validated before materialization, including later malformed, unresolved
or out-of-scope rows. Unknown coverage, geometry/time and unavailable predictions retain their
existing meanings. Worlds still use one cohort-wide choice. Unused binary encodings remain
excluded. No probability distribution over interpretations is introduced.

A shared graph node is unconditional because that same declared object exists in every
admitted world. Other nodes keep their complete world guards. In any admitted world there is
a bijection between source objects and enabled graph nodes, preserving every same-class edge
at strict squared distance below 4. Therefore the two matching problems, their maximum
cardinalities and their full additive losses agree in that world. This also preserves weighted
differences under any restriction to retained worlds. Exactness does not establish that these
worlds cover physical reality.

The compiler preflights the evaluator's current work formula. For an anchor with N retained
detections, O proposed graph objects and S shared objects, a finite graph has at most
E=min(2048,N*O) edges. Its work is bounded by
`bits*(O-S) + 4*(N+1)*(O+E+1)`; add exact variable/clause work and multiply by the complete
binary encoding domain. Anchors already known open or necessarily over the object limit add
no finite-graph work. If this upper bound exceeds the existing evaluator limit, use ordinary
world nodes throughout the cohort. Only one representation is materialized; geometry is not
recomputed in a second compilation. The conservative preflight can decline useful sharing in
sparse graphs. It is neither a measured latency guarantee nor a claim of universal improvement.

No input/output fields, versions or core limits change. Graph IDs are local representation
identities; source identity uses anchor, world and object together. Several world-specific
mapping rows may now name one graph node. Always retain all rows, record digests and proposal
members. The unchanged common projection copies the complete model and mappings and checks
its inverse structurally. Rebuild admissions/common preparations in a fresh output when
selecting this compiler; a prior report remains bound to its original code and bytes.

## Reproduce and challenge

[Case identities](cases.json) bind the two small original input tuples. Each tuple supplies
reference, normalized comparison, normalization receipts and catalog, in that order. All records
are explicitly synthetic. They are not admitted reviewer judgments.

From a selected source checkout, use the repository Python environment:

```sh
python3 -B research/perception-reference-sharing/0.1.0/replay.py \
  "$PWD" "$PWD/research/perception-reference-sharing/0.1.0/cases" /absolute/private/fresh-result
python3 -B research/perception-reference-sharing/0.1.0/budget_probe.py \
  "$PWD" /absolute/private/fresh-budget-result
python3 -B -m unittest tests.test_perception_reference tests.test_perception_reference_sharing \
  tests.test_perception_reviewed_operands tests.test_perception_varying_match
```

Select source and expected case digests from the retained exchange before execution. Replays
refuse existing output directories. The small-case replay independently enumerates partial
injections using original coordinates and complete losses, then checks each finite world graph
and each source mapping. It does not use the compiler's geometry construction or producer's
matcher. The normalizer, input parser and rational representation remain shared premises.
Cost files contain measurements; the result files are deterministic.

The larger probe constructs 64 worlds with 128 immutable objects at X=10 and 128 base
predictions at X=0 in one anchor. Its addition at X=3 matches none, so delta=-1. At the other
anchor an addition at X=3 alone matches the object there, so delta=+1. Equal weights give zero
in every declared world. The compiler preserves all 8,256 source mapping rows, but retains an
open first anchor when sharing would exceed the evaluator budget. The test pins the original
compiled bytes. Its conditional [0,1] result remains conservative, not exact.

The original two representation-sensitive reference assertions and one common-projection
forgery target are retained with their failures in the private exchange. Current tests check
per-world base-neighbor counts, an actual unshareable 130-node overflow, and a conditional
object that the forgery truly changes. No resource rejection or semantic check was weakened.
Additional checks include 125 three-world patterns, reordered anchors/objects/worlds, distinct
record provenance, late unknown/malformed rows, and loss of an isolated shared object that
does not change the aggregate result. The latter must still fail the common structural check.

## Cost and remaining evidence

[Verification](verification.json) retains exact source, outputs, failures and costs. Graph
compression is not total-file compression: the small finite outputs are larger than their
earlier open fallbacks. All per-world provenance remains. The larger guarded process uses
more memory and compilation time than the original in the retained single-run measurements.
No latency advantage or human-effort budget is inferred from these observations.

The material design review considered general Boolean sharing. Bryant's annotated author
copy describes redundant-vertex and duplicate-subgraph reduction and its representation
limits. This checkpoint uses a much narrower all-world equality check; no BDD implementation
or performance claim is made. [Primary paper](https://www.cs.cmu.edu/~bryant/pubdir/ieeetc86.pdf).
Publication: IEEE Transactions on Computers C-35(8), August 1986; the exact date of this
annotated revision is not established. [Retained source metadata](sources.json) records the
private bytes and access/redistribution boundary. No third-party payload is redistributed.

Fable owns comparator/checker repairs, review planning and its reference-error model. This
Engine change supplies shared operands; it does not implement those tasks. The actual
two-window comparison remains [-8,8] without admitted human references. Actual participant
usability and external scientific review are missing. Gate A is unaccepted; the physical
study has not run. P005 is operator-reported published; no further publication or outreach.
