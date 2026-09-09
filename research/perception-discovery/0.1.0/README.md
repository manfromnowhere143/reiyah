# Unassisted discovery record custody

Document ID: `reiyah.perception-discovery.interface`

Version: `0.1.0`

Lifecycle status: `exploratory`

This offline component binds a reviewer's unassisted discovery proposals to a verified
[observation package](../../perception-observation/0.1.0/README.md). It accounts for every
window/capture occurrence, preserves unresolved observations and seals a canonical record.
It does not create a human judgment, prove reviewer independence or release assisted evidence.

## Commands

Use the pinned dependencies in [requirements.txt](requirements.txt). Supply a separately
retained observation-package seal digest. All output paths must be new and their parents must
exist. Record IDs are neutral 32-character lowercase hexadecimal identifiers, not selection
seeds. A record's content identity includes its digest; the identifier is not a global registry.

```sh
python -B -m tools.perception_discovery draft \
  --package /private/observation-package --package-seal-sha256 PACKAGE_SEAL_SHA256 \
  --record-id NEW_32_HEX_RECORD_ID --output /private/new-draft.json

python -B -m tools.perception_discovery seal \
  --package /private/observation-package --package-seal-sha256 PACKAGE_SEAL_SHA256 \
  --record /private/completed-record.json --record-sha256 RECORD_FILE_SHA256 \
  --output /private/new-sealed-record.json

python -B -m tools.perception_discovery verify \
  --package /private/observation-package --package-seal-sha256 PACKAGE_SEAL_SHA256 \
  --record /private/sealed-record.json --record-sha256 SEALED_FILE_SHA256

python -B -m tools.perception_discovery pair \
  --package /private/observation-package --package-seal-sha256 PACKAGE_SEAL_SHA256 \
  --first /private/first-sealed.json --first-sha256 FIRST_SEALED_FILE_SHA256 \
  --second /private/second-sealed.json --second-sha256 SECOND_SEALED_FILE_SHA256
```

`draft` enumerates the existing package population with an unassigned reviewer, unknown exposure,
an unrecorded completion time, every capture `not_inspected`, and no proposals. It must never
prefill negative findings or reported blinding. A human uses a separate record; do not overwrite
a retained input, sealed record or another reviewer's work. An unassigned draft cannot be sealed
as a submitted review. No real human record is supplied with this implementation.

Exit 0 means the requested operation completed. For `pair`, it can still return
`needs_resolution`. Exit 2 reports an invalid input, changed bytes, unsupported state, malformed
record or failed I/O. Inspect the structured outcome instead of treating successful process
exit as an approval.

## Record contract

The closed root object contains `artifact_id`, `version`, `record_id`, `package_id`,
`package_seal_sha256`, `phase`, `reviewer_id`, `completed_at`, `reported_exposure`,
`capture_reviews` and `proposals`. The artifact ID is `reiyah.perception-discovery.record`,
version `0.1.0`, and phase `unassisted_discovery`.

An assigned reviewer is a bounded, nonempty handle. Different strings do not prove that the
authors are different people. Completion time is either `{ "state": "unrecorded" }` or
`{ "state": "reported", "utc": "YYYY-MM-DDTHH:MM:SSZ" }`. Calendar validity is checked;
clock accuracy and whether the event actually occurred at that time are not established.

Reported exposure has five required fields: annotations, predictions, configuration identities,
other reviewer records and prior candidate rankings. Each is `reported_not_exposed`,
`reported_exposed` or `unknown`. Missing fields and Boolean replacements are invalid. An exposed
or uncertain record can be retained without being characterized as successfully blinded.

Every capture occurrence has `window_id`, `capture_id`, `state` and `limitations`, in the exact
package population order. The same capture in two overlapping windows has two accounting rows.
Omission, duplication, reordering and substitution are rejected.

