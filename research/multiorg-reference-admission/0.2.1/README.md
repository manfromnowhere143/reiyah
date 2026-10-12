# Supervisor correction, checked without model inference

Artifact ID: `reiyah.multiorg.supervisor-correction`, version `0.2.1`.
12 October 2026. Authored-worker qualification; no empirical retry.

**The supervisor now runs outside the operating-system sandbox, while the
unchanged numerical worker enters network denial before Python starts.** This
allows the host to monitor the worker's memory without granting network access
to the numerical process. The [failed first attempt](../0.2.0/README.md) and
original numerical runner remain unchanged.

[Seven controls](correction.json) pass: normal completion with RSS observation,
wall-time termination, memory-threshold termination, denied worker networking
with working host observation, retained nonzero exit, pre-spawn hash rejection,
and preservation of the selected virtual environment. A review caught a venv
symlink-resolution error before any empirical retry. The follow-up control also
needed to compare macOS `/var` and `/private/var` by resolved identity; the earlier
assertion failure is retained. The original executable spelling is still checked.

[supervise.py](supervise.py) verifies the numerical runner, manifest, source and
policy bytes, then creates only the declared worker. It retains completion and
failure receipts and terminates that exact PID when required. The numerical
worker keeps the original scientific protocol, preprocessing, model pair,
reference policy and output contract. This correction is process supervision,
not a detector or scientific-method change.

The default monitor samples every 0.2 seconds. RSS and wall termination are
sampled controls, with additional process-inspection latency; they are not an
instantaneous hard memory or time bound. RSS covers the owned worker PID, not
an arbitrary descendant process tree. The child additionally receives a CPU
limit of `ceil(2 × wall_seconds)` with a two-second hard-limit allowance, and
a 64 MiB per-file output limit. The frozen numerical worker does not start
child processes. No stronger general process-containment claim is made.

Run the authored controls on macOS from outside a process-restricting sandbox:

```sh
python3 -B research/multiorg-reference-admission/0.2.1/test_supervise.py
```

For a separately recorded future empirical attempt, preserve the retained
numerical runner and qualified virtual environment, rehash the existing sources,
and invoke this supervisor from the host with explicit `--owner`, `--manifest`,
`--runner`, `--runner-sha256`, `--python` and a new `--output` directory. The worker
receives network denial through the bound policy. Do not wrap the host supervisor
in the policy that caused the original failure.

No real model ran under this correction in this owner. Actual ONNX compatibility,
complete paired output, native comparison and the four-image reference-coupling
endpoint remain unverified. The next experiment uses the same first whole image
and pair; it does not restart source discovery or change the cohort.
