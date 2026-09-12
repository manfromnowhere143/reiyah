# Trace a native point selection to its source

Interface ID: `reiyah.perception-viewer`; version `0.1.0`; status `exploratory`.

The [adapter](../../../tools/perception_viewer.py) prepares a native Blender point scene
and checks a saved selection against separately bound source bytes. A reviewer uses ordinary
vertex selection and **Save As**; no add-on, embedded script, console command or new viewer
is needed. The [opening procedure](OPENING.md) is prepared but has not been observed through
the GUI. Background save/reopen conformance is distinct from interactive or human usability.

The baseline is Blender's native PLY import with the already retained exact options:
scale 1, scene units off, forward Y/up Z, vertex merging off, custom attributes on.
The adapter adds a persistent `original_index` integer attribute and an external binding.
It does not change observations, infer objects or decide which points matter.

## Source and interface

First verify the neutral observation package using its separately retained seal and
`tools.perception_observation verify`; see its [contract](../../perception-observation/0.1.0/README.md).
The coordinator selects a delivered LIDAR_TOP capture from that verified manifest and creates
this closed binding. Values below illustrate the types, not an actual source identity:

```json
{
  "artifact_id": "reiyah.perception-viewer.binding",
  "version": "0.1.0",
  "package_seal_sha256": "SEPARATELY_RETAINED_64_HEX_DIGEST",
  "capture_id": "capture-000001",
  "asset": {"byte_size": 180, "sha256": "MANIFEST_ASSET_64_HEX_DIGEST"},
  "point_count": 1
}
```

The actual asset size must equal the exact fixed PLY header length plus 20 times the point
count. The binding is limited to 4096 bytes, rejects duplicate/unknown fields and requires
integer counts. Retain its expected SHA-256 outside the editable scene. The adapter checks
the selected PLY against this binding; it does not independently re-admit a package or prove
that a caller-selected seal belongs to it. That remains the preceding package verification
and custody step. Never derive the expected binding from the scene being checked.

Use the installed, separately identified Blender 5.1.2 binary. From the repository root:

```sh
"$BLENDER" --background --factory-startup --disable-autoexec --python-exit-code 2 \
  --python tools/perception_viewer.py -- prepare \
  --binding /private/binding.json --binding-sha256 EXPECTED_BINDING_SHA256 \
  --asset /private/observation-package/assets/capture-000001.ply \
  --output /private/new-opening-directory
```

Preparation checks all five float32 fields against the original PLY body, retains the
identity transform, creates no edges/faces, deselects every point, and saves in vertex Edit
Mode with an orthographic top view and X-Ray enabled. Background state checks do not show
that the screen actually displayed these points. The viewer can change apparent scale and
orientation without changing source coordinates; the default view is not an anchor-time
registration or a physical calibration claim.

After actual selection and Save As, bind the submitted .blend's byte size and SHA-256 in
separate custody, then extract to a **new** output file:

```sh
"$BLENDER" --background --factory-startup --disable-autoexec --python-exit-code 2 \
  --python tools/perception_viewer.py -- extract \
  --binding /private/binding.json --binding-sha256 EXPECTED_BINDING_SHA256 \
  --asset /private/observation-package/assets/capture-000001.ply \
  --scene /private/submitted-selection.blend --scene-sha256 EXPECTED_SCENE_SHA256 \
  --scene-bytes ACTUAL_INTEGER_BYTE_SIZE --output /private/new-selection.json
```

The adapter loads a verified temporary snapshot with scripts disabled. A saved Edit Mode
scene must leave Edit Mode **inside that temporary background copy** before its attribute
arrays can be read in Blender 5.1.2. The original scene file is not changed.

The output carries sorted unique zero-based original `point_indices`, exact little-endian
five-float record hex, raw and PLY byte offsets, source/binding/scene identities and runtime
version. For index i, raw offset is 20i and PLY offset is header_length + 20i. The coordinator
can connect the neutral capture back to the upstream asset using the existing private custody
map and verify the PLY body equals the raw capture. That map stays outside discovery delivery.

## Rejections and limits

Every point is checked, including unselected ones. A pure vertex reordering is accepted only
when persistent indices remain a bijection onto the complete original records and every
mapped float32 field is byte-identical. A one-ULP change or signed-zero change fails. Missing,
duplicate or out-of-range indices, changed fields, population, edges, faces, transforms,
modifiers, shape keys, materials, constraints, animation, extra objects, linked libraries,
embedded text and wrong capture/binding identities are rejected. Empty selection produces
`VIEW_EMPTY_SELECTION`; it never means an empty reference or observed absence.

Preparation refuses existing directories; extraction refuses existing output files. Failures
exit nonzero; expected input failures emit a diagnostic code. A partial output from a failed
operation is not complete and cannot be reused. A binding or input identity does not establish
the origin, truth or authorship of its contents. The adapter never creates a discovery record,
assigns a role, admits a judgment or certifies what anyone saw.

Limits are one capture, one million points, 4096 binding bytes and 256 MiB of input .blend
bytes. The adapter uses Python's standard library plus the installed Blender runtime. The
native parsers are trusted dependencies; file-size limits are not an operating-system memory
or CPU isolation policy. No network is used. This is a local engineering workflow, not a
general-purpose validator for hostile Blender files. Tests cover the documented point/scene
contract, not every possible Blender data block or GUI overlay.

## Evidence and next check

See the [dated checkpoint](../../../docs/PERCEPTION_VIEWER_CHECKPOINT_2026-09-12.md) and
[verification record](verification.json). Unit tests challenge byte identity; a separate
[native probe](../../../tests/blender_perception_viewer_probe.py) actually saves/reopens scenes,
reverses vertex order, and attacks fields, indices and geometry. Its selections are explicitly
programmatic. No screenshot or independent human judgment is generated.

The next falsifiable observation is a person opening the exact prepared capture, reporting
whether points are visible, selecting visible points and saving a new scene whose extracted
indices match the source. Record actual onboarding, active interaction, interruptions and
repair time. The same procedure is available to both analysts at the authorized stage.
Image pixel equivalence and a usable workflow for all captures remain separate questions.
