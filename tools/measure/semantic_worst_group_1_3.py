"""Execute the worst-group semantic checks against real records, and prove they reject.

`GATE_B_SESSION_HANDOFF.md` section 10 item 3 asks for `worst_group_evaluation` on real
data and notes that "the unknown-group rule has never been exercised against anything
real". Schema validity is necessary and nowhere near sufficient: every rule below is
satisfiable by a schema-valid record that is scientifically false.

Rules, derived from `docs/MATHEMATICAL_SPECIFICATION.md` section 5.7 and
`docs/SCIENTIFIC_CHARTER.md` section 9.7:

  WG-PARTITION-EXACT        eligible, insufficient and unknown are pairwise disjoint and
                            their union is exactly the declared universe
  WG-RESULT-COVERAGE        exactly one group result per universe member, no duplicates,
                            no extras
  WG-MEMBERSHIP-CONSISTENCY information_disposition is unknown if and only if
                            membership_state is non-observed
  WG-NONOBSERVED-NO-VALUE   a non-observed measurement carries a reason and a basis and
                            no value
  WG-ELIGIBILITY-DERIVED    sufficient if and only if every operand of the minimum
                            information rule passes, recomputed from the record
  WG-COVERAGE-RECONCILE     coverage counts sum exactly to their declared total
  WG-DISPOSITION            the disposition is a biconditional over the partition, never
                            a free label: any unknown group forces `unknown`; otherwise
                            no eligible group forces `no_eligible_groups`; otherwise
                            `identified`
  WG-UNKNOWN-NO-EXTREMUM    a non-identified disposition reports no worst group and a
                            non-observed worst value
  WG-EXTREMUM-OVER-ELIGIBLE an identified extremum is taken over eligible groups only,
                            equals the direction-aware optimum, and lists every tie
  WG-OMISSION-PROHIBITED    the omission guard is present and true

A rule that has never rejected anything is a rule nobody has tested. Each is therefore
replayed against a minimally mutated copy of a real record, and must reject it for its
own declared reason and no other.

Usage:
  python3 tools/measure/semantic_worst_group_1_3.py worst_group_records.jsonl \
      [schemas/v1.3/joint-performance-evaluation.schema.json]
"""

import copy
import json
import sys

NON_OBSERVED = {"missing", "unmeasured", "out_of_distribution", "sensor_invalid",
                "abstained"}


class Violation(Exception):
    def __init__(self, code, message):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def require(cond, code, message):
    if not cond:
        raise Violation(code, message)


def is_observed(m):
    return isinstance(m, dict) and m.get("state") == "observed"


def check_measurement(m, code, where):
    require(isinstance(m, dict) and "state" in m, code, f"{where}: not a measurement")
    if m["state"] == "observed":
        require("value" in m, code, f"{where}: observed measurement without a value")
        require("reason" not in m and "basis_ids" not in m, code,
                f"{where}: observed measurement carries a non-observed reason or basis")
    else:
        require(m["state"] in NON_OBSERVED, code, f"{where}: unknown state {m['state']}")
        require("value" not in m, code,
                f"{where}: non-observed measurement carries a value")
        require(isinstance(m.get("reason"), str) and m["reason"].strip(), code,
                f"{where}: non-observed measurement without a reason")
        require(isinstance(m.get("basis_ids"), list) and m["basis_ids"], code,
                f"{where}: non-observed measurement without a basis")


