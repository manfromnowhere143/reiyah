# Keep native viewer outputs outside their observation package

Document ID: `reiyah.viewer-custody.checkpoint`; version `0.1.0`; status `exploratory`.

The native viewer CLI now requires `--package`. It checks the located seal against the
separately selected binding, checks that the supplied asset names that package's capture
file, and rejects output inside the observation package or source checkout before invoking
native writers. Binding and selection records remain version 0.1.0. The required CLI argument
is a command-contract change: use the commands below with this source. Earlier checkpoint
commands remain historical instructions for their separately bound implementation.

The change addresses a reproduced custody failure. On 2026-09-13, both preparation and
extraction returned success when directed into a verified synthetic observation package.
Fresh package verification then failed with `OBS_FILE_SET`. The same happened at its root,
in `assets`, through a symlink and through a filesystem case alias: eight cases in total.
The corrected CLI rejects all eight with `VIEW_OUTPUT`, without changing package files.
Private sibling outputs still work and trace a selected point to its exact original record.

## Decision, baseline and limits

The comparator is the existing Blender 5.1.2 adapter, complete observation verification against
an independently supplied expected seal, and direct before/after source inventories. The
synthetic fixture contains two original points; native Blender actually imports, saves,
reopens and extracts a programmatic selection. No new viewer, renderer, planner or labeler
was built. The conventional manual rule to keep output elsewhere allowed all eight invalidating
commands. A second coordinator or duplicate package verifier is unnecessary for this correction.

