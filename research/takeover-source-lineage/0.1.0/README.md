# Close the TD2D history route and qualify the next source lead

Document ID: `reiyah.takeover-source-lineage`. Version: `0.1.0`.
Lifecycle status: `exploratory`. 15 October 2026.

**The two published simulator branches contain no historical copy of the missing
T500RS controller and no additional Python blob variants beyond the current
snapshot.** The Git-history repair route is closed at the inspected refs. This
narrows the source gap; it does not qualify TD2D outcome timing or invalidate
its original experiment. The completed [500-trial census](../../takeover-outcome/0.2.0/README.md)
remains unchanged. Gate A remains operator-unaccepted.

A separate [next-source screen](next-source.json) examines manD 1.0 documentation
and access conditions. Its purpose is to identify a concrete observation channel
for a new bounded protocol, before any recovery labels or readiness model.

## What the history establishes

| Retained scope | Checked result |
| --- | ---: |
| Advertised public branch heads | 2 |
| Commits in their combined parent closure | 47 |
| Distinct root trees | 45 |
| Git tree objects reconstructed and checked | 175 |
| Recursive entries checked by standard Git | 11,781 |
| Blob paths in current main | 429 |
| Blob paths across the retained history | 454 |
| Python blob variants across the history | 160 |
| Python variants beyond current main | 0 |
| Corruption/incompleteness controls rejected | 8 |