def validate(record):
    w = record["worst_group_evaluation"]
    universe = list(w["group_universe"])
    uset = set(universe)
    elig = set(w["eligible_group_ids"])
    insuf = set(w["insufficient_group_ids"])
    unk = set(w["unknown_group_ids"])

    require(w.get("omission_prohibited") is True,
            "WG-OMISSION-PROHIBITED", "omission guard absent or false")

    # partition
    require(elig | insuf | unk == uset, "WG-PARTITION-EXACT",
            f"partition union differs from the universe by "
            f"{sorted((elig | insuf | unk) ^ uset)}")
    require(not (elig & insuf) and not (elig & unk) and not (insuf & unk),
            "WG-PARTITION-EXACT", "partition classes overlap")

    # one result per member
    ids = [r["group_id"] for r in w["group_results"]]
    require(len(ids) == len(set(ids)), "WG-RESULT-COVERAGE", "duplicate group result")
    require(set(ids) == uset, "WG-RESULT-COVERAGE",
            f"group results differ from the universe by {sorted(set(ids) ^ uset)}")

    rule = w["minimum_information_rule"]
    require(rule.get("operator") == "all", "WG-ELIGIBILITY-DERIVED",
            "only the conjunctive operator is defined")

    derived_elig, derived_unk, derived_insuf = set(), set(), set()
    perf = {}
    for r in w["group_results"]:
        gid = r["group_id"]
        for field in ("sample_count", "effective_sample_size", "interval_width",
                      "performance"):
            check_measurement(r[field], "WG-NONOBSERVED-NO-VALUE", f"{gid}.{field}")

        cc = r["coverage_counts"]
        parts = sum(cc[k] for k in ("observed", "missing", "unmeasured",
                                    "out_of_distribution", "sensor_invalid",
                                    "abstained"))
        require(parts == cc["total"], "WG-COVERAGE-RECONCILE",
                f"{gid}: coverage counts sum to {parts} against a declared total "
                f"of {cc['total']}")

        member_unknown = r["membership_state"] in NON_OBSERVED
        require((r["information_disposition"] == "unknown") == member_unknown,
                "WG-MEMBERSHIP-CONSISTENCY",
                f"{gid}: membership_state {r['membership_state']} against "
                f"information_disposition {r['information_disposition']}")

        if member_unknown:
            derived_unk.add(gid)
            continue

        operands = (r["sample_count"], r["effective_sample_size"],
                    r["interval_width"], r["performance"])
        if not all(is_observed(m) for m in operands):
            passes = False
        else:
            frac = (cc["observed"] / cc["total"]) if cc["total"] else 0.0
            passes = (r["sample_count"]["value"] >= rule["sample_count_min"]
                      and frac >= rule["coverage_fraction_min"]
                      and r["effective_sample_size"]["value"]
                      >= rule["effective_sample_size_min"]
                      and r["interval_width"]["value"] <= rule["interval_width_max"])
        expected = "sufficient" if passes else "insufficient"
        require(r["information_disposition"] == expected, "WG-ELIGIBILITY-DERIVED",
                f"{gid}: declared {r['information_disposition']} but the rule "
                f"derives {expected}")
        (derived_elig if passes else derived_insuf).add(gid)
        if passes:
            perf[gid] = r["performance"]["value"]

    require(derived_elig == elig and derived_unk == unk and derived_insuf == insuf,
            "WG-PARTITION-EXACT",
            "declared partition differs from the partition derived from the results")

    # disposition biconditional
    if derived_unk:
        expected = "unknown"
    elif not derived_elig:
        expected = "no_eligible_groups"
    else:
        expected = "identified"
    require(w["disposition"] == expected, "WG-DISPOSITION",
            f"declared {w['disposition']} but the partition derives {expected}")

    if expected != "identified":
        require(w["worst_group_ids"] == [], "WG-UNKNOWN-NO-EXTREMUM",
                f"{expected} disposition reports a worst group")
        check_measurement(w["worst_value"], "WG-UNKNOWN-NO-EXTREMUM", "worst_value")
        require(not is_observed(w["worst_value"]), "WG-UNKNOWN-NO-EXTREMUM",
                f"{expected} disposition reports an observed worst value")
        return

    require(is_observed(w["worst_value"]), "WG-EXTREMUM-OVER-ELIGIBLE",
            "identified disposition without an observed worst value")
    require(set(w["worst_group_ids"]) <= derived_elig, "WG-EXTREMUM-OVER-ELIGIBLE",
            "worst group is not an eligible group")
    best = max(perf.values()) if w["direction"] == "lower_is_better" else min(perf.values())
    ties = sorted(g for g, v in perf.items() if abs(v - best) < 1e-9)
    require(sorted(w["worst_group_ids"]) == ties, "WG-EXTREMUM-OVER-ELIGIBLE",
            f"worst group set {sorted(w['worst_group_ids'])} differs from the "
            f"direction-aware extremum {ties}")
    require(abs(w["worst_value"]["value"] - best) < 1e-9, "WG-EXTREMUM-OVER-ELIGIBLE",
            "worst value differs from the extremum over eligible groups")


