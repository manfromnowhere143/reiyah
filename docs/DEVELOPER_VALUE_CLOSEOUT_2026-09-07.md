# Developer-value research closeout

Document ID: `reiyah.developer-value-closeout.2026-09-07`

Version: `0.1.0`

Lifecycle status: `exploratory`

This local research revision extends commit `9d8a18eab7144bd02b1f64c41bc8f179f32ee653`
on `research/2026-09-07-developer-value`. Its exact final commit, tree, changed-file inventory,
author and readback are recorded in the private task root's `delivery.json`. The canonical
Gate A worktree and concurrent Gate B worktree are not switched or integrated by this delivery.
The branch is a local candidate; no push, publication or external outreach was performed.

## Completed work and what it establishes

The [sibling review](SIBLING_RESEARCH_TRANSFER_2026-09-07.md) inspects selected, exact Git
blobs from Sentinel, Telos and Inbar and independently recalculates their named results. It
identifies experimental controls worth adopting, not grounds for a codebase merger. Its
32 retained source blobs remain private, and the report states the limited inspected scope.

The [portable auditor](REFERENCE_AUDIT_DEMO_2026-09-07.md) is an offline, standard-library
tool with an authored synthetic example. It distinguishes a supplied evaluation reference,
excluded annotations, unmatched predictions and unavailable references, emitting exact
proximity witnesses. Supplied coordinates, alignment and membership remain assumptions.
The tool never promotes proximity into physical correctness or object-existence knowledge.

The [real-data replay](REFERENCE_AUDIT_REAL_DATA_2026-09-07.md) reproduces AO's retained
reference-population correction. A separate complete-frame comparison exposes 66 frames
outside the object-row cache. The frozen probability sample remains cache-conditioned and
unchanged. An independently written spatial-index calculation agrees on all 222,902 retained
prediction classifications. Source construction is shared, so this is numerical corroboration,
not independent truth or new sensor inference.

The [developer-access investigation](DEVELOPER_ACCESS_RESEARCH_2026-09-07.md) compares
existing evaluation workflows and the versioned July 2026 MCP specification. It proposes a
test of external engineer value against competent, equally informed baselines. No transport,
latency, adoption or scientific-novelty advantage has been established. A service deployment
would not resolve the current empirical uncertainty.

## Validation and its limits

The [verification record](../evidence/developer-value/verification-0.1.0.json) binds the
executed code, schema, aggregates and process captures. The 12 portable-auditor tests and
7 adapter tests pass. Controls include unavailable references, excluded annotations, exact
threshold boundaries, invalid input, changed input bytes and frame-census disagreement.
The verifier also reaggregates the selected sibling results, checks private source/output
digests, binds the real-data report's two numerical tables and rejects a changed-count example.

The [Gate B development check](../evidence/developer-value/gate-b-check-0.1.0.json) checks
all retained transcript digests, the current claim register, admitted source custody,
documentation links and the inherited result-document checks. It does not freshly replay
the 52 inherited experiments. No passing development check constitutes Gate A release evidence.

The verifier confirms 748 protected release files and the scientific claim register remain
byte-identical to the parent snapshot. The frozen reference-study protocol, selection,
released manifests and replay manifest are preserved. Gate A operator acceptance remains
`unaccepted`; this revision does not change that state.

## Exact local verification and resumption

Begin a new session at `/Users/danielwahnich/workspace/reiyah`, read its current `AGENTS.md`
and handoff, and check the active worktrees before changing anything. Resolve the research
ref with:

```sh
git rev-parse research/2026-09-07-developer-value
git show --stat research/2026-09-07-developer-value
```

The task export is under:

```text
/Users/danielwahnich/.codex/reports/reiyah/developer-value-2026-09-07/
```

From that export's `implementation/`, the following commands replay local development
checks against the retained private evidence. They do not regenerate or overwrite the
completed empirical runs:

```sh
python3 -B tools/measure/reference_population_audit.py research/reference-audit/0.1.0/demo.json
python3 -B -m unittest discover -s tools/measure -p test_reference_population_audit.py -v
python3 -B -m unittest discover -s tools/measure -p test_reference_replay_adapter.py -v
python3 -B tools/measure/verify_developer_value.py --private-root ../private --baseline-root ../baseline
```

The core tool and two test modules use the Python standard library. The development
verifier requires `jsonschema`; the numerical comparator and inherited Gate B checker also
use the recorded scientific Python environment. The retained captures name the exact
interpreter and versions used. An arbitrary replacement environment is not identical replay.

The completed empirical runs have final result files and successful supervisor captures;
none needs a continuing laptop process. Private inputs, bundles, reports, sources and
review packets are retained on disk. The temporary cloud reader and cloned disk from the
preceding study were deleted at its recorded closeout; this revision created no cloud resources.
The original GPU was last observed stopped in that earlier closeout, not newly queried here.

The [continuation ledger](RESEARCH_CONTINUATION_2026-09-07.md) identifies every pending
task. The next scientific observation is two independent blinded reviews of the already
prepared 240 cases. There are zero human judgments at this checkpoint. Physical-performance
estimates remain null; software checks and multiple model responses cannot supply those
observations. An independently selected external pipeline can separately test the narrower
evaluator-scope value proposition if an outside evaluator becomes available.
