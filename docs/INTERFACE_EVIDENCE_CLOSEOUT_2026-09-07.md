# Evidence-consumer research checkpoint

Document ID: `reiyah.interface-evidence-closeout.2026-09-07`

Version: `0.1.0`

Lifecycle status: `exploratory`

This local continuation extends `9aceb3d1d39b27b54d1fdfe6f91a3828b2cb50c5` on
`research/2026-09-07-interface-evidence`. The private delivery record retains the exact
commit, tree and patch digests after commit/readback. Daniel Wahnich is the sole author
and committer. The active Gate A, Gate B, measurement and console worktrees retain their
owners, files and indexes. Nothing is pushed, merged, published or deployed.

## Completed work

The [interface review](INTERFACE_EVIDENCE_REVIEW_2026-09-07.md) reconstructs the measurement
companion and console's actual evidence paths. It reports seven consumer failure families,
with twelve output rows including four positive controls. The
[source probe](../tools/measure/probe_console_evidence.mjs) executes captured implementations
under fixed mocked responses. The original source result reproduces all specified failures;
that is not an application pass or proof of a compromised live service.

A four-file console repair is prepared privately and binds to unchanged committed source
files at `b316d4bf618cc0e6fbf3b485a23fe94d876623d2`. The repaired probe has fourteen output
rows: six positive controls, five repaired observations and three remaining failure families.
TypeScript `--noEmit` passes against the private copy and installed dependencies. Applying
the patch to a fresh four-file fixture reproduces every prepared file digest. The
[repair record](../evidence/interface-evidence/private-repair-0.1.0.json) names the exact
scope and unresolved F02-F04. This patch is prepared for the console owner; it has not
been applied to that repository, built for deployment or checked in a browser.

The known matcher validation-output defect remains in the historical `reiyah-measure`
companion. A paired synthetic control confirms it there and confirms rejection in the
already-corrected research lineage. No old result is silently rewritten.

The [consumer design](MEASUREMENT_CONSUMER_DESIGN_2026-09-07.md) proposes one typed
measurement/interpretation bundle and a single vertical migration. It uses current TUF
and SLSA primary documentation as engineering prior art. It does not add signing or
publication infrastructure or claim conformance. Raw primary payloads stay private.

## Verification boundary

The process captures and original/repaired outputs are under
[`evidence/interface-evidence`](../evidence/interface-evidence/custody-0.1.0.json).
The [Gate B development check](../evidence/interface-evidence/gate-b-check-0.1.0.json)
records inherited transcript integrity and documentation consistency. It does not replay
every historical experiment or validate the separate console's deployment.

The [development closure verifier](../tools/measure/verify_interface_evidence.py) binds public aggregates to retained process streams,
recompute source and patch digests, check internal links and compare every predecessor
file. Only the README and three navigation documents may differ among inherited files.
All studies, claim registers, empirical transcripts, Gate A release operands and earlier
corrections are preserved. Gate A release evidence and operator acceptance remain unchanged;
operator acceptance is still unaccepted.

One earlier repair probe failed because a test of version binding supplied a coefficient
outside the newly checked interval. Its stderr is preserved; a new in-interval replacement
isolates that failure mode. The final original and repaired runs use the same revised
probe source. The first closure preflight also exposed an incorrect audit expectation that
collapsed `argv_unrecorded_historical` into `not_replayed_here`; the closure now checks
each distinct state against its replay class. No gate checker was changed, no rejection
was weakened and no failed process is counted as a pass.

## Exact private continuation

Start at the canonical Reiyah root, verify repository identity, read its current instructions
and handoff, then inspect this local research branch without switching other sessions'
worktrees. Task custody is:

```text
/Users/danielwahnich/.codex/reports/reiyah/interface-evidence-2026-09-07/
```

`baseline/` exports the parent. `implementation/` holds this candidate. `private/`
contains the read-only source captures, source indexes, `console-repair/`, the four-file
`console-repair.patch`, its exact delta and an isolated patch replay. Its local dependency
symlink is only for TypeScript checking; neither the symlink nor sibling source is a
candidate repository artifact. `checks/` retains every process stream and failure.
`external-sources/` retains the primary HTML privately. The final `delivery.json` and
`committed-readback.json` resolve this checkpoint's Git identity.

From `implementation/`, reproduce the consumer probes with:

```sh
node tools/measure/probe_console_evidence.mjs --task-root ..
node tools/measure/probe_console_evidence.mjs --task-root .. --repair
python3 -B tools/measure/verify_interface_evidence.py --task-root ..
```

The probe requires the captured files and the exact local TypeScript compiler named in
the private additional-capture index. It has no network fallback and rejects changed
source bytes. The typecheck argument vector is retained in the repair record. Do not run
the console's seal, publish, build or live-server scripts to reproduce these source probes.

## Next action

For the interface owner, review the four-file patch against its bound base and complete
the snapshot/receipt migration with the proposed reordering controls and real browser tests.
For the scientific program, the next observation remains independently supported physical
reference evidence. The 240-case study still has no independent human judgments, and the
independent-opportunity pilot remains proposed. This engineering work cannot substitute for
either. The earlier laptop shutdown deadline remains canceled; all processes recorded in
this checkpoint have completed.
