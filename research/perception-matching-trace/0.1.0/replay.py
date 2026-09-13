"""Replay source joins on the retained two-world synthetic admission fixture.

This is a bounded engineering example, not an admission or reviewer interface.
Existing common-source and decision checks run before any endpoint is followed.
The complete trace goes to stdout; measured process stages go to stderr.
"""
import argparse
from fractions import Fraction
import hashlib
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tools import perception_operands as operands, perception_reviewed_operands as reviewed
from tools.perception_decision import cli, contract
from tools.perception_inputs import catalog as inventory
from tools.perception_inputs.source_io import snapshot


def one(rows, **keys):
    selected = [row for row in rows if all(row.get(k) == v for k, v in keys.items())]
    if len(selected) != 1:
        raise ValueError(f'Expected one row for {keys}; found {len(selected)}')
    return selected[0]


def read(spec):
    with snapshot(spec) as stream:
        return contract.parse(stream.read())


def same_prediction(record, raw):
    return (record['sample_token'] == raw['sample_token']
            and record['class'] == raw['detection_name']
            and all(contract.rational(q) == Fraction(x)
                    for q, x in zip(record['xy'], raw['translation'][:2]))
            and contract.rational(record['score']) == Fraction(raw['detection_score']))


def trace(case, packet, renamings, admission, normalizations, catalog, custody, package):
    assert case['evidence_kind'] == 'synthetic'
    assert packet['payload']['proof']['kind'] == 'enumerated'
    assert len(packet['payload']['proof']['worlds']) == 2
    rows, prediction_frames, checked_captures = [], {}, {}
    for world in packet['payload']['proof']['worlds']:
        assignment = dict(zip(case['model']['variables'], world['assignment'], strict=True))
        wid = one([w for w in renamings['world_encodings'] if all(
            assignment[c['variable']] == c['value'] for c in w['when'])])['world_id']
        reference_world = one(admission['reference']['worlds'], id=wid)
        for anchor in world['anchors']:
            aid = anchor['anchor']
            assert one(case['anchors'], id=aid)['reference']['state'] == 'finite'
            mapping = one(renamings['anchors'], neutral_anchor_id=aid)
            original_anchor = mapping['original_anchor_id']
            normal = one(normalizations, anchor_id=original_anchor)
            source_anchor = one(catalog['anchors'], sample_token=mapping['sample_token'])
            reference_anchor = one(reference_world['anchors'], anchor_id=original_anchor)
            for configuration in ('base', 'augmented'):
                for detection_id, graph_id in anchor[configuration]['matching']:
                    obj = one(renamings['object_mapping'], world_id=wid,
                              anchor_id=original_anchor, graph_id=graph_id)
                    original_object = one(reference_anchor['objects'], id=obj['object_id'],
                                          record_sha256=obj['record_sha256'], members=obj['members'])
                    translation = one([r for r in mapping['detections']
                                       if r['neutral']['id'] == detection_id])
                    normalized = one(normal['qualified_records'], detection=translation['original'])
                    record = normalized['record']
                    assert hashlib.sha256(contract.encoded(record)).hexdigest() == translation['original']['record_sha256']
                    source = catalog['sources'][record['source']]
                    assert source['sha256'] == record['source_sha256']
                    key = (mapping['sample_token'], record['source'])
                    if key not in prediction_frames:
                        prediction_frames[key] = inventory.extract_frame(source, key[0], source_anchor[key[1]])
                    raw = prediction_frames[key][record['source_index']]
                    assert same_prediction(record, raw)
                    # This fixture has one retained row, one low-score row and one
                    # out-of-range row. The other row indices cannot stand in for it.
                    assert record['source_index'] == 0
                    assert not any(same_prediction(record, other) for other in prediction_frames[key][1:])
                    evidence = []
                    for member in obj['members']:
                        proposal = admission['proposal_registry'][member]
                        assert proposal['phase'] == 'unassisted_discovery'
                        sealed = one(admission['discovery_records'],
                                     canonical_record_sha256=proposal['canonical_record_sha256'])
                        assert member == sealed['canonical_record_sha256']+':'+proposal['proposal']['id']
                        assert one(sealed['record']['proposals'], id=proposal['proposal']['id']) == proposal['proposal']
                        assert hashlib.sha256(contract.encoded(proposal['proposal'])).hexdigest() == proposal['proposal_sha256']
                        assert proposal['proposal']['window_id'] == aid
                        for observation in proposal['proposal']['evidence']:
                            capture_id = observation['capture_id']
                            capture = one(custody['captures'], capture_id=capture_id)
                            assert observation['locator'] == {'kind': 'capture'}
                            if capture_id not in checked_captures:
                                original = capture['raw_identity']
                                raw_path = Path(custody['request']['raw_root'])/original['filename']
                                raw_bytes = operands.checked_bytes(raw_path, original['sha256'], original['byte_size'], original['byte_size'])
                                asset = capture['disclosed_evidence']['asset']
                                asset_bytes = operands.checked_bytes(package/asset['filename'], asset['sha256'], asset['byte_size'], asset['byte_size'])
                                assert raw_bytes == asset_bytes  # This fixture's image is copied unchanged.
                                checked_captures[capture_id] = capture
                            evidence.append({'member': member, 'proposal_sha256': proposal['proposal_sha256'],
                                'capture_id': capture_id, 'original_capture': capture['raw_identity'],
                                'sample_data_token': capture['sample_data_token'],
                                'capture_timestamp_us': capture['source']['capture_timestamp_us'],
                                'locator': observation['locator'],
                                'point_or_pixel_selection': {'state': 'unavailable', 'reason': 'capture_only_locator'}})
                    rows.append({'world_id': wid, 'assignment': world['assignment'], 'anchor_id': aid,
                        'configuration': configuration, 'matching_endpoint': [detection_id, graph_id],
                        'reference': {'original_anchor_id': original_anchor, 'object_id': obj['object_id'],
                            'record_sha256': obj['record_sha256'], 'xy': original_object['xy'],
                            'timestamp_us': original_object['timestamp_us'], 'evidence': evidence},
                        'prediction': {'source_sha256': source['sha256'], 'source_role': record['source'],
                            'sample_token': record['sample_token'], 'source_index': record['source_index'],
                            'index_basis': 'zero_based_in_original_sample_array',
                            'frame_byte_span': source_anchor[record['source']],
                            'original_node': translation['original'], 'normalized_record': record}})
    assert len(rows) == 10 and len(prediction_frames) == 4 and len(checked_captures) == 2
    # Independent, fixture-specific source expectations; no graph name parsing.
    for row in rows:
        window = row['anchor_id']; ref = row['reference']; pred = row['prediction']
        assert pred['sample_token'] == {'window-0001': 'f0-2', 'window-0002': 'f1-2'}[window]
        assert pred['normalized_record']['xy'] == [contract.wire(Fraction(10 if pred['source_role'] == 'base' else 13)), contract.wire(Fraction(20))]
        assert ref['evidence'][0]['capture_id'] == {'window-0001': 'capture-000006', 'window-0002': 'capture-000041'}[window]
        assert ref['timestamp_us']-ref['evidence'][0]['capture_timestamp_us'] == 2_000_000
    ambiguous = []
    for keys in ({'graph_id': 'shared:o0'}, {'graph_id': 'shared:o0', 'world_id': 'world-0'},
                 {'graph_id': 'shared:o0', 'anchor_id': 'one'}):
        try:
            one(renamings['object_mapping'], **keys)
        except ValueError as exc:
            ambiguous.append({'lookup': keys, 'refused': str(exc)})
        else:
            raise AssertionError('An incomplete provenance key became unique')
    shared = [m for m in renamings['object_mapping'] if m['graph_id'] == 'shared:o0']
    assert len(shared) == len({m['record_sha256'] for m in shared}) == 4
    first = one(shared, world_id='world-0', anchor_id='one')
    other = one(shared, world_id='world-1', anchor_id='one')
    try:
        one(shared, world_id='world-0', anchor_id='one', record_sha256=other['record_sha256'])
    except ValueError as exc:
        ambiguous.append({'lookup': 'other_world_record_for_same_shared_node', 'refused': str(exc)})
    else:
        raise AssertionError('A different world supplied the selected source record')
    assert first['record_sha256'] != other['record_sha256']
    return {'artifact_id': 'reiyah.perception-matching-trace.example', 'version': '0.1.0',
            'scope': 'retained_two_world_synthetic_fixture_only', 'matching_endpoints': rows,
            'ambiguous_lookups_refused': ambiguous, 'source_identity_checked': True,
            'human_observation': False, 'physical_association': 'not_established',
            'capture_to_reference_motion': 'not_established', 'stage_release': 'not_performed'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('inputs', 'common', 'decision'):
        parser.add_argument('--'+name, type=Path, required=True)
        parser.add_argument('--'+name+'-sha256', required=True)
    args = parser.parse_args()
    start = time.perf_counter()
    inputs = contract.load(args.inputs, args.inputs_sha256, 16384, validate_input=False)
    for key in ('binding_request', 'admission_request', 'admission_report', 'assistance'):
        inputs[key] = Path(inputs[key])
    reviewed.check(args.common, args.common_sha256, **inputs)
    preparation = contract.parse(operands.checked_bytes(args.common/'PREPARATION.json', args.common_sha256, reviewed.RECEIPT_LIMIT))
    common = {r['path']: operands.checked_bytes(args.common/r['path'], r['sha256'], r['byte_size'], r['byte_size'])
              for r in preparation['files']}
    case_path = args.common/'common/comparison.json'
    case_digest = hashlib.sha256(common['common/comparison.json']).hexdigest()
    cli.verify(case_path, case_digest, args.decision, args.decision_sha256)
    packet = contract.load(args.decision, args.decision_sha256, contract.MAX_PACKET_BYTES, validate_input=False)
    verified = time.perf_counter()
    admission = contract.parse(common['common/admission.json'])
    bound = admission['binding']['inputs']
    request = read(admission['inputs']['binding_request'])
    result = trace(contract.parse(common['common/comparison.json']), packet,
        contract.parse(common['common/renamings.json']), admission, read(bound['normalizations']),
        read(bound['catalog']), read(bound['observation_custody']), Path(request['package']['path']))
    result['selected'] = {'inputs_sha256': args.inputs_sha256, 'common_preparation_sha256': args.common_sha256,
                          'decision_sha256': args.decision_sha256, 'comparison_sha256': case_digest}
    sys.stdout.buffer.write(contract.encoded(result))
    sys.stderr.buffer.write(contract.encoded({'common_and_decision_verify_seconds': verified-start,
        'trace_and_controls_seconds': time.perf_counter()-verified}))


if __name__ == '__main__':
    main()
