# Fixed comparison with benchmark annotations

Artifact family: `reiyah.perception-annotations`. Version: `0.1.0`.
Status: `exploratory`. Prepared 14 September 2026.

The offline [adapter](../../../tools/perception_annotations.py) evaluates an existing detector
comparison against the retained nuScenes annotation table. It scans every annotation row for
the exact supplied anchor tokens, retains literal row indices, byte offsets and hashes, resolves
sample/instance/category joins, and feeds one explicitly conditional world to the existing
reference compiler. The existing projection preserves the same common prediction identities.
No reviewer record or human admission is created. The original comparison is not modified.

The [first actual replay](../../../docs/PERCEPTION_ANNOTATION_CASE_2026-09-14.md) has weighted
loss difference **+1** on the two already exposed anchors. The original comparison with open
physical references remains **[-8,8]**. These answer different reference assumptions.

## Target and policy

Policy `reiyah.annotation-conditional-fixed-comparison.0.1.0` fixes:

- The existing base/addition membership, anchor weights, loss and tolerance.
- Source keyframe timestamps and nominal global XY; no temporal interpolation.
- The official nuScenes detection-category mapping. Unmapped source categories remain explicit
  exclusions. An unresolved instance/category join is an invalid input.
- Mapped labels with squared nominal XY distance to the bound ego position **<=2500**.
- Retention of zero-point annotations; no visibility or bicycle-rack filter.
- The existing maximum same-class one-to-one matching with squared XY distance **<4**.

The numerical target is this selected label table under Reiyah's fixed rules. It is **not the
official nuScenes score**: the SDK has additional distance/point/bicycle-rack filtering and a
different detection evaluation procedure. Completeness of the one label world is a target
definition, not evidence of complete physical coverage. Missing labels, nominal localization
error and missing objects remain possible limitations of this conditional result. The adapter
does not estimate their frequency or generate alternative physical readings.

The mapping and SDK filter semantics were inspected at official devkit commit
`b40adc467b919192899405d9b77871afee8efa07`, retrieved 14 September 2026:
[category mapping](https://github.com/nutonomy/nuscenes-devkit/blob/b40adc467b919192899405d9b77871afee8efa07/python-sdk/nuscenes/eval/detection/utils.py),
[filter implementation](https://github.com/nutonomy/nuscenes-devkit/blob/b40adc467b919192899405d9b77871afee8efa07/python-sdk/nuscenes/eval/common/loaders.py).
Exact source bytes and Apache-2.0 license notice are retained privately in the checkpoint's
`private/primary/LEDGER.json`. Mapping source SHA-256:
`aec85e921c5c89161ae65bec38acd1f72ad48c203f13bceaca4c14a0cd2e2b48`.
The software license does not grant rights to redistribute benchmark data. No annotation,
prediction or sensor payload is included in this public artifact family.

## Command and input contract

```sh
python -B -m tools.perception_annotations \
  --request /absolute/private/request.json \
  --request-sha256 EXPECTED_REQUEST_SHA256 \
  --output /absolute/private/fresh-result
```

The request has exactly `artifact_id`, `version`, `policy`, `inputs`. Its artifact ID is
`reiyah.perception-annotations.request`; the version and policy are given above. `inputs` has
exactly six descriptors: `comparison`, `normalizations`, `catalog`, `common_comparison`,
`renamings`, `metadata`. Each descriptor has `path`, `byte_size`, `sha256`. Supply the original
open normalized comparison and its existing common projection, not a previously compiled
finite comparison. `renamings` is the existing operands custody document containing the
original-to-common detection/anchor mapping. Metadata must independently match the catalog's
source identity.

Inputs are copied into verified unlinked snapshots before interpretation. A missing source,
changed digest, dangling identity, wrong scene/time, duplicate source token, malformed selected
coordinate or oversized object set fails; it never becomes a confident empty reference. An
actually empty annotation population in a fully scanned table can be a finite empty benchmark
world. At most 128 eligible objects per anchor are supported; none are clipped to meet a limit.
Unknown coverage/resource conditions from the inherited compiler can retain open bounds.
Schema and upstream normalization validity remain shared trusted premises as described below.

The output directory must be fresh and outside the source/code directories. It contains:

| File | Meaning |
|---|---|
| `annotations.json`, `source-custody.json` | Selected labels, exact table and original row identities, source joins |
| `dispositions.json` | Included and excluded labels with category and exact squared distance |
| `reference.json`, `compilation.json` | One declared benchmark world and compiler source mappings |
| `comparison.json`, `decision-payload.json` | Common core input and checked matching/cover proof |
| `RESULT.json` | Conditional result, scope and counts; zero human admissions |
| `PACKET.json` | Completion written last; request, output and implementation file digests |

The packet records code identity before and after the replay. It is not a signed scientific
acceptance record. Later verification must select expected packet/source identities separately.

## Validation boundary

The adapter uses the existing source JSON/archive readers, normalization lineage checks,
reference compiler, common projection and core witness checker. The checker establishes graph
matching optimality and loss arithmetic; it cannot establish correctness of label geometry or
physical truth. Upstream prediction-file qualification is separately inherited; detector weights
and inference configuration are not reproduced here.

The first consumer audit scans the original metadata again, resolves literal source-row
identities and reconstructs graph edges without calling this adapter or the reference compiler.
It shares JSON/archive readers and the core certificate checker. Fable's separately owned
comparator receives identical objects and edges. Engine's replay of Fable's existing code is
compatibility evidence, not a separate analyst study or evidence of lower total effort.

```sh
python -B -m unittest tests.test_perception_annotations -v
```

The tests use synthetic data to attack custody, selection boundaries, matching competition,
missing-versus-empty sources, numerical validity and output preservation. They add no human
observations. This adapter is an offline research capability, not a deployment or a new Gate A
release. New preparation definitions require an explicit new policy identity.
