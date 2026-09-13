# Replay local reference identity

Artifact ID: `reiyah.perception-reference-identity.reproduction`; version `0.1.0`; exploratory.

The [checkpoint](../../../docs/PERCEPTION_REFERENCE_IDENTITY_2026-09-13.md) states the changed
decision, proof, failed prototypes, limits and measured costs. All examples are synthetic.

From the repository root, using the selected Python environment and a fresh temporary directory:

```sh
task_baseline_dir=$(mktemp -d)
git show 61d290bb77dca41b9af0198b3254d2d359e32942:tools/perception_reference.py > "$task_baseline_dir/reference.py"
python -B research/perception-reference-identity/0.1.0/reproduce.py --baseline-compiler "$task_baseline_dir/reference.py"
```

The selected baseline commit must already be available locally. The program checks its exact
compiler SHA-256 before importing it and prints deterministic JSON without writing any files.
It compares stable/local names against both compiler versions on the same inputs, checks every
synthetic source mapping and recomputes matchings from original coordinates by partial injections.

Add `--geometry-control` to include the larger actual-cap regression. On the retained machine,
the complete two-compiler replay took 7.718 and 7.768 seconds in concurrent runs and returned
identical 4,219-byte reports, SHA-256
`6a2a39d5b9406c58805753dfca237475826e3c02b8e4336d513518cbd4045ba7`.
This is reproducibility evidence, not a performance comparison between the compilers.

The replay shares the existing synthetic fixture helpers, normalizer, parser and rational
contract. The core checker does not call the producer's matcher; it still trusts those shared
inputs. The tiny direct matcher uses original coordinates and a different exhaustive calculation.
The large geometry case relies on its explicit injection/count proof and preserved old output
bytes. This script checks these selected fixtures, not arbitrary admission reports or physical
reference truth. [verification.json](verification.json) binds the retained sources and runs.

One complete source-to-common synthetic workflow is retained privately under
`~/.codex/reports/reiyah/engine-reference-identity-2026-09-13/private/common-example/`.
It is replayable through `tests.test_perception_reviewed_operands` and is not a human reference.
The sealed own-lane outbox requests only a consumer review of this bounded identity behavior;
no Fable source change or ownership transfer is requested.
