"""The group the cohort average hides, and why it has to be found jointly.

A cohort comparison reports a weighted average over anchors:

    D(w) = sum_i weight_i * delta_i(w)

An average is exactly the wrong summary for the question "is this addition safe
to ship". A result can be `supported` on the cohort while a named group inside it
is harmed in every admitted reading, and the cohort report as this lane has
written it so far would not say so. That is a defect in the instrument, not in
the analyst reading it, and this module is the correction.

Anchors carry an optional `group`. For a group `g` the value is renormalised
inside the group, so it is comparable against the same tolerance:

    value_g(w) = ( sum_{i in g} weight_i * delta_i(w) ) / ( sum_{i in g} weight_i )

MASKING. When the cohort criterion is `supported` and some group's enclosure is
`excluded`, the aggregate is hiding a harmed group. The report names the group
rather than leaving it to be noticed.

THE WORST GROUP MUST BE FOUND JOINTLY. The quantity of interest is

    worst(w) = min over groups g of value_g(w)

and its enclosure over admitted worlds is `[min_w worst(w), max_w worst(w)]`.
Computing each group's enclosure separately and then combining them is a
different and weaker thing. The lower ends agree, because a minimum over groups
of a minimum over worlds is a minimum over pairs either way. The upper ends do
not: `max_w min_g` is at most `min_g max_w`, and the inequality is often strict.

The direction of the gap matters. The separate view is too wide at the top, so it
can report the worst group as `unresolved` when the joint view shows it is harmed
in every admitted world. `worst-group-flip-case.json` is exactly that: two groups
that trade places between the two admitted readings, joint enclosure a single
point at `-1`, separate relaxation `[-1, 1]`. Treating groups one at a time loses
a decisive negative result. The separate figures are still reported, labelled as
a relaxation, and never as the answer.

Exact rational arithmetic, standard library only, no data read.
"""
from fractions import Fraction
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cohort_packet import CaseError, build  # noqa: E402

VERSION = "0.1.0"
UNGROUPED = "ungrouped"


def declared_groups(case):
    """Group name to anchor ids, from the case. Every anchor belongs to exactly one."""
    groups = {}
    for anchor in case["anchors"]:
        name = anchor.get("group", UNGROUPED)
        if not isinstance(name, str) or not name:
            raise CaseError(f"anchor {anchor['id']} has a group that is not a name")
        groups.setdefault(name, []).append(anchor["id"])
    return groups


def _criterion(lower, upper, tolerance):
    return ("supported" if lower > tolerance else
            "excluded" if upper <= tolerance else "unresolved")


