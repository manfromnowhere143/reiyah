# A source-traceable point-selection procedure

Checkpoint ID: `reiyah.perception-viewer.checkpoint.2026-09-12`; version `0.1.0`.

The engineering change is a bounded bridge from ordinary native viewer selection to exact
source record indices. The [procedure and adapter](../research/perception-viewer/0.1.0/README.md)
use installed Blender 5.1.2. A prepared scene opens in vertex Edit Mode; a person selects
points and saves a new .blend. Offline extraction verifies every mapped point and returns
original indices and byte offsets. There is no new viewer, add-on, embedded script or
perception algorithm. The real detector comparison remains [-8,8].

## Evidence retained separately

The previously verified observation package contains 725 captures. Its existing verification
was replayed against the separately retained seal. The first delivered LIDAR_TOP capture in
neutral capture order was chosen for this development exercise. Its 34,720 records have all
five float32 fields byte-identical between the PLY body and the exact original raw asset;
the fixed wrapper adds 164 bytes. No filtering, sorting, registration, downsampling or
reference selection occurred. Private custody retains the source mapping, payloads and hashes.

The native probe saves and reopens programmatically selected scenes and verifies indices
0, 17360 and 34719. An actual reversal of Blender vertex order preserves these original
indices and exact records. Fifteen adversarial/absence cases reject one-ULP changes in each
field of an unselected point, missing/duplicate indices, deleted points, added topology,
transforms, capture/binding substitution, modifiers, embedded text and empty selection.
Together these are 17 native checks: two positive cases and fifteen rejection cases.

The first probe failed: leaving an object in Edit Mode and calling `update_from_editmode`
did not expose its attribute arrays. The correction exits Edit Mode in the temporary
background copy before extraction. A unit test also exposed field comparison occurring
before a complete index-bijection check; the checks were reordered without weakening the
expected failure. Original code, diagnostics and failed runs remain in private custody.
The [verification record](../research/perception-viewer/0.1.0/verification.json) binds final checks.

## What was not observed

One current Computer Use inspection call failed before any Blender state or screenshot
was returned. The detailed cause was native-pipe path unavailable, OS error 2. Targeted
local inspection found the default Computer Use socket absent. The packaged transport
code attempts service startup before its final connection attempt; this describes that
code path, not an independently observed service lifecycle. Why the service did not supply
a reachable endpoint is not established. No evidence diagnoses screen permissions or
gcloud authentication. No identical bootstrap loop or alternate GUI automation was used.

The actionable alternative is the exact prepared .blend and ordinary File → Open,
vertex selection, File → Save As procedure. The smallest next input is a person performing
that exercise and returning the new scene plus an actual observation/effort note. Automation
instead requires a functioning host-managed Computer Use endpoint, followed by a successful
state/screenshot call. Neither route requires restarting the engineering mission.

No point was selected through the UI during this checkpoint. No generated picture stands
in for a screenshot. Background preparation, saved application state, selection extraction,
image dimensions, image pixel equivalence, interactive observation and human usability are
different evidence obligations. Only the first three are checked here. The procedures need
an actual participant before they can establish usability. No discovery or review record
was populated. Reviewer roles, independence and staged exposure remain unestablished.

## Scope and conventional comparison

Blender's existing native PLY import is the baseline; the already retained all-file import
checks are inherited evidence rather than a new experiment. The added code removes repeated
import setup and verifies persistent indices. The final one-file preparation took about
1.23 seconds with 234 MiB peak process memory. The measured native probe and extraction costs
are retained in the verification record. These are single local process observations,
including startup, not a benchmark or participant-time estimate. No relative usability,
time-saving, changed engineering decision or state-of-the-art claim is made.

The adapter is one standard-library Python module plus Blender; its tests add no deployment
or service dependency. Point and file limits are explicit. Native Blender parsers remain
trusted and are not wrapped in a new OS isolation policy. Read the exact source/API basis
in [source-basis.json](../research/perception-viewer/0.1.0/source-basis.json).

## Research lane review

The separately selected immutable Fable outbox at `681efcc8dc693c0215403b93bca6a96b7faba4c5`
was inspected without changing its source or branch. Its preference-checker correction
rejects the three replayed forgeries accepted by the predecessor at the coupled [0,0] case.
Its nine focused tests pass on copied, hash-verified outbox files. This does not integrate
the research branch or constitute independent scientific review.

The proposed observation-relevance classifier complements viewing, with a necessary scope
qualification. Inertness applies to the **current** admitted world set and declared objective.
An Engine-side constructed counterexample uses t = q XOR r and delta = 2t - 1: q is initially
inert because either answer leaves [-1,1], but becomes decisive after r is established absent.
Relevance therefore needs recomputing after accepted answers; the particular 18-comparison
constant-delta example does not establish universal stability under conditioning. The
counterexample, exact selected source manifests and review are retained in the private
exchange. No reference judgment was created. Prediction-dependent triage must not bias the
required independent unassisted discovery. Actual effort must be compared with a competent
analyst allowed the same graph, evidence and calculation, including onboarding and repairs.

P005 publication is now **operator-reported published** on 12 September. Earlier deferred
statements remain dated history. The new permalink and exact platform formatting are not
captured. No further publication or outreach occurred or is authorized. Its commitment to
equal evidence and all effort counted remains in force. Gate A remains unaccepted, the
physical study remains unselected/unrun, and the frozen loss, weights, tolerance, matching
competition, joint alternatives and explicit unknown states remain unchanged.
