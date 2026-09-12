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

The important output is often the negative one, and there are three different
negatives which version 0.1.0 collapsed into one:

  no_admitted_reference              there is no admitted joint world at all. The
                                     count bound still holds, but nothing has been
                                     said about the world, so there is no model to
                                     be ambiguous about and no question to ask.
  unresolvable_by_declared_questions two or more admitted worlds agree on which
                                     objects exist and differ only in which
                                     detections could match them. Presence
                                     questions cannot separate them, and the
                                     witnessing group is named.
  unresolvable_due_to_open_anchors   every world is separable, but an open anchor
                                     contributes an interval that leaves even a
                                     single world undecided.
  blocked_by_unanswerable_questions  a declared question would divide the witness
                                     cell, but the case marks it unanswerable. The
                                     obstacle is the observation procedure.
  undecided_single_world             the witness cell is one finite world whose
                                     value does not clear the tolerance. Nothing
                                     is ambiguous; the configurations are close.

Version 0.1.0 reported the first as the second, on a cohort with zero admitted
worlds and an empty indistinguishable group, which invented a finite-model reason
for an absent reference basis. That conflation is retained as a rejected case.

An answer model is declared rather than assumed. The depth below is a guarantee
only if every permitted question can actually be answered, truthfully, as a
binary, at equal cost. That is an assumption about an observation procedure and
not an observation. A question may be marked unanswerable in the case, and it is
then excluded from the permitted set instead of being silently counted as free.

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
            if entry.get("answerable") is False:
                continue
            if yes and yes != every:
                questions.append({"anchor": anchor["id"], "object": entry["id"], "yes": yes})
    if len(questions) > MAX_QUESTIONS:
        raise CaseError("too many declared questions for an exhaustive plan")
    return questions


def unanswerable_questions(case):
    """Declared questions that would split the worlds but are marked unanswerable.

    These are kept visible. A question that cannot be answered is not a question
    that costs nothing; it is one the plan may not use, and saying so is the
    difference between a missing observation and an ambiguous world.
    """
    withheld = []
    every = frozenset(w["world_id"] for w in case["joint_worlds"])
    for anchor in case["anchors"]:
        if anchor.get("reference_state") != "finite":
            continue
        for entry in anchor.get("objects", []):
            if entry.get("answerable") is not False:
                continue
            yes = frozenset(w["world_id"] for w in case["joint_worlds"]
                            if entry["id"] in w["per_anchor"][anchor["id"]]["objects_present"])
            if yes and yes != every:
                withheld.append({"anchor": anchor["id"], "object": entry["id"], "yes": yes,
                                 "reason_not_answerable": entry.get("answer_obstacle",
                                                                    "not stated")})
    return withheld


def indistinguishable(worlds, questions):
    """Groups of worlds no declared question can separate."""
    signature = {}
    for world in worlds:
        key = tuple(world in q["yes"] for q in questions)
        signature.setdefault(key, []).append(world)
    return [sorted(group) for group in signature.values() if len(group) > 1]


ANSWER_MODEL = {
    "assumed": "every permitted question is answerable, truthfully, as a binary, at equal cost",
    "status": "an assumption about an observation procedure, not an observation",
    "not_modelled": ["unable to judge", "an ambiguous answer", "no evidence at that location",
                     "an exposure or staging restriction", "unequal cost between questions"],
    "mechanism": ("a case may mark a question unanswerable, which removes it from the permitted "
                  "set rather than counting it as free"),
}


