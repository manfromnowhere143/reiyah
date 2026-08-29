"""Semantic validator for the 1.4 coincident-miss metric record.

Schema validity is necessary and nowhere near sufficient: every rule below is
satisfiable by a schema-valid record that is scientifically false. That is the same
position `docs/MATHEMATICAL_SPECIFICATION.md` section 9 takes, and the same one the
Gate B schema work reached by pointing a schema at real data.

THIS IS A PORT-CLASS ARTIFACT, NOT THE ARTIFACT OF RECORD. The shipped offline
production handler lives in a released Gate A byte whose substitution guard compares
against a frozen in-module constant pinned to synthetic fixture identities, so it
cannot accept a real record and a successor to it is a Gate A act in another lane.
See `docs/CLAIM_AUDIT_2026-08-29.md` section 4. Any record this tool accepts carries
`validated_by` of at most `port`, never `artifact_of_record`.

THE RULES

  SR-01  cells sum to the eligible denominator plus the unknown-operand count
  SR-02  c is recomputable from the cells within tolerance
  SR-03  a zero marginal yields the explicit undefined state, never a number
  SR-04  any unknown operand propagates into c_state
  SR-05  the universe is not filtered by an evaluated channel
  SR-06  the reference process is independent of every evaluated channel
  SR-07  the matcher does not use channel-specific geometry
  SR-08  no channel that failed its headline reproduction gate is admitted
  SR-09  a box-unit record reports its design effect
  SR-10  an L3 identification claim rests on blinded reannotation
  SR-11  the outer identification set contains the inner sampling interval
  SR-12  a port-validated record may not claim `supported`
  SR-13  a non-sufficient stratum may not claim `supported`

The run FAILS unless the good fixture passes every rule AND every rule is rejected by
at least one applicable known-bad fixture. A rule with no counterexample is untested,
and an untested rule is not a rule.

A fixture may trip more than one rule. That is acceptable provided it trips its own
declared rule: a mutation that breaks the cell sum also breaks the recomputation of c,
and pretending otherwise would mean weakening one of the two checks.

Usage:
  python3 tools/measure/validate_metric_record_1_4.py
"""

import json
import pathlib

SCHEMA = "schemas/v1.4/coincident-miss-metric-record.schema.json"
GOOD_DIR = "fixtures/v1.4/good"
BAD_DIR = "fixtures/v1.4/known-bad"
TOL = 1e-6

ALL_RULES = [f"SR-{i:02d}" for i in range(1, 14)]


def check(record):
    """Return the ordered list of violated rule ids."""
    bad = []
    cells = record["cells"]
    a = cells["both_miss"]
    b = cells["first_only_miss"]
    c2 = cells["second_only_miss"]
    d = cells["neither_miss"]
    unk = cells["unknown_operand"]
    ev = record["estimand_vector"]
    uni = record["universe"]

    n = a + b + c2 + d
    if n + unk != uni["eligible_denominator"] + unk or n != uni["eligible_denominator"]:
        bad.append("SR-01")

    p1 = (a + b) / n if n else 0.0
    p2 = (a + c2) / n if n else 0.0
    pj = a / n if n else 0.0
    denom = p1 * p2
    if denom <= 0:
        if ev["c_state"] != "undefined_zero_denominator" or ev["c"] is not None:
            bad.append("SR-03")
    else:
        expected = pj / denom
        if ev["c"] is None or abs(ev["c"] - expected) > 1e-3:
            bad.append("SR-02")

    if unk > 0 and ev["c_state"] != "unknown_operand_present":
        bad.append("SR-04")

    if uni["filter_defined_on_evaluated_channel"] is not False:
        bad.append("SR-05")
    if uni["reference_process_ref"]["independent_of_every_evaluated_channel"] is not True:
        bad.append("SR-06")
    if record["operating_point"]["matcher_uses_channel_specific_geometry"] is not False:
        bad.append("SR-07")
    if any(ch["headline_metric_reproduced"] != "within_declared_tolerance"
           for ch in record["channels"]):
        bad.append("SR-08")

    clus = record["clustering"]
    if clus["primary_unit"] == "detection_box" and not isinstance(
            clus["design_effect_state"], (int, float)):
        bad.append("SR-09")

    ident = record["identification"]
    if ident["ladder_level"] == "L3" and ident["delta_source"] != "blinded_reannotation":
        bad.append("SR-10")

    unc = record["uncertainty"]
    ol, oh = ident["outer_low"], ident["outer_high"]
    il, ih = unc["interval_low"], unc["interval_high"]
    if isinstance(oh, str):
        contains = ol is not None and il is not None and ol <= il + TOL
    else:
        contains = (ol is not None and oh is not None and il is not None
                    and ih is not None and ol <= il + TOL and oh + TOL >= ih)
    if not contains:
        bad.append("SR-11")

    if record["lifecycle_status"] == "supported":
        if record["validated_by"] != "artifact_of_record":
            bad.append("SR-12")
        if record["stratum"]["partition_class"] != "sufficient":
            bad.append("SR-13")

    return bad


def load(path):
    record = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    expected = record.pop("_expected_rejection_rule", None)
    return record, expected


def main() -> int:
    schema = json.loads(pathlib.Path(SCHEMA).read_text(encoding="utf-8"))
    import jsonschema

    print("=" * 92)
    print("COINCIDENT-MISS METRIC RECORD 1.4 - SCHEMA PLUS SEMANTIC VALIDATION")
    print("port-class validator; the artifact of record cannot accept a real record")
    print("=" * 92)

    failures = 0
    print("\nKNOWN-GOOD")
    for path in sorted(pathlib.Path(GOOD_DIR).glob("*.json")):
        record, _ = load(path)
        try:
            jsonschema.validate(record, schema)
            schema_ok = True
        except jsonschema.ValidationError as exc:
            schema_ok = False
            print(f"  {path.name}: SCHEMA FAIL {str(exc).splitlines()[0]}")
        violations = check(record)
        status = "PASS" if schema_ok and not violations else "FAIL"
        if status == "FAIL":
            failures += 1
        print(f"  {path.name:<44} schema={'ok' if schema_ok else 'FAIL':<5} "
              f"semantic={'clean' if not violations else ','.join(violations):<12} {status}")

    print("\nKNOWN-BAD, each must be rejected for its declared reason")
    covered = set()
    for path in sorted(pathlib.Path(BAD_DIR).glob("*.json")):
        record, expected = load(path)
        violations = check(record)
        hit = expected in violations
        if hit:
            covered.add(expected)
        else:
            failures += 1
        print(f"  {path.name:<44} expected={expected:<7} "
              f"got={','.join(violations) if violations else 'NONE':<14} "
              f"{'REJECTED for its reason' if hit else 'DID NOT REJECT FOR ITS REASON'}")

    missing = [r for r in ALL_RULES if r not in covered]
    print("\n" + "-" * 92)
    print(f"  rules declared : {len(ALL_RULES)}")
    print(f"  rules covered  : {len(covered)}")
    if missing:
        failures += 1
        print(f"  UNCOVERED      : {', '.join(missing)}")
        print("  A rule with no counterexample is untested, and an untested rule is not a rule.")
    else:
        print("  every rule is rejected by at least one applicable known-bad fixture")

    print("-" * 92)
    if failures:
        print(f"  RESULT: FAIL, {failures} problem(s)")
        return 1
    print("  RESULT: PASS")
    print("  A record accepted here carries validated_by of at most `port`.")
    print("  Schema validity plus these rules is still not a measurement.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
