"""Independent check of a resolution plan, with a differently structured oracle.

The planner searches top down and minimises: at each cell it tries every
question and keeps the smallest `1 + max(left, right)`. If that single
recursion is wrong, a checker built the same way is wrong in the same way and
agrees anyway. So the oracle here is a *decision* procedure, not an
optimisation: for a budget d it asks whether any tree of depth at most d
resolves the cell, and the reported depth is accepted only when the answer is
yes at d and no at d - 1. Agreement between a minimiser and a feasibility
ladder is worth something; agreement between two minimisers is not.

A minimum fixed resolving set is also computed, by brute force over subsets. It
is reported for contrast and is only an upper bound on the adaptive optimum: a
fixed set must answer every question on every branch, while a plan may ask
different questions after different answers. `adaptive-beats-fixed-case.json`
is the retained witness that the inequality is strict, so the fixed number can
never be used to certify the adaptive one.

What is verified, node by node: the question asked is one this checker derived
itself from the case; the two branches are exactly the worlds that answer yes
and no, with nothing dropped, duplicated or invented; every leaf's verdict is
recomputed from the cohort packet rather than read from the plan; every
declared depth equals one plus the larger branch; and the root depth is both
achievable and not achievable one cheaper.

What is trusted: `cohort_packet.build` for the enclosure and the criterion, and
the Python standard library. No planner code is imported. A field this checker
does not verify is listed in `fields_not_verified` rather than passed over.
"""
from itertools import combinations
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cohort_packet import CaseError, build  # noqa: E402

VERSION = "0.1.0"
MAX_WORLDS = 64
MAX_QUESTIONS = 32
MAX_DEPTH = 16

DECIDED = ("supported", "excluded")
NEGATIVE_STATES = ("no_admitted_reference", "unresolvable_by_declared_questions",
                   "unresolvable_due_to_open_anchors", "undecided_single_world",
                   "blocked_by_unanswerable_questions", "unresolved_without_witness")


class PlanRefused(Exception):
    """The plan does not survive an independent check."""


def _criterion(case, cell):
    subset = [w for w in case["joint_worlds"] if w["world_id"] in cell]
    trimmed = dict(case)
    trimmed["joint_worlds"] = subset
    report = build(trimmed)
    if report.get("enclosure") is None:
        return None
    return report["decision"]["improvement_criterion"]


def _declared_object(case, key):
    for anchor in case["anchors"]:
        if anchor["id"] != key[0]:
            continue
        for entry in anchor.get("objects", []):
            if entry["id"] == key[1]:
                return entry
    return None


def _yes_set(case, key):
    return frozenset(w["world_id"] for w in case["joint_worlds"]
                     if key[1] in w["per_anchor"][key[0]]["objects_present"])


def permitted_questions(case):
    """Re-derived here, not read from the plan."""
    worlds = [w["world_id"] for w in case["joint_worlds"]]
    every = frozenset(worlds)
    questions = {}
    for anchor in case["anchors"]:
        if anchor.get("reference_state") != "finite":
            continue
        for entry in anchor.get("objects", []):
            if entry.get("answerable") is False:
                continue
            yes = frozenset(w["world_id"] for w in case["joint_worlds"]
                            if entry["id"] in w["per_anchor"][anchor["id"]]["objects_present"])
            if yes and yes != every:
                questions[(anchor["id"], entry["id"])] = yes
    if len(questions) > MAX_QUESTIONS:
        raise PlanRefused("more declared questions than the checker budget allows")
    return questions


def resolvable_within(case, cell, budget, questions, cache):
    """Is there ANY tree of depth <= budget that decides this cell?

    A feasibility ladder, not a minimisation. Deliberately a different shape
    from the planner it checks.
    """
    key = (cell, budget)
    if key in cache:
        return cache[key]
    verdict = _criterion(case, set(cell))
    if verdict in DECIDED:
        cache[key] = True
        return True
    if budget <= 0:
        cache[key] = False
        return False
    answer = False
    for yes in questions.values():
        left = frozenset(w for w in cell if w in yes)
        right = frozenset(w for w in cell if w not in yes)
        if not left or not right:
            continue
        if (resolvable_within(case, left, budget - 1, questions, cache)
                and resolvable_within(case, right, budget - 1, questions, cache)):
            answer = True
            break
    cache[key] = answer
    return answer


