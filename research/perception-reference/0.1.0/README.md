# Joint reference interpretations

Document ID: `reiyah.perception-reference.guide`

Version: `0.1.0`

Lifecycle status: `exploratory`

This offline compiler connects explicit point-reference interpretations to the
[paired-loss core](../../perception-decision/0.1.0/README.md). It derives same-class matching
edges from exact coordinates and keeps one shared interpretation across the entire cohort.
It uses the [verified input catalog](../../perception-inputs/0.1.0/README.md) and the existing
normalization receipts. The [checkpoint](checkpoint.json) binds tested code and demonstrations.

The compiler's finite model is a declared assumption about possible reference worlds. It does
not discover objects, convert an annotation list into complete physical truth, or establish
independent review. Unknown geometry, time, joint coverage or unlisted matchable objects keep
the affected reference open. Continuous geometric regions are not discretized into selected
points; they remain unresolved in this version.

## Boundary interface

Use `tools.perception_reference.compile_files` with five keyword arguments:

```python
compiled_input, compilation_receipt = compile_files(
    reference_path=reference_path,
    reference_sha256=expected_reference_sha256,
    comparison_path=normalized_input_path,
    normalizations_path=normalization_receipts_path,
    catalog_path=verified_catalog_path,
)
```

The reference file identifies the expected exact bytes of the other three files. All four
identities are checked before compilation. The function returns data without writing output.
Persist the compiled input and receipt to fresh private paths using the existing atomic writer,
then run and verify the core packet against the compiled-input digest. Keep all four source
files and the compilation receipt alongside that packet. The pure `compile_model` function is
an internal composition interface for already-bound inputs, not a file-verification boundary.

The comparison must still be the unchanged open-reference normalized input, with empty model
variables and clauses. The compiler refuses to replace an existing reference model or discard
its constraints. Anchor identities and weights remain unchanged. Every normalization receipt
must bind its exact input anchor, sample, source identities and nominal ego position. Retained
detections require their exact role-bound geometric records; suppressed camera records do not
become matching vertices.

Normalization itself remains an identified trusted input: this compiler does not repeat
source parsing, qualification or suppression. The core certificate checker verifies the
compiled graph computation. It does not independently validate the compiler, upstream
normalization or physical reference coverage. The separate geometric calculation in the tests
addresses a bounded part of that computational trust boundary.

## Reference contract

The root object has exactly these fields:

| Field | Meaning |
| --- | --- |
| `artifact_id` | `reiyah.perception-reference.input` |
| `version` | `0.1.0` |
| `coordinate_frame` | `nominal_global_xy` |
| `inputs` | Exact `comparison_sha256`, `normalizations_sha256`, `catalog_sha256` |
| `joint_coverage` | Declared finite-envelope assumption or explicit unknown |
| `worlds` | One to 64 complete joint interpretations of the same anchor population |

`joint_coverage` is either `{state: unknown, reason: ...}` or
`{state: assumed_complete, statement: ..., basis_sha256: ...}`. A basis digest identifies an
external assumption record; its content and authority are not established by the digest.
No `verified`, `accepted` or physical-confidence state is accepted in this field.

Each world has exactly `id`, `basis_sha256` and `anchors`. Every world must name every comparison
anchor exactly once. Each anchor entry has exactly `anchor_id`, `unlisted_objects` and `objects`.
`unlisted_objects` is either explicit unknown or `excluded_by_assumption` with the same statement
and basis fields. The closure assumption concerns every object that could change matching,
including paths through neighbors of base detections. It is not a camera-only neighborhood.

Each object is one of two closed forms:

```text
Point:      id, members, record_sha256, state=point, class, xy, timestamp_us
Unresolved: id, members, record_sha256, state=unresolved, reason
```

`members` names one to 32 observation-proposal identities represented by that object. A member
cannot belong to two objects in one anchor interpretation. Alias uncertainty is represented
by separate complete worlds with different groupings. Object presence is represented by
inclusion or absence in those worlds; an omitted proposal needs a reason in the bound world
basis. The compiler checks the formal grouping, not whether the proposed grouping is physically
correct. The original reference file preserves alternatives, including out-of-range and
unresolved records that do not become graph nodes.