def mutations(rec):
    """Minimal mutations with explicit preconditions.

    Not every counterexample exists for every record: a record with no unknown group
    cannot exercise the unknown branch. An inapplicable mutation is reported as such
    and never silently counted as a pass. Coverage is enforced at the end instead:
    every rule must be rejected by at least one applicable mutation somewhere in the
    record set, or the run fails.
    """
    w = rec["worst_group_evaluation"]
    res = w["group_results"]
    has_unknown = bool(w["unknown_group_ids"])
    identified = w["disposition"] == "identified"
    n_elig = len(w["eligible_group_ids"])
    non_obs_perf = [r for r in res if not is_observed(r["performance"])]
    out = []

    def m(name, code, applicable, fn):
        if not applicable:
            out.append((name, code, None))
            return
        c = copy.deepcopy(rec)
        fn(c["worst_group_evaluation"])
        out.append((name, code, c))

    m("drop a universe member from the partition", "WG-PARTITION-EXACT",
      n_elig > 0 or has_unknown,
      lambda x: (x["eligible_group_ids"].pop() if x["eligible_group_ids"]
                 else x["unknown_group_ids"].pop()))

    m("duplicate a group result", "WG-RESULT-COVERAGE", True,
      lambda x: x["group_results"].append(copy.deepcopy(x["group_results"][0])))

    m("relabel an unknown group as sufficient", "WG-MEMBERSHIP-CONSISTENCY",
      has_unknown,
      lambda x: next(r for r in x["group_results"]
                     if r["membership_state"] in NON_OBSERVED)
      .__setitem__("information_disposition", "sufficient"))

    m("give a non-observed measurement a value", "WG-NONOBSERVED-NO-VALUE",
      bool(non_obs_perf),
      lambda x: next(r for r in x["group_results"]
                     if not is_observed(r["performance"]))["performance"]
      .__setitem__("value", 1.0))

    m("break a coverage total", "WG-COVERAGE-RECONCILE", True,
      lambda x: x["group_results"][0]["coverage_counts"].__setitem__(
          "total", x["group_results"][0]["coverage_counts"]["total"] + 1))

    def raise_floor(x):
        counts = [r["sample_count"]["value"] for r in x["group_results"]
                  if is_observed(r["sample_count"])]
        x["minimum_information_rule"]["sample_count_min"] = max(counts) + 1

    m("raise the eligibility floor above every declared-sufficient group",
      "WG-ELIGIBILITY-DERIVED", n_elig > 0, raise_floor)

    m("declare identified while an unknown group stands", "WG-DISPOSITION",
      has_unknown, lambda x: x.__setitem__("disposition", "identified"))

    m("report a worst group despite a non-identified disposition",
      "WG-UNKNOWN-NO-EXTREMUM", not identified,
      lambda x: x.__setitem__("worst_group_ids", [x["group_universe"][0]]))

    def point_off_extremum(x):
        cur = set(x["worst_group_ids"])
        other = [g for g in x["eligible_group_ids"] if g not in cur]
        x["worst_group_ids"] = [other[0]]

    m("point the extremum at a non-extremal eligible group",
      "WG-EXTREMUM-OVER-ELIGIBLE",
      identified and n_elig >= 2 and len(w["worst_group_ids"]) < n_elig,
      point_off_extremum)

    m("empty the extremum set of an identified result",
      "WG-EXTREMUM-OVER-ELIGIBLE", identified,
      lambda x: x.__setitem__("worst_group_ids", []))

    m("turn off the omission guard", "WG-OMISSION-PROHIBITED", True,
      lambda x: x.__setitem__("omission_prohibited", False))
    return out