def minimum_fixed_resolving_set(case, questions):
    """Smallest set of questions whose answer vectors decide every cell.

    An upper bound on the adaptive depth, never a proof of it.
    """
    worlds = [w["world_id"] for w in case["joint_worlds"]]
    keys = list(questions)
    for size in range(0, len(keys) + 1):
        for chosen in combinations(keys, size):
            cells = {}
            for world in worlds:
                signature = tuple(world in questions[k] for k in chosen)
                cells.setdefault(signature, set()).add(world)
            if all(_criterion(case, cell) in DECIDED for cell in cells.values()):
                return size, [{"anchor": k[0], "object": k[1]} for k in chosen]
    return None, None


def _check_node(case, node, cell, questions, path, seen):
    """Verify one node of the declared plan against the case."""
    where = " -> ".join(path) if path else "root"
    if not isinstance(node, dict):
        raise PlanRefused(f"{where}: plan node is not an object")
    if node.get("ask") is None:
        verdict = _criterion(case, set(cell))
        if verdict not in DECIDED:
            raise PlanRefused(
                f"{where}: declared a leaf, but the cell {sorted(cell)} recomputes as "
                f"{verdict!r}, which is not a decision")
        if node.get("decided") != verdict:
            raise PlanRefused(
                f"{where}: leaf claims {node.get('decided')!r}; the cohort packet says "
                f"{verdict!r}")
        if node.get("depth") != 0:
            raise PlanRefused(f"{where}: a leaf must have depth 0, not {node.get('depth')!r}")
        seen.append({"cell": sorted(cell), "decided": verdict})
        return 0
    key = (node["ask"].get("anchor"), node["ask"].get("object"))
    if key not in questions:
        raise PlanRefused(
            f"{where}: asks {key}, which is not a question this checker derived from the case")
    if _criterion(case, set(cell)) in DECIDED:
        raise PlanRefused(f"{where}: asks a question in a cell that is already decided")
    yes = questions[key]
    expect_present = frozenset(w for w in cell if w in yes)
    expect_absent = frozenset(w for w in cell if w not in yes)
    if not expect_present or not expect_absent:
        raise PlanRefused(f"{where}: {key} does not divide the cell {sorted(cell)}")
    for branch, expected in (("if_present", expect_present), ("if_absent", expect_absent)):
        if branch not in node:
            raise PlanRefused(f"{where}: missing branch {branch}")
    left = _check_node(case, node["if_present"], expect_present, questions,
                       path + [f"{key[0]}.{key[1]}=present"], seen)
    right = _check_node(case, node["if_absent"], expect_absent, questions,
                        path + [f"{key[0]}.{key[1]}=absent"], seen)
    depth = 1 + max(left, right)
    if node.get("depth") != depth:
        raise PlanRefused(
            f"{where}: declares depth {node.get('depth')!r}; its branches give {depth}")
    if depth > MAX_DEPTH:
        raise PlanRefused(f"{where}: depth {depth} exceeds the checker budget")
    return depth


