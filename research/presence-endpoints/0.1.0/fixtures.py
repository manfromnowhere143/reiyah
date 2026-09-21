"""Authored development inputs; no empirical records or reserved images."""

from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
from itertools import product


def ratio(n, d=1):
    value = Fraction(n, d)
    return {"numerator": str(value.numerator), "denominator": str(value.denominator)}


def detection(name):
    return {
        "id": name,
        "record_sha256": sha256(("authored:" + name).encode()).hexdigest(),
    }


def case_for(name, base, extra, objects, mandatory, edges):
    optional = [o for o in objects if o not in mandatory]
    return {
        "artifact_id": "reiyah.perception-decision.input",
        "version": "0.1.0",
        "comparison_id": name,
        "cohort_id": "authored-presence-endpoints",
        "evidence_kind": "synthetic",
        "input_scope": "normalized_research_graphs",
        "assumptions": [
            "Authored graph and presence premises only; no physical or human observations."
        ],
        "model": {"variables": ["v_" + o for o in optional], "clauses": []},
        "loss": {
            "false_negative": ratio(1),
            "false_positive": ratio(1),
            "tolerance": ratio(0),
        },
        "anchors": [
            {
                "id": "anchor",
                "weight": ratio(1),
                "base": {"state": "observed", "value": [detection(n) for n in base]},
                "additions": {
                    "state": "observed",
                    "value": [detection(n) for n in extra],
                },
                "reference": {
                    "state": "finite",
                    "objects": [
                        {
                            "id": o,
                            "when": []
                            if o in mandatory
                            else [{"variable": "v_" + o, "value": True}],
                        }
                        for o in objects
                    ],
                    "edges": [
                        {"detection": d, "object": o, "when": []}
                        for d, o in sorted(edges)
                    ],
                },
            }
        ],
    }


def small_cases():
    choices = list(product(["a", "b"], ["x", "y", "z"]))
    for mask in range(64):
        edges = {e for i, e in enumerate(choices) if mask & (1 << i)}
        for required in range(8):
            mandatory = {
                o for i, o in enumerate(["x", "y", "z"]) if required & (1 << i)
            }
            yield case_for(
                f"small-{mask:02d}-{required}",
                ["a"],
                ["b"],
                ["x", "y", "z"],
                mandatory,
                edges,
            )


def large_cases():
    objects = [f"o{i:02d}" for i in range(20)]
    base = [f"d{i:02d}" for i in range(20)]
    edges = set(zip(base, objects))
    good = case_for(
        "large-guaranteed-gain",
        base,
        ["added"],
        objects + ["fixed"],
        {"fixed"},
        edges | {("added", "fixed")},
    )
    bad = case_for("large-unmatched-addition", base, ["added"], objects, set(), edges)
    competition = case_for(
        "large-competition",
        base + ["competing"],
        ["added"],
        objects + ["fixed", "rival"],
        {"fixed"},
        edges | {("competing", "fixed"), ("competing", "rival"), ("added", "fixed")},
    )
    zero = deepcopy(competition)
    zero["comparison_id"] = "large-zero-loss"
    zero["loss"].update(false_negative=ratio(0), false_positive=ratio(0))
    weighted = deepcopy(good)
    weighted["comparison_id"] = "large-weighted"
    weighted["anchors"][0]["weight"] = ratio(1, 3)
    other = deepcopy(bad["anchors"][0])
    other.update(id="second", weight=ratio(2, 3))
    for obj in other["reference"]["objects"]:
        obj["when"][0]["variable"] = "second_" + obj["when"][0]["variable"]
    weighted["anchors"].append(other)
    weighted["model"]["variables"] += ["second_" + v for v in bad["model"]["variables"]]
    boundary = deepcopy(good)
    boundary["comparison_id"] = "large-strict-boundary"
    boundary["loss"]["tolerance"] = ratio(1)
    return [good, bad, competition, zero, weighted, boundary]


def refusal_cases():
    original = case_for(
        "refusal-source", ["a"], ["b"], ["x", "y"], set(), {("a", "x"), ("b", "y")}
    )
    values = []

    def add(name, code, change):
        case = deepcopy(original)
        change(case)
        values.append((name, code, case))

    add(
        "negative_presence",
        "object_condition",
        lambda c: c["anchors"][0]["reference"]["objects"][0]["when"][0].update(
            value=False
        ),
    )
    add(
        "conjunctive_presence",
        "object_condition",
        lambda c: c["anchors"][0]["reference"]["objects"][0]["when"].append(
            {"variable": "v_y", "value": True}
        ),
    )
    add(
        "shared_presence",
        "shared_presence_variable",
        lambda c: c["anchors"][0]["reference"]["objects"][1]["when"][0].update(
            variable="v_x"
        ),
    )
    add(
        "model_clause",
        "model_clauses",
        lambda c: c["model"]["clauses"].append([{"variable": "v_x", "value": True}]),
    )
    add(
        "inconsistent_model",
        "model_clauses",
        lambda c: c["model"]["clauses"].append([]),
    )
    add(
        "conditional_edge",
        "conditional_edge",
        lambda c: c["anchors"][0]["reference"]["edges"][0]["when"].append(
            {"variable": "v_x", "value": True}
        ),
    )
    add(
        "open_reference",
        "open_reference",
        lambda c: c["anchors"][0].update(
            reference={"state": "open", "reason": "authored open premise"}
        ),
    )
    add(
        "missing_output",
        "outputs_unavailable",
        lambda c: c["anchors"][0].update(
            additions={"state": "missing", "reason": "authored missing input"}
        ),
    )
    add(
        "non_synthetic",
        "research_scope",
        lambda c: c.update(evidence_kind="benchmark_annotation_conditional"),
    )
    add(
        "invalid_contract",
        "invalid_input",
        lambda c: c["anchors"][0].update(weight=ratio(2)),
    )
    return values
