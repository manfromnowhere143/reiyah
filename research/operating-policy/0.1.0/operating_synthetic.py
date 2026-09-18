"""Full 64-image pipeline fixture; these are not research observations."""
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
import sys
import time

from operating_sources import ROLES, admit, digest, file_binding, filtered_operand, put, q, read, qualify, w
from operating_math import FAMILIES, aggregate, analyze_state, world_banks
from operating_run import run
from operating_verify import run as verify
from test_admission import fixture
from test_operating_math import synthetic_sources


def execute(destination, candidate):
    tick = time.perf_counter(); destination = Path(destination).resolve(); candidate = Path(candidate).resolve()
    destination.mkdir(); root = destination/'synthetic_session'; root.mkdir(); comparison = root/'private/comparison-01'
    for folder in ('inputs', 'oracle', 'custody', 'runs/analysis-01'): (comparison/folder).mkdir(parents=True)
    temporal = root/'private/synthetic-temporal'; temporal.mkdir(); packet = destination/'experiment'; packet.mkdir()
    base_image, source_packets, original, edit, source_temporal = synthetic_sources()
    allocation, configuration, original_packet = fixture()
    allocated = [{'id': 'image-'+str(i).zfill(2), 'width': 100, 'height': 100, 'image_sha256': digest({'synthetic_image': i})}
                 for i in range(64)]
    allocation['images'] = allocated; packets = {}; bindings = []; images = []; temporal_entries = []; states = {}; proofs = {}
    for role, stage in zip(ROLES, ('export-06-64', 'export-07-64')):
        folder = root/'results'/stage; folder.mkdir(parents=True); rows = []
        for value in allocated:
            detections = deepcopy(source_packets[role]['synthetic']['detections'])
            rows.append({**value, 'configuration_sha256': digest(configuration), 'state': 'processed', 'detections': detections,
                         'source_detection_count': len(detections), 'empty_basis': None})
        publisher = {**original_packet, 'allocation_sha256': digest(allocation), 'configuration_sha256': digest(configuration), 'images': rows}
        for name, value in {'ALLOCATION': allocation, 'CONFIGURATION': configuration, 'PACKET': publisher,
                            'RESULT': {'admission': admit(allocation, configuration, publisher)}}.items():
            path = folder/(name+'.json'); put(path, value); bindings.append(file_binding(path))
        packets[role] = {row['id']: row for row in rows}
    put(comparison/'custody/SOURCE_BINDINGS.json', bindings)
    for i, value in enumerate(allocated):
        image = {**value, 'ordinal': i, 'policy_sha256': '1'*64, 'reference_input_state': 'available'}
        for role in ROLES: image[role], _ = filtered_operand(packets[role][value['id']], q(w(1))/4)
        images.append(image); iid = value['id']; temporal_record = deepcopy(source_temporal)
        if i % 2 == 0:
            temporal_record['current_unknown_instances'] = []
            temporal_record['proofs'] = {'known': temporal_record['proofs']['known']}
        if i != 63: temporal_record['union_unknown_instances'] = temporal_record['current_unknown_instances']
        temporal_record['image_id'] = iid
        path = temporal/(iid+'.json'); put(path, temporal_record); temporal_entries.append({'image_id': iid, **file_binding(path)})
        put(comparison/'oracle'/(iid+'.json'), {'answer': original})
        put(comparison/'runs/analysis-01'/(iid+'.json'), edit)
        bank = world_banks(original, edit, temporal_record)
        state = {'image': image, 'analysis': analyze_state(image, bank, proofs)}; states[iid] = state
    cases = [{'id': value['id'], 'group': 'singleton', 'images': [value['id']]} for value in allocated]
    cases.extend({'id': 'block-'+str(i//8).zfill(2), 'group': 'block', 'images': [row['id'] for row in allocated[i:i+8]]}
                 for i in range(0, 64, 8))
    cases.append({'id': 'all-64', 'group': 'primary', 'images': [row['id'] for row in allocated]})
    put(comparison/'inputs/visible.json', {'images': images, 'cases': cases})
    original_rows = []; temporal_rows = []
    for case in cases:
        for family in FAMILIES:
            row = aggregate(case, family, case['images'], states)
            if family in FAMILIES[:3]: original_rows.append({key: row[key] for key in ('case_id', 'family', 'bounds', 'decision')})
            else: temporal_rows.append({'case_id': case['id'], 'contract': family, 'bounds': row['bounds'], 'decision': row['decision']})
    put(comparison/'runs/analysis-01/RESULTS.json', {'cases': original_rows})
    put(temporal/'RESULTS.json', {'image_records': temporal_entries, 'cases': temporal_rows})
    put(temporal/'VERIFICATION.json', {'results_sha256': file_binding(temporal/'RESULTS.json')['sha256'], 'all_complete_rows_verified': True,
                                    'scope': 'Synthetic fixture construction, not external source verification'})
    qualification = packet/'SCORE_QUALIFICATION.json'; qualify(root, qualification)
    source_paths = set(root.rglob('*.json')) | {qualification}
    source_paths.update((candidate/'research/operating-policy/0.1.0').glob('*.py'))
    plan = candidate/'research/operating-policy/0.1.0/PLAN.md'; source_paths.add(plan)
    freeze = {'artifact_id': 'reiyah.operating-policy.synthetic-freeze', 'version': '0.1.0',
        'synthetic_only': True, 'frozen_utc': datetime.now(timezone.utc).isoformat(),
        'bindings': [file_binding(path) for path in sorted(source_paths)], 'policy_sha256': file_binding(plan)['sha256'],
        'session_root': str(root), 'comparison': str(comparison), 'score_qualification': str(qualification),
        'temporal_results': str(temporal/'RESULTS.json'), 'temporal_verification': str(temporal/'VERIFICATION.json')}
    put(packet/'FREEZE.json', freeze); run(packet, 'synthetic-01'); verify(packet, 'synthetic-01')
    result = read(packet/'runs/synthetic-01/RESULTS.json'); checked = read(packet/'runs/synthetic-01/VERIFICATION.json')
    nominal = [row for row in result['primary_rows'] if row['family'] == 'exact_projection']
    assert [q(row['bounds'][0]) for row in nominal] == [-2, -1, 0, -1, 0, 0]
    assert checked['primary_rows'] == 42 and checked['anchor_rows'] == 4088
    assert checked['individual_threshold_cells'] == [4, 4] and checked['nominal_threshold_pairs'] == 16
    report = {'artifact_id': 'reiyah.operating-policy.synthetic-pipeline', 'version': '0.1.0',
        'synthetic_only': True, 'seconds': time.perf_counter()-tick, 'images': 64, 'cases': 73,
        'primary_rows': checked['primary_rows'], 'anchor_rows': checked['anchor_rows'],
        'analytically_known_primary_deltas': [-2, -1, 0, -1, 0, 0],
        'native_proofs': checked['native_proofs'], 'all_pipeline_checks_passed': True,
        'results': file_binding(packet/'runs/synthetic-01/RESULTS.json'),
        'verification': file_binding(packet/'runs/synthetic-01/VERIFICATION.json')}
    put(destination/'SYNTHETIC_REPORT.json', report); print(__import__('json').dumps(report), flush=True)


if __name__ == '__main__':
    execute(*sys.argv[1:])