def check(case, result):
    """Refuse or accept a plan. Raises PlanRefused with a reason."""
    if not isinstance(result, dict) or "state" not in result:
        raise PlanRefused("result has no state")
    worlds = [w["world_id"] for w in case["joint_worlds"]]
    if len(worlds) != len(set(worlds)):
        raise PlanRefused("the case declares two worlds with the same identifier")
    if len(worlds) > MAX_WORLDS:
        raise PlanRefused("more worlds than the checker budget allows")
    report = build(case)
    findings = {"artifact_id": "reiyah.resolution-plan.check", "version": VERSION,
                "state": result["state"], "worlds": len(worlds)}

    if result["state"] in NEGATIVE_STATES:
        if result["state"] == "no_admitted_reference":
            if worlds:
                raise PlanRefused(
                    "claims no admitted reference, but the case declares "
                    f"{len(worlds)} joint worlds")
            if result.get("indistinguishable_world_groups"):
                raise PlanRefused(
                    "an empty world population cannot exhibit indistinguishable worlds")
            findings["verified"] = "no joint world is admitted; the enclosure is the count bound"
        else:
            questions = permitted_questions(case)
            cache = {}
            if resolvable_within(case, frozenset(worlds), MAX_DEPTH, questions, cache):
                raise PlanRefused(
                    "claims the comparison is unresolvable, but the oracle found a plan "
                    f"within depth {MAX_DEPTH}")
            witness = result.get("witness_cell") or []
            if result["state"] == "blocked_by_unanswerable_questions":
                withheld = result.get("withheld_questions") or []
                if not withheld:
                    raise PlanRefused(
                        "claims an unanswerable question is the obstacle without naming one")
                available = permitted_questions(case)
                for entry in withheld:
                    key = (entry.get("anchor"), entry.get("object"))
                    if key in available:
                        raise PlanRefused(
                            f"{key} is named as withheld but is permitted by the case")
                    declared = _declared_object(case, key)
                    if declared is None or declared.get("answerable") is not False:
                        raise PlanRefused(
                            f"{key} is named as withheld but the case does not mark it "
                            "unanswerable")
                    yes = _yes_set(case, key)
                    if not (set(witness) & yes and set(witness) - yes):
                        raise PlanRefused(
                            f"{key} is named as withheld but would not divide the witness cell")
                findings["verified"] = (
                    f"witness cell {sorted(witness)} is undecided, no permitted question divides "
                    "it, and each named withheld question is marked unanswerable in the case and "
                    "would have divided it")
            elif result["state"] == "unresolvable_by_declared_questions":
                if len(witness) < 2:
                    raise PlanRefused(
                        "geometry ambiguity is claimed without a witness cell of at least two "
                        "worlds. An absent or single-world population is a different state")
                if _criterion(case, set(witness)) in DECIDED:
                    raise PlanRefused("the witness cell is decided, so it witnesses nothing")
                for key, yes in questions.items():
                    if set(witness) & yes and set(witness) - yes:
                        raise PlanRefused(
                            f"question {key} does divide the declared witness cell")
                findings["verified"] = (
                    f"witness cell {sorted(witness)} is undecided and no declared question "
                    "divides it")
            else:
                findings["verified"] = f"no plan exists within depth {MAX_DEPTH}"
        findings["fields_not_verified"] = ["reason", "answer_model", "search_nodes"]
        return findings

    if result["state"] != "resolvable":
        raise PlanRefused(f"unknown state {result['state']!r}")

    questions = permitted_questions(case)
    declared = result.get("worst_case_observations")
    if not isinstance(declared, int) or declared < 0:
        raise PlanRefused("worst_case_observations is not a non-negative integer")
    if result.get("enclosure") != report["enclosure"]:
        raise PlanRefused("the declared enclosure does not match the cohort packet")

    seen = []
    depth = _check_node(case, result["plan"], frozenset(worlds), questions, [], seen)
    if depth != declared:
        raise PlanRefused(f"declares {declared} observations; its own tree needs {depth}")
    first = result.get("first_question")
    root_ask = result["plan"].get("ask")
    if first != root_ask:
        raise PlanRefused("first_question does not match the root of the plan")

    cache = {}
    if not resolvable_within(case, frozenset(worlds), declared, questions, cache):
        raise PlanRefused(f"the oracle finds no tree of depth {declared}")
    if declared > 0 and resolvable_within(case, frozenset(worlds), declared - 1, questions, cache):
        raise PlanRefused(
            f"the oracle resolves within {declared - 1} observations, so {declared} is not "
            "the worst-case optimum")

    fixed_size, fixed_set = minimum_fixed_resolving_set(case, questions)
    findings.update({
        "worst_case_observations": declared,
        "leaves": len(seen),
        "questions_permitted": [{"anchor": k[0], "object": k[1]} for k in questions],
        "oracle": {"resolvable_at": declared, "resolvable_at_one_less": False,
                   "method": "iterative feasibility over a depth budget"},
        "minimum_fixed_resolving_set": {
            "size": fixed_size, "questions": fixed_set,
            "relation": "an upper bound on the adaptive optimum, never a proof of it",
            "strict_here": fixed_size is not None and fixed_size > declared},
        "fields_not_verified": ["reason", "answer_model", "search_nodes",
                                "indistinguishable_world_groups", "questions_available"]})
    return findings


def main(argv):
    if len(argv) != 3:
        sys.stderr.write("usage: check_resolution_plan.py CASE.json PLAN.json\n")
        return 2
    with open(argv[1], "r", encoding="utf-8") as handle:
        case = json.load(handle)
    with open(argv[2], "r", encoding="utf-8") as handle:
        result = json.load(handle)
    try:
        findings = check(case, result)
    except (PlanRefused, CaseError) as error:
        sys.stderr.write(f"plan refused: {error}\n")
        return 1
    json.dump(findings, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
