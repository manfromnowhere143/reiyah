"""How many observations are needed to decide, and when none will do.

Classifying single questions says which observations can move the enclosure. It
does not say how many are needed, in what order, or whether the declared
alternatives can settle the comparison at all. This computes those three exactly.

A set of questions induces a partition of the admitted worlds by answer vector.
The set **resolves** the comparison when every cell of that partition yields a
definite improvement criterion. The plan is an adaptive decision tree over the
declared questions, and its cost is the worst-case number of answers required.

Worst case, not expected. No probability over reference interpretations exists in
this program, so none is assumed here: the depth reported is a guarantee, not an
average, and it needs no prior.

The important output is often the negative one. Two admitted worlds can agree on
which objects exist and disagree only on which detections could match them. No
question about existence separates them, so no amount of looking for objects
decides the comparison. The program returns `unresolvable_by_declared_questions`
and names the worlds it cannot separate, rather than reporting a plan that would
not work.

Exhaustive over the declared questions within a stated bound, exact rational
arithmetic, standard library only, no data read, no reference invented.
"""
from fractions import Fraction
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cohort_packet import CaseError, build  # noqa: E402

MAX_WORLDS = 64
MAX_QUESTIONS = 32
MAX_NODES = 200000


def criterion_for(case, world_ids):
    """The improvement criterion over a subset of the admitted worlds."""
    subset = [w for w in case["joint_worlds"] if w["world_id"] in world_ids]
    trimmed = dict(case)
    trimmed["joint_worlds"] = subset
    report = build(trimmed)
    if report.get("enclosure") is None:
        return None
    return report["decision"]["improvement_criterion"]


def presence_questions(case):
    """Declared 'is this object present at this anchor' questions that actually split."""
    questions = []
    for anchor in case["anchors"]:
        if anchor.get("reference_state") != "finite":
            continue
        for entry in anchor.get("objects", []):
            yes = frozenset(w["world_id"] for w in case["joint_worlds"]
                            if entry["id"] in w["per_anchor"][anchor["id"]]["objects_present"])
            every = frozenset(w["world_id"] for w in case["joint_worlds"])
            if yes and yes != every:
                questions.append({"anchor": anchor["id"], "object": entry["id"], "yes": yes})
    if len(questions) > MAX_QUESTIONS:
        raise CaseError("too many declared questions for an exhaustive plan")
    return questions


def indistinguishable(worlds, questions):
    """Groups of worlds no declared question can separate."""
    signature = {}
    for world in worlds:
        key = tuple(world in q["yes"] for q in questions)
        signature.setdefault(key, []).append(world)
    return [sorted(group) for group in signature.values() if len(group) > 1]


def plan(case):
    report = build(case)
    if report.get("enclosure") is None:
        return {"state": report.get("state"), "reason": report.get("reason")}
    worlds = [w["world_id"] for w in case["joint_worlds"]]
    if len(worlds) > MAX_WORLDS:
        raise CaseError("too many worlds for an exhaustive plan")
    questions = presence_questions(case)

    # A cell that is already decided needs no more answers.
    memo = {}
    nodes = [0]

    def solve(cell):
        key = frozenset(cell)
        if key in memo:
            return memo[key]
        nodes[0] += 1
        if nodes[0] > MAX_NODES:
            raise CaseError("plan search exceeded the declared node budget")
        verdict = criterion_for(case, set(cell))
        if verdict != "unresolved":
            memo[key] = {"depth": 0, "decided": verdict, "ask": None}
            return memo[key]
        best = None
        for question in questions:
            yes = frozenset(w for w in cell if w in question["yes"])
            no = frozenset(w for w in cell if w not in question["yes"])
            if not yes or not no:
                continue
            left, right = solve(yes), solve(no)
            if left is None or right is None:
                continue
            depth = 1 + max(left["depth"], right["depth"])
            if best is None or depth < best["depth"]:
                best = {"depth": depth, "decided": None,
                        "ask": {"anchor": question["anchor"], "object": question["object"]},
                        "if_present": left, "if_absent": right}
        memo[key] = best
        return best

    root = solve(frozenset(worlds))
    blocked = indistinguishable(worlds, questions)
    if root is None:
        return {"state": "unresolvable_by_declared_questions",
                "reason": ("no sequence of declared presence questions makes every cell decided. "
                           "Some admitted worlds differ in a way that asking which objects exist "
                           "cannot separate, so more looking for objects will not settle this"),
                "indistinguishable_world_groups": blocked,
                "enclosure": report["enclosure"],
                "improvement_criterion": report["decision"]["improvement_criterion"],
                "questions_available": len(questions), "search_nodes": nodes[0]}
    return {"state": "resolvable", "enclosure": report["enclosure"],
            "improvement_criterion": report["decision"]["improvement_criterion"],
            "worst_case_observations": root["depth"],
            "first_question": root["ask"],
            "questions_available": len(questions),
            "indistinguishable_world_groups": blocked,
            "search_nodes": nodes[0], "plan": root}


def main(argv):
    if len(argv) != 2:
        sys.stderr.write("usage: resolution_plan.py CASE.json\n")
        return 2
    with open(argv[1], "r", encoding="utf-8") as handle:
        case = json.load(handle)
    try:
        result = plan(case)
    except CaseError as error:
        sys.stderr.write(f"case refused: {error}\n")
        return 3
    json.dump({"artifact_id": "reiyah.resolution-plan.report", "version": "0.1.0",
               "cohort_id": case.get("cohort_id"), **result,
               "cost_basis": ("worst case over the declared alternatives. Not an expectation, "
                              "because no probability over reference interpretations has been "
                              "established, and not a human time estimate"),
               "scope": ("the declared alternatives and declared presence questions only. An "
                         "unresolvable verdict means these questions cannot settle it, not that "
                         "no observation could")},
              sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
