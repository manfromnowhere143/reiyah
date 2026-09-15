"""The declared scale study: how many label deletions remove support, over a census.

Protocol frozen at 4c601ca94bc1e34e155fda0b16a7e45d660c5084e913f5630938224b74686368
before any outcome here. This module implements it and nothing else. Where the
protocol and this code disagree, the protocol is the specification.

One decision unit is one scene cohort under one ordered detector pair. The base is
the first detector fully retained after qualification; the additions are the
second detector's qualifying rows that survive same class suppression against the
retained base and against earlier retained additions, in ascending source row
order. Frames inside a scene carry equal weight.

    delta_f = (a + b) * (TP_augmented - TP_base) - b * r_f
    D       = sum_f weight_f * delta_f

Every stopping outcome is a first class result: a unit with no admissible crossing,
an unsupported baseline, an empty reference or an exhausted budget is reported as
that, never folded into a frequency it did not earn.

Exact rational arithmetic for the decision. Geometry is float from the source
tables, which is what the source provides; the 2 metre rules are strict and are
applied to squared distances to avoid a square root.

0.2.0 REPAIRS, all four reproduced on the consumer's controls before any change.

SEARCH. Version 0.1.0 grew a witness only from deletions that immediately removed
one unit of gain, and reported `no_admissible_crossing` when none existed. That is
a false negative. One base at x=0, one addition at x=3 and three objects between
them: no single deletion changes the gain, every pair drops it, so the floor is 1
and the true minimum is 2. The arithmetic floor bounds the gain that must be
removed; it does NOT bound the number of deletions needed to remove it, and that
was the error behind this lane's tautology claim. A stalled search is now bounded
or unresolved, never a claim that no crossing exists, and a bounded exhaustive
pass can certify a minimum above the floor.

MISSING FRAMES. `unit([frame, None])` used to return exactly what `unit([frame])`
returns, silently dropping a declared anchor and reweighting the rest. Missing,
invalid and observed empty are three different states and are now three different
outcomes.

INVALID RECORDS. The qualifier accepted NaN and infinite scores, Boolean scores
and NaN coordinates, because every comparison against them is False. The policy is
now explicit: a malformed record fails its declared case rather than being quietly
dropped and the remainder renormalised.

WITNESSES. A count and an `at_floor` flag are not a certificate. Every reported
witness now carries its ordered frame bindings, the annotation identities deleted,
and the before and after decision.
"""
from fractions import Fraction
import json
import math
import os
import sys
import time
from itertools import combinations

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

VERSION = "0.2.0"
PROTOCOL = "4c601ca94bc1e34e155fda0b16a7e45d660c5084e913f5630938224b74686368"
SCORE_CUTOFF = 0.30
RANGE_LIMIT = 50.0
NEAR = 4.0          # strict distance < 2 m, compared as squared
PENALTY_FN = Fraction(1)
PENALTY_FP = Fraction(1)
TOLERANCE = Fraction(1, 10)
CLASSES = ("car", "truck", "bus", "trailer", "construction_vehicle",
           "pedestrian", "motorcycle", "bicycle", "traffic_cone", "barrier")


class InvalidRecord(ValueError):
    """A source record this study will not silently drop."""


def finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) \
        and math.isfinite(value)


