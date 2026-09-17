"""Check observation applicability, conditioning and a fresh matching/cover proof."""
from tools.perception_decision.checker import _keys, _require
from . import localization_checker
from .checker import result_template
from .contract import MAX_PACKET_BYTES, encoded
from .position_contract import FAMILY, VERSION, condition


def conclude(case, request, observations, proof):
    _require(len(encoded(proof)) <= MAX_PACKET_BYTES, 'Position proof exceeds byte limit')
    _keys(proof, ('kind', 'version', 'conditioning', 'geometry'))
    _require(proof['kind'] == 'position_audit' and proof['version'] == VERSION, 'Wrong position proof kind/version')
    report, derived = condition(case, request, observations)
    _require(encoded(proof['conditioning']) == encoded(report), 'Incorrect applicability or conditioning claim')
    if derived is not None:
        _require(type(proof['geometry']) is dict and proof['geometry'].get('kind') in ('localization_envelope', 'localization_linear'),
                 'Only a universal enclosure proof is admitted; a point in an outer ball may violate the intersection')
        result = localization_checker.conclude(*derived, proof['geometry'])
    else:
        _require(proof['geometry'] is None, 'Unavailable conditioning cannot carry a geometry conclusion')
        result = result_template(case)
        result.update(position_basis=request['position_basis'], robustness='not_evaluated', witness_value=None)
        if report['status'] == 'inconsistent_premises':
            result['model_status'] = 'inconsistent'
        else:
            reason = report['reason']
            result['execution_status'] = ('input_blocked' if reason == 'unavailable_outputs' else
                                          'resource_limited' if reason.endswith('_limit') else 'scope_unavailable')
    result.update(geometry_family=FAMILY, observation_basis=observations['observation_basis'],
                  supplied_observation_count=len(observations['observations']),
                  conditioning_status=report['status'], conditioning_reason=report['reason'],
                  partial_intersection_enclosures=sum(r['relation'] == 'partial_overlap' for r in report['records']))
    return result


def check(case, request, observations, payload):
    _require(len(encoded(payload)) <= MAX_PACKET_BYTES, 'Position packet exceeds byte limit')
    _keys(payload, ('result', 'proof'))
    result = conclude(case, request, observations, payload['proof'])
    _require(encoded(payload['result']) == encoded(result), 'Result not entailed by position proof')
    return result
