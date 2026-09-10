# Development review rehearsal preparation

Interface ID: `reiyah.perception-rehearsal.interface`; version `0.1.0`; status `proposed`.

This is a practical wrapper around existing observation, discovery and comparison binding.
It prepares private starting material for people to test the workflow on already exposed
development evidence. It does not generate judgments or execute the proposed physical study.
Prior development exposure is a coordinator-established premise; the preparation tool does
not verify exposure history. Practical viewing tools and later assisted evidence are still
required before an actual review workflow can be called ready.

The [plan](plan.json) declares the question, staging, conventional comparator and negative
results to retain. The [operator guide](OPERATOR.md), [discovery guide](DISCOVERY_REVIEWER.md)
and [analyst guide](ANALYST.md) specify the actual work. Independent reviewers and a competent
conventional analyst remain unassigned. Their usability, physical judgment and total effort
cannot be substituted by a synthetic test or another validator.

```sh
python -B -m tools.perception_rehearsal \
  --binding-request /private/selected-binding-request.json \
  --binding-request-sha256 EXPECTED_FILE_SHA256 \
  --rehearsal-id NEW_32_HEX_PREPARATION_ID \
  --output /private/new-rehearsal
```

Use the existing observation/discovery dependencies, including Pillow and jsonschema. The
input is the exact [binding request](../../perception-binding/0.1.0/README.md); it is verified
before parsing and read again before output. The implementation freshly checks the package,
source population, clocks and original asset inventory. Original raw paths are not reopened;
the retained inventory remains a premise of the existing binding component.

The output directory must be new, absolute, outside the current source tree and observation
package, and have an existing parent. The caller must choose a private location outside all
public checkouts. The tool cannot infer every repository on a host or prove filesystem access
control. It creates a private directory, writes draft files without overwriting and writes
`PREPARATION.json` last. An interrupted directory without that record is incomplete and cannot
be reused. A preparation digest must be retained separately; it cannot establish human events.

Each discovery folder contains a neutral guide, package identity, capture index and an existing
format discovery draft. All reviewer handles remain null, exposure unknown, completion time
unrecorded, capture states not inspected and proposals empty. IDs distinguish drafts, not people
or study seeds. The CSV is a navigation index, not a record importer or an automatic inspection
claim. It preserves every window/capture occurrence and explicit availability; it discloses
only fields already in the neutral manifest. Geometry stays in that manifest. No raw assets
are duplicated, and no assistance is released.

The operator retains the binding report and request, role assignment draft, proposed plan and
empty effort sheet. The later analysis folder supplies identical empty conclusion templates
for both methods and instructions allowing conventional tools and the same mathematics.
These convenience drafts are not a new review schema or acceptance contract. Completed records,
assisted inspection and adjudication use the existing versioned interfaces.

Code, guide bytes and runtime identities are checked before/after preparation. The existing
binding request/package limits apply; each discovery draft is limited to 16 MiB and the kit
to 256 MiB. Larger jobs are rejected without truncation. Exit 0 means unassigned drafts were
prepared; exit 2 means invalid input, changed bytes or failed I/O. No decision is evaluated.

The [implementation](../../../tools/perception_rehearsal.py) and
[tests](../../../tests/test_perception_rehearsal.py) check population preservation, restricted
projection, empty initial states, invalid bindings and interrupted output. See the
[checkpoint](../../../docs/PERCEPTION_REHEARSAL_CHECKPOINT_2026-09-10.md) for actual runs and limits.
