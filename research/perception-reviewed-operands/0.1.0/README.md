# Reference-preserving common operands

Document ID: `reiyah.perception-reviewed-operands.guide` · Version `0.1.0` · Exploratory

The admission workflow retains reviewed contents and a joint conditional model. The existing
open-stage preparer deliberately refuses that model. This separate offline stage carries it
into a common private comparison for both analysts, together with every original review byte.
It prepares no physical judgment, grants no disclosure permission and performs no decision.

```sh
python -B -m tools.perception_reviewed_operands prepare \
  --binding-request /private/binding.json --binding-request-sha256 EXPECTED_BINDING \
  --admission-request /private/admission-request.json --admission-request-sha256 EXPECTED_REQUEST \
  --admission-report /private/admission.json --admission-report-sha256 EXPECTED_REPORT \
  --assistance /private/source-assistance --preparation-sha256 EXPECTED_ASSISTANCE \
  --output /private/fresh-reviewed-operands
```

For consumption, replace `prepare` and `--output` with `check`, `--packet` and
`--packet-sha256 EXPECTED_PACKET`; retain all separately selected source arguments. Exit 0
means prepared or checked; malformed, changed or unsupported input exits 2. Existing output
identities are refused. Partial writes have no completion receipt. All paths are private.

The report cannot select its own admission request or comparison. Its exact bytes must match a
fresh replay of the caller-selected [admission](../../perception-admission/0.1.0/README.md),
whose binding descriptor must equal the separately selected binding request. Source assistance
is checked through the unchanged [open operand stage](../../perception-operands/0.1.0/README.md),
including fresh population/assets, normalization and canonical row mappings. Different clocks,
sources, review contents or compiled models are refused. The original open stage is unchanged.

Only anchor and detection IDs are renamed in the compiled comparison. Every variable, clause,
feasible witness, object identity, edge condition, weight, loss, tolerance, assumption, availability
state and open reason is preserved. An inverse structural check restores the canonical comparison
and requires byte equality. No matcher is needed for this check. For each allowed assignment,
the detection renaming is a bijection on each graph, so it induces a bijection on matchings.
Maximum matched counts and the weighted loss difference therefore remain identical. The
unchanged joint model preserves the set of allowed assignments across anchors.

`common/admission.json` retains the complete original report, including all proposals, exclusions,
unresolved dispositions, world rationale, locators, nominal geometry/timing and coverage premises.
`common/renamings.json` exposes the source-to-common mapping and the original world/object links.
Both analysts receive exactly these bytes. This deliberate retention avoids a second lossy review
schema, but carries private source IDs, handles, paths and text. It is neither anonymity nor
demonstrated blindness. See the [analyst procedure](ANALYST.md) for tracing a graph object back
to a proposal and capture. Actual reviewer interaction still needs a working viewer and humans.

The inherited rules are explicitly labelled for this reviewed stage and bind their unchanged
open-stage predecessor bytes. Normalization, geometry, matching, loss and decision conventions
are preserved. Unknown or incomplete coverage stays open. Unavailable outputs stay unavailable.
Explicit finite empty worlds require the original admission's closure assumptions. A full
structural check rejects lost reference information even when the coarse interval agrees.

The limits inherited from admission include 64 worlds, 128 anchors, 128 objects per anchor/world,
200,000 proposal/world dispositions and the existing compilation resource fallbacks. The selected
report is at most 128 MiB, assistance at most 128 MiB, output at most 256 MiB, receipt at most
128 KiB and renamed core comparison at most 4 MiB. Rechecks bind ordinary source changes; they
do not create an OS-isolated snapshot or authenticate the people behind the selected records.
Replaying an old report against changed admission code/runtime may require a separately selected
new admission artifact. Never rewrite an old report or silently accept changed source identities.

The serious control is conventional per-world source-position matching and complete source joins.
This stage adds custody and an invertible projection, not a new matching algorithm or a measured
advantage. The [checkpoint](../../../docs/PERCEPTION_REVIEWED_OPERANDS_CHECKPOINT_2026-09-12.md)
records measured synthetic costs, adversarial checks, research-lane conformance and remaining gaps.
Current real evidence still supports only [-8,8]. No actual reviewed interpretation, selected
study cohort, external scientific review or Gate A acceptance is supplied here.
