"""Independent output qualification for a declared nuScenes replacement comparison.

This composes the existing adapter's base qualification twice. No detections are
suppressed against the other output. Original source identity remains upstream.
"""
import hashlib

from tools.perception_decision.nuscenes import normalize_frame as qualify_legacy
from .contract import encoded, require

POLICY = 'reiyah.nuscenes-replacement-comparison.0.1.0'


def normalize_frame(*, sample_token, anchor_id, ego_xy, weight, output_a, output_b, source_sha256):
    require(type(source_sha256) is dict and set(source_sha256) == {'output_a', 'output_b', 'clock'},
            'ADAPTER_SOURCE', 'Name independent output A, output B and clock source identities')
    receipts, records, trace, outputs = [], {}, [], {}
    for role, output in [('output_a', output_a), ('output_b', output_b)]:
        # Only the base half is consumed. An empty second half cannot suppress it.
        anchor, receipt = qualify_legacy(sample_token=sample_token, anchor_id=anchor_id,
            ego_xy=ego_xy, weight=weight, base=output, camera={'state': 'observed', 'value': []},
            source_sha256={'base': source_sha256[role], 'camera': source_sha256['clock'],
                           'clock': source_sha256['clock']})
        receipts.append(receipt)
        nodes = []
        for row in receipt['qualified_records']:
            record = dict(row['record'])
            record.update(policy=POLICY, source='independent_detector_output')
            digest = hashlib.sha256(encoded(record)).hexdigest()
            node = {'id': 'd:' + record['source_sha256'] + ':' + str(record['source_index']),
                    'record_sha256': digest}
            require(node['id'] not in records or records[node['id']]['detection'] == node,
                    'COMMON_OUTPUT_IDENTITY', 'Same source row identity has conflicting supplied content')
            records[node['id']] = {'detection': node, 'record': record}
            nodes.append(node)
        outputs[role] = {'state': 'observed', 'value': nodes} if output['state'] == 'observed' else dict(output)
        trace.extend({'output': role, 'source_index': t['source_index'],
                      'score_eligible': t['score_eligible'], 'range_eligible': t['range_eligible'],
                      'retained': t['score_eligible'] and t['range_eligible']} for t in receipt['trace'])
    anchor = {'id': anchor_id, 'weight': anchor['weight'], **outputs,
              'reference': {'state': 'open', 'reason': 'No finite reference graph supplied'}}
    receipt = {'artifact_id': 'reiyah.perception-revision.normalization', 'version': '0.1.0',
               'policy': POLICY, 'sample_token': sample_token, 'anchor_id': anchor_id,
               'ego_xy': receipts[0]['ego_xy'], 'source_sha256': dict(source_sha256),
               'source_availability': {r: outputs[r]['state'] for r in outputs},
               'selection': 'Each output independently: score >= 0.30 and global XY range <= 50 metres',
               'additional_suppression': 'none',
               'normalized_anchor_sha256': hashlib.sha256(encoded(anchor)).hexdigest(),
               'qualified_records': [records[k] for k in sorted(records)], 'trace': trace,
               'input_counts': {r: len(o['value']) if o['state'] == 'observed' else None
                                for r, o in [('output_a', output_a), ('output_b', output_b)]},
               'upstream_source_verification': 'caller_obligation',
               'unused_prediction_fields': receipts[0]['unused_prediction_fields']}
    return anchor, receipt