def analyse(case):
    report = build(case)
    if report.get("enclosure") is None:
        return {"artifact_id": "reiyah.worst-group.report", "version": VERSION,
                "state": report.get("state"), "reason": report.get("reason")}
    tolerance = Fraction(str(case["loss"]["tolerance"]))
    a = Fraction(str(case["loss"]["false_negative"]))
    b = Fraction(str(case["loss"]["false_positive"]))
    groups = declared_groups(case)
    weight = {anchor["id"]: Fraction(anchor["weight"]) for anchor in report["anchors"]}
    state = {anchor["id"]: anchor["reference_state"] for anchor in report["anchors"]}
    retained = {anchor["id"]: anchor["retained_additions"] for anchor in report["anchors"]}

    share = {}
    open_low, open_high = {}, {}
    for name, members in groups.items():
        total = sum((weight[i] for i in members), Fraction(0))
        if total == 0:
            raise CaseError(f"group {name} has zero total weight, so it has no value")
        share[name] = total
        open_low[name] = sum((weight[i] * (-b * retained[i]) for i in members
                              if state[i] != "finite"), Fraction(0)) / total
        open_high[name] = sum((weight[i] * (a * retained[i]) for i in members
                               if state[i] != "finite"), Fraction(0)) / total

    # Per world, every group's value, then the worst group in that same world.
    per_world = []
    for world in report["joint_worlds"]:
        contribution = {entry["anchor"]: Fraction(entry["delta"]) for entry in world["anchors"]}
        values = {}
        for name, members in groups.items():
            finite = sum((weight[i] * contribution[i] for i in members if i in contribution),
                         Fraction(0))
            values[name] = finite / share[name]
        # The worst group is chosen inside the world, at its least favourable end.
        low = {g: values[g] + open_low[g] for g in groups}
        high = {g: values[g] + open_high[g] for g in groups}
        worst_name = min(low, key=lambda g: (low[g], g))
        per_world.append({"world_id": world["world_id"],
                          "group_values": {g: str(values[g]) for g in sorted(groups)},
                          "worst_group": worst_name,
                          "worst_value_low": low[worst_name],
                          "worst_value_high": min(high.values())})

    group_enclosures = {}
    for name in sorted(groups):
        if per_world:
            lows = [Fraction(w["group_values"][name]) + open_low[name] for w in per_world]
            highs = [Fraction(w["group_values"][name]) + open_high[name] for w in per_world]
        else:
            lows, highs = [open_low[name]], [open_high[name]]
        lower, upper = min(lows), max(highs)
        group_enclosures[name] = {
            "anchors": groups[name], "weight_share": str(share[name]),
            "enclosure": {"lower": str(lower), "upper": str(upper)},
            "criterion": _criterion(lower, upper, tolerance)}

    if per_world:
        joint_low = min(w["worst_value_low"] for w in per_world)
        joint_high = max(w["worst_value_high"] for w in per_world)
    else:
        joint_low = min(open_low.values())
        joint_high = max(open_high.values())

    relax_low = min(Fraction(g["enclosure"]["lower"]) for g in group_enclosures.values())
    relax_high = min(Fraction(g["enclosure"]["upper"]) for g in group_enclosures.values())

    cohort_criterion = report["decision"]["improvement_criterion"]
    worst_criterion = _criterion(joint_low, joint_high, tolerance)
    masked = [name for name, entry in group_enclosures.items()
              if entry["criterion"] == "excluded" and cohort_criterion == "supported"]

    return {
        "artifact_id": "reiyah.worst-group.report", "version": VERSION,
        "cohort_id": report["cohort_id"],
        "cohort": {"enclosure": report["enclosure"], "criterion": cohort_criterion},
        "groups": group_enclosures,
        "per_world_worst_group": [
            {"world_id": w["world_id"], "worst_group": w["worst_group"],
             "group_values": w["group_values"]} for w in per_world],
        "worst_group_enclosure": {"lower": str(joint_low), "upper": str(joint_high),
                                  "criterion": worst_criterion},
        "separate_group_relaxation": {
            "lower": str(relax_low), "upper": str(relax_high),
            "status": ("a relaxation, never the answer. The lower ends agree; the upper end is at "
                       "least the joint one, so treating groups one at a time can only lose "
                       "decisiveness"),
            "strictly_wider": relax_high > joint_high or relax_low < joint_low},
        "masking": {
            "cohort_criterion": cohort_criterion,
            "groups_excluded_while_the_cohort_is_supported": masked,
            "finding": (f"the cohort average is {cohort_criterion} while {', '.join(masked)} "
                        "is harmed in every admitted reading" if masked else
                        "no group is excluded while the cohort is supported")},
        "scope": ("the declared groups, the declared anchors and the declared admitted readings. A "
                  "group is a partition the case asserts; this program does not discover groups, "
                  "and an unexamined split can still hide a harm"),
    }


def main(argv):
    if len(argv) != 2:
        sys.stderr.write("usage: worst_group.py CASE.json\n")
        return 2
    with open(argv[1], "r", encoding="utf-8") as handle:
        case = json.load(handle)
    try:
        result = analyse(case)
    except CaseError as error:
        sys.stderr.write(f"case refused: {error}\n")
        return 1
    json.dump(result, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