The heads are `main` at `115320f093f40650218f4312381680966ef27528` and
`HAI-lab-KNU-patch-1` at `6a70d3c04abb83baab060319bdc10b0bb9ec05be` in the
[authors' simulator repository](https://github.com/HAI-lab-KNU/L2-vehicle-simulator).
The retained branch list has no next page; both histories reach their common
root with every parent present. Tags and release lists are empty in the retained
responses. The supplementary repository history and initial notebook inventory
were inspected separately; its complete code history is not claimed checked.

The historical snapshots add 29 non-Python path/blob variants, covering README,
changelog and leaderboard website material. They supply no earlier Python
implementation hidden by a later deletion. The only T500RS-named path is
`scenario_runner-0.9.10/manual_control_T500RS.py`, the wrapper already inspected.
Its required `examples.manual_control_T500RS` path does not appear in these trees.
This is a path and identity finding, not execution of an import resolver.

The root README instructs users to install CARLA 0.9.11 and overlay this
repository's files. That describes a dependency; it is not a complete capture
manifest. The original runtime may have included other files or configuration.
Neither these histories nor the prior summary CSVs bind that runtime, exporter,
clock mapping, outcome-monitor termination or censoring to TD2D v2. No statement
is made about private files, unadvertised refs or all possible external sources.

## A concrete next source, with unresolved clocks

The retained [manD release metadata](https://doi.org/10.7910/DVN/SG9TMD) identifies
**manD 1.0, Dataverse version 2.0**, released 24 January 2024, under CC BY 4.0.
The [primary descriptor](https://www.nature.com/articles/s41597-024-03137-y) and
official structure page describe vehicle and environment time-series files.
The released `DataInfoSheet.xlsx` was captured and matched to its advertised MD5;
[next-source.json](next-source.json) binds its SHA256 and exact cell references.

Both `Environment!A1` and `Vehicle!A1` state native acquisition at 20 Hz and supplied
rows at 256 Hz. Upsampling does not establish finer event precision. The `time`
unit cells (`Environment!C3`, `Vehicle!C4`) are empty. Actual units, clock origin,
interpolation, cross-file alignment and recording termination still need checking.

The dictionary distinguishes environment codes 5 (takeover situation) and 6
(accident) from vehicle interaction codes 3 (takeover request), 12 (end-of-ride
message) and 13 (accident-detected message). An interaction message, a scripted
scenario event and a measured ego-vehicle collision must remain separate.
Neither an end message nor a file ending proves complete follow-up. The distance
sentinel 99000 also requires an explicit unavailable state.

No participant records were acquired. The 50 participant archives range from
59,858,301 to 1,612,101,312 bytes, exceeding this owner's 2 MiB per-response cap.
Next, inspect the small coverage workbook and extraction source under a fresh
bounded protocol, then establish whether vehicle/environment-only extraction is
feasible. Freeze selection and resource bounds before opening outcomes; do not
choose a short archive as a substitute for verified scenario coverage. This is a
qualified documentation lead, not qualified outcome timing or an admitted model.

## Evidence and conventional reference

The [inventory](inventory.json) contains derived Git tree metadata and API-derived
commit relationships, with exact source SHA256 bindings. [The auditor](audit.py)
reconstructs each Git tree object, checks its SHA1 identity, rejects missing
parents/subtrees and enumerates every retained root. It reports all extra blob
variants in [result.json](result.json).

[The conventional reference](git_check.py) writes only tree metadata into a fresh
temporary bare Git store, then uses Git `hash-object` and `ls-tree` to check all
175 objects and all 45 recursive inventories. [Its result](git-verification.json)
agrees with the Python reconstruction. No upstream code or participant payload
is executed. This is integrity checking within one investigation, not independent
scientific replication or a novelty/work-saving claim.

[Eight controls](controls.json) exercise corruption, omitted objects/parents,
false complete-entry counts, missing root evidence, cycles and duplicate JSON
keys. An initial seven-control run omitted a head rather than an internal parent;
review corrected that control and added an explicit valid-format corrupt object
ID. The final runner also asserts each exact rejection reason. All earlier code and
outputs remain in private custody. The source inventory and scientific conclusion
did not change.

## Reproduce offline

Python 3.10 or newer; Git is needed only for the conventional check. Use a fresh
output directory. No network is needed:

```sh
reiyah_study=research/takeover-source-lineage/0.1.0
reiyah_run=/absolute/path/to/new-run
mkdir "$reiyah_run"
python3 -B "$reiyah_study/audit.py" --inventory "$reiyah_study/inventory.json" \
  --output "$reiyah_run/result.json"
python3 -B "$reiyah_study/git_check.py" --inventory "$reiyah_study/inventory.json" \
  --output "$reiyah_run/git-verification.json"
python3 -B "$reiyah_study/controls.py" > "$reiyah_run/controls.json"
cmp "$reiyah_run/result.json" "$reiyah_study/result.json"
cmp "$reiyah_run/git-verification.json" "$reiyah_study/git-verification.json"
cmp "$reiyah_run/controls.json" "$reiyah_study/controls.json"
```

The retained validation denied network before Python started and denied writes
to the input projection. Git tree identity is checked; commit identity/signatures
are not independently reconstructed. Commit dates and parent links remain
API-derived observations. Public metadata and passing checks confer no scientific,
measurement, acceptance or publication authority.

## Source custody and disposition

[Custody](source-custody.json) records exact captures, byte limits and eligibility.
The HAI Lab author page links the simulator and supplementary repositories. Credit
for those sources remains with their authors; this packet publishes authored
analysis and derived inventory metadata, not upstream code, PDFs or HTML.
No complete repository license is asserted. Original payload stays private.

An organization-list request returned HTTP404 because the account endpoint was
inapplicable; it supports no absence claim. A related-study PDF exceeded the
2 MiB response cap; the retained prefix is incomplete and evidence-ineligible.
Neither failure was retried under a larger cap or silently discarded. Historical
TD2D failures and costs remain preserved. [Provenance](provenance.json) distinguishes
source requests, validation, publication and unmeasured effort.

The [decision](DECISION.md) closes this history route. Reopen TD2D timing only for
a materially new release-linked capture/export or outcome-monitoring artifact.
For the next source, qualify event coding, clock resolution, coverage and censoring
on actual permitted records under a fresh protocol. Documentation alone cannot
admit a recovery endpoint or readiness model. No outreach, training, inference,
private participant ingestion or operational claim is part of this step.
