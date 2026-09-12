"""Why adding a reference object can never lower the additive delta, and when it can.

The additive loss is `delta = (a + b) * (TP_augmented - TP_base) - b * r`. Only the
gain `TP_augmented - TP_base` depends on which reference objects are present, so
delta falls exactly when the gain falls. A search over gadgets found no case where
it does. A search is not a reason, so here is one.

THEOREM. Fix a bipartite graph on detections `D = B + C` and objects `O` with a
fixed edge set. For a present-object set `S` write `nu_X(S)` for the maximum
matching between detections `X` and objects `S`. Then

    gain(S) = nu_D(S) - nu_B(S)

is nondecreasing in `S`. Adding a reference object never lowers the gain, so it
never lowers delta.

PROOF. By the defect form of Konig's theorem, for any detection set `X`,

    nu_X(S) = |X| - def_X(S),    def_X(S) = max over T subset of X of val_S(T),
    val_S(T) = |T| - |N(T) & S|.

`def` is the largest number of detections that cannot be matched. Substituting,

    gain(S) = |C| - def_D(S) + def_B(S).

Let `d` be an object not in `S` and put `Delta_X = def_X(S) - def_X(S + d)`. Then

    gain(S + d) - gain(S) = Delta_D - Delta_B,

so the theorem says `Delta_D >= Delta_B`.

Step 1. `Delta_X` is 0 or 1, and it is 1 exactly when EVERY maximizer of `val_S`
over subsets of `X` has `d` in its neighbourhood. This is immediate from
`val_{S+d}(T) = val_S(T) - [d in N(T)]`: if some maximizer misses `d` the maximum
is unchanged, and otherwise every maximizer drops by exactly one.

Step 2. `val_S` is supermodular on subsets of `D`. `|T|` is modular, and
`N(T1 | T2) = N(T1) | N(T2)` while `N(T1 & T2)` is contained in `N(T1) & N(T2)`,
so `|N(.) & S|` is submodular and its negation is supermodular.

Step 3. Suppose `Delta_B = 1`, and let `T*` be any maximizer of `val_S` over
subsets of `D`. Let `T0` be any maximizer over subsets of `B`, with values `m` and
`k`. Supermodularity gives

    k + m = val(T0) + val(T*) <= val(T0 | T*) + val(T0 & T*) <= m + k,

because `T0 | T*` is a subset of `D` and `T0 & T*` is a subset of `B`. Both
inequalities are therefore tight, so `val(T0 & T*) = k`: the intersection is
itself a maximizer over `B`.

Step 4. `Delta_B = 1`, so by Step 1 that intersection has `d` in its
neighbourhood. Since `T0 & T*` is contained in `T*`, so is its neighbourhood, and
`d` lies in `N(T*)`. `T*` was an arbitrary maximizer over `D`, so by Step 1 again
`Delta_D = 1`. Hence `Delta_D >= Delta_B`. QED.

The hypothesis that the edge set is FIXED is doing real work, and it is not a
technicality. A joint world declares its own match edges as well as its own
present objects, so two admitted worlds may disagree about which detection could
have matched which object. Across worlds that disagree in that way the theorem
says nothing, and `adaptive-beats-fixed-varying-edges-case.json` is a retained
instance where the world value genuinely falls as objects are added. The
monotone conclusion covers worlds that differ only in which objects exist.

This module is a check on the argument, not a substitute for it. Each numbered
step is a separate predicate evaluated on concrete instances, so a misstated step
fails on its own rather than being carried by the conclusion.

Exhaustive over small instances, random over larger ones, standard library only,
no data read.
"""
from itertools import chain, combinations
import random
import sys


def subsets(items):
    items = list(items)
    return chain.from_iterable(combinations(items, r) for r in range(len(items) + 1))


def matching(dets, objs, edges):
    """Maximum matching between detections and objects, by augmenting paths."""
    objs = set(objs)
    adj = {d: [o for o in objs if (d, o) in edges] for d in dets}
    matched = {}

    def augment(det, seen):
        for obj in adj[det]:
            if obj in seen:
                continue
            seen.add(obj)
            if obj not in matched or augment(matched[obj], seen):
                matched[obj] = det
                return True
        return False

    return sum(1 for det in dets if augment(det, set()))


def neighbourhood(subset, edges):
    return {o for (d, o) in edges if d in subset}


def val(subset, present, edges):
    """|T| - |N(T) & S|, the deficiency contribution of a detection set."""
    return len(subset) - len(neighbourhood(subset, edges) & set(present))


def deficiency(dets, present, edges):
    """max over T of val(T), and every maximizer."""
    best = None
    maximizers = []
    for candidate in subsets(dets):
        value = val(set(candidate), present, edges)
        if best is None or value > best:
            best, maximizers = value, [set(candidate)]
        elif value == best:
            maximizers.append(set(candidate))
    return best, maximizers


