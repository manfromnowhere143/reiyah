# Original-world partition conformance, 0.1.0

This offline, explicitly synthetic audit checks the selected compiler against ordinary
original-world graphs and maximum partial injections. Read the
[question, finite scope and failures](../../../docs/PERCEPTION_PARTITION_CONFORMANCE_2026-09-13.md).

From the repository root:

```sh
python -B research/perception-partition-conformance/0.1.0/test_conformance.py -v
python -B research/perception-partition-conformance/0.1.0/reproduce.py
```

The complete run emits 5,400 compact JSON case rows followed by one summary. The summary's
`case_rows_sha256` covers the preceding rows, including their newline bytes. A cost pilot can
use `--limit 48`; its summary explicitly says the declared grid is incomplete. `--case 192`
expands a selected case to full original inputs, synthetic source bodies, compiled graph,
compilation receipt, checked core packet and direct original-world graphs. Case 192 uses
partitions 0 and 8, the separate and fully merged groups, with equal weights; its joint loss
is [0,0]. The pair with unequal weights is case 193 and gives [-1/3,1/3]. Limits and indices
outside this declared grid are rejected; no cases are sampled or silently skipped.

The program writes only stdout/stderr and uses no network or third-party package installation.
It imports the existing test fixture's input construction, normalization and source encoding,
plus the selected compiler and core producer/checker. Those are shared trusted code. The
source audit builds edges and computes matching cardinalities independently of compiler edge
construction and the core augmenting-path algorithm. It parses known canonical rational
fields directly with `Fraction`; production input admission remains a separate contract.
The core checker is invoked with the producer's matching-certificate function disabled.

`verification.json` binds the generator, tests, selected tool/test sources, initial failed
auditors, fault controls, complete output and local command costs. Private retained transcripts
include every case row, and eight indexed examples retain full operands and outputs. Inputs
and source bodies for any other row reproduce from its deterministic recipe and the bound
generator. No generated body is presented as an actual human judgment or a physical capture.

This validates representation within the declared tiny grid. It is not a model of permitted
reference errors, a review ordering method, an effort estimate or an official benchmark score.
No Fable source or interface change is requested. The actual two-window enclosure remains
[-8,8]; independent human references and participant observation remain missing.
