# Observation evidence belongs to the detector comparison

Document ID: `reiyah.perception-binding.checkpoint-note`

Version: `0.1.0`

Lifecycle status: `exploratory`

Do the delivered observation assets belong to this comparison's samples and times, and do
they match the retained original inventory? The new binding command passed those checks on
the same two previously exposed development windows: 725 captures, comprising 566 images
and 159 lidar files with 5,521,024 point records. All delivered source bodies matched.

This resolves a provenance gap. The open-reference unit-loss enclosure remains [-8,8]; no new
physical judgments constrain it. There is no selected study cohort or seed, no sealed real
discovery record and no new empirical detector-performance result. Gate A remains unaccepted.

## Decision and implementation

The missing join made the recommended binding task the first priority after inspecting main.
An internally valid package could previously accompany a comparison of different anchors or
absolute times. Its valid seal also could not show that a new image or point body matched the
original source inventory. These are concrete missing joins before reference admission.

The conventional solution is an explicit relational join plus byte comparison. The
[single-module implementation](../tools/perception_binding.py) uses existing bounded consumers,
rederives the private mapping and checks exact correspondence. No matching algorithm, loss,
protocol, reference interpretation or recorded result changes. Its
[interface](../research/perception-binding/0.1.0/README.md) states the full input and trust boundary.

| Method considered | What it establishes | Decision |
| --- | --- | --- |
| Existing package verifier alone | Internal package identities, formats and disclosure constraints | Insufficient for comparison population or original-inventory identity |
| Explicit source-bound join and asset comparison | Exact declared population and delivered-body correspondence | Implemented; ordinary dictionaries, bounded reads and hashes suffice |
| Replay complete prediction and geometry construction | Recomputes additional upstream premises | Existing upstream checks remain bound dependencies; this task adds the missing join |

This choice follows the inspectable code obligation and existing format contracts. It introduces
no scientific novelty or state-of-the-art claim requiring a new literature comparator. The
physical study still requires a competent independent conventional analyst with the same
staged evidence and permission to use the same mathematics.

## Evidence and corrections

The [machine checkpoint](../research/perception-binding/0.1.0/checkpoint.json) binds implementation,
test and source identities, captured run receipts, report identities and limits. Its public
summary contains no dataset tokens, raw payloads, private absolute paths or reviewer records.

The new tests construct valid observation packages and resealed substitutes. They reject a wrong
anchor, sample or scene, changed catalog/metadata identity, omitted/extra/duplicate anchors,
changed nominal geometry, substituted JPEG/PLY bodies and contradictory availability. A
one-microsecond shift of every absolute clock leaves the neutral package byte-identical yet
is rejected against the comparison catalog. Missing evidence, unavailable geometry and missing
detector outputs retain their distinct states. Output reuse and private-output placement are checked.

The first test run exposed an erroneous fixture assertion: synthetic scene tokens are `s0` and
`s1`, while `scene-0` and `scene-1` are names. The assertion was corrected after inspecting the
fixture; no production requirement changed. Subsequent review reproduced a real boundary gap:
consistently negative metadata sizes passed an equality-only comparison. The failing regression
is retained, and the new consumer now checks that the shared size is a bounded integer.

The final suite passes 259 repository tests and 93 measurement tests, including 21 new binding
tests. Gate B integrity checks pass and verify 52 retained transcript identities; historical
experiments were not replayed. This is offline development validation, not Gate A release evidence.

The measured first development run took 6.02 seconds wall time and reported 255,000,576 bytes
maximum resident set size on the recorded local runtime. Other test processes ran concurrently.
This is a resource observation for this input, not a general performance benchmark. No cloud
compute, training, detector inference, new dataset download or new sampling was needed.

## Limits and continuation

The binding trusts the selected original inventory, upstream catalog/normalization and nominal
geometry, shared parsing/projection/join code and local runtime. It does not prove that a person
reviewed any capture, that records are independent, or that the physical scene is completely
represented. A valid missing observation remains a missing observation.

Next: specify and implement the reviewed-source admission boundary from locked discovery,
assisted proposals and adjudication to shared reference alternatives. Attack it with fabricated
record digests, wrong-package references, conflicting judgments and attempted closed-world
promotion. Use synthetic records until independent humans supply real observations. Preserve
the proposed study's freeze, reviewer, comparator and adjudication prerequisites.
The existing reference compiler is unchanged; enforcing this binding when admitting reviewed
source contents remains part of that next task.

This checkpoint adds a reusable check needed before evidence can influence an engineering
choice. An actual changed decision and repeated product value remain unestablished.
