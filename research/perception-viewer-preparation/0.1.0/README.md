# Checked capture preparation, 0.1.0

The coordinator can derive an existing point-viewer binding from a verified observation
package without transcribing its asset size, digest or point count. The coordinator still
selects the expected package seal and neutral capture ID. This command neither chooses a
relevant observation nor creates a reference interpretation.

## Coordinator procedure

Use the Engine Python environment with the observation package's existing dependencies.
Choose a new private binding filename whose parent already exists, outside both the
observation directory and source checkout. From the selected Engine checkout:

```sh
python -B -m tools.perception_viewer_preparation \
  --package /private/selected-observations \
  --package-seal-sha256 EXPECTED_SEAL_SHA256 \
  --capture capture-000001 \
  --output /private/new-binding.json
```

`EXPECTED_SEAL_SHA256` is the separately selected seal identity, not a digest learned from
whatever package happens to be at that path. `capture-000001` is an example of an explicit
choice; the command has no default capture. The complete package is verified, including
unselected assets, before the selected manifest row is read again against its expected hash.
Only a delivered `LIDAR_TOP` row is supported by this point adapter. A missing, invalid,
unavailable or camera capture fails without a binding output. Missing is never an empty scan.

The result reports `binding_prepared`, its exact binding digest/size, and
`viewer_source_arguments`, a JSON array of arguments for the
[existing native adapter](../../perception-viewer-custody/0.1.0/README.md). Supply that array
as arguments, preserving each element, rather than assembling a shell command from its text:

```python
result = json.loads(binding_command_stdout)
subprocess.run([
    selected_blender, "--background", "--factory-startup", "--disable-autoexec",
    "--python-exit-code", "2", "--python", selected_viewer_script, "--", "prepare",
    *result["viewer_source_arguments"], "--output", fresh_opening_directory,
], check=True)
```

Here `binding_command_stdout` is the retained stdout of a successful command above;
`selected_blender` and `selected_viewer_script` name the separately selected Blender 5.1.2
binary and this checkout's `tools/perception_viewer.py`. `fresh_opening_directory` is a new
private output outside sources. This illustrative Python fragment uses `json` and
`subprocess` from the standard library; it is not an additional orchestration service.
Extraction uses the same source array and the existing separately bound scene arguments.
The native adapter rechecks the selected source bytes when it consumes them.

Retain the binding, preparation result and selected code/runtime identities with the private
procedure. Paths in that result locate files; they do not supply authority. Complete package
verification and output guards assume a stable directory hierarchy. Concurrent directory
replacement, mounts and hostile native files remain outside that guarantee. Existing files,
directories and links are never overwritten. All source-directory aliases are refused.

The binding and selection records remain version 0.1.0. The new preparation result identifies
itself as `reiyah.perception-viewer.preparation`, version 0.1.0. It is coordinator output,
not a reviewer submission. No annotations, predictions or later-stage assistance are added.

## Result and comparator

The comparator is the correct existing manual procedure on the same capture: verify the
complete package, locate its capture, transcribe source fields, retain the binding digest
and invoke the existing viewer. These are five logical actions, not measured clicks or human
minutes. The command automates verification and three derived record values, and returns the
derived source arguments. It preserves explicit source selection and capture choice.

On the already exposed 34,720-point development capture, the new binding is byte-identical
to the prior correct 353-byte manual binding. The returned argument array works with native
preparation and extraction. Extraction from the retained programmatic selection returns the
same 1,651-byte report. Original indices 0, 17,360 and 34,719 match separate raw/PLY slices;
all 34,720 original records agree. These are background source checks. Native scene bytes
and temporary paths are not claimed deterministic, and no actual UI or human selection was
observed. The earlier participant exercise remains ready and unchanged.

The new command took 3.366 seconds including startup and full package verification, with
80,625,664 bytes peak process RSS. Native preparation/extraction took 2.855/2.823 seconds in
overlapping processes. These single local runs measure machine cost only. No human-effort
advantage or state-of-the-art performance is established. See [verification](verification.json).

## Validation and next evidence

Ten new focused tests cover manual-byte equivalence, explicit capture/modality, unavailable
evidence, wrong seals, selected and unrelated asset substitutions, extra files, existing
outputs, protected-source aliases and the CLI. All 30 preparation/viewer tests and all 379
repository tests pass. Replay from the selected checkout with:

```sh
python -B -m unittest tests.test_perception_viewer_preparation tests.test_perception_viewer -v
```

The 93 earlier measurement tests are retained with their 107 source files checked unchanged,
not claimed as new execution. The shared verifier, schemas and Python/native runtimes remain
trusted dependencies; internal conformance is not external scientific review.

The next useful observation is an actual participant opening the ready scene, selecting
visible points and saving a separate return with the observation form. Successful background
preparation does not discharge that obligation. The official desktop failure remains the
diagnosed native Swift loader incompatibility; no unchanged bootstrap was repeated. Independent
reference judgments, practical usability and external scientific review are still missing.