def rotate_inverse(q, v):
    w, x, y, z = q
    r = [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
         [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
         [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]
    return [sum(r[j][i] * v[j] for j in range(3)) for i in range(3)]


def qualify(rows, pose, strict=True):
    """Score cutoff, common range, declared classes. Order preserved as the source gives it.

    A malformed record raises rather than being dropped. A Boolean is not a score,
    and NaN passes every comparison, so neither is allowed to survive by accident.
    """
    kept = []
    tr, q = pose["translation"], pose["rotation"]
    if not (isinstance(tr, list) and len(tr) == 3 and all(finite(v) for v in tr)):
        raise InvalidRecord("the pose translation is not three finite numbers")
    if not (isinstance(q, list) and len(q) == 4 and all(finite(v) for v in q)):
        raise InvalidRecord("the pose rotation is not four finite numbers")
    for index, row in enumerate(rows):
        name = row.get("detection_name")
        score = row.get("detection_score")
        g = row.get("translation")
        if strict:
            if name is not None and not isinstance(name, str):
                raise InvalidRecord(f"row {index} has a non string class")
            if score is not None and not finite(score):
                raise InvalidRecord(f"row {index} has a score that is not a finite number")
            if g is not None and not (isinstance(g, list) and len(g) == 3
                                      and all(finite(v) for v in g)):
                raise InvalidRecord(f"row {index} has a translation that is not three finite "
                                    "numbers")
        if name not in CLASSES:
            continue
        if not finite(score) or score < SCORE_CUTOFF:
            continue
        if not (isinstance(g, list) and len(g) == 3 and all(finite(v) for v in g)):
            continue
        rel = rotate_inverse(q, [g[0] - tr[0], g[1] - tr[1], g[2] - tr[2]])
        if rel[0] * rel[0] + rel[1] * rel[1] > RANGE_LIMIT * RANGE_LIMIT:
            continue
        kept.append({"i": index, "c": name, "x": g[0], "y": g[1]})
    return kept


def suppress(base, candidates):
    """Additions surviving same class suppression, in ascending source row order."""
    retained = []
    for row in sorted(candidates, key=lambda r: r["i"]):
        hit = False
        for other in base:
            if other["c"] != row["c"]:
                continue
            if (row["x"] - other["x"]) ** 2 + (row["y"] - other["y"]) ** 2 < NEAR:
                hit = True
                break
        if not hit:
            for other in retained:
                if other["c"] != row["c"]:
                    continue
                if (row["x"] - other["x"]) ** 2 + (row["y"] - other["y"]) ** 2 < NEAR:
                    hit = True
                    break
        if not hit:
            retained.append(row)
    return retained


def edges(detections, objects):
    """Same class pairs within the strict 2 metre rule."""
    out = {}
    for index, d in enumerate(detections):
        near = []
        for j, o in enumerate(objects):
            if o["c"] != d["c"]:
                continue
            if (d["x"] - o["x"]) ** 2 + (d["y"] - o["y"]) ** 2 < NEAR:
                near.append(j)
        out[index] = near
    return out


def matching_size(left, adjacency):
    assigned = {}

    def augment(node, seen):
        for other in adjacency.get(node, ()):
            if other in seen:
                continue
            seen.add(other)
            if other not in assigned or augment(assigned[other], seen):
                assigned[other] = node
                return True
        return False

    return sum(1 for node in left if augment(node, set()))


class Frame:
    """One frame's prepared graph, so a deletion is a cheap recomputation."""

    __slots__ = ("objects", "base", "added", "adj_base", "adj_all", "r")

    def __init__(self, objects, base, added):
        self.objects = objects
        self.base = base
        self.added = added
        self.r = len(added)
        self.adj_base = edges(base, objects)
        self.adj_all = edges(base + added, objects)

    def delta(self, dropped=frozenset()):
        if dropped:
            adj_b = {k: [j for j in v if j not in dropped] for k, v in self.adj_base.items()}
            adj_a = {k: [j for j in v if j not in dropped] for k, v in self.adj_all.items()}
        else:
            adj_b, adj_a = self.adj_base, self.adj_all
        tp_base = matching_size(range(len(self.base)), adj_b)
        tp_all = matching_size(range(len(self.base) + len(self.added)), adj_a)
        return (PENALTY_FN + PENALTY_FP) * (tp_all - tp_base) - PENALTY_FP * self.r

    def gain(self, dropped=frozenset()):
        if dropped:
            adj_b = {k: [j for j in v if j not in dropped] for k, v in self.adj_base.items()}
            adj_a = {k: [j for j in v if j not in dropped] for k, v in self.adj_all.items()}
        else:
            adj_b, adj_a = self.adj_base, self.adj_all
        return (matching_size(range(len(self.base) + len(self.added)), adj_a)
                - matching_size(range(len(self.base)), adj_b))


def decide(frames):
    """The scene cohort decision under equal frame weights."""
    if not frames:
        return None
    weight = Fraction(1, len(frames))
    return sum((weight * f.delta() for f in frames), Fraction(0))


def arithmetic_floor(decision, frames):
    """The proved lower bound on how many deletions can cross."""
    weight = Fraction(1, len(frames))
    step = (PENALTY_FN + PENALTY_FP) * weight
    margin = decision - TOLERANCE
    if margin <= 0:
        return {"margin": str(margin), "step": str(step), "k_floor": 0}
    return {"margin": str(margin), "step": str(step), "k_floor": int(-((-margin) // step))}


def all_references_witness(frames, weight):
    """Deleting every qualifying reference. A valid, usually loose, crossing witness.

    With no objects left both matchings are empty, so every frame contributes
    `-b * r_f` and the decision is `-R/F <= 0 <= tolerance`. It is an upper bound on
    the minimum and it always exists on this finite family, which is why a stalled
    search never has to claim that no crossing exists.
    """
    members = {index: set(range(len(f.objects))) for index, f in enumerate(frames)
               if f.objects}
    value = sum((weight * f.delta(frozenset(members.get(i, ()))))
                for i, f in enumerate(frames))
    return members, value, sum(len(v) for v in members.values())


def exhaustive_minimum(frames, weight, need, step, start_size, budget):
    """Certify a minimum above the floor, or report how far the search reached.

    Sizes are tried in order, so the first crossing found is the exact minimum. No
    label is pruned for having no singleton effect, because the whole point of the
    repaired search is that such labels can be decisive in combination.
    """
    slots = [(i, j) for i, f in enumerate(frames) for j in range(len(f.objects))]
    evaluations = 0
    for size in range(start_size, len(slots) + 1):
        for chosen in combinations(slots, size):
            evaluations += 1
            if evaluations > budget:
                return {"state": "budget", "searched_through": size - 1,
                        "evaluations": evaluations}
            per_frame = {}
            for i, j in chosen:
                per_frame.setdefault(i, set()).add(j)
            value = sum((weight * frames[i].delta(frozenset(per_frame.get(i, ()))))
                        for i in range(len(frames)))
            if value <= TOLERANCE:
                return {"state": "found", "size": size, "members": per_frame,
                        "value": value, "evaluations": evaluations}
    return {"state": "exhausted", "evaluations": evaluations}


def unit(scene_frames, budget=200000, exhaustive_budget=200000):
    """One decision unit, with every stopping outcome distinct."""
    if not scene_frames:
        return {"status": "missing_input", "reason": "no frames were supplied"}
    if any(f is None for f in scene_frames):
        # 0.2.0: a missing frame used to be dropped and the rest reweighted, which
        # silently answered a different question from the declared one.
        return {"status": "input_blocked", "declared_frames": len(scene_frames),
                "missing_frames": sum(1 for f in scene_frames if f is None),
                "reason": ("a declared frame is missing. Missing, invalid and observed empty "
                           "are different states and this unit is not answered by dropping one")}
    frames = list(scene_frames)
    if not any(f.objects for f in frames):
        return {"status": "empty_reference"}
    decision = decide(frames)
    weight = Fraction(1, len(frames))
    if decision <= TOLERANCE:
        return {"status": "unsupported_baseline", "decision": str(decision)}
    floor = arithmetic_floor(decision, frames)
    base_gain = [f.gain() for f in frames]
    step = (PENALTY_FN + PENALTY_FP) * weight
    need = decision - TOLERANCE
    k = floor["k_floor"]
    evaluations = 0

    # Grow a witness one deletion at a time, reverifying the gain after each. A
    # witness of floor size is the exact minimum, since the floor is a proved lower
    # bound. Anything larger is only an upper bound until smaller sets are ruled out.
    dropped = {index: set() for index in range(len(frames))}
    current = list(base_gain)
    taken = 0
    lost_total = 0
    while True:
        best = None
        for index, f in enumerate(frames):
            if current[index] == 0:
                continue
            for j in range(len(f.objects)):
                if j in dropped[index]:
                    continue
                evaluations += 1
                if evaluations > budget:
                    return {"status": "budget_exhausted", "decision": str(decision),
                            "k_floor": k, "deletions_so_far": taken,
                            "evaluations": evaluations}
                if current[index] - f.gain(frozenset(dropped[index] | {j})) == 1:
                    best = (index, j)
                    break
            if best:
                break
        if best is None:
            break
        index, j = best
        dropped[index].add(j)
        current[index] -= 1
        taken += 1
        lost_total += 1
        if step * lost_total >= need:
            break

    if step * lost_total >= need:
        check = sum((weight * frames[i].delta(frozenset(dropped[i])))
                    for i in range(len(frames)))
        if check <= TOLERANCE and taken == k:
            return {"status": "certified_at_floor", "decision": str(decision),
                    "k_floor": k, "k_observed": taken, "at_floor": True,
                    "verified_decision_after": str(check), "evaluations": evaluations,
                    "witness": {str(i): sorted(v) for i, v in dropped.items() if v},
                    "note": ("the floor is a proved lower bound and this witness meets it, so "
                             "it is the exact minimum")}
        if check <= TOLERANCE:
            upper = taken
            upper_members = {i: set(v) for i, v in dropped.items() if v}
        else:
            upper_members, _value, upper = all_references_witness(frames, weight)
    else:
        # 0.2.0: the stall used to be reported as no crossing existing. It is not.
        upper_members, _value, upper = all_references_witness(frames, weight)

    exact = exhaustive_minimum(frames, weight, need, step, k, exhaustive_budget)
    if exact["state"] == "found":
        value = exact["value"]
        return {"status": "certified_at_floor" if exact["size"] == k else "certified_above_floor",
                "decision": str(decision), "k_floor": k, "k_observed": exact["size"],
                "at_floor": exact["size"] == k, "verified_decision_after": str(value),
                "evaluations": evaluations + exact["evaluations"],
                "witness": {str(i): sorted(v) for i, v in exact["members"].items()},
                "note": ("every smaller size was searched in full, so this is the exact minimum")}
    if exact["state"] == "exhausted":
        return {"status": "no_admissible_crossing", "decision": str(decision), "k_floor": k,
                "evaluations": evaluations + exact["evaluations"],
                "reason": "every deleting set was searched and none crosses"}
    return {"status": "bounded_only", "decision": str(decision), "k_floor": k,
            "lower_bound": max(k, exact.get("searched_through", k) + 1),
            "upper_bound": upper,
            "upper_bound_witness": {str(i): sorted(v) for i, v in upper_members.items()},
            "evaluations": evaluations + exact["evaluations"],
            "reason": ("the growing search stalled and the exhaustive pass reached its budget. "
                       "A crossing exists, its size lies in the reported bracket, and no minimum "
                       "is claimed")}
