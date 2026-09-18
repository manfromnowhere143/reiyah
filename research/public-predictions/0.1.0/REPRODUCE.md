# Reproduction and verification

Version `0.1.0`. These are development commands. They do not invoke the
historical Gate A release machinery or read outcome-reserved material.

Run synthetic controls from this directory with Python 3.14 and NumPy available:

```sh
python -B -m unittest discover -s . -p 'test_*.py' -v
```

The actual export also requires the byte-bound public checkpoints, retained
Ultralytics 8.4.155 source, PyTorch 2.10.0, torchvision 0.25.0, OpenCV 4.13.0 and
the remaining exact private wheel/runtime bindings. The projection phase uses
the held nuScenes devkit 1.2.0 environment, its retained wheel and the bound
metadata archive. A name/version alone is not the original runtime binding.
The complete input/runtime identities and command environments are retained
privately in `FALLBACK_RUNTIME_BINDING.json`, each export request and the
launch receipts. The public test suite uses synthetic inputs; it cannot
substitute for source-image custody or repeat the empirical result by itself.

The allocation, source imagery, cached outputs and oracle answers are not in
Git. An authorized custodian needs the complete owned continuation packet
`value-10h-2026-09-18-c1y8k9yc`, including `sources`, `results`, `private`,
`logs`, the existing linked source/runtime files and the exact candidate tree.
Released freezes bind absolute local files. Relocating or changing them needs
a separately retained reproduction binding, not silently rewriting the original.

The acquisition stage retains 112 physical request receipts and every available
body. `admission.py` validates complete prediction membership, explicit state,
geometry, dimensions, categories and settings. Semantic source qualification
remains a separate obligation. `local_export.py` accepts a request file, its
expected digest and a fresh output directory; it checks its frozen allocation
and cumulative inference ledger. It is intentionally specific to this bounded
experiment, not a general inference service.

`project_reference.py` takes `--allocation`, `--archive`, `--sdk-wheel` and
`--output`; `prepare_comparison.py` takes the owned continuation root. It reads
the two final local stages and the projection, requalifies exact-decimal height
eligibility, and writes separate visible/oracle packets. Its original output
is `private/comparison-01`. Do not overwrite it. The corresponding
`PROTOCOL_FREEZE.json`, `FREEZE.json` and `ANALYSIS_FREEZE.json` retain each
pre-execution boundary, with original failures alongside completed runs.

For a fresh assay using unchanged retained bindings, from the repository root:

```sh
REIYAH_COMPARISON=/path/to/owned/private/comparison-01
python -B research/public-predictions/0.1.0/experiment.py --run "$REIYAH_COMPARISON" assay-reproduction-01
python -B research/public-predictions/0.1.0/replay.py "$REIYAH_COMPARISON" assay-reproduction-01
```

Use the selected existing Python environment and macOS `sandbox-exec` worker
boundary recorded in the original receipt. The trusted service parent starts
outside an outer sandbox; each worker enters its own policy, with private-read
and network-denial probes before querying. The parent uses local bound files.
The first attempt to nest sandbox policies failed before any scored query and
is retained as `assay-01`; the completed original is `assay-02`.

The full-answer analysis deliberately references the original `assay-02`
results and its separate analysis freeze. With a fresh run name:

```sh
python -B research/public-predictions/0.1.0/analyze_results.py "$REIYAH_COMPARISON" analysis-reproduction-01
python -B research/public-predictions/0.1.0/verify_full_answers.py "$REIYAH_COMPARISON" analysis-reproduction-01
```

The scripts refuse to overwrite existing result/verification records. Their
science fields are deterministic; timings, timestamps and resulting byte
digests are execution-specific. New execution is internal reproduction, not
independent scientific replication. The current retained verification already
checks the completed original; do not repeat unchanged runs to create a
larger sample count or pad duration.

`report_results.py --area OWNED_ROOT --output FRESH_REPORT_DIR` extracts the
876 scored rows, 219 full-answer rows, summary and known-cost snapshot after
checking the retained verification/result bindings. It publishes no raw
reference or prediction geometry. Cost receipt names are private navigation,
not claims that the receipts are distributed. A later cost snapshot must state
its cutoff; it cannot stand for the entire ongoing session's economic cost.

The default repository research consistency command, through the selected
existing runtime with its already installed dependencies, is:

```sh
python -B tools/measure/gate_b_check.py
```

Retain exit codes, output and first failures. No training, paid compute, new
population, reserved outcomes, weakening of controls or historical Gate A
acceptance follows from these commands.
