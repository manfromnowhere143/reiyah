"""Compare all frozen cases under complete and partial temporal references."""
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
import sys
import time

from timing_bounds import (CONTRACTS, ROLES, candidates, case_rows, certify, digest, iou,
                           optional_bounds, q, search, validate_canvas, validate_rows, w)
from timing_metadata import file_binding, put, read, require


def modeled_reference(value, alternative=False):
    coordinates = value['numerical_check']['alternative_projection'] if alternative else value['projection']['xyxy']
    body = {'id': 'reference:' + value['annotation_token'],
            'xyxy': [w(Fraction(str(x))) for x in coordinates]}
    return {**body, 'record_sha256': digest({'basis': 'declared_camera_time_motion_model', 'object': value, **body})}


def known_references(projection, image):
    require(projection['state'] == 'complete', 'Projection or numerical verification incomplete')
    known, alternative = [], []
    for value in projection['objects']:
        if value['state'] != 'modeled':
            continue
        require(value['numerical_check']['state'] == 'passed', 'Missing independent numerical check')
        if value['projection']['eligibility'] == 'eligible':
            known.append(modeled_reference(value)); alternative.append(modeled_reference(value, True))
    validate_rows(known); validate_canvas(known, image)
    validate_rows(alternative); validate_canvas(alternative, image)
    for role in ROLES:
        for detection in image[role]['value']:
            for first, second in zip(known, alternative):
                require((iou(detection, first) >= Fraction(1, 2)) == (iou(detection, second) >= Fraction(1, 2)),
                        'Independent projection changes a threshold matching edge')
    return known


def changes(projection, original):
    old = {row['id']: row for row in original}; counts = Counter(); displacement = []
    for value in projection['objects']:
        identity = 'reference:' + value['annotation_token']; was = identity in old
        if value['state'] != 'modeled':
            counts['originally_eligible_unassessed' if was else 'originally_ineligible_unassessed'] += 1
            continue
        now = value['projection']['eligibility'] == 'eligible'
        state = 'stayed_eligible' if was and now else 'entered_eligibility' if now else 'left_eligibility' if was else 'stayed_ineligible'
        counts[state] += 1
        if was and now:
            differences = [abs(Fraction(str(x))-q(y)) for x, y in zip(value['projection']['xyxy'], old[identity]['xyxy'])]
            displacement.append({'annotation_token': value['annotation_token'], 'maximum_coordinate_change': w(max(differences)),
                                 'coordinate_changes': list(map(w, differences))})
    return {'counts': dict(counts), 'paired_changes': displacement,
            'maximum_coordinate_change': w(max((q(row['maximum_coordinate_change']) for row in displacement), default=Fraction(0)))
            if displacement else None}


def blocked_contract(reason):
    return {'state': 'input_blocked', 'reason': reason, 'bounds': None, 'attained': None, 'proof_keys': None}


def analyze_image(image, projection, original, original_nominal):
    tick = time.perf_counter(); known = known_references(projection, image)
    unknown_current = sorted(value['instance_token'] for value in projection['objects'] if value['state'] == 'unavailable')
    union_available = projection['preceding_census_state'] == 'available'
    unknown_union = sorted(set(unknown_current) | set(projection['preceding_only_instances'])) if union_available else None
    pool = candidates(image); proofs = {}; searches = {}; contracts = {}; reuse = {}
    known_key = certify(image, known, [], [], pool['rectangles'], proofs)
    nominal = proofs[known_key]['measurement']
    for scope, unknown in [('current', unknown_current), ('union', unknown_union)]:
        if unknown is None:
            contracts[scope+'_strict'] = blocked_contract('preceding_census_unavailable')
            contracts[scope+'_partial'] = blocked_contract('preceding_census_unavailable')
            continue
        if unknown:
            contracts[scope+'_strict'] = blocked_contract('motion_unavailable_for_census_instances')
        else:
            contracts[scope+'_strict'] = {'state': 'available', 'unknown_count': 0,
                'bounds': [nominal['delta'], nominal['delta']], 'attained': [nominal['delta'], nominal['delta']],
                'proof_keys': [known_key, known_key]}
        if scope == 'union' and unknown == unknown_current:
            found = searches['current']; reuse[scope] = 'current'
        else:
            found = search(image, known, unknown, pool); reuse[scope] = None
        require(found['known'] == nominal, 'Search and checked known matching differ')
        keys, attained = [], []
        for direction in ('lower', 'upper'):
            world = found['worlds'][direction]
            key = certify(image, known, unknown, world['candidate_indices'], pool['rectangles'], proofs)
            require(proofs[key]['measurement'] == world['measurement'], 'Attained matching differs from checked proof')
            keys.append(key); attained.append(world['measurement']['delta'])
        searches[scope] = found
        contracts[scope+'_partial'] = {'state': 'available', 'unknown_count': len(unknown), 'bounds': found['bounds'],
                                      'attained': attained, 'proof_keys': keys}
    return {'image_id': image['id'], 'state': 'complete', 'known_references': known, 'known_proof_key': known_key,
            'original_nominal': original_nominal, 'known_only_measurement': nominal,
            'current_unknown_instances': unknown_current, 'union_unknown_instances': unknown_union,
            'candidate_pool': pool, 'searches': searches, 'search_reuse': reuse, 'proofs': proofs, 'contracts': contracts,
            'projection_changes': changes(projection, original), 'seconds': time.perf_counter()-tick}


