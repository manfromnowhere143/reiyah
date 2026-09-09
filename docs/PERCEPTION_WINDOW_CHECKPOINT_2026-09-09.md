# Raw observation-window checkpoint

Document ID: `reiyah.perception-windows.checkpoint-2026-09-09`

Version: `0.1.0`

Lifecycle status: `exploratory`

The Engine now checks complete recorded camera/lidar windows against exact clock, metadata and
payload identities. The [interface](../research/perception-windows/0.1.0/README.md) defines its
states and bounds; the [machine checkpoint](../research/perception-windows/0.1.0/checkpoint.json)
binds code, transcripts and private result identities. It extends main `2ac9afc` without
changing the reference compiler, paired-loss core or selected study-plan bytes.

## What the development audit established

The audit used the same two previously exposed development anchors as the preceding input and
reference checkpoints. The complete metadata timeline contains **725 captures** in their
closed ±2-second windows. The existing private inventory covered 42, and all 42 decoded.
The other 683 were unlisted in that inventory. Thus neither recorded window was complete;
the retained three-keyframe packets could not establish the required four-second context.
The initial incomplete reports remain retained.

A bounded acquisition from the existing dataset storage supplied all 725 required payloads.
The source metadata tables matched the archive used by the Engine. The 42 overlapping raw
identities matched their earlier retained versions. Separate local checks verified the bundle,
every member's identity and exact requested-file coverage before writing a fresh private cache.
No source data or existing packet was modified, and no raw payload enters public Git.

The same final window implementation then verified and decoded **566 camera images and
159 lidar files**, containing **5,521,024 point records** and **187,631,386 raw bytes** in total.
Both recorded windows are now complete under the declared profile. There are no repeated
verified payload hashes across distinct filenames in this development input.

Recorded time gaps remain visible: the largest internal gap is 200,000 microseconds for a
camera channel and 99,530 microseconds for lidar. Those are metadata observations on these
windows, not asserted outage causes or acceptable physical-review thresholds. Boundary
distances, asynchronous capture times and every individual capture remain in the report.

## What is checked and what remains unknown

The adapter checks complete selected-scene clocks, reciprocal sensor links, strict timestamp
order, channel/format/dimension bindings, both interval endpoints, unique identities and paths.
Every recorded non-keyframe sweep inside the interval is included. Outside-window payloads are
not opened. Missing files, unknown custody, unavailable decoding and corrupt payloads remain
distinct states and never cause anchor substitution or silent window shortening.

Raw files must match their declared size and SHA-256 before decoding those same bytes. JPEG
validation forces all pixels to decode, with truncation tolerance disabled; metadata dimensions
and color format must agree. Lidar validation checks the nonempty five-float record layout and
finite values in every field. Malformed required input aborts with a diagnostic; an assessment
with incomplete raw custody can still be written, with that incompleteness explicit.

Nineteen new tests cover these rejection and missingness paths, including symlink escape,
source mutation, malformed clock states, resource caps, absent channels, repeated captures,
truncated JPEGs, nonfinite point fields, decoder configuration and non-overwriting output.
All **257 offline tests** passed: 164 repository and 93 measurement-tool tests.

A separate direct scene/time calculation agrees on all 725 capture identities, timestamps,
filenames and keyframe states. It shares the generic archive and JSON framing, so it is not
independent physical verification. A transition check proves that acquiring the missing raw
files changed neither the anchors nor their clocks, requested captures, original verified
payloads or computation code.

Full recorded windows still do not establish physical visibility, complete object discovery,
calibration/pose accuracy, correct coordinate transforms, per-point acquisition timing or
online availability. The paired-loss result is not recomputed or narrowed by this file audit.
No physical judgment, model inference, training run or new study selection occurred.

## Next work and continuation

Check the nominal spatial/time operands needed to interpret these raw observations and define
the locked blinded-observation boundary. Operational catalogs contain information unsuitable
for discovery reviewers and must not be passed through as a reviewer packet. Preserve unknown
motion, calibration accuracy and unlisted matchable objects when building reference alternatives.

The 60-scene study remains unselected and unrun. Two independent reviewers, the independent
conventional comparator, adjudication and the exact method/input/reviewer freeze are still
required. This checkpoint establishes a reusable input-checking component and complete raw
development windows; it does not establish frontier superiority or a physical benchmark.

The 52 empirical transcripts, 57 claim-register rows, main README and its six Mermaid diagrams
are preserved. Gate B closeout checks existing evidence integrity and document consistency;
it does not replay the experiments or accept Gate A. Gate A remains operator-unaccepted.
Work is isolated from both owner checkouts, the parallel research worktree and the Console.
Resolve final main integration, cloud closeout and publisher readback from the private delivery
record. Publisher custody/readback is not independent scientific or transport authority.
