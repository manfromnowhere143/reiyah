"""Propose a complete local-deletion proof; no audit-query selection."""
from tools.perception_decision.kernel import _matching_certificate
from .component_plan import VERSION, make_plan, variants


def propose(case, domains):
    plan = make_plan(case, domains)
    if plan.limit:
        return {'kind': 'component_resource_limit', 'version': VERSION, 'reason': plan.limit}
    proof = {'kind': 'component_deletions', 'version': VERSION, 'worlds': []}
    for world in plan.worlds:
        rows = []
        for c, method in zip(world.components, world.methods):
            row = {'anchor': c.anchor, 'objects': sorted(c.objects),
                   'kind': method}
            if not c.cancels:
                entries = []
                for deleted in variants(c, world.budget) if method == 'enumerated' else [()]:
                    removed = set(deleted)
                    entry = {'deletions': list(deleted)}
                    for role, left in (('output_a', c.output_a), ('output_b', c.output_b)):
                        edges = {(d, o) for d, o in c.edges if d in left and o not in removed}
                        entry[role] = _matching_certificate(set(left), edges)
                    entries.append(entry)
                row['variants'] = entries
            rows.append(row)
        proof['worlds'].append({'assignment': list(world.bits), 'components': rows})
    return proof
