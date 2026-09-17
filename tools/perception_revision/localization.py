"""Propose graph-envelope certificates or a supplied geometric displacement."""
import copy
from tools.perception_decision.kernel import _matching_certificate
from .contract import MAX_WORK, require
from .localization_contract import VERSION, displacement_graphs, matching_work, prepare
from .localization_checker import conclude


def produce(case, request, candidate=None):
    reason, prepared = prepare(case, request)
    displaced = None
    if reason is None:
        displaced = displacement_graphs(request, prepared, candidate) if candidate is not None else None
        if matching_work(prepared, displaced) > MAX_WORK:
            # A witness outside this bound is rejected, never repackaged as a
            # statement that the universal-envelope computation was attempted.
            require(candidate is None, 'LOCALIZATION_WITNESS_WORK', 'Displacement proof exceeds work limit')
            reason = 'matching_work_limit'
    if reason is not None:
        proof = {'kind': 'localization_unavailable', 'version': VERSION, 'reason': reason}
    else:
        proof = {'kind': 'localization_displacement' if candidate is not None else 'localization_envelope',
                 'version': VERSION, 'anchors': []}
        if candidate is not None:
            proof['candidate'] = copy.deepcopy(candidate)
        for row in prepared['rows']:
            entry = {'anchor': row['anchor']['id']}
            for role, key, edges in [('a', 'a_possible', row['possible']), ('b', 'b_guaranteed', row['guaranteed'])]:
                if displaced is not None:
                    key = 'output_' + role
                    edges = displaced[row['anchor']['id']]
                entry[key] = _matching_certificate(row[role], {(d, o) for d, o in edges if d in row[role]})
            proof['anchors'].append(entry)
    return {'result': conclude(case, request, proof), 'proof': proof}
