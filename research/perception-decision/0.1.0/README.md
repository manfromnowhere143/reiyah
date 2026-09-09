# Checked paired-loss core

Document ID: `reiyah.perception-decision.core-guide`

Version: `0.1.0`

Lifecycle status: `exploratory`

This offline research primitive calculates whether a fixed addition improves a base configuration
under an explicit reference graph model. It implements the calculation and certificate checks
from the [architecture](../../../docs/PERCEPTION_DECISION_ARCHITECTURE_2026-09-09.md).

The core input is a normalized graph contract. A per-frame nuScenes adapter implements the
declared output selection and suppression rules. Full-source extraction, the clock/cohort
builder, the geometry/identity coverage argument and the blinded reference study remain separate
work. Passing this core does not establish physical coverage, detector quality, a safety
guarantee or product value.

## Run and independently check a packet

From the exported research candidate, use the existing Python environment with the repository's
pinned `jsonschema` dependency. No network call, model, database or external solver is used.

```sh
python3 -m tools.perception_decision run \
  --input research/perception-decision/0.1.0/matching-ambiguity.json \
  --input-sha256 INPUT_SHA256 \
  --output /absolute/private/path/decision.json

python3 -m tools.perception_decision verify \
  --input research/perception-decision/0.1.0/matching-ambiguity.json \
  --input-sha256 INPUT_SHA256 \
  --packet /absolute/private/path/decision.json \
  --packet-sha256 OUTPUT_SHA256
```

Supply the expected hashes from the selected source or output record; a hash carried only inside
an untrusted payload is insufficient. The run command prints the output hash. It checks the
certificate before creating a complete output and refuses to overwrite an existing identity.
Verification rechecks the actual input and packet bytes before parsing, then checks the proof
against the exact input. A different producer-source digest is reported, not silently rewritten;
the current checker still verifies the mathematics of a compatible packet.

Exit 0 means a checked result with a consistent model, including a valid unresolved comparison.
Exit 3 means a checked diagnostic packet with blocked inputs, inconsistent assumptions or model
consistency not established within the work limit. Exit 2 means malformed input, failed integrity,
failed certificate or I/O failure. A packet with an unavailable output cannot carry a decision.
The current CLI is an offline research process, not a hermetically isolated Gate A release runner.

The [synthetic example](matching-ambiguity.json) has exactly two reference interpretations.
Its valid enclosure is [-1,1] error units and its preference is unresolved. Restricting the model
to the disputed object being absent gives -1; requiring it to exist gives +1. Those are designed
mathematical cases, not nuScenes observations. The input file's own assumptions describe the
center-distance construction.

## Input semantics

The [closed schema](input.schema.json) rejects unknown fields. Each anchor has a fixed weight,
an availability-tagged base and retained additions, and an open or finite reference. The
augmented configuration is constructed as the base plus additions. Duplicate detection IDs,
including overlaps between the two roles, fail. A record digest names the normalized detection
record; verifying the normalization that produced it remains an adapter obligation. It is not
proof that a physical detection was correct. Already-retained additions are supplied here; this
core does not silently infer or implement a vehicle fusion policy.

Observed empty arrays are valid. Missing, unmeasured, sensor-invalid, abstained, outside-support
and unknown outputs require a reason and prohibit a value. All selected anchors stay represented;
missing required outputs block the comparison even when their weight is zero. Weights are common
to both alternatives, nonnegative, reduced rationals and sum exactly to one.

The global model declares Boolean variables and clauses. Each clause is a disjunction; all
clauses must hold. An empty clause is false. Objects and edges have conjunctive `when` guards;
an empty guard is true. Edges to absent objects are inactive. Shared variables and clauses may
couple different anchors, so joint extrema are computed over global assignments. Alias, class,
geometry and temporal relations must be encoded as explicit constraints by the reference adapter.
The core does not infer those constraints from a human-written assumption.

`conditional_reference_graph` means an enclosure relative to those formal operands and their
declared assumptions. The caller must justify whether the graph covers physical alternatives.
Use `open` where unlisted matchable objects or other alternatives remain unconstrained. Open
anchors contribute the verified count enclosure, not invented object labels. In a mixed model,
the resulting enclosure is a conservative relaxation, even when every finite assignment was
enumerated. A graph interpretation is not automatically a physically feasible witness.