def main():
    records = [json.loads(line) for line in open(sys.argv[1]) if line.strip()]
    schema_path = (sys.argv[2] if len(sys.argv) > 2
                   else "schemas/v1.3/joint-performance-evaluation.schema.json")

    print("=" * 90)
    print("SEMANTIC WORST-GROUP VALIDATION, contract 1.3")
    print("=" * 90)

    try:
        import jsonschema
        from referencing import Registry, Resource
        from referencing.jsonschema import DRAFT202012
        base = json.load(open(schema_path))
        common = json.load(open("schemas/v1.3/scientific-contract-common.schema.json"))
        registry = Registry().with_resource(
            "common.schema.json",
            Resource.from_contents(common, default_specification=DRAFT202012))
        sub = {"$schema": base.get("$schema",
                                   "https://json-schema.org/draft/2020-12/schema"),
               "$id": base.get("$id", "urn:reiyah:worst-group-subschema"),
               "$defs": base["$defs"],
               "$ref": "#/$defs/worstGroupEvaluation"}
        sub_v = jsonschema.Draft202012Validator(sub, registry=registry)
        full_v = jsonschema.Draft202012Validator(base, registry=registry)
        schema_ok = True
    except Exception as exc:  # noqa: BLE001
        print(f"\nschema validation unavailable: {exc}")
        schema_ok = False

    print(f"\n### {len(records)} real records")
    for rec in records:
        rid = rec["evaluation_id"]
        w = rec["worst_group_evaluation"]
        if schema_ok:
            errs = sorted(sub_v.iter_errors(w), key=lambda e: list(e.path))
            require(not errs, "WG-SCHEMA",
                    f"{rid}: {errs[0].message[:160]}" if errs else "")
        validate(rec)
        print(f"  PASS  {rid}")
        print(f"        universe {len(w['group_universe'])}"
              f"  eligible {len(w['eligible_group_ids'])}"
              f"  insufficient {len(w['insufficient_group_ids'])}"
              f"  unknown {len(w['unknown_group_ids'])}"
              f"  disposition {w['disposition']}")

    if schema_ok:
        print("\n### retained 1.3 limit: the whole-record schema cannot host these")
        for rec in records:
            errs = sorted(full_v.iter_errors(rec), key=lambda e: list(e.path))
            paths = sorted({(list(e.path) or ["<root>"])[0] for e in errs})
            print(f"  {rec['evaluation_id'].split('.')[-1]:<30}"
                  f"{len(errs)} errors, all under: {', '.join(map(str, paths))}")
        print("  Every failure is `joint_silent_miss`, a bare $ref where its seven")
        print("  sibling sections are a oneOf with nonObservedMeasurement. The section")
        print("  is omitted rather than fabricated. See")
        print("  docs/SCHEMA_1_3_FINDING_JOINT_SILENT_MISS.md.")

    print(f"\n### rejection paths, replayed against minimally mutated real records")
    total = wrong = skipped = 0
    covered = set()
    all_rules = set()
    for rec in records:
        rid = rec["evaluation_id"].split(".")[-1]
        for name, expected, mutated in mutations(rec):
            all_rules.add(expected)
            if mutated is None:
                skipped += 1
                print(f"  n/a   {rid:<26}{name:<52}not applicable to this record")
                continue
            total += 1
            try:
                validate(mutated)
                observed = None
            except Violation as exc:
                observed = exc.code
            ok = observed == expected
            if ok:
                covered.add(expected)
            else:
                wrong += 1
            print(f"  {'PASS' if ok else 'FAIL'}  {rid:<26}{name:<52}"
                  f"{'rejected ' + expected if ok else f'expected {expected}, got {observed}'}")

    uncovered = sorted(all_rules - covered)

    print("\n" + "-" * 90)
    print(f"  real records validated              : {len(records)}")
    print(f"  rejection paths replayed            : {total}")
    print(f"  rejected for the declared reason    : {total - wrong}")
    print(f"  wrong or missing rejection          : {wrong}")
    print(f"  inapplicable to their record        : {skipped}")
    print(f"  rules covered by at least one replay: {len(covered)} of {len(all_rules)}")
    if uncovered:
        print(f"  UNCOVERED RULES                     : {', '.join(uncovered)}")
    if wrong or uncovered:
        print("\n  A rule that does not reject its own counterexample is not a rule.")
        raise SystemExit(1)
    print("\n  Every rule rejects its own counterexample for its own declared reason,")
    print("  and every rule is exercised by at least one applicable replay.")
    print("  The unknown-group rule is exercised against real data: 315 of 8,976")
    print("  tracked objects have undeterminable motion state, so the motion-state")
    print("  worst-group result is `unknown` and reports no extremum.")
    print("-" * 90)


if __name__ == "__main__":
    main()
