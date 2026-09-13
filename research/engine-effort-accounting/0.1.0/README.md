# Engine command accounting, 0.1.0

This bounded offline audit reconstructs timing arithmetic from the first fourteen closed
Engine checkpoints of the 13 September autonomous window. It is not a human-effort estimate
or an implementation of Fable's comparator. Read the
[question, result and limits](../../../docs/ENGINE_EFFORT_ACCOUNTING_2026-09-13.md).

From the repository root:

```sh
python -B research/engine-effort-accounting/0.1.0/analyze.py
python -B research/engine-effort-accounting/0.1.0/test_accounting.py -v
```

The default input is the adjacent `observations.json`. An explicit positional path selects a
different input; it must declare this version's exact bounded projection. The analyzer writes
only JSON to stdout, or an invalid diagnostic to stderr with exit 2. It performs no network
access or source mutation and has no third-party package dependency. Lists are bounded at
1,000 entries and the UTC scope at one day. Decimal durations are explicit strings, while
missing measurements are null in the result. Missing input fields are invalid, not empty.

The public replay checks structure, declared execution/copy relationships and arithmetic on
the projection. It cannot authenticate private original executions or prove the selection is
complete. Private `extract_receipts.py` and independently structured `check_sources.py` retain
that source comparison under the exact closed checkpoint selection. Their source, transcripts,
the selected original receipts and the initial failed extraction are in the new Engine outbox.

The serious conventional method is ordinary source selection and timeline accounting using
the same records. No advantage over it is established. The 1,024 tiny interval subsets are
synthetic arithmetic controls; the retained command timeline records actual local engineering
commands. Neither is actual participant viewing or independent human reference evidence.

`verification.json` binds the input, repeat output, validation and measured preparation costs.
No absent human time is inferred, and the uninstrumented portions of the selected interval
must not be reported as idle or free work. All effort required for the prospective fair
comparison remains a separate obligation.
