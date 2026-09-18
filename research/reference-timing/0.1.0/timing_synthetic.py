"""Exercise the SDK-to-matching-runtime boundary with synthetic source records.

Prepare with the retained SDK Python, then check with the selected research
Python. No image files, development metadata or prediction runtime are used.
"""
from copy import deepcopy
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys

from timing_metadata import file_binding, put, read, require


def digest(value):
    return hashlib.sha256((json.dumps(value, sort_keys=True, separators=(',', ':'))+'\n').encode()).hexdigest()


def rectangle(identity, geometry):
    numbers = [Fraction(str(x)) for x in geometry]
    body = {'id': identity, 'xyxy': [{'numerator': str(x.numerator), 'denominator': str(x.denominator)} for x in numbers]}
    return {**body, 'record_sha256': digest(body)}


def prepare(path):
    from test_timing_model import fixture
    from timing_model import sdk_motion, sdk_project
    from timing_project import project_image
    variants = ('complete', 'birth_and_disappearance', 'scene_start', 'empty_current_census', 'zero_time', 'invalid_rotation',
                'behind_camera', 'rotated_and_clipped')
    rows = []
    for index, variant in enumerate(variants):
        selected, preceding, sd, current, previous, sample, previous_sample = fixture()
        iid = 'synthetic-'+str(index)
        if variant == 'birth_and_disappearance':
            extra = {**deepcopy(current), 'token': 'a2', 'instance_token': 'car1', 'prev': '', 'translation': [7, 0, 20]}
            selected['sample_annotation']['a2'] = extra; selected['instance']['car1'] = {'category_token': 'car'}
            old = {**deepcopy(previous), 'token': 'old_only', 'instance_token': 'car2', 'next': ''}
            preceding['sample_annotation']['old_only'] = old; preceding['instance']['car2'] = {'category_token': 'car'}
        elif variant == 'scene_start':
            sample['prev'] = ''
        elif variant == 'empty_current_census':
            selected['sample_annotation'] = {}; selected['instance'] = {}
        elif variant == 'zero_time':
            sd['timestamp'] = sample['timestamp']
        elif variant == 'invalid_rotation':
            previous['rotation'] = [0, 0, 0, 0]
        elif variant == 'behind_camera':
            previous['translation'][2] = current['translation'][2] = -20
        elif variant == 'rotated_and_clipped':
            current['rotation'] = [1, .2, -.1, .3]; previous['rotation'] = [1, -.1, .05, -.2]
            current['translation'] = [15, 0, 20]; previous['translation'] = [14, 1, 20]
            selected['ego_pose']['pose'].update(translation=[.2, -.1, .05], rotation=[1, .04, -.02, .01])
            selected['calibrated_sensor']['cal'].update(translation=[.1, .2, 0], rotation=[1, -.03, .01, -.02])
        app = {'image_id': iid, 'image_sha256': '0'*64, 'sample_data_token': sd['token'], 'sample_token': sample['token'],
               'sensor_timestamp_us': sd['timestamp'], 'annotation_sample_timestamp_us': sample['timestamp']}
        projected = project_image(iid, app, selected, preceding)
        require(projected['state'] == 'complete', 'Synthetic numerical projection failed')
        original = []
        for annotation in selected['sample_annotation'].values():
            modeled = sdk_motion(annotation, None, {'state': 'available', 'kind': 'current_time', 'amount': '1', 'span_us': None})
            result = sdk_project(selected, sd, annotation, modeled)
            if result['eligibility'] == 'eligible':
                original.append(rectangle('reference:'+annotation['token'], result['xyxy']))
        shared = rectangle('shared', [789, 397, 1000, 503])
        a = [shared, rectangle('old_unique', [350, 350, 400, 400])]
        b = [shared, rectangle('new_unique', [355, 355, 405, 405])]
        image = {'id': iid, 'ordinal': index, 'width': 1600, 'height': 900, 'image_sha256': '0'*64, 'policy_sha256': '1'*64,
                 'reference_input_state': 'available', 'output_a': {'state': 'observed', 'value': a},
                 'output_b': {'state': 'observed', 'value': b}}
        rows.append({'variant': variant, 'selected': selected, 'preceding': preceding, 'applicability': app,
                     'projection': projected, 'image': image, 'original': original})
    put(path, {'artifact_id': 'reiyah.reference-timing.synthetic-cross-runtime', 'version': '0.1.0', 'cases': rows,
               'all_records_synthetic': True, 'new_image_reads': 0, 'model_calls': 0})
    print(json.dumps({'prepared_cases': len(rows), 'binding': file_binding(path)}))


