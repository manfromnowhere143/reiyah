# Common assistance preparation, 0.1.0

Question: can the coordinator prepare complete, identical source assistance for both analysts
over an already bound observation population? This offline interface rebuilds source membership
and prepares a new private folder. It does not run or authorize human review.

```sh
python -B -m tools.perception_assistance \
  --binding-request /private/binding-request.json \
  --binding-request-sha256 EXPECTED_SHA256 \
  --base-label configuration-2 \
  --output /private/new-assistance-folder
```

The label choice is explicit and recorded privately; it is neither a random seed nor a claim
of blinding. Keep output outside every public checkout. The tool rejects its own source tree,
the observation package and reused output identities. Exit 0 means preparation only; exit 2
means invalid input or failed preparation. Partial output remains without a completion receipt.

The existing [binding interface](../../perception-binding/0.1.0/README.md) freshly checks exact
comparison/observation correspondence and original asset bytes. This tool then reads the
hash-bound metadata and prediction sources before interpretation. Source snapshots are unlinked
temporary descriptors, not a new permanent raw-data cache. No source payload enters public Git.

The complete metadata sample table must agree with catalog membership, scene and time for
every keyframe inside every bound closed window. All annotation rows are scanned, with unique
identities and selected instance/category/attribute/visibility joins. Immediate temporal links
are checked for existence, same source instance/scene, clock order and reciprocity, including
outside-package neighbors. Empty links must agree with instance endpoints. Missing tables
or broken joins cannot become empty annotations.

Each full prediction source is scanned to rebuild its results-key index. Selected catalog spans,
counts and availability must match exactly, including absent keys and present empty arrays.
All selected rows survive regardless of class eligibility, score, range or suppression. The
unchanged normalizer reruns at comparison anchors and must reproduce every receipt field and
every base/addition/weight operand. No matcher or physical-reference judgment runs here.

The [reader](READER.md) specifies field projection and temporal interpretation. Source numeric
values are preserved as decimal text; nonfinite numbers are explicit. Unsupported field sets,
malformed vectors and missing joins fail. This version supports the retained source schema;
new source variants require explicit handling. The nominal coordinate convention inherits the
existing [pinned SDK basis](../../perception-geometry/0.1.0/source-basis.json). Identifier and
configuration masking are not anonymity or verified blindness. Global poses are deliberately
present only in this later private assistance, outside the original discovery boundary.

The common folder contains only assistance and its reader. Operator custody retains source
IDs, original selected rows, table digests, source roles, normalization receipts and comparison.
Both common files have exact size/SHA-256 entries in `PREPARATION.json`, written last after
output readback. Input sources, existing package and implementation/runtime identities are
rechecked before output. This catches ordinary mutations; it is not an OS isolation guarantee.

Bounds include the inherited 1-GiB parent and 4-GiB expanded archive limits, 50,000 metadata
samples, two million annotations, one million instances, 10,000 lookup rows, 256 selected
frames, 100,000 selected annotations, 24 MiB each of selected raw annotations, projected
annotations and combined selected prediction frames, and 128 MiB
of final packet bytes. Prediction frames inherit the 512-row/1-MiB limits. Tables are streamed;
annotation identity checking retains a bounded set, and selected neighbor checking scans the
annotation table again. Costs must be measured, not inferred from test counts.

This is conventional source selection and projection. Its comparator is direct complete
source-table selection with the same evidence, coordinates and staged information. It claims
no new algorithm, superiority, physical accuracy, statistical coverage or changed decision.
The [rehearsal plan](../../perception-rehearsal/0.1.0/plan.json) still requires actual reviewers,
independence, staged delivery, equally informed conventional analysis and adjudication. The
separate 60-scene study remains unselected and unrun; Gate A remains unaccepted.
