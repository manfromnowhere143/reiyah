"""Meaningful authored input and decision boundaries before actual execution."""

import copy
import json
from fractions import Fraction
from pathlib import Path
import sys

import conventional
import native


def row(identity, score, status="Completed"):
    return {
        "route_id": identity,
        "scenario_name": "Authored",
        "town_name": "Town",
        "weather_id": "1",
        "status": status,
        "infractions": {"collision": []},
        "scores": {"score_composed": score},
    }


def doc(rows):
    return {"_checkpoint": {"records": rows}}


def call(module, a, b, n=2):
    return module.calculate(module.read(json.dumps(a)), module.read(json.dumps(b)), n)


def main():
    outcomes = []
    cases = [
        ("equal_complete", [100, 0], [100, 0], "excluded", ("0", "0")),
        ("strict_positive", [100, 1], [100, 0], "supported", ("1/2", "1/2")),
        ("strict_negative", [0, 1], [100, 0], "excluded", ("-99/2", "-99/2")),
        ("missing_is_not_zero", [100, 0], [0], "unresolved", ("0", "50")),
        ("missing_can_still_resolve", [100, 1], [0], "supported", ("1/2", "101/2")),
        ("both_missing", [], [], "unresolved", ("-100", "100")),
        ("recorded_failures_retained", [50, 0], [0, 0], "supported", ("25", "25")),
    ]
    for name, a, b, decision, bounds in cases:
        aa = doc(
            [
                row(
                    str(i),
                    x,
                    "Failed - TickRuntime"
                    if name.startswith("recorded")
                    else "Completed",
                )
                for i, x in enumerate(a)
            ]
        )
        bb = doc([row(str(i), x) for i, x in enumerate(b)])
        got = [call(m, aa, bb) for m in (conventional, native)]
        assert got[0]["summary"] == got[1]["summary"]
        s = got[0]["summary"]
        assert s["conditional_aggregate_decision"] == decision
        assert tuple(s["difference_bounds"]) == bounds
        outcomes.append({"id": name, "passed": True})
    a, b = doc([row("0", 20), row("1", 30)]), doc([row("0", 10)])
    mutations = []
    x = copy.deepcopy(a)
    x["_checkpoint"]["records"][1]["route_id"] = "0"
    mutations.append(("duplicate_route", x, b))
    x = copy.deepcopy(a)
    x["_checkpoint"]["records"][0]["scores"]["score_composed"] = 101
    mutations.append(("score_range", x, b))
    x = copy.deepcopy(a)
    x["_checkpoint"]["records"][0]["scores"]["score_composed"] = -1
    mutations.append(("score_range_negative", x, b))
    x = copy.deepcopy(a)
    del x["_checkpoint"]["records"][0]["scores"]["score_composed"]
    mutations.append(("missing_score", x, b))
    x = copy.deepcopy(a)
    x["_checkpoint"]["records"][0]["scores"]["score_composed"] = True
    mutations.append(("boolean_score", x, b))
    x = copy.deepcopy(a)
    x["_checkpoint"]["records"][0]["scores"]["score_composed"] = "20"
    mutations.append(("string_score", x, b))
    x = copy.deepcopy(a)
    x["_checkpoint"]["records"][0]["status"] = "Started"
    mutations.append(("started_not_observed", x, b))
    x = copy.deepcopy(a)
    x["_checkpoint"]["records"][0]["status"] = "Unknown"
    mutations.append(("unknown_status", x, b))
    x = copy.deepcopy(a)
    x["_checkpoint"]["records"][0]["scenario_name"] = "Conflicting"
    mutations.append(("metadata_conflict", x, b))
    x = copy.deepcopy(a)
    x["_checkpoint"]["records"][0]["infractions"] = None
    mutations.append(("missing_infractions", x, b))
    x = copy.deepcopy(b)
    x["_checkpoint"]["records"][0]["route_id"] = "2"
    mutations.append(("union_exceeds_population", a, x))
    x = copy.deepcopy(a)
    x["_checkpoint"]["records"].append(row("2", 0))
    mutations.append(("too_many_records", x, b))
    for name, aa, bb in mutations:
        for module in (conventional, native):
            try:
                call(module, aa, bb)
            except ValueError:
                pass
            else:
                raise AssertionError(name)
        outcomes.append({"id": name, "passed": True})
    for name, bad in (("nan", '{"x":NaN}'), ("duplicate_json", '{"x":1,"x":2}')):
        for module in (conventional, native):
            try:
                module.read(bad)
            except ValueError:
                pass
            else:
                raise AssertionError(name)
        outcomes.append({"id": name, "passed": True})
    p = native.calculate(native.read(json.dumps(a)), native.read(json.dumps(b)), 2)[
        "population"
    ]
    missing = [u for u in p["units"] if u["status"] == "missing"]
    assert missing and all((u["lower"], u["upper"]) == ("-1", "1") for u in missing)
    assert sum(Fraction(u["weight"]) for u in p["units"]) == 1
    value = {
        "document_id": "reiyah.public-decision.authored-controls",
        "version": "0.1.0",
        "controls": outcomes,
        "passed": len(outcomes),
        "source_outcomes_used": False,
    }
    target = Path(sys.argv[1])
    assert not target.exists()
    target.write_text(json.dumps(value, indent=2) + "\n")
    print(json.dumps(value))


if __name__ == "__main__":
    main()
