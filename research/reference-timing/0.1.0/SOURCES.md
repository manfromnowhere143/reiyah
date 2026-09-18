# Timing source scope

Version `0.1.0`, 18 September 2026. No new image or model asset was acquired.

The already held nuScenes metadata archive is 461,678,030 bytes, SHA-256
`db48746b10e3544d5ef619eaa3d687e3960626fe1b4422ed856711da5aa7325b`.
The inherited 64-image selected metadata is SHA-256
`b2f53e74780c62414a477dd725bea1b1f16e8f2200fb45abf3e0d1cb77bc2bb6`.
Image allocation, prediction qualification and source terms remain in the
[original source record](../../public-predictions/0.1.0/SOURCES.md) and its
[source ledger](../../public-predictions/0.1.0/sources.json).

Before the new scored protocol, a separate metadata preparation freeze bound
the exact source and scoped extractor. Its SHA-256 is
`f1ccbfef7550c115ee1e949e60074f5afa7921589c38d8ff3c46a8ae3c1ab4ec`.
One archive pass scanned the complete sample, annotation and instance tables,
retaining 63 immediately preceding samples, their 1,018 car annotations and
792 relevant instance records. Unrelated records were discarded; no image was
opened. The 1,025,593-byte retained subset has SHA-256
`0178bf46a6dc3b39fdeb1659184135f42656ca3fb89317dfad94375b7282b4b3`.
Missing samples, duplicate identities and broken sample/scene joins are distinct
from an explicitly empty census. The retained preparation does not score models.

The official nuScenes devkit 1.2.0 wheel is 315,983 bytes, SHA-256
`76cee0e7f96ec96d6269ee3acb4ff69e8ac2f9413e974d9eb542233ea7479bf1`.
Installed SDK member bytes match that wheel. The relevant bindings include:

| SDK member | SHA-256 |
| --- | --- |
| `nuscenes/nuscenes.py` | `7d511213c3fa4452f4c0c68fb05c299e803ad7ca3f369275f756958287307871` |
| `nuscenes/scripts/export_2d_annotations_as_json.py` | `7d2f6a1771d487142e5984b6f1eeefdb03c0db980c359a3d704fea814498769a` |
| `nuscenes/utils/geometry_utils.py` | `6dca908d593e90645d67f0ddf00f3ca7d4d45f6fcf12933da0a70f9eb62caf33` |
| `nuscenes/utils/data_classes.py` | `9fd4eb980630af3177768e248de4fa48f5cacf36a1327ec16da56cdc9a64a3ae` |

`get_boxes` returns current annotations for keyframes. Its intermediate-frame
branch interpolates center and quaternion orientation, keeps current size,
clamps time to the sample bracket and falls back to the current box for a
missing preceding instance. The keyframe 2D export calls current `get_box`
directly. The supplied 64 camera timestamps precede their associated sample
timestamps by 33.120–38.308 milliseconds. These source facts do not establish
mislabeling or validate a physical motion model.

This experiment explicitly changes the model for sensitivity analysis. It
uses strict bracket membership, a declared 1.5-second span limit and no missing-
instance fallback. It retains the exporter convention of using positive-depth
corners, then intersecting their projected convex hull with the canvas. It does
not add near-plane edge intersections, visible-surface labeling or occlusion
reasoning. Its current-dimension, linear-center and SLERP assumptions remain
conditional, not source-authorized annotation corrections.

The projection runtime is Python 3.11.15 with NumPy 1.26.4, SciPy 1.17.1,
pyquaternion 0.9.9 and Shapely 2.0.7. The private `RUNTIME.json` binds version
strings, the interpreter, quaternion implementation and relevant native modules.
The interpreter and numerical dependencies are reused without installation or
modification. A separate scalar geometry implementation and the selected
research Python check the resulting operands. Neither agreement nor hashes
make the supplied annotations independent ground truth.

Raw source records, subset metadata, source packages and SDK-derived geometry
remain private. Public content is confined to authored code, synthetic controls
and derived reports under [the retained distribution scope](DISTRIBUTION.md).