def plan(case):
    report = build(case)
    if report.get("enclosure") is None:
        return {"state": report.get("state"), "reason": report.get("reason"),
                "answer_model": ANSWER_MODEL}
    worlds = [w["world_id"] for w in case["joint_worlds"]]
    if not worlds:
        # No admitted joint world at all. The count bound stands; nothing has been
        # said about the world, so there is no model to be ambiguous about.
        return {"state": "no_admitted_reference",
                "reason": ("there is no admitted joint reference interpretation. The enclosure is "
                           "the conditional count bound and no question is available, because "
                           "nothing has been asserted that an observation could confirm or deny. "
                           "This is an absent reference basis, not an ambiguous model"),
                "enclosure": report["enclosure"],
                "improvement_criterion": report["decision"]["improvement_criterion"],
                "indistinguishable_world_groups": [], "questions_available": 0,
                "prerequisite": "an admitted joint reference interpretation from the owning lane",
                "answer_model": ANSWER_MODEL}
    if len(worlds) > MAX_WORLDS:
        raise CaseError("too many worlds for an exhaustive plan")
    questions = presence_questions(case)

    # A cell that is already decided needs no more answers.
    memo = {}
    nodes = [0]
    stuck = []

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
        splittable = False
        for question in questions:
            yes = frozenset(w for w in cell if w in question["yes"])
            no = frozenset(w for w in cell if w not in question["yes"])
            if not yes or not no:
                continue
            splittable = True
            left, right = solve(yes), solve(no)
            if left is None or right is None:
                continue
            depth = 1 + max(left["depth"], right["depth"])
            if best is None or depth < best["depth"]:
                best = {"depth": depth, "decided": None,
                        "ask": {"anchor": question["anchor"], "object": question["object"]},
                        "if_present": left, "if_absent": right}
        if not splittable:
            # No declared question divides this cell, and it is not decided. This
            # exact cell is the obstacle; it is recorded rather than inferred.
            stuck.append(sorted(cell))
        memo[key] = best
        return best

    root = solve(frozenset(worlds))
    blocked = indistinguishable(worlds, questions)
    if root is None:
        # Name the obstacle from a cell actually reached and actually stuck.
        witness = sorted(stuck, key=lambda cell: (-len(cell), cell))[0] if stuck else []
        open_anchors = [a["id"] for a in case["anchors"]
                        if a.get("reference_state") != "finite"]
        withheld = [q for q in unanswerable_questions(case)
                    if set(witness) & q["yes"] and set(witness) - q["yes"]]
        if withheld:
            state = "blocked_by_unanswerable_questions"
            reason = ("the witness cell would be divided by a declared question that this case "
                      "marks unanswerable. The obstacle is the observation procedure, not the "
                      "reference model: these worlds are distinguishable in principle and the "
                      "means to distinguish them has not been declared available")
        elif len(witness) > 1:
            state = "unresolvable_by_declared_questions"
            reason = ("the admitted worlds in the witness cell agree on which objects exist and "
                      "differ only in which detections could match them. No declared presence "
                      "question divides that cell, and its enclosure stays undecided, so looking "
                      "for objects will not settle this")
        elif witness and open_anchors:
            state = "unresolvable_due_to_open_anchors"
            reason = ("every admitted world is separable, but the witness cell is a single world "
                      "whose enclosure still straddles the tolerance because an open anchor "
                      "contributes an interval. The obstacle is the absent reference there, not "
                      "the questions")
        elif witness:
            state = "undecided_single_world"
            reason = ("the witness cell is a single fully finite world whose value does not clear "
                      "the declared tolerance. Nothing is ambiguous about the reference; the two "
                      "configurations simply do not separate by enough")
        else:
            state = "unresolved_without_witness"
            reason = ("the search returned no plan and no stuck cell was recorded. This is a "
                      "defect in this program, not a statement about the cohort")
        return {"state": state, "reason": reason,
                "witness_cell": witness, "open_anchors": open_anchors,
                "withheld_questions": [{"anchor": q["anchor"], "object": q["object"]}
                                       for q in withheld],
                "indistinguishable_world_groups": blocked,
                "enclosure": report["enclosure"],
                "improvement_criterion": report["decision"]["improvement_criterion"],
                "questions_available": len(questions), "search_nodes": nodes[0],
                "answer_model": ANSWER_MODEL}
    return {"state": "resolvable", "enclosure": report["enclosure"],
            "answer_model": ANSWER_MODEL,
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