All numeric operands are canonical rational strings. A shared target count cancels only in the
specified additive FN/FP loss. The tool does not accept a different nonlinear loss under that
identity. Cohort sampling validity and selection bias are separate obligations.

## Per-frame output normalization

`tools.perception_decision.nuscenes.normalize_frame` takes already source-verified base and camera
frame records, their sample identity, clock-bound global ego XY, fixed cohort weight and upstream
source hashes. Source checking remains a caller obligation; supplying a digest does not verify
the file that it names. This API has been exercised on synthetic inputs only. It does not load
the real prediction files, choose scenes or create human reference judgments.

Parse used source numbers as `Decimal`, preserving their decimal values. Required XY coordinates
and scores accept bounded finite Decimals or integers, and reject binary floats. The adapter
uses exact rational arithmetic for score >= 0.30, squared XY range <= 2500 square metres,
and same-class suppression at squared distance < 4 square metres. It preserves every qualified
base output, including duplicates. Camera rows are processed by descending score, then original
file position. An addition is retained only if no retained same-class detection suppresses it.
The ten detector labels are explicit; an unknown label fails rather than being dropped.

Each raw frame is limited to 512 predictions. Oversized frames fail without clipping. The receipt
accounts for every source row, both eligibility predicates and the suppression blocker. It also
retains each qualified normalized record and the digest used by its core detection node.
Unused Z, size, rotation, velocity and attribute fields remain outside this XY/count computation;
their omission from the normalized representation is recorded and is not a valid-measurement claim.

Missing frames keep their availability state and any known parent-file identity. Camera output
cannot become retained additions when the base frame is unavailable. An observed empty frame
remains distinct from an unavailable frame. The returned reference is always `open`; reviewed
constraints must be supplied by a later reference adapter. The normalization receipt is provenance
for this transformation, not an independently checked physical-reference certificate.

## Proof and limits

The producer uses deterministic augmenting paths in sorted detection/object identity order.
For every finite anchor and admitted assignment, it emits matching and vertex-cover witnesses
for the base and augmented graphs. The checker reconstructs eligibility separately, validates
every edge and endpoint, and checks cover completeness and equal cardinality. It does not call
the producer's matcher. It independently enumerates the Boolean domain and rejects omitted,
duplicate or inadmissible worlds before checking the aggregate extrema and decision fields.

The producer and checker share the strict input parser and rational representation. This is a
small explicit trusted surface, not independent physical validation or two independent software
implementations of the entire pipeline. An additional independent brute-force assignment search
checks all small graphs exercised by the test suite.

The input schema caps anchors, detections, objects, edges, variables and string sizes. Parsing is
limited to 4 MiB for inputs and 16 MiB for packets. Complete enumeration is attempted only with
at most 4,096 assignments and at most 2,000,000 deterministic estimated-work units. These are
computational scope controls, not a measured latency guarantee or OS memory/time containment.
The estimate includes clause/guard checks and matching work. Beyond that budget, the producer
returns the unconditional count bound and checks a supplied feasible assignment, or tries the
all-false assignment. Failure of that attempt does not prove inconsistency or non-identifiability.
It leaves model consistency not checked and the decision not evaluated.

The checker verifies a coarse result independently from addition counts and weights. It accepts
an exact finite result only after the complete permitted assignment set and all required matching
certificates pass. The output separately records execution, model, enclosure, decision, research
scope and physical-coverage status. No probability confidence level is assigned to this enclosure.

## Verification

```sh
python3 -m unittest discover -s tests -p 'test_perception*.py' -v
```

The suite uses an independent exhaustive partial-assignment calculation for small graphs,
shared-variable cancellation across anchors, the disputed-base-neighbor example, asymmetric
penalties, strict tolerance boundaries, open references and each unavailable-output state.
It attacks omitted worlds, forged bounds, invalid matching/cover witnesses, malformed numbers,
unknown properties, bad source hashes, partial writes and overwrite attempts. An actual CLI
process checks exit distinctions. Adapter checks cover exact boundaries, deterministic suppression,
base duplicates, every unavailable state, rejected required nonfinite numbers, ambient decimal
precision, translation invariance, source identity and complete selection accounting. These tests
validate the bounded computation; the planned physical study and external workflow comparison
remain unexecuted.