The small standard-library guard compares the resolved output parent's ancestor identities
with each source directory. Python documents [filesystem identity](https://docs.python.org/3.13/library/os.path.html#os.path.samefile)
in terms of device and inode; this catches the demonstrated aliases that path spelling misses.
Returning the resolved private destination also avoids following a subsequently retargeted
parent symlink. Focused tests isolate that retargeting boundary for both CLI actions using
stand-in writers; the eight mutation probes use actual native Blender writers. Those are
separate forms of engineering evidence.

The source-context check hashes `SEAL.json` and requires the supplied asset to refer to the
same filesystem file as `assets/CAPTURE_ID.ply`. A separate byte-identical copy, a different
capture file or an unrelated package location is rejected. The PLY bytes and all five fields
still undergo the existing exact binding and record checks.

This is not complete package verification. A matching seal alone does not establish the
contents of every member, physical origin, author or truth. The caller must first verify the
whole observation package and select the binding from its manifest. Directory replacement,
mount changes and privileged concurrent mutation are outside the stable-filesystem assumption.
The adapter remains standard-library-only inside Blender; importing the Engine verifier there
would add dependencies to the native runtime. No new schema, service or dependency is added.

## Coordinator procedure

Use the selected Engine Python environment to verify the complete observation package against
its separately retained expected seal. The binding must refer to the same seal and a delivered
LIDAR_TOP capture in the verified manifest; keep its expected hash outside the editable scene.
The existing [binding contract](../../perception-viewer/0.1.0/README.md) describes these records.

```sh
python -B -m tools.perception_observation verify \
  --package /private/observation-package --seal-sha256 EXPECTED_PACKAGE_SEAL

"$BLENDER" --background --factory-startup --disable-autoexec --python-exit-code 2 \
  --python tools/perception_viewer.py -- prepare \
  --package /private/observation-package \
  --binding /private/binding.json --binding-sha256 EXPECTED_BINDING_SHA256 \
  --asset /private/observation-package/assets/capture-000001.ply \
  --output /private/new-opening-directory
```

Output parents must already exist. Preparation refuses an existing output directory, and
extraction refuses an existing output file. A partial failed output is never reused. A missing
package argument fails argument parsing. A wrong seal fails `VIEW_BOUND`; a different existing
capture file fails `VIEW_PACKAGE`; missing or unreadable files fail closed through `VIEW_IO`.

The person's existing opening, selection and **Save As** procedure does not change. Bind the
submitted scene's exact byte size and SHA-256 separately before extraction, then use:

```sh
"$BLENDER" --background --factory-startup --disable-autoexec --python-exit-code 2 \
  --python tools/perception_viewer.py -- extract \
  --package /private/observation-package \
  --binding /private/binding.json --binding-sha256 EXPECTED_BINDING_SHA256 \
  --asset /private/observation-package/assets/capture-000001.ply \
  --scene /private/submitted-selection.blend --scene-sha256 EXPECTED_SCENE_SHA256 \
  --scene-bytes ACTUAL_INTEGER_BYTE_SIZE --output /private/new-selection.json
```

Extraction is source conformance, not a statement that anyone inspected the evidence. Empty
selection remains `VIEW_EMPTY_SELECTION`, never an empty reference. Original indices stay
zero-based; raw offset is 20i, PLY offset is header_length + 20i. The private custody map retains
the link from the neutral capture to the original source record. Do not disclose that private
map or assisted material during independent unassisted discovery.

## Reproduce and assess

The [reproducer](reproduce.py) accepts a selected source digest and exact Blender binary digest.
It creates synthetic observations in its own temporary directory, runs the native CLI, records
inventories and original-record slices, and removes only those controls. Case-alias probes
explicitly skip on filesystems without that behavior. No real package is a mutation target.
Before and after use the same script bytes; the protected invocation adds `--package` explicitly.

```sh
python -B research/perception-viewer-custody/0.1.0/reproduce.py \
  --source-root . \
  --source-sha256 976f15d1a0be7bf2db0d10ebd3f0668ce922854bde307ea1e7d8b171922661cc \
  --blender "$BLENDER" \
  --blender-sha256 e0b80264bea559673212e0afc819fb33f3cef8b3dcfcc8d994b195132857ac8a \
  --expect protected --output /private/new-viewer-custody-control

python -B -m unittest -v tests.test_perception_viewer
```

For before behavior, run the same script against a read-only checkout of
`ae6a37173897157cd39c073fceb396514a6a3e56`, source digest
`d9f4afac9642ef1811db19724269e95efde0ff8e9144fb1eb9f9395d50f1ebe0`, with `--expect vulnerable`.
Use the pinned observation dependencies and Blender 5.1.2. Runtime/package byte selections,
primary-source custody, process costs and limits are in [verification.json](verification.json)
and the private `engine-viewer-custody-2026-09-13` packet. Native scene bytes and receipts include
run-specific data; only the compact result/source-binding files are candidates for deterministic
replay. Individual native RSS figures are cumulative child maxima, not per-case measurements.

All 20 focused tests and 369 repository tests pass. The prior 93 measurement tests are retained
with all 107 measurement files checked unchanged; they were not replayed for this viewer-only
change. On the same exposed development capture, complete package verification and native
preparation/extraction pass. The 1,651-byte extraction report is identical to the previous one;
its three selected original records independently match raw and PLY slices. All 34,720 records
still pass the existing extraction checks. Preparation took about 1.76 seconds and extraction
1.73 seconds, including startup, while sharing the host. Human time remains unmeasured.

Actual participant interaction, independent human references and external scientific review
remain missing. The supported desktop prerequisite and ready manual exercise are preserved;
no unchanged tool bootstrap was repeated. No physical study, cohort or seed was selected.
Real bounds remain [-8,8]; Gate A is unaccepted. Joint reference alternatives, matching,
weights, loss, tolerance, unknown states and Fable's independently owned work are unchanged.
P005 is operator-reported published; no further publication or outreach is authorized.

The next question is whether the coordinator can select a capture and create its source binding
without manually transcribing identities, using the existing verifier and native viewer. Measure
the steps and challenge incorrect capture/package selections before adding an interface. Actual
participant return takes priority if supplied. No usability or state-of-the-art win is claimed.
