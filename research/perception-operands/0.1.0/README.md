# Equal analysis operand preparation, 0.1.0

Question: can an analyst trace every normalized detection and disposition to the full source
assistance and use the same exact comparison inputs as the Engine? This offline preparer makes
one private common folder for both methods. It handles the open-reference, pre-review stage only.

```sh
python -B -m tools.perception_operands \
  --binding-request /private/binding-request.json \
  --binding-request-sha256 EXPECTED_REQUEST_SHA256 \
  --assistance /private/existing-assistance \
  --preparation-sha256 EXPECTED_ASSISTANCE_PREPARATION_SHA256 \
  --output /private/new-analysis-folder
```

The expected assistance receipt and binding request are separate caller-selected inputs. All six
listed assistance files are read from bounded regular files and checked against the pinned
receipt before parsing. Extra/missing entries, symlinked role directories/files and duplicate
inventory paths fail. Receipt request identity, input identities and observation seal must match
the separately supplied request and a fresh [population/asset binding](../../perception-binding/0.1.0/README.md).

The preparer restores the retained source decimals and rechecks all common prediction rows,
frame membership, configuration roles and comparison clocks. It reruns the existing normalizer at
every comparison anchor and requires exact receipt and detection equality. The original complete
parent scan and annotation projection are the expected [assistance preparation](../../perception-assistance/0.1.0/README.md)'s
premise; this step does not rerun them or authenticate their physical truth. It checks source
artifacts again before return and assistance bytes before output. This catches ordinary changes;
it is not operating-system isolation or independent source provenance verification.

Projection renames structured anchor/detection IDs and regenerates each neutral record digest.
Source-row indices remain distinct through neutral IDs, even for equal-valued rows. All trace
entries, suppression blockers, qualification records, source availability, counts, rational loss,
weights, tolerance, assumptions and reason text remain represented. The [rules](rules.json) and
[analyst instructions](ANALYST.md) specify the unchanged comparison conventions. A finite reference
or nonempty joint model is refused explicitly, never reduced to an open model. Later admitted
references require their own source-bound common operands; this preparation is not that stage.

No producer matcher, reference compiler or human review runs during preparation. The result is a
conventional exact projection, not a new matching algorithm. Its comparator is direct complete
source-row accounting with the same evidence. It claims no speedup, novelty, physical accuracy,
statistical coverage or demonstrated decision value.

The output has a `common` folder and private `operator` custody. `PREPARATION.json` binds every
file's actual bytes and is written after readback, last. Outputs must be fresh and outside the
code, source assistance and observation package. Input and output each have a 128-MiB total limit;
the receipt is at most 64 KiB. Existing binding, source parsing and comparison limits also apply.
Malformed or unsupported input returns exit 2; exit 0 means prepared only. Partial output is
retained without a completion receipt. Nothing is disclosed, selected, adjudicated or accepted.

Source descriptions, assumptions and reasons can reveal identities. Keep this packet private;
renaming structured IDs is not a blindness or privacy guarantee. The unchanged
[rehearsal plan](../../perception-rehearsal/0.1.0/plan.json) still needs actual reviewers, conventional
analysis, adjudication, preserved discovery records and complete effort accounting. Gate A remains
unaccepted. The proposed physical study remains unselected and unrun.
