# Open a source capture at the declared anchor time

Document ID: `reiyah.engine.anchor-opening`

Version: `0.1.0`

Lifecycle status: `exploratory`

The existing viewer can prepare the unique delivered LIDAR_TOP capture whose declared timestamp
equals the first development window's anchor. All **34,720 original point records** match its PLY
body byte for byte. Saved programmatic selections preserve original indices, including after
vertex reordering. Actual interactive viewing and participant usability remain unobserved.

This changes the opening procedure, not the Engine's runtime or reference interface. The real
comparison remains **[-8,8]**, no human reference has been admitted and Gate A is unaccepted.

## Decision and source selection

The earlier exercise opens the first capture in this window, **1,998,383 microseconds before**
the declared anchor. Whole-capture identity alone does not communicate that temporal separation.
The stronger bounded route here is a better specified observation through the existing viewer,
with a complete observation index. Another renderer or planner is not needed for this question.

The selected sealed development package contains **725 captures and occurrences across two
windows**, all delivered. The private index lists all of them, retaining signed microsecond
offsets, channels and evidence states. The criterion was explicit: in the same window as the
earlier exercise, require one delivered LIDAR_TOP occurrence with exactly zero declared offset.
Missing or ambiguous matches would leave this procedure unresolved; no nearest-time substitution
or detector-result ranking is permitted. The criterion yields `window-0001/capture-000041`.
The other window and all surrounding observations remain available and unchanged.

Separately selected private custody bytes link this occurrence to its original capture. The
declared capture and anchor timestamps and sample identities agree. This establishes a metadata
join, not physical clock accuracy, simultaneous acquisition of every return, motion compensation
or an object correspondence. Original sensor coordinates remain unchanged. The package is already
exposed development material; its manifest phase cannot turn this exercise into independent discovery.

The serious comparator is manual lookup in the same complete verified manifest, followed by the
same source check and native opening. No human-effort advantage has been measured. The procedure
does not prioritize review questions or duplicate Fable's comparator, planner or error-model work.

## Working procedure and verification

The private packet is `~/.codex/reports/reiyah/engine-anchor-opening-2026-09-13/`.
Its `private/opening/OPENING.md` gives the concrete File > Open, visible selection and Save As
procedure, the source context, exact scene/binding digests and a separate return location:
`~/.codex/reports/reiyah/engine-anchor-input-2026-09-13/`. The observation form is an unfilled
template, not a participant record. The older opening and its pending return path are preserved.

The existing [preparation command](../tools/perception_viewer_preparation.py) verifies the package
and creates the existing binding. The existing [native adapter](../tools/perception_viewer.py)
prepares the scene through Blender 5.1.2, build `ec6e62d40fa9`, in background mode with factory
startup and automatic script execution disabled. No desktop bootstrap was retried and no GUI
operation or screenshot was performed through these commands.

The existing [native probe](../tests/blender_perception_viewer_probe.py) exercises 17 controls on
this capture. The pristine scene has no selection; save/reopen retains original indices
`[0,17360,34719]`; reversing every vertex retains those same indices and records. Changes to
unselected coordinates, intensity or ring, original indices, topology, transforms, capture or
binding identity, modifiers and embedded text are rejected. A separate practical control submits
the older scene against the new binding: `VIEW_BINDING` rejects it without creating an output.

The native probe uses the adapter's own verifier. It is not an independent implementation of
every scene premise. Separately structured checks compare the entire PLY body with the original
raw capture and slice the selected report records directly from that original file. Each record
is 20 bytes; original index `i` maps to raw byte offset `20*i` and PLY byte offset `164+20*i`.
This is record custody, not evidence that any selected point belongs to a particular object.

## Costs, retained failure and limits

[Machine-readable verification](../research/perception-anchor-opening/0.1.0/verification.json)
binds the source, runtime, outputs, controls and measured command costs. The full occurrence audit
took 3.399 seconds, source/body and binary verification 0.228 seconds, package-to-binding preparation
3.382 seconds, native preparation 3.093 seconds, the successful native probe 2.151 seconds and
the stale-capture control 1.217 seconds. The highest observed child RSS among these commands was
274,563,072 bytes. These are single local command measurements, not a comparative performance result.

The first probe command mistakenly retained the adapter script argument and exited during argument
parsing, before creating probe output. Its command and failure are retained; a fresh command selects
the probe directly. It cost 1.049 seconds. The adapter and expected controls did not change. Blender's
standard-locale fallback messages remain in the captured streams. Preparation, diagnosis, authoring
and checking effort is not exhausted by process elapsed time; human review time is unmeasured.

No production code or tests changed. The earlier 399-test repository run, the subsequent twelve
fixture-module tests and 93 measurement tests remain separately bound retained evidence; they were
not replayed here. This checkpoint's fresh checks concern the selected actual capture, with
programmatically constructed selections. Original and derived capture payloads remain private.

The next falsifier is one actual opening, visible selection and saved return checked against this
exact source. Record unreadable displays, ambiguous selections, interruptions, help and unmeasured
time honestly. Preserve both analysts' independent discovery stages before later assistance.
Neither an automated selection nor this exposed exercise admits a human reference interpretation,
establishes physical truth or measures an advantage over a competent analyst.
