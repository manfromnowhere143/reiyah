# Portable reference-population audit

Document ID: `reiyah.reference-audit-demo.2026-09-07`

Version: `0.1.0`

Lifecycle status: `exploratory`

This deterministic research tool makes the reference-population defect behind
[Result AO](RESULT_AO_REFERENCE_POPULATION_AUDIT.md) inspectable without a dataset download,
model, API key, cloud service or sibling repository. It compares the supplied evaluation
reference with a supplied wider annotation table and returns an exact proximity witness.
It does not discover all evaluator filters or adjudicate whether a physical object exists.

The [real-data replay](REFERENCE_AUDIT_REAL_DATA_2026-09-07.md) also exercises the tool on
the complete cache-conditioned AO population and separately audits the omitted-frame boundary.

From an exported or checked-out research candidate:

```sh
python3 tools/measure/reference_population_audit.py research/reference-audit/0.1.0/demo.json
python3 -m unittest discover -s tools/measure -p test_reference_population_audit.py -v
```

The command reads one bounded JSON input and writes a JSON report to stdout. It has no
non-standard Python dependency, network call or external write. Invalid input produces an
error diagnostic on stderr, a nonzero exit and no success report. No MCP server is installed
or claimed. The current research topic is a local candidate, not a published package.

## What the example establishes

The fixture is authored synthetic data, not a benchmark or empirical performance sample.
It contains four predictions. One is near an included annotation; one is near an annotation
excluded from the supplied evaluation population; one has no nearby annotation in the wider
supplied table; the fourth has unavailable reference data. These yield distinct report rows.

The second prediction is a constructive counterexample to calling every evaluation-unmatched
prediction unmatched against the wider table. Its exclusion fraction in this synthetic input
is 1/2 among the two evaluation-unmatched predictions with available references. That number
is a demonstration of the definition, not a measured rate on real sensors.

Every row retains physical object presence as `unknown`, and the physical false-positive rate
is null. An empty, available annotation table is different from an unavailable table. Withheld,
invalid and unavailable inputs retain their original states even when the comparison cannot
be computed. Unavailable predictions are not folded into the observed denominator.

## Input and mathematical contract

The [input schema](../research/reference-audit/0.1.0/input.schema.json) pins JSON Schema
2020-12 and rejects unknown properties. The offline semantic checks additionally enforce
unique identifiers, distinct reference-scope identities, positive radius, reference-subset
membership, an 8 MiB input limit and at most one million distance evaluations. This is a
bounded research utility. No production throughput or latency has been benchmarked.

Each frame has a timestamp and coordinate-frame identity. The caller must supply positions
already aligned to that frame and time. Selection policy and reference scopes have explicit
identifiers bound by the input digest, but the tool cannot establish that these declarations
are true. Missing references cannot be represented as an empty array.

For prediction p, supplied wider annotation set W and evaluation subset E, define:

```text
d_E²(p) = min over e in E of ||p - e||²
d_W²(p) = min over w in W of ||p - w||²

excluded-reference witness: d_E²(p) > r² and d_W²(p) <= r²
```

An empty set has no nearest witness. It is handled explicitly rather than emitting infinity
as a JSON number. Coordinates and radius are bounded decimal strings; squared distances
are computed as rational numbers and emitted with integer strings for the numerator and
denominator. This avoids both an approximate square root at the boundary and precision loss
when a JavaScript client reads a large integer. It does not increase the accuracy of the
source measurements. Ties are broken by annotation identifier, and the radius boundary is
inclusive. Proximity is not one-to-one detection matching or a claim that the nearby
annotation corresponds to the predicted object.

The report binds the input and analyzer digests. A reader can rerun the calculation or write
an independent verifier from the equation. Agreement with the same implementation is an
integrity check, not independent scientific verification. Arbitrary file paths are read only
because an operator invoked a local command; this CLI is not a safe remote file-access API.

## Controls and remaining limitations

The tests include excluded-reference and unavailable-reference counterexamples, exact
radius boundaries, ordering invariance, rigid-transform invariance, large rational output,
invalid subset membership, duplicate JSON and object identifiers, nonfinite/unsupported
numbers, boolean timestamps, work-budget limits and the actual failing CLI path.

The [captured demo](../evidence/developer-value/reference-audit-demo-0.1.0.json) and
[verification record](../evidence/developer-value/verification-0.1.0.json) describe the
executed scope. These are conformance controls, not a held-out test set for discovering
evaluation errors.

The tool currently accepts explicit reference membership. Reconstructing the real evaluator's
selection from raw inputs, with all range/class/point-count/ignore rules and an independently
written comparator, is the harder next adapter problem. Such an adapter must retain its
upstream protocol and version. A second library containing the same mistaken filter would
not provide independence. The previous full-data AO analysis remains the real Reiyah evidence;
this portable example does not replace it or establish a comparison against other products.
