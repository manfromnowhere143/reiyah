# Resource-qualified pair consumer, 0.1.0

`check_pair_resource.py` wraps the unchanged 0.6.0 numerical checker. It does
not import the worker or run a model. All files belong to the new owner; old
source and failed outputs remain unchanged. The separate wrapper identity is
reported honestly. A downstream matching gate must qualify this composition,
not silently pretend that the wrapper is the old checker.

Run in the original audited virtual environment:

```
python -B consumer/check_pair_resource.py --owner OWNER \
  --contract OWNER/consumer-contract.json --contract-sha256 SHA \
  --freeze-sha256 SHA --report OWNER/review/PAIR_CHECK.json
```

The contract has exactly these keys:

```json
{
  "artifact_id": "reiyah.multiorg.resource-consumer-contract",
  "version": "0.1.0",
  "sources": {
    "supervisor": {"path": "ABSOLUTE_OWNED_PATH", "sha256": "cc275f8ca48eb832001ca78be8d8614f7c74f2dfd228139551d8c94f449ec698"},
    "worker": {"path": "ABSOLUTE_OWNED_PATH", "sha256": "7b2991f6b68719d815afc8137e563fc6d12e868689132850c9b9a483d957de1e"},
    "numerical_checker": {"path": "ABSOLUTE_OWNED_PATH", "sha256": "2cefacc5c6fef3e6c61ae944b16d4d23542ea7cbe03d47773604f808e124a431"},
    "manifest": {"path": "ABSOLUTE_OWNED_PATH", "sha256": "EXACT_SHA256"},
    "protocol": {"path": "ABSOLUTE_OWNED_PATH", "sha256": "EXACT_SHA256"},
    "capacity_plan": {"path": "ABSOLUTE_OWNED_PATH", "sha256": "EXACT_SHA256"},
    "runtime_before": {"path": "ABSOLUTE_OWNED_PATH", "sha256": "EXACT_SHA256"}
  },
  "paths": {
    "output": "ABSOLUTE_OWNED_OUTPUT_DIRECTORY",
    "outer": "ABSOLUTE_OWNED_OUTER_JSON",
    "stdout": "ABSOLUTE_OWNED_SUPERVISOR_STDOUT",
    "stderr": "ABSOLUTE_OWNED_SUPERVISOR_STDERR",
    "runtime_after": "ABSOLUTE_OWNED_RUNTIME_AFTER_JSON",
    "freeze": "ABSOLUTE_OWNED_FREEZE_JSON"
  },
  "python_entrypoint": "EXACT_AUDITED_VENV_ENTRYPOINT",
  "outer_wall_limit_seconds": 660
}
```

Placeholders are not valid inputs. The prospective freeze has a `bindings`
mapping of owner-relative filenames to exact `{sha256,bytes}` objects. It must
bind this contract, both consumer Python files and every named source, including
the runtime-before report. The freeze digest is supplied externally to avoid a
circular self-hash. All its bindings are checked before and after admission.
The numerical checker's exact sibling helpers must be present unchanged.

The outer launcher records exactly:

```json
{
  "artifact_id": "reiyah.resource-admission.outer-execution",
  "version": "0.1.0",
  "returncode": 0,
  "timed_out": false,
  "wall_seconds": 0.0,
  "command": [],
  "freeze_sha256": "EXACT_SHA256",
  "supervisor_sha256": "EXACT_SHA256",
  "manifest_sha256": "EXACT_SHA256",
  "stdout_sha256": "EXACT_SHA256",
  "stderr_sha256": "EXACT_SHA256",
  "worker_log_sha256": "EXACT_SHA256",
  "worker_log_bytes": 0
}
```

`command` must be the exact supervisor invocation, in this argument order:
`PYTHON -B SUPERVISOR --owner OWNER --manifest MANIFEST --runner WORKER
--runner-sha256 WORKER_SHA --python PYTHON --output OUTPUT --capacity-plan PLAN
--capacity-plan-sha256 PLAN_SHA`. The consumer derives this command from the
contract instead of accepting a different self-consistent command. Successful
stderr must be empty; stdout must contain one JSON object exactly equal in
canonical form to the retained receipt.
The outer launcher binds the worker log's exact bytes immediately after the
supervisor exits; a current same-size replacement cannot silently pass that pin.

Acceptance requires outer exit zero without timeout, published complete receipt,
no remaining pending receipt, persisted true, child exit zero, no stop, original
system observation providers, unchanged bindings, exact journal/result/policy
hashes and a complete resource sample sequence. It independently recomputes the
sample resource arithmetic, peak RSS, clock/phase/PID relationships, gaps,
durations, bounds, prelaunch window and final output inventory. Missing,
truncated, mismatched, errored or unknown samples refuse admission.

Runtime-before and runtime-after reports must match exactly except `at` and
report no failures or unrecorded files. The consumer hashes the current declared
installed files, RECORD files and interpreter/config pins. It does not repeat
the audit's entire unrecorded-file census or authenticate excluded bytecode,
system libraries and all dynamic execution. The consumer's own executable and
virtual environment must match the audited interpreter/environment before the
numerical checker imports its scientific libraries.
The two report paths must be distinct and cannot alias frozen inputs. Their
timezone-aware timestamps must be strictly ordered and enclose the resource
samples. This checks declared chronology; it does not authenticate the clock.

After those checks the actual unmodified receipt is passed to the unchanged
numerical checker's `verify_output`, with its normal `bind_inputs` reconstruction.
No synthetic legacy receipt is created. Success reports artifact
`reiyah.multiorg.resource-qualified-pair-check`, version `0.1.0`, with distinct
`consumer_sha256`, `resource_gate_sha256` and `numerical_checker_sha256` fields,
the original numerical result nested under `numerical_result`, and exact source,
input, output, outer, runtime and journal bindings.

These are consistency and declared-byte checks within the same assisted study.
A wholly fabricated self-consistent execution history is not authenticated by
hashes. Neither sampled capacity nor this adapter reserves shared APFS space,
guarantees resource bounds between samples, establishes independent scientific
replication, supplies reference matching, or authorizes another inference run.

## Authored replay

`test_resource_consumer.py` covers the resource and file-custody gates.
`test_integration.py` passes an authored two-tile, two-model packet through the
actual unchanged numerical checker, including all 70 raw arrays and global NMS.
Only `bind_inputs` is replaced by that explicit fixture context; no empirical
source is accepted by the test. It also checks that outer failure prevents the
numerical call, altered raw bytes fail, and unreported output files fail.

Both tests operate offline. The integration test requires the existing numerical
test dependencies and unchanged published 0.6.0 support files. Portable paths
can be supplied explicitly:

```
python -B consumer/test_resource_consumer.py
python -B consumer/test_integration.py --support PATH_TO_0.6.0 \
  --supervisor PATH_TO_0.6.1/monitor/supervise.py
```

The first integration development replay reached and passed numerical checking
but failed final report assembly because the authored context omitted
`input_reconstruction`. The fixture now labels that field explicitly as an
authored context; the earlier failure remains retained. This was not an
empirical failure or a relaxed production check.