def gain(base, added, present, edges):
    return (matching(list(base) + list(added), present, edges)
            - matching(base, present, edges))


def check_defect_identity(base, added, present, edges):
    """Step 0: nu_X(S) = |X| - def_X(S) for both detection sets."""
    for dets in (list(base), list(base) + list(added)):
        best, _ = deficiency(dets, present, edges)
        if matching(dets, present, edges) != len(dets) - best:
            return False
    return True


def check_supermodular(dets, present, edges):
    """Step 2: val is supermodular on subsets of the detection set."""
    for first in subsets(dets):
        for second in subsets(dets):
            a, b = set(first), set(second)
            if (val(a, present, edges) + val(b, present, edges)
                    > val(a | b, present, edges) + val(a & b, present, edges)):
                return False
    return True


def check_intersection_lemma(base, added, present, edges):
    """Step 3: a B-maximizer meets a D-maximizer in another B-maximizer."""
    dets = list(base) + list(added)
    k, base_max = deficiency(list(base), present, edges)
    _, full_max = deficiency(dets, present, edges)
    for t0 in base_max:
        for star in full_max:
            if val(t0 & star, present, edges) != k:
                return False
    return True


def check_delta_inequality(base, added, present, edges, extra):
    """Step 4 and the conclusion: Delta_D >= Delta_B, and the gain does not fall."""
    dets = list(base) + list(added)
    grown = list(present) + [extra]
    before_b, _ = deficiency(list(base), present, edges)
    after_b, _ = deficiency(list(base), grown, edges)
    before_d, _ = deficiency(dets, present, edges)
    after_d, _ = deficiency(dets, grown, edges)
    delta_b, delta_d = before_b - after_b, before_d - after_d
    if delta_b not in (0, 1) or delta_d not in (0, 1):
        return False
    if delta_d < delta_b:
        return False
    return gain(base, added, grown, edges) >= gain(base, added, present, edges)


def check_instance(base, added, objects, edges):
    """Every step of the proof, on one fixed graph, over every present-object set."""
    dets = list(base) + list(added)
    for present in subsets(objects):
        present = list(present)
        if not check_defect_identity(base, added, present, edges):
            return "defect identity"
        if not check_supermodular(dets, present, edges):
            return "supermodularity"
        if not check_intersection_lemma(base, added, present, edges):
            return "intersection lemma"
        for extra in objects:
            if extra in present:
                continue
            if not check_delta_inequality(base, added, present, edges, extra):
                return "delta inequality"
    return None


def exhaustive(max_base=2, max_added=1, max_objects=3):
    """Every edge set on every small shape."""
    checked = 0
    for nb in range(1, max_base + 1):
        for nc in range(1, max_added + 1):
            for no in range(1, max_objects + 1):
                base = [f"b{i}" for i in range(nb)]
                added = [f"c{i}" for i in range(nc)]
                objects = [f"o{i}" for i in range(no)]
                pairs = [(d, o) for d in base + added for o in objects]
                for bits in range(2 ** len(pairs)):
                    edges = {pairs[i] for i in range(len(pairs)) if bits >> i & 1}
                    failure = check_instance(base, added, objects, edges)
                    if failure:
                        return checked, (base, added, objects, sorted(edges), failure)
                    checked += 1
    return checked, None


def randomised(trials=150, seed=20260912):
    """Larger shapes, sampled. Each instance costs O(4^|D|) in the supermodularity
    step, so the count is chosen to keep the whole check near ten seconds rather
    than to sound large."""
    rng = random.Random(seed)
    for _ in range(trials):
        base = [f"b{i}" for i in range(rng.randint(1, 4))]
        added = [f"c{i}" for i in range(rng.randint(1, 3))]
        objects = [f"o{i}" for i in range(rng.randint(1, 5))]
        density = rng.choice((0.2, 0.4, 0.6, 0.8))
        edges = {(d, o) for d in base + added for o in objects if rng.random() < density}
        failure = check_instance(base, added, objects, edges)
        if failure:
            return trials, (base, added, objects, sorted(edges), failure)
    return trials, None


def main(argv):
    exhaustive_checked, exhaustive_failure = exhaustive()
    random_checked, random_failure = randomised()
    if exhaustive_failure or random_failure:
        sys.stderr.write(f"proof step failed: {exhaustive_failure or random_failure}\n")
        return 1
    print("theorem: the gain is nondecreasing in the present-object set, for a fixed edge set")
    print(f"  exhaustive instances checked : {exhaustive_checked}")
    print(f"  random instances checked     : {random_checked}")
    print("  steps checked per instance   : defect identity, supermodularity, "
          "intersection lemma, delta inequality")
    print("  scope: a fixed edge set. Worlds that disagree about which detection could have")
    print("         matched which object are outside the hypothesis and are not covered.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
