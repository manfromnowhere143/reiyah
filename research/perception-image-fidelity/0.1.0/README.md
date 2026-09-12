# Camera pixel correspondence, 0.1.0

On 12 September 2026, the first delivered CAM_FRONT capture in the already exposed
development package matched its original JPEG bytes and all 4,320,000 RGB samples from
Pillow 12.3.0 after native Blender 5.1.2 import. This is one 1600 by 900 capture, selected
before decoding, not all 566 delivered camera images. Exact private identities, outputs,
sources and process receipts are retained in `engine-image-fidelity-2026-09-12`.
See [verification](verification.json) and the [checkpoint](../../../docs/PERCEPTION_IMAGE_FIDELITY_CHECKPOINT_2026-09-12.md).

## Decision and coordinate convention

Dimension agreement was insufficient to establish pixel correspondence. The existing
Blender importer can now be used for this capture's **buffer correspondence** under the
checked settings. Record image observations with the exact original JPEG identity, width,
height and zero-based **top-left** integer `(x,y)` coordinates. For width `W`, height `H`:

```text
decoded pixel index = y*W + x
top-down RGB byte offset = 3*(y*W + x)
Blender bottom-up RGBA binary32 byte offset = 16*((H-1-y)*W + x)
0 <= x < W; 0 <= y < H
```

The image index identifies a decoded raster sample, not a byte offset in the compressed
JPEG. It differs from the point capture's fixed-width original-record indexing. No image
selection was made by a person or through the GUI in this checkpoint.

The pinned Blender [JPEG loader](https://github.com/blender/blender/blob/v5.1.2/source/blender/imbuf/intern/format_jpeg.cc)
writes rows in reverse order and supplies opaque alpha. Its
[RNA accessor](https://github.com/blender/blender/blob/v5.1.2/source/blender/makesrna/intern/rna_image.cc)
exposes byte-buffer channels as binary32 values. The probe exactly inverts that 256-value
mapping using bit patterns; it does not accept nearby values by rounding. Then it checks
alpha and reverses rows. Pillow's [coordinate convention](https://pillow.readthedocs.io/en/stable/handbook/concepts.html#coordinate-system)
places the origin at the upper left. [Source bindings](source-basis.json) retain the exact
versioned source identities used here; primary payloads remain private.

## Bounded replay

[probe.py](probe.py) is a local offline verification script, not a viewer, importer for
admission, new review protocol or product runtime. Supply operator-held paths and expected
identities from an already verified observation package. Keep all outputs private. The
native step uses an exclusive snapshot of the selected JPEG in a fresh output directory.
Both steps refuse reused output files/directories. Failed attempts remain under their own
identities. Limits are 32 MiB per input and two million pixels, narrower than the observation
package's general profile. The native parser and local runtime remain trusted dependencies;
these commands provide no OS sandbox or source authentication.

Run the installed, pinned Blender 5.1.2 build `ec6e62d40fa9` in a fresh background process:

```sh
Blender --background --factory-startup --disable-autoexec --python-exit-code 2 \
  --python research/perception-image-fidelity/0.1.0/probe.py -- native \
  --asset /private/neutral.jpg --byte-size EXPECTED_BYTES --sha256 EXPECTED_SHA256 \
  --width 1600 --height 900 --output /private/fresh-native-output
```

Select the resulting report's exact size and digest separately before comparison. Run
the conventional decode in a separate Python process with Pillow 12.3.0:

```sh
python -B research/perception-image-fidelity/0.1.0/probe.py compare \
  --asset /private/neutral.jpg --original /private/original.jpg \
  --byte-size EXPECTED_BYTES --sha256 EXPECTED_SHA256 --width 1600 --height 900 \
  --native /private/fresh-native-output --report-bytes REPORT_BYTES \
  --report-sha256 REPORT_SHA256 --output /private/fresh-comparison.json
python -B -m unittest discover -s research/perception-image-fidelity/0.1.0 -p 'test_*.py'
```

Encoded JPEG dimensions are checked before either decoder runs. The comparison checks
unchanged original/neutral/snapshot bytes, the existing restricted
JPEG disclosure profile, dimensions, full native buffer identity and all RGB values.
No EXIF reorientation, ICC transform, image editing, recompression, resampling or rendering
is performed. A single mismatch or unsupported value rejects the comparison; missing
images are not empty observations. The native report alone is not a comparison result.

An initial attempt to reuse the full Engine profile inside Blender failed because it imported
`jsonschema`, which is absent from bundled Blender Python. The failure and attempted wrong-size
check are retained. The native header check is now standalone; the full profile remains
required in the existing comparison environment. The corrected wrong-size request rejects
before native import. No dependency was installed or profile requirement relaxed.

The twelve small adversarial tests cover an asymmetric four-pixel coordinate example, flipped
rows, swapped channels, a changed valid byte, non-grid values including one-ULP perturbations,
negative zero/nonfinite values, nonopaque alpha, truncation/extra data, bounds, wrong source
identity, encoded dimension/header validation and output reuse. They are constructed software controls, not generated reference
judgments. Native data and all source identifiers stay private.

## Comparator, cost and limits

Pillow's installed decoder reports libjpeg-turbo 3.1.4.1. Blender's versioned dependency
source selects libjpeg-turbo 2.1.3; that source declaration is not an independent attestation
of every linked byte. Both use the libjpeg family, so these are separate application paths
with shared decoder lineage. No independent JPEG-conformance, scientific or state-of-the-art
claim follows from agreement.

The final native probe took 1.085 seconds with 321,355,776 bytes peak process RSS;
comparison took 0.541 seconds with 120,717,312 bytes peak RSS. Both include process startup.
The earlier native run took 2.722 seconds; retained variation is not an optimization claim.
These single-machine measurements are engineering costs, not a human-review budget.

The native image reported sRGB input and `use_view_as_render=False`; the factory scene's
view transform was AgX. A decoded pixel match does not verify color management on a display,
screen pixels, magnification, pointer positioning, visibility or a person's understanding.
There was no screenshot, actual interactive image/point selection, human observation or
new reference interpretation. This check does not narrow the real comparison, which remains
[-8,8]. Keep joint worlds, weights, loss, tolerance, matching competition and unknown states.

The next falsifiable observation remains the prepared native point exercise: an actual
participant opens the bound scene, reports visible display, selects points and saves a fresh
file for original-index extraction, retaining real preparation, navigation and repair time.
Do not substitute this buffer check for that exercise. Independent unassisted discoveries
must still be locked before assisted material is released. A competent analyst receives the
same staged evidence and may use the same coordinate checks and mathematics.
