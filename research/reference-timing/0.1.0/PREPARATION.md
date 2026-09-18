# Reference timing preparation

Version: `0.1.0`. Status: `exploratory`.

The frozen 64-image development packet records camera captures before their
associated sample timestamps. The retained nuScenes devkit 1.2.0 deliberately
uses the current sample annotations for keyframes. Its non-keyframe path uses
linear center interpolation and quaternion spherical interpolation, with
current dimensions. Neither behavior establishes physical ground truth.

This preparation reads only metadata from the already held, hash-bound
nuScenes archive. It retains each selected sample's immediate preceding sample,
every car annotation in those preceding samples, and their instance records.
It reads no new image bytes, model outputs, outcome reserve or scores. The
complete source arrays are streamed to establish membership; records unrelated
to these joins are discarded. Source and new preparation code are bound before
the pass. Missing preceding samples are distinguished from an explicitly empty
car census. Duplicate keys, duplicate instance membership, incomplete tables
and inconsistent sample/scene links fail closed.

The next scored protocol must be separately frozen. Its proposed question is
whether a declared motion model changes the original replacement proxy and
whether missing motion evidence prevents that conclusion. A linear/SLERP model
is an assumption, not an annotation correction. Any fixed current-annotation
census must say that predecessor-only or otherwise unannotated objects are
outside that census. Missing brackets cannot silently become zero velocity,
current boxes, empty references or completed observations. No selector tuning,
new inference, new images or reserved outcomes are authorized here.
