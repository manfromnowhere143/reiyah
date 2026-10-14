# Resource-qualified selected-cohort matching, 0.7.0

This is the original four-image, twelve-reference-case comparison with a newly
qualified admission composition. The first checked pair retains its exact 0.5
worker, checker and custody records. The other three pairs require the unchanged
0.6 numerical worker and checker wrapped by the explicit resource consumer. A
wrapper report is not relabeled as a report authored by the numerical checker.
No empirical matching was performed while qualifying this adapter.

`contract.json` fixes the same images, model variants, references, unit FP+FN loss,
exact continuous IoU >= 1/2, native limits and equal image weights. The three new
manifest digests change owned paths only. The consumer contract for each image is
prospectively pinned. `NUMERICAL_PRESERVATION.json` records byte/AST comparisons:
maximum-flow reference and native dependency map are unchanged; numerical code
changes only its result-version metadata.

`input_gate.py` requires each new wrapper's source identity, resource gate identity
and nested numerical checker identity separately. It binds the exact pair and
process bytes, checks every named wrapper observation, recomputes the resource
journal gate using the byte-identical qualified `resource_gate.py`, and requires
successful outer supervisor and consumer execution. The exact consumer command
includes its network-denying sandbox prefix. Missing, partial, stopped, unknown,
changed or misbound records refuse the full cohort. It does not create a legacy
receipt or stitch retained prefixes together.

`match_analysis.py` invokes the unchanged native fixed-case implementation for
all twelve graphs. `check_matching.py` independently parses source coordinates,
uses the unchanged Edmonds–Karp reference and checks the exact global-procedure
and imagewise intervals. Global G uses one procedure across all four images;
imagewise P admits all 81 procedure combinations. Either zero boundary remains
unresolved. Native caps, thresholds, matching semantics and failure rules remain
unchanged. All four complete pairs and twelve cells are required.

## Replay

Run in the selected matching Python environment with network denied and an
external 120-second/3-GiB limit. The candidate repository must contain the exact
native files in `DEPENDENCIES.json`. The tests use only authored inputs:

```sh
python -B test_matching.py --repository REIYAH --output NEW_AUTHORED_REPORT.json
python -B test_resource_matching.py --repository REIYAH --output NEW_RESOURCE_REPORT.json
```

The first command has 28 controls, including a complete mocked cohort, twelve
native cases, a separate oracle and direct enumeration of all 81 imagewise
choices. The second has 36 resource-composition rejection controls. It preserves
one initial expectation-string failure: truncation was correctly refused; the
test expected the wrong error substring. The original test source and log remain
in the development history. These are same-investigation authored controls, not
independent scientific replication or empirical source qualification.

The private input template is deliberately incomplete until all pairs qualify.
For new pairs, `resource_contract` joins the original pair/supervisor/checker and
checker-execution descriptors. `checker_execution` must use artifact
`reiyah.multiorg.resource-consumer-execution`, version `0.1.0`, and the exact
schema enforced in `admit_resource`. The first pair keeps its historical schema.

```sh
python -B match_analysis.py --input INPUT.json --input-sha256 SHA --repository REIYAH --output NEW_DIRECTORY
python -B check_matching.py --input INPUT.json --input-sha256 SHA --repository REIYAH --result NEW_DIRECTORY/result.json --result-sha256 SHA --output NEW_CHECK.json
```

## Limits

This gate consumes the hash-bound consumer execution record; it does not rerun
input preprocessing, inference or the whole-image checker. It rechecks the
resource journal but does not independently measure the past host. It reads the
runtime-after observation and consumes the wrapper's runtime qualification; it
does not repeat the installed-file census. The exact wrapper and its successful
outer execution remain necessary provenance. Consistent hashes do not authenticate
a wholly fabricated execution history. Sampling provides no exclusive disk
reservation, continuous bound or crash-durability guarantee. No physical truth,
cohort generalization, superiority or total-work advantage follows from passing
this adapter.