def check(path, report_path):
    from timing_bounds import case_rows
    from timing_certificate import matching
    from timing_run import analyze_image
    from timing_source_certificate import check_source_image
    from timing_verify import check_cases, check_image_record
    packet = read(path); require(packet['all_records_synthetic'] is True, 'Not a synthetic packet')
    cache = {'native': set(), 'native_check_seconds': 0.0}; rows = {}; contexts = {}; probes = []
    for row in packet['cases']:
        source = check_source_image(row['projection'], row['applicability'], row['selected'], row['preceding'])
        original_nominal = matching(row['image'], row['original'])
        result = analyze_image(row['image'], row['projection'], row['original'], original_nominal)
        check_image_record(result, row['image'], row['projection'], source, row['original'], original_nominal, cache)
        rows[row['image']['id']] = result
        contexts[row['variant']] = (row, source, original_nominal, result)
    cases = [{'id': iid, 'group': 'synthetic_singleton', 'images': [iid]} for iid in rows]
    cases.append({'id': 'all', 'group': 'synthetic_primary', 'images': list(rows)})
    aggregates = case_rows(cases, rows); check_cases(aggregates, cases, rows)
    def rejects(name, function, contains):
        try:
            function()
        except Exception as exc:
            require(contains.lower() in str(exc).lower(), 'Unexpected rejection for '+name+': '+str(exc))
            probes.append({'name': name, 'rejection': type(exc).__name__+': '+str(exc)})
        else:
            raise ValueError('Failed to reject: '+name)
    row, source, nominal, result = contexts['birth_and_disappearance']
    def check_result(value):
        return check_image_record(value, row['image'], row['projection'], source, row['original'], nominal, cache)
    mutation = deepcopy(result); mutation['current_unknown_instances'] = []
    rejects('missing_motion_not_empty', lambda: check_result(mutation), 'unknown census')
    mutation = deepcopy(result); mutation['union_unknown_instances'] = mutation['current_unknown_instances']
    rejects('predecessor_only_not_omitted', lambda: check_result(mutation), 'unknown census')
    mutation = deepcopy(result); mutation['contracts']['current_strict'] = mutation['contracts']['current_partial']
    rejects('strict_contract_not_silently_filled', lambda: check_result(mutation), 'silently filled')
    mutation = deepcopy(result); mutation['searches']['current']['bounds'][0] = {'numerator': '999', 'denominator': '1'}
    rejects('universal_bound_not_forged', lambda: check_result(mutation), 'universal bound')
    mutation = deepcopy(result); mutation['searches']['current']['candidate_evaluations'] += 1
    rejects('search_budget_accounted', lambda: check_result(mutation), 'evaluations omitted')
    mutation = deepcopy(result); key = mutation['known_proof_key']; mutation['proofs'][key]['references'] = []
    rejects('native_world_geometry_bound', lambda: check_result(mutation), 'geometry')
    mutation = deepcopy(result); key = mutation['known_proof_key']
    mutation['proofs'][key]['proof']['payload']['result']['bounds']['lower'] = {'numerator': '999', 'denominator': '1'}
    rejects('payload_mutation_after_cache_checked', lambda: check_result(mutation), 'Result not entailed by certificate')
    mutation = deepcopy(row['projection']); mutation['current_census'] = []
    rejects('current_census_complete', lambda: check_source_image(mutation, row['applicability'], row['selected'], row['preceding']), 'census')
    mutation = deepcopy(row['projection']); mutation['objects'][0]['modeled']['translation'][0] += 1
    rejects('motion_numerics_checked', lambda: check_source_image(mutation, row['applicability'], row['selected'], row['preceding']), 'centers')
    mutation = deepcopy(row['projection']); mutation['objects'][0]['projection']['record']['filename'] = 'wrong.jpg'
    rejects('source_filename_bound', lambda: check_source_image(mutation, row['applicability'], row['selected'], row['preceding']), 'source record')
    missing_row, _, _, _ = contexts['scene_start']; mutation = deepcopy(missing_row['projection']); mutation['preceding_census'] = []
    rejects('missing_predecessor_not_empty', lambda: check_source_image(mutation, missing_row['applicability'], missing_row['selected'], missing_row['preceding']), 'census')
    rejects('allocated_case_not_omitted', lambda: check_cases(aggregates[:-1], cases, rows), 'omitted')
    mutation = deepcopy(aggregates); mutation[-1]['membership'] = mutation[-1]['membership'][:-1]
    rejects('blocked_case_not_complete_subset', lambda: check_cases(mutation, cases, rows), 'full allocation')
    value = {'artifact_id': 'reiyah.reference-timing.synthetic-verification', 'version': '0.1.0',
             'source': file_binding(path), 'synthetic_images': len(rows), 'case_contract_rows': len(aggregates),
             'adversarial_probes': probes, 'unique_native_proofs_checked': len(cache['native']),
             'cross_runtime_source_and_geometry_passed': True, 'new_image_reads': 0, 'model_calls': 0}
    put(report_path, value)
    print(json.dumps({'synthetic_images': len(rows), 'case_contract_rows': len(aggregates), 'adversarial_probes': len(probes),
                      'unique_native_proofs_checked': len(cache['native'])}))


if __name__ == '__main__':
    if sys.argv[1] == 'prepare': prepare(sys.argv[2])
    elif sys.argv[1] == 'check': check(sys.argv[2], sys.argv[3])
    else: raise ValueError('Choose prepare or check')
