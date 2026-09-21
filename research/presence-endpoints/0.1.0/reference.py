"""Independent partial-injection truth and conventional assignment certificates."""

from fractions import Fraction
from itertools import product

import numpy as np
from scipy.optimize import linear_sum_assignment


def rational(value):
    return Fraction(int(value["numerator"]), int(value["denominator"]))


def wire(value):
    return {"numerator": str(value.numerator), "denominator": str(value.denominator)}


def classify(lower, upper, tolerance):
    criterion = "unresolved"
    if lower > tolerance:
        criterion = "supported"
    elif upper <= tolerance:
        criterion = "excluded"
    preference = "unresolved"
    if lower > tolerance:
        preference = "prefer_augmented"
    elif upper < -tolerance:
        preference = "prefer_base"
    elif lower >= -tolerance and upper <= tolerance:
        preference = "equivalent_within_tolerance"
    return {"improvement_criterion": criterion, "preference": preference}


def graph(anchor, env):
    objects = [
        o["id"]
        for o in anchor["reference"]["objects"]
        if all(env[t["variable"]] == t["value"] for t in o["when"])
    ]
    edges = {
        (e["detection"], e["object"])
        for e in anchor["reference"]["edges"]
        if e["object"] in objects
        and all(env[t["variable"]] == t["value"] for t in e["when"])
    }
    return objects, edges


def brute_rank(left, objects, edges):
    best = 0
    for values in product([None] + list(objects), repeat=len(left)):
        used = [v for v in values if v is not None]
        if len(set(used)) == len(used) and all(
            obj is None or (det, obj) in edges for det, obj in zip(left, values)
        ):
            best = max(best, len(used))
    return best


def exhaustive(original):
    values = []
    names = original["model"]["variables"]
    for bits in product((False, True), repeat=len(names)):
        env = dict(zip(names, bits))
        if not all(
            any(env[t["variable"]] == t["value"] for t in clause)
            for clause in original["model"]["clauses"]
        ):
            continue
        total = Fraction()
        fn, fp = (
            rational(original["loss"][k]) for k in ("false_negative", "false_positive")
        )
        for anchor in original["anchors"]:
            objects, edges = graph(anchor, env)
            aa = [d["id"] for d in anchor["base"]["value"]]
            bb = aa + [d["id"] for d in anchor["additions"]["value"]]
            # Compute each full loss, rather than reuse the engine's delta formula.
            losses = []
            for left in (aa, bb):
                matches = brute_rank(left, objects, edges)
                losses.append(
                    fn * (len(objects) - matches) + fp * (len(left) - matches)
                )
            total += rational(anchor["weight"]) * (losses[0] - losses[1])
        values.append(total)
    return values


def validate_certificate(left, edges, certificate):
    assert set(certificate) == {"matching", "cover"}
    matching = certificate["matching"]
    cover = certificate["cover"]
    assert set(cover) == {"detections", "objects"}
    ld, ro = cover["detections"], cover["objects"]
    assert len(ld) == len(set(ld)) and len(ro) == len(set(ro))
    assert set(ld) <= set(left) and set(ro) <= {o for _, o in edges}
    assert all(
        len(pair) == 2 and tuple(pair) in edges and pair[0] in left for pair in matching
    )
    assert (
        len({d for d, _ in matching}) == len({o for _, o in matching}) == len(matching)
    )
    assert all(d in ld or o in ro for d, o in edges if d in left)
    assert len(matching) == len(ld) + len(ro)
    return len(matching)


def assignment_certificate(left, objects, edges):
    weights = np.array(
        [[int((d, o) in edges) for o in objects] for d in left], dtype=np.int64
    )
    pairs = []
    if left and objects:
        rows, cols = linear_sum_assignment(weights, maximize=True)
        pairs = [
            [left[i], objects[j]] for i, j in zip(rows, cols) if weights[i, j] == 1
        ]
    match_l = dict(pairs)
    match_r = {o: d for d, o in pairs}
    seen_l, seen_r = set(left) - set(match_l), set()
    queue = list(seen_l)
    while queue:
        det = queue.pop()
        for obj in objects:
            if (det, obj) not in edges or match_l.get(det) == obj or obj in seen_r:
                continue
            seen_r.add(obj)
            if obj in match_r and match_r[obj] not in seen_l:
                seen_l.add(match_r[obj])
                queue.append(match_r[obj])
    cert = {
        "matching": sorted(pairs),
        "cover": {"detections": sorted(set(left) - seen_l), "objects": sorted(seen_r)},
    }
    validate_certificate(left, edges, cert)
    return cert


def conventional(original):
    endpoints = []
    values = []
    fn, fp = (
        rational(original["loss"][k]) for k in ("false_negative", "false_positive")
    )
    for bit in (False, True):
        env = {v: bit for v in original["model"]["variables"]}
        total = Fraction()
        anchors = []
        for anchor in original["anchors"]:
            objects, edges = graph(anchor, env)
            aa = [d["id"] for d in anchor["base"]["value"]]
            bb = aa + [d["id"] for d in anchor["additions"]["value"]]
            a = assignment_certificate(
                aa, objects, {(d, o) for d, o in edges if d in aa}
            )
            b = assignment_certificate(bb, objects, edges)
            loss_a = fn * (len(objects) - len(a["matching"])) + fp * (
                len(aa) - len(a["matching"])
            )
            loss_b = fn * (len(objects) - len(b["matching"])) + fp * (
                len(bb) - len(b["matching"])
            )
            total += rational(anchor["weight"]) * (loss_a - loss_b)
            anchors.append({"anchor": anchor["id"], "base": a, "augmented": b})
        endpoints.append({"all_variables": bit, "anchors": anchors})
        values.append(total)
    assert values[0] <= values[1]
    return {
        "bounds": {"lower": wire(values[0]), "upper": wire(values[1])},
        "decision": classify(*values, rational(original["loss"]["tolerance"])),
        "endpoints": endpoints,
        "method": "scipy_assignment_with_matching_cover_checks",
    }
