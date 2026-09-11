#!/usr/bin/env python3
"""Bounded synthetic matching examples; standard library only, no Reiyah imports.

Compute maximum counts by exhaustive reachable object subsets, independently of
the Engine's augmenting-path producer and matching/vertex-cover checker. This is
a small reference calculation, not a scalable alternative or physical study.
"""
from fractions import Fraction
import json


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def maximum_count(neighbors):
    """Each row lists eligible object indices for one detection."""
    reachable = {0}
    for row in neighbors:
        following = set(reachable)  # Leaving this detection unmatched is allowed.
        for mask in reachable:
            for obj in row:
                if not mask & (1 << obj):
                    following.add(mask | (1 << obj))
        reachable = following
    return max(mask.bit_count() for mask in reachable)


def edges(detections, objects):
    return [[j for j, y in enumerate(objects) if (x - y) ** 2 < 4]
            for x in detections]


def component_worlds(count):
    """Disjoint copies of the architecture's strict-2m, same-class example."""
    base = [Fraction(6 * i) for i in range(count)]
    additions = [x + 3 for x in base]
    known = [x + Fraction(3, 2) for x in base]
    disputed = [x - 1 for x in base]
    require(all(abs(x) <= 50 for x in base + additions + known + disputed),
            'Constructed coordinates must remain within the declared 50m range')
    require(all((x - y) ** 2 >= 4 for x in additions for y in base),
            'Every addition must survive base suppression')
    require(all((x - y) ** 2 >= 4 for i, x in enumerate(additions)
                for y in additions[:i]), 'Earlier additions must not suppress later ones')
    worlds = []
    candidate_edges = []
    for present in (False, True):
        objects = known + disputed if present else known
        candidate_edges.append(edges(additions, objects))
        tp_base = maximum_count(edges(base, objects))
        tp_augmented = maximum_count(edges(base + additions, objects))
        loss_base = len(objects) + len(base) - 2 * tp_base
        loss_augmented = len(objects) + len(base + additions) - 2 * tp_augmented
        delta = loss_base - loss_augmented
        require(delta == 2 * (tp_augmented - tp_base) - len(additions),
                'Direct unit loss must equal the paired matching identity')
        worlds.append({'disputed_base_neighbors_present': present,
                       'tp_base': tp_base, 'tp_augmented': tp_augmented,
                       'loss_base': loss_base, 'loss_augmented': loss_augmented,
                       'delta': delta})
    require(candidate_edges[0] == candidate_edges[1],
            'Candidate-to-object edges must be identical in both worlds')
    require([w['delta'] for w in worlds] == [-count, count], 'Incorrect example bounds')
    return worlds


def tiny_graph_control():
    """All 512 labelled bipartite graphs: two base + one added, three objects."""
    penalties = [(0, 0), (0, 1), (1, 0), (1, 1), (1, 4), (4, 1)]
    for bits in range(1 << 9):
        graph = [[j for j in range(3) if bits & (1 << (3 * i + j))]
                 for i in range(3)]
        base_tp = maximum_count(graph[:2])
        augmented_tp = maximum_count(graph)
        gain = augmented_tp - base_tp
        require(0 <= gain <= 1, 'Base preservation must bound the matching gain')
        for a, b in penalties:
            direct = a * (3 - base_tp) + b * (2 - base_tp)
            direct -= a * (3 - augmented_tp) + b * (3 - augmented_tp)
            require(direct == (a + b) * gain - b, 'Paired-loss identity failed')
            require(-b <= direct <= a, 'Count enclosure failed')
    return {'labelled_graphs': 512, 'penalty_pairs': len(penalties),
            'loss_checks': 512 * len(penalties)}


def main():
    single = component_worlds(1)
    eight = component_worlds(8)
    # An unreachable object changes both absolute losses equally.
    remote_losses = []
    for objects in ([0, 3], [0, 3, 10]):
        base_tp = maximum_count(edges([0], objects))
        augmented_tp = maximum_count(edges([0, 3], objects))
        remote_losses.append([len(objects) + 1 - 2 * base_tp,
                              len(objects) + 2 - 2 * augmented_tp])
    require(remote_losses == [[1, 0], [2, 1]], 'Remote-object cancellation failed')
    paired = [base - augmented for base, augmented in remote_losses]
    separate = [min(x[0] for x in remote_losses) - max(x[1] for x in remote_losses),
                max(x[0] for x in remote_losses) - min(x[1] for x in remote_losses)]
    require(paired == [1, 1] and separate == [0, 2], 'Paired vs separate ranges failed')
    # Same world at both equally weighted anchors: 16 additions, weighted R=8.
    together = [Fraction(w['delta'], 2) + Fraction(w['delta'], 2) for w in eight]
    require(together == [-8, 8], 'Incorrect two-anchor bound')
    # A different declared model: disputed presence is opposite across anchors.
    # Neither world lets both anchors achieve their individual minima/maxima.
    opposed = [(Fraction(single[i]['delta'], 2) +
                Fraction(single[1 - i]['delta'], 2)) for i in range(2)]
    require(opposed == [0, 0], 'Shared-world cancellation failed')
    output = {
        'artifact_id': 'reiyah.perception-decision-review.examples', 'version': '0.1.0',
        'evidence_kind': 'synthetic',
        'calculation': 'exhaustive_reachable_object_subsets',
        'single_component': {'worlds': single, 'exact_interval': [-1, 1]},
        'unreachable_disputed_object': {
            'world_losses_base_augmented': remote_losses, 'exact_interval': paired,
            'separate_loss_relaxation': separate},
        'sixteen_candidate_objects_confirmed': {
            'anchors': 2, 'weight_each': '1/2', 'retained_additions_each': 8,
            'candidate_edges_identical_in_both_worlds': True,
            'worlds_per_anchor': eight, 'exact_interval': [int(x) for x in together]},
        'oppositely_coupled_anchors': {
            'joint_world_deltas': [str(x) for x in opposed], 'exact_interval': [0, 0],
            'separate_anchor_relaxation': [-1, 1]},
        'tiny_graph_control': tiny_graph_control(),
        'limit': 'Constructed worlds only; no real observations, review budget, statistical coverage or novelty claim.'}
    print(json.dumps(output, sort_keys=True, separators=(',', ':')))


if __name__ == '__main__':
    main()
