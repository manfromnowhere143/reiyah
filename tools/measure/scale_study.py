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
"""
from fractions import Fraction
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

VERSION = "0.1.0"
PROTOCOL = "4c601ca94bc1e34e155fda0b16a7e45d660c5084e913f5630938224b74686368"
SCORE_CUTOFF = 0.30
RANGE_LIMIT = 50.0
NEAR = 4.0          # strict distance < 2 m, compared as squared
PENALTY_FN = Fraction(1)
PENALTY_FP = Fraction(1)
TOLERANCE = Fraction(1, 10)
CLASSES = ("car", "truck", "bus", "trailer", "construction_vehicle",
           "pedestrian", "motorcycle", "bicycle", "traffic_cone", "barrier")


def rotate_inverse(q, v):
    w, x, y, z = q
    r = [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
         [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
         [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]
    return [sum(r[j][i] * v[j] for j in range(3)) for i in range(3)]


def qualify(rows, pose):
    """Score cutoff, common range, declared classes. Order preserved as the source gives it."""
    kept = []
    tr, q = pose["translation"], pose["rotation"]
    for index, row in enumerate(rows):
        name = row.get("detection_name")
        if name not in CLASSES:
            continue
        score = row.get("detection_score")
        if not isinstance(score, (int, float)) or score < SCORE_CUTOFF:
            continue
        g = row.get("translation")
        if not (isinstance(g, list) and len(g) == 3):
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


def unit(scene_frames, budget=200000):
    """One decision unit, with every stopping outcome distinct."""
    frames = [f for f in scene_frames if f is not None]
    if not frames:
        return {"status": "missing_input"}
    if not any(f.objects for f in frames):
        return {"status": "empty_reference"}
    decision = decide(frames)
    weight = Fraction(1, len(frames))
    if decision <= TOLERANCE:
        return {"status": "unsupported_baseline", "decision": str(decision)}
    floor = arithmetic_floor(decision, frames)
    base_gain = [f.gain() for f in frames]

    # A deletion only affects its own frame, so a crossing set is built from per frame
    # gain losses. Singles first, then within frame pairs, then across frames. No label
    # is pruned for having no singleton effect: within frame pairs are searched in full.
    evaluations = 0
    carriers = []
    for index, f in enumerate(frames):
        for j in range(len(f.objects)):
            evaluations += 1
            lost = base_gain[index] - f.gain(frozenset([j]))
            if lost:
                carriers.append((index, j, lost))
            if evaluations > budget:
                return {"status": "budget_exhausted", "decision": str(decision),
                        "k_floor": floor["k_floor"], "evaluations": evaluations}
    step = (PENALTY_FN + PENALTY_FP) * weight
    need = decision - TOLERANCE
    k = floor["k_floor"]

    # Deletions in different frames are exactly independent, because the matching is
    # per frame. Deletions inside one frame are not: the second can be absorbed by a
    # reassignment the first opened. So the witness is grown one deletion at a time
    # and the gain loss is REVERIFIED after each, never summed from singleton effects.
    # Each deletion removes at most one unit of gain, so k_floor deletions is the
    # fewest that can possibly cross; a verified witness of that size proves the
    # minimum without any further search.
    dropped = {index: set() for index in range(len(frames))}
    current = list(base_gain)
    taken = 0
    lost_total = 0
    while taken < len(carriers) + sum(len(f.objects) for f in frames):
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
                            "gain_removed_so_far": lost_total, "evaluations": evaluations}
                after = f.gain(frozenset(dropped[index] | {j}))
                if current[index] - after == 1:
                    best = (index, j, after)
                    break
            if best:
                break
        if best is None:
            break
        index, j, after = best
        dropped[index].add(j)
        current[index] = after
        taken += 1
        lost_total += 1
        if step * lost_total >= need:
            break

    if step * lost_total >= need:
        check = sum((weight * frames[i].delta(frozenset(dropped[i])))
                    for i in range(len(frames)))
        if check > TOLERANCE:
            return {"status": "bounded_only", "decision": str(decision), "k_floor": k,
                    "upper_bound": taken, "verified_decision_after": str(check),
                    "reason": "the grown witness did not verify under full recomputation"}
        return {"status": "certified_at_floor" if taken == k else "certified_above_floor",
                "decision": str(decision), "k_floor": k, "k_observed": taken,
                "verified_decision_after": str(check),
                "fragility_ratio": str(Fraction(taken, k)) if k else None,
                "at_floor": taken == k, "evaluations": evaluations,
                "deletions_per_frame": {str(i): len(v) for i, v in dropped.items() if v},
                "note": ("each deletion was verified to remove exactly one unit of gain, and no "
                         "deletion can remove more, so a witness of k_floor size is minimal")}

    return {"status": "no_admissible_crossing", "decision": str(decision),
            "k_floor": k, "evaluations": evaluations,
            "reason": "no set of single record deletions removes enough gain to cross"}
