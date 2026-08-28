# Schema 1.3 limit: `joint_silent_miss` compels a fabrication

Document ID: `reiyah.schema-1-3-finding-joint-silent-miss`

Version: `0.1.0`

Lifecycle status: `proposed`

## The limit

`schemas/v1.3/joint-performance-evaluation.schema.json` declares eight evaluation
sections. Seven accept either a complete evaluation or an explicit non-observed state:

| Section | Form |
|---|---|
| `selective_evaluation` | `oneOf` complete or `nonObservedMeasurement` |
| `ood_evaluation` | `oneOf` complete or `nonObservedMeasurement` |
| `conformal_evaluation` | `oneOf` complete or `nonObservedMeasurement` |
| `transfer_evaluation` | `oneOf` complete or `nonObservedMeasurement` |
| `worst_group_evaluation` | `oneOf` complete or `nonObservedMeasurement` |
| `evidence_binding` | `oneOf` gap binding or `nonObservedMeasurement` |
| `study_ref`, `odd_ref` | `oneOf` reference or `nonObservedMeasurement` |
| **`joint_silent_miss`** | **bare `$ref`, no non-observed form** |

`SCHEMA_1_3_FINDINGS.md` records that eight sections rejected a non-observed state and
that this "inverts Reiyah's own status model one level up". Seven were repaired.
`joint_silent_miss` was missed.

## Why it matters, found by use rather than by reading

Building the first `worst_group_evaluation` records from measured data surfaced it. Those
records measure worst-group dependence. They do not measure joint silent misses, and
cannot: this source observes neither warning issuance nor fallback activation, which
`CONTRACT_CAUGHT_AN_ERROR.md` already established.

The honest statement is "joint silent miss: unmeasured, because silence is not
establishable from this source". Schema 1.3 cannot express it. `jointSilentMiss` requires
thirteen properties, and four of them have no non-observed form:

- `opportunity_set_ref`, a versioned reference to an opportunity set that does not exist;
- `opportunity_window`, a window for an analysis that was never scoped;
- `opportunity_rows`, rows for opportunities that were never enumerated; and
- `channel_contract`, binding array positions for channels never compared this way.

The counts inside it are measurements and can honestly be non-observed. The scaffolding
around them cannot. To emit a schema-valid record, an author must **invent four
identities for an analysis that was never run**.

That is the same defect class as the five in `SCHEMA_1_3_FINDINGS.md`: the contract
refuses a truthful record and would accept a fabricated one.

## What was done

The section is **omitted**, not fabricated. The three records in
`worst_group_records.jsonl` therefore fail whole-record validation with exactly one error
each, and that failure is retained as the evidence for this finding rather than hidden.

`tools/measure/semantic_worst_group_1_3.py` validates the `worst_group_evaluation`
subtree against `#/$defs/worstGroupEvaluation`, which is the part of the contract that
legitimately applies, and prints the whole-record failure separately so the limit stays
visible on every run.

No schema was weakened. No record was fabricated. The refusal is preserved.

## Proposed successor change

One line, in the `1.4` successor:

```json
"joint_silent_miss": {
  "oneOf": [
    {"$ref": "#/$defs/jointSilentMiss"},
    {"$ref": "common.schema.json#/$defs/nonObservedMeasurement"}
  ]
}
```

This restores parity with the seven sibling sections and with the status model. It does
not relax `jointSilentMiss` itself: a record that *does* measure joint silent misses must
still satisfy every one of its thirteen properties and every semantic rule.

**This change must not be made to any released `1.3` byte.** It belongs in a versioned
successor with its own lineage, and it needs the same treatment the `1.3` successor got:
known-bad fixtures proving that a non-observed `joint_silent_miss` cannot be used to
smuggle a favourable disposition past the joint rules.

## Non-claims

This is a representational finding about a proposed schema. It creates no scientific
support, no safety finding, and no operator acceptance, and it modifies no released byte.
