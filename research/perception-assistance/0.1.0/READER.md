# Later assistance, 0.1.0

This folder contains source suggestions for assisted inspection of the same observation
windows. It is prepared privately. Its existence is not permission to disclose it. Both
independent discovery records must be locked and actual exposure order verified first.

Read `assistance.json` with the exact observation package named inside it. Its `windows`
list every keyframe in each closed interval. Each occurrence has a relative microsecond
time and a packet-wide frame identity; overlapping windows reuse the same frame. Only the
named `comparison_frame_id` in each window is a comparison opportunity. Other keyframes
provide context and do not add loss observations or independent statistical replicates.

Every source annotation and every supplied prediction at these frames is included. There
is no class, score, range, visibility, point-count or suppression filter. Configuration
labels mask source names. They do not identify which configuration is the existing one.
An observed empty prediction array means the source explicitly supplied an empty array;
an unavailable output retains its state and has no array. A source annotation array,
including an empty one, does not establish complete physical coverage or absence of objects.

Source box, score and velocity operands are exact decimal text, or an explicit
`nonfinite_source_value` record. Matrices use the observation interface's exact rational
objects with numerator and denominator strings; point counts remain integers.
Nonfinite records must not become zero or a valid coordinate. Geometry is the nominal
source global frame: translation is XYZ in metres, size preserves width/length/height,
and rotation preserves the WXYZ quaternion. Prediction velocity retains its two source
components. The prior detector adapter validated class, score and translation XY only.
Preservation of the remaining components does not establish a physically valid 3D box,
calibration, velocity, pose or track. Annotation categories remain in their source taxonomy;
they have not been silently mapped to detector classes. Visibility may be `not_annotated`.

Each window supplies the previously bound nominal anchor-ego-to-global transform, or its
unavailable state. Together with the observation package's sensor-to-anchor-ego matrices,
this makes the coordinate relationship explicit. Boxes belong to keyframe times. Camera
and lidar captures have their own relative times. There is no interpolation, object motion
compensation, visibility inference or asserted box correspondence at another capture time.

Annotation `prev` and `next` distinguish a source endpoint, a link inside this packet and
a valid immediate source link outside it. Shared track IDs preserve source instance
identity; they do not prove physical identity or make tracked observations independent.
All row IDs are packet-wide. Source tokens, absolute timestamps, paths and configuration
role mapping remain with the coordinator. Global geometry and the data themselves may
identify a scene or detector: this is identifier masking, not guaranteed blinding or anonymity.

Both methods must receive these exact same common files at the same logical stage. Before
either method performs the detector comparison, the coordinator must also deliver identical
neutral row-to-retained-detection mappings, configuration roles, normalization rules, loss,
weights, joint reference alternatives and permitted clarifications. This common inspection
packet is not that complete analysis input. Neither method may see the other's conclusion
before locking its own. Record all preparation, review, integration, calculation and repair
effort, including unavailable measurements and failed attempts.

Dataset annotations are suggestions to inspect and challenge, not newly supplied independent
judgments. Retain discoveries, assisted proposals, disagreements and unresolved states.
This preparation admits no reference constraints and computes no detector verdict.
