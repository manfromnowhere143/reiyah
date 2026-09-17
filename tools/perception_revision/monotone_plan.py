"""Admission for endpoint audit proofs of preserved-base additions (0.1.0)."""
from .contract import MAX_WORK, ROLES, capacity, graph

VERSION = '0.1.0'


def admission(case, domains):
    """General audit availability must be checked before this method admission."""
    for a in case['anchors']:
        aa, bb = ({d['id'] for d in a[r]['value']} for r in ROLES)
        if not aa <= bb:
            return {'reason': 'outputs_not_nested', 'work_bound': None}
    count, unit = capacity(case)
    work = count * unit  # Reserve the existing full upper-endpoint work estimate.
    for _, env, (required, free, _) in domains:
        removed = required | set(free)
        for a in case['anchors']:
            present, edges = graph(a, env, removed)
            for role in ROLES:
                left = {d['id'] for d in a[role]['value']}
                ne = sum(d in left for d, _ in edges)
                work += 2 * (len(left) + 1) * (len(present) + ne + 1)
    return {'reason': 'endpoint_work_limit' if work > MAX_WORK else None, 'work_bound': work}