| Inspection state | Meaning in the submitted record |
| --- | --- |
| `inspected` | The reviewer reports inspecting this delivered capture; this does not establish full physical visibility |
| `partly_inspected` | The reviewer reports partial inspection and supplies a limitation |
| `unviewable` | The reviewer reports inability to inspect, with a limitation |
| `not_inspected` | No inspection is reported; a limitation is required |

An undelivered capture cannot be marked inspected or partly inspected through this package.
Incomplete records remain sealable after assignment so omissions and interruptions can be
preserved. They cannot satisfy complete recorded-capture inspection in the pair report.

Each proposal contains a sequential `proposal-NNNNN` ID, one `window_id`, a nonempty description,
`class_hypotheses` and one to 128 evidence references. Class is explicitly unresolved, or a
nonempty set of proposed alternatives among the ten declared detection classes and
`outside_target`. These are hypotheses, not adjudicated object labels. An empty proposed-class
list is invalid; uncertainty is not encoded as no object.

Each evidence reference contains `capture_id` and a locator. It must belong to the same window
and refer to an inspected or partly inspected capture. One proposal cannot repeat a capture
reference. Supported locators are:

- `{ "kind": "capture" }`, for support that is not localized more narrowly;
- `{ "kind": "image_region", "xyxy": [x0,y0,x1,y1] }`, an integer, nonempty half-open pixel
  rectangle within the nominal camera dimensions; and
- `{ "kind": "point_indices", "indices": [...] }`, sorted unique zero-based indices into
  the original delivered lidar point records, with at most 4096 indices.

These locators identify evidence. They do not determine a physical object's position at anchor
time, temporal identity, existence, exhaustive class alternatives or a reference world's
completeness. The [reference compiler](../../perception-reference/0.1.0/README.md) still needs
an explicitly constructed shared reference model and its separate coverage assumptions.
No automatic proposal-to-physical-object conversion is implemented here.

## Sealing and verification

The sealer verifies the submitted file hash before parsing, freshly verifies the observation
package, then reopens and verifies the exact bound manifest used for record validation. It
validates inspection accounting, references and states before writing one non-overwriting atomic
output. Source and runtime changes during sealing are rejected.

The sealed artifact embeds the complete parsed record in canonical JSON. It retains the
original submitted-file hash as a producer custody assertion and a separate hash of the
canonical record. Later verification checks the embedded canonical record; without the original
input file it cannot independently validate the producer's original-file assertion. Keep the
original submitted file and its identity in private custody.

The seal's UTC timestamp comes from the local system clock and explicitly carries an unattested
clock basis. It is not an independent timestamp or evidence that the reviewer had not already
seen assisted material. Verification requires a separately retained expected sealed-file digest,
recomputes the canonical record identity and summary, and verifies the package. Matching hashes
do not authenticate a person's identity or validate the content of a human report.

Records and seals are each limited to 16 MiB, proposals to 5000, descriptions and limitations to
4096 characters, and reviewer handles to 128 characters. The observation package's population,
file and geometry limits still apply. Duplicate JSON keys, floating-point tokens and nonfinite
values are rejected. Bound violations produce errors instead of clipped observations.

## Pair report and authority boundary

Two copies of the same record cannot form a pair. Both records must cover the same package and
pass structural verification. The report separately checks distinct handles, reported complete
inspection, reported clear blinding and recorded completion times. It reports unresolved reasons
or `eligible_for_external_review`; neither is a physical judgment or permission to advance.

Even a structurally eligible pair reports human independence, independently verified blinding,
sealing before assisted exposure and physical-reference completeness as `not_established`.
`phase_2_release` remains `not_authorized_by_this_tool`. The actual study procedure must retain
the independent reviewers' identities and exposure/order evidence before assisted review.
This component does not fetch, display or transmit annotations or predictions.

An empty proposal list is permitted. Its summary always states that physical absence is not
established by zero proposals. Two zero-proposal records cannot become a complete empty reference
world through this interface. The [tests](../../../tests/test_perception_discovery.py) exercise
that case, incomplete inspection, wrong evidence, exposure uncertainty, forged summaries,
tampering, duplicate records and the distinction between handles and independent people.