def run(area, projection_name='projection-01', run_name='timing-01'):
    area = Path(area).resolve(); tick = time.perf_counter(); started = datetime.now(timezone.utc).isoformat()
    freeze_path = area/'FREEZE.json'; freeze = read(freeze_path)
    require(freeze['contracts'] == list(CONTRACTS) and freeze['actual_temporal_projection_before_freeze'] is False,
            'Frozen temporal protocol differs')
    for row in freeze['bindings']:
        require(file_binding(row['path']) == row, 'Frozen input or implementation changed')
    comparison = Path(freeze['predecessor_comparison']); visible = read(comparison/'inputs/visible.json')
    projection_path = area/'runs'/projection_name/'RESULTS.json'; projected = read(projection_path)
    require(projected['freeze_sha256'] == file_binding(freeze_path)['sha256'], 'Projection belongs to another freeze')
    require(len(visible['images']) == 64 and len(visible['cases']) == 73 and len(projected['image_records']) == 64,
            'Wrong complete allocation')
    projected_records = {entry['image_id']: entry for entry in projected['image_records']}
    require(set(projected_records) == {image['id'] for image in visible['images']}, 'Projection membership differs')
    applicability = {row['image_id']: row for row in read(freeze['applicability'])}
    require(set(applicability) == set(projected_records) and all(image['image_sha256'] == applicability[image['id']]['image_sha256']
            for image in visible['images']), 'Prediction and projection image bytes differ')
    output = area/'runs'/run_name; output.mkdir(parents=True)
    records = {}; failures = {}; bindings = []
    for image in visible['images']:
        iid = image['id']; entry = projected_records[iid]
        require(file_binding(entry['path']) == {key: entry[key] for key in ('path', 'sha256', 'bytes')}, 'Projection bytes changed')
        projection = read(entry['path'])
        source = comparison/'oracle'/(iid+'.json'); original = read(source)['answer']
        baseline_path = comparison/'runs/analysis-01'/(iid+'.json'); baseline = read(baseline_path)['nominal']['nominal']
        try:
            record = analyze_image(image, projection, original, baseline)
        except Exception as exc:
            error = type(exc).__name__ + ': ' + str(exc); failures[iid] = error
            record = {'image_id': iid, 'state': 'analysis_incomplete', 'error': error,
                      'contracts': {name: blocked_contract('analysis_incomplete') for name in CONTRACTS}}
        record['projection_source'] = entry; record['original_reference_source'] = file_binding(source)
        record['original_nominal_source'] = file_binding(baseline_path)
        records[iid] = record; path = output/(iid+'.json'); put(path, record)
        bindings.append({'image_id': iid, **file_binding(path)})
    rows = case_rows(visible['cases'], records)
    require(len(rows) == 292, 'Assigned case/contract row omitted')
    decision_counts = {name: dict(Counter(row['decision'] for row in rows if row['contract'] == name)) for name in CONTRACTS}
    result = {'artifact_id': 'reiyah.reference-timing.results', 'version': '0.1.0', 'status': 'exploratory',
              'started_utc': started, 'finished_utc': datetime.now(timezone.utc).isoformat(), 'seconds': time.perf_counter()-tick,
              'freeze_sha256': file_binding(freeze_path)['sha256'], 'projection_source': file_binding(projection_path),
              'allocated_images': 64, 'allocated_cases': 73, 'allocated_case_contract_rows': 292,
              'contracts': list(CONTRACTS), 'cases': rows, 'image_records': bindings, 'failures': failures,
              'decision_counts': decision_counts, 'human_seconds': None, 'economic_cost': None,
              'model_inference_calls': 0, 'new_image_reads': 0, 'reserved_outcomes_accessed': 0,
              'independent_scientific_replication': False}
    put(output/'RESULTS.json', result)
    print(__import__('json').dumps({'decisions': decision_counts, 'failures': failures, 'seconds': result['seconds']}), flush=True)


if __name__ == '__main__':
    run(*sys.argv[1:])