Known classes are the ten declared detection classes or the explicit category `outside_target`.
An unknown class remains unresolved; a misspelled class fails. A point contains two reduced
canonical rational-string components, each with at most 32 digits and magnitude at most
10^12. Binary floats, unreduced fractions and nonfinite values are rejected. Its timestamp must
equal the catalog anchor time to support finite compilation. A different time leaves the anchor
open; no interpolation or motion reconstruction is inferred.

Positions and the nominal ego point use the same global XY frame. Objects at horizontal range
at most 50 m are in scope. Same-class detection/object pairs match at squared distance strictly
less than 4 m^2. These are the existing research comparison's rules, not an official nuScenes
benchmark, a calibrated physical tolerance, or a deployment loss.

## Joint choices and bounds

For W supplied worlds, the compiler uses `ceil(log2(W))` Boolean choice variables. Clauses exclude
unused binary encodings. Every anchor uses those same variables; objects from mutually exclusive
worlds cannot coexist. The model admits exactly W joint choices before any conservative
open-reference projection. It neither takes a Cartesian product of per-anchor alternatives nor
silently breaks cross-anchor constraints.

For every finite interpretation, graph edges include every qualifying base and retained added
detection. Maximum matching remains the core's task. An unresolved reference in any world
opens that anchor for all worlds, losing potential tightness conservatively. Unknown coverage of
the joint world list opens all anchors. The count enclosure remains valid for the declared
additive loss, without assuming those unlisted objects absent.

The compiler caps each graph at 128 object vertices and 2,048 edges and budgets at most
2,000,000 detection/object geometry comparisons. Once a limit is reached, it validates remaining
object records but emits an open reference instead of a partial finite graph. The receipt names
the fallback reason. The core retains its own independent work and world limits. An oversized
required file, malformed record or more than 64 supplied worlds is rejected; no input list is
clipped. File caps are 4 MiB for reference and normalized comparison, 16 MiB for normalizations,
and 128 MiB for the catalog.

Open-reference projection can remove cross-anchor constraints affecting that open anchor; it
only widens the enclosure. Finite anchors keep their original joint choice. A wide result is
not proof of non-identifiability. Every resulting packet keeps physical coverage unestablished
and statistical confidence unspecified.

## Runnable constructed example

[joint-world-example.json](joint-world-example.json) contains two constructed anchors with
opposite matching-trap interpretations. Both joint worlds have mean contrast zero; separate
per-anchor extrema would give [-1,1]. Source and basis identities in this fixture are explicit
synthetic placeholders. They do not identify real sensors or reviewer judgments.

```python
from pathlib import Path
import hashlib
import json
from tools.perception_decision import cli, contract
from tools.perception_reference import compile_files

bundle = json.loads(Path("research/perception-reference/0.1.0/joint-world-example.json").read_bytes())
out = Path("/absolute/private/fresh-example")
out.mkdir()  # Refuse an existing run identity.
paths = {name: out / (name + ".json") for name in ("reference", "comparison", "normalizations", "catalog")}
for name, path in paths.items():
    cli.atomic_write(path, contract.encoded(bundle[name]))
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
compiled, receipt = compile_files(
    reference_path=paths["reference"], reference_sha256=sha(paths["reference"]),
    comparison_path=paths["comparison"], normalizations_path=paths["normalizations"],
    catalog_path=paths["catalog"],
)
source, packet = out / "compiled.json", out / "packet.json"
cli.atomic_write(source, contract.encoded(compiled))
cli.atomic_write(out / "compilation.json", contract.encoded(receipt))
cli.run(source, sha(source), packet)
print(cli.verify(source, sha(source), packet, sha(packet))["result"])
```

Expected result: exact finite-model bounds `[0,0]`, equivalence within the declared tolerance,
and physical coverage `not_established`. This illustrates preservation of a shared hypothesis;
it is not an empirical improvement over a conventional analyst.

## Next integration

Reference and partial-identification research can supply explicit alternatives or justified
outer enclosures through this boundary. Preserve sample, class, alias, clock and source identity
and label every coverage assumption. A tail exponent, dependence coefficient or censored-rate
bound does not establish those observation-to-object links. Proposed new uncertainty types
must have a sound enclosure argument and tests before extending this finite-point interface.

Raw observation-window validation and the blinded reviewer/comparator workflow remain separate
unfinished work. No independent reviewer records or new study selection were created here.
