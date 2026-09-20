# A public source candidate for physical clearance evidence

Document ID: `reiyah.physical-source.report`. Version: `0.1.0`.
Status: exploratory source qualification; physical experiment blocked.

7V-Scanario is a concrete candidate for Reiyah's geometry-and-motion input
contract. This investigation pins its public documentation, dataset inventory
and manufacturer precision/timing context. It does **not** admit a physical
clearance benchmark. No trajectory, mesh or sensor archive was downloaded, and
no physical, simulation or deployment case ran. Missing numerical bounds remain
JSON null, never zero. All 1,433 reserved images remain closed.

The useful result is an exact path from the existing conditional calculation to
a measurable experiment. The [contract](CONTRACT.md) specifies how measured body
geometry, pose error and rotation affect projected bumper clearance; it also
separates a deterministic envelope from statistical whole-trajectory coverage.
The [smallest useful extract](minimum-extract.json) names the missing records.
Daniel need not possess private team records. No request was sent to anyone.

| Requirement | Result of this bounded review |
| --- | --- |
| Source identity | Paper, documentation, dataset revision and captured bytes pinned. |
| Two-actor numeric samples | Unmeasured here; all 34 listed archives exceed current caps. |
| Both body geometries and residual errors | Unresolved; actual footprint/transform records not inspected. |
| Applicable pose uncertainty | Unresolved; manufacturer statistics are not hard error bounds. |
| Dataset clock residual | Unresolved; a generic navigation timing statement is insufficient. |
| Motion between observations | Unresolved; high-rate interpolation does not establish a physical rate bound. |
| Statistical whole-horizon alternative | Unresolved; joint calibration/coverage records not obtained. |
| Transformed data distribution | Unresolved; source terms and permitted extract form need exact binding. |

The metadata lists 37 files, including 34 archives totalling 985,337,261,632 bytes.
The smallest is 1,070,666,248 bytes; INS alone is 1,490,317,000 bytes. These are
host-declared inventory facts, not measurements of downloaded archive contents.
No blanket absence claim is made about archive members, other public exports or
the authors' calibration records. See the [source review](SOURCES.md) for exact
versions, limitations, conflicting documentation and terms.

## What the checks establish

The offline audit binds 14 primary captures and three derived text files. It
checks inventories, four Git blob identities, source receipts and the review's
claim limits. Eight rejection controls target false physical promotion, unknown
coercion, omitted timing requirements, unknown properties and broken custody.
Two additional mutations check the frozen review and code bindings. These are
artifact checks; there is no conventional arm, A/B tie, new physical accuracy
estimate, independent calibration check or workflow advantage claim.

The exact frozen inputs/code and current check results are named in
[freeze.json](freeze.json), [audit-result.json](audit-result.json),
[controls-result.json](controls-result.json) and [validation.json](validation.json).
[PLAN.md](PLAN.md) states the allocation and limits. Later private publication and
cost receipts close the increment; public distribution is not operator acceptance.
Gate A remains operator-unaccepted, and historical validation identities are
not counted as new replay evidence.

## Reproduce the bounded audit

The primary bodies and receipts stay in the owner's `private/sources` directory,
whose exact file identities are published in [sources.json](sources.json).
The owner is `~/.codex/reports/reiyah/physical-source-2026-09-20-vgy6sjik/`.
With its pinned Python, supervisor and owner record, the retained command is:

```text
PY -B OWNER/private/supervise.py audit-01 checking PY -B \
  research/physical-source/0.1.0/audit.py \
  --sources OWNER/private/sources --freeze-sha256 FREEZE_SHA256 \
  --output OWNER/private/audit-01.json
```

`PY`, `OWNER` and `FREEZE_SHA256` are literal placeholders for the pinned runtime,
owner path and full freeze digest. Use a new command name/output for a new replay;
retained command directories are immutable. The controls use `controls.py` with
the same arguments and a distinct output. The supervisor denies network before
the child runtime. Missing private bodies must fail, not fall back to URLs.
These commands are development checks, not Gate A release validation.

The next useful action is public compact-extract qualification, or a distinct
public source with independently usable uncertainty records. Freeze an exact
actor/window selector before observing future numeric results. Do not expand the
monitor or rerun closed examples to compensate for unavailable measurements.
