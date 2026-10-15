# Complete-cohort admission, version 0.8.0

The contract preserves the original four images, twelve reference cases and
exact numerical methods. Profile 0 remains the historical 0.5 pair; profile 1 is
the completed 0.7 resource-qualified pair. Only profiles 2 and 3 bind new owned
manifest and consumer-contract paths. The new contract digest and version are
explicit; historical receipts are never rewritten or relabeled.

The new code differs from 0.7 only in version literals and the bound contract
digest. The [preservation record](../NUMERICAL_PRESERVATION.json),
[28 matching controls](../qualification/matching-controls.json) and
[36 resource controls](../qualification/resource-controls.json) qualify this
composition. These 64 software controls belong to the same investigation;
they are not independent scientific replication.

`match_analysis.py` consumes all four complete bundles, verifies source and
resource custody, and calls the unchanged native and conventional matcher on
all twelve cases. `check_matching.py` uses separate coordinate parsing and exact
Edmonds–Karp matching, then independently recomputes G and P. It shares the
admission gate. Source bytes are bound; generated GO text or copied totals do
not authenticate an execution history.

For an authorized exact replay with all required private source records, use
`--input`, `--input-sha256`, `--repository` and a fresh `--output` with the
producer. The checker additionally requires `--result` and `--result-sha256`.
Retain the network-denying sandbox, 120-second and 3-GiB sampled process bounds,
exact runtime audit, no-overwrite outputs and pre/post freeze checks. Both
runtime audits retain explicit unhashed exclusions. The empirical owner is
closed; these source interfaces are not an instruction to restart inference.
