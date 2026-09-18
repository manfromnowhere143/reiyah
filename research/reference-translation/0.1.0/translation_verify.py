"""Check partition completeness, attained worlds and critical-radius claims."""
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
import sys
import time

from axis_certificate import checked_radius_membership, exact_iou, expected_cells, maximum_matching
from translation_search import RADII, digest, q, require, subject, validate_canvas, validate_image, validate_rows, w
from compare_math import graph
from tools.perception_revision import checker
from translation_run import file_digest, put, read


def geometry(row):
    return tuple(q(value) for value in row['xyxy'])


def independent_measure(image, references):
    ranks = []
    for role in ('output_a', 'output_b'):
        adjacency = {d['id']: {r['id'] for r in references if exact_iou(geometry(d), geometry(r)) >= Fraction(1, 2)}
                     for d in image[role]['value']}
        ranks.append(maximum_matching(adjacency))
    return {'ranks': ranks, 'delta': w(Fraction(len(image['output_a']['value']) - len(image['output_b']['value'])
                                                + 2 * (ranks[1] - ranks[0])))}


def check_partition(image, references, record):
    validate_image(image); validate_rows(references); validate_canvas(references, image)
    require(record['image_id'] == image['id'] and record['subject_sha256'] == subject(image)
            and record['reference_sha256'] == digest(references), 'BINDING', 'Wrong translation subject or source')
    require(record['exhaustive_for_declared_axis_family'] is True, 'COVERAGE', 'Incomplete search')
    nominal = independent_measure(image, references)
    require(record['nominal'] == nominal, 'MATCHING', 'Nominal matching differs')
    detections = {row['id']: row for role in ('output_a', 'output_b') for row in image[role]['value']}
    detection_ids = sorted(detections); boxes = [geometry(detections[did]) for did in detection_ids]
    expected = {}
    for index, reference in enumerate(references):
        for axis in (0, 1):
            cells, _ = expected_cells(geometry(reference), boxes, axis, image['width'], image['height'])
            for left, right in cells:
                expected[index, axis, left, right] = reference['id']
    require(len(record['states']) == len(expected) == record['cells'], 'COVERAGE', 'Cell count differs')
    require(record['axes'] == 2 * len(references), 'COVERAGE', 'Missing translation axis')
    seen = set(); states = {}; matching = {}
    for state in record['states']:
        left, right = map(q, state['cell']); index, axis = state['reference_index'], state['axis']
        key = index, axis, left, right
        require(key in expected and key not in seen and state['id'] not in states,
                'COVERAGE', 'Unknown, repeated or missing cell')
        require(state['reference_id'] == expected[key] and state['point'] == (left == right),
                'COVERAGE', 'Cell/reference identity differs')
        seen.add(key); base = geometry(references[index]); center = base[axis]
        pos = (left + right) / 2
        moved = tuple(value + pos - center if dimension in (axis, axis + 2) else value
                      for dimension, value in enumerate(base))
        neighbors = tuple(did for did in detection_ids if exact_iou(boxes[detection_ids.index(did)], moved) >= Fraction(1, 2))
        require(state['neighbors'] == list(neighbors), 'GEOMETRY', 'Cell neighborhood differs')
        match_key = index, neighbors
        if match_key not in matching:
            world = [row if i != index else {**row, 'xyxy': [w(value) for value in moved]}
                     for i, row in enumerate(references)]
            matching[match_key] = independent_measure(image, world)
        require(state['measurement'] == matching[match_key], 'MATCHING', 'Cell maximum matching differs')
        if left == right:
            distance, attained = abs(left - center), True
        elif left < center < right:
            distance, attained = Fraction(0), True
        else:
            distance, attained = min(abs(left - center), abs(right - center)), False
        require(q(state['radius_infimum']) == distance and state['infimum_attained'] is attained,
                'BOUNDARY', 'Cell activation infimum or attainment differs')
        states[state['id']] = {'left': left, 'right': right, 'center': center, 'distance': distance,
                               'attained': attained, 'delta': q(matching[match_key]['delta']),
                               'reference_index': index, 'axis': axis}
    require(seen == set(expected) and len(matching) == record['matching_states'], 'COVERAGE', 'Partition not exhausted')
    return {'states': states, 'nominal': q(nominal['delta']), 'native_checked': set(), 'native_payloads': {}}


def extrema(verified, radius, side='at'):
    values = [verified['nominal']]
    for state in verified['states'].values():
        eligible = (state['distance'] < radius if side == 'before' else
                    state['distance'] <= radius if side == 'after' else
                    checked_radius_membership(state['left'], state['right'], state['center'], radius))
        if eligible:
            values.append(state['delta'])
    return min(values), max(values)


def check_world(image, references, verified, witness, radius, proof_cache):
    state_id = witness['state_id']; edit = witness['edit']
    if state_id is None:
        require(edit == {'operation': 'none'}, 'EDIT', 'No-edit world changed')
        world = references
    else:
        require(state_id in verified['states'], 'EDIT', 'Unknown translation cell')
        state = verified['states'][state_id]; original = references[state['reference_index']]
        require(set(edit) == {'operation', 'source_reference_id', 'source_reference_sha256', 'axis',
                              'position', 'distance', 'translated_reference'}, 'EDIT', 'Extra or missing edit field')
        require(edit['operation'] == 'translation' and edit['source_reference_id'] == original['id']
                and edit['source_reference_sha256'] == original['record_sha256'] and edit['axis'] == state['axis'],
                'EDIT', 'Wrong reference or translation axis')
        pos = q(edit['position']); distance = abs(pos - state['center'])
        require(distance <= radius and q(edit['distance']) == distance, 'RADIUS', 'Translation exceeds radius')
        require((pos == state['left'] if state['left'] == state['right'] else state['left'] < pos < state['right']),
                'BOUNDARY', 'Position outside claimed cell')
        base = geometry(original)
        expected = tuple(value + pos - state['center'] if dimension in (state['axis'], state['axis'] + 2) else value
                         for dimension, value in enumerate(base))
        translated = edit['translated_reference']
        require(geometry(translated) == expected, 'EDIT', 'Shape, orthogonal coordinate or position changed')
        require(translated['id'] not in {row['id'] for row in references}, 'IDENTITY', 'Translated reference identity collides')
        world = [row for index, row in enumerate(references) if index != state['reference_index']] + [translated]
        require(len(world) == len(references), 'EDIT', 'Reference cardinality changed')
    validate_rows(world); validate_canvas(world, image)
    key = digest({'subject_sha256': subject(image), 'references': world})
    require(witness['proof_key'] == key and key in proof_cache, 'PROOF', 'Wrong current-world proof binding')
    proof = proof_cache[key]
    require(proof['subject_sha256'] == subject(image) and proof['reference_sha256'] == digest(world),
            'PROOF', 'Wrong proof subject or reference')
    measured = independent_measure(image, world)
    require(proof['measurement'] == measured and q(witness['delta']) == q(measured['delta']),
            'MATCHING', 'Claimed attained value differs')
    native = graph(image, world)
    require(proof['proof']['graph_sha256'] == digest(native), 'PROOF', 'Wrong native graph')
    if key in verified['native_checked']:
        require(verified['native_payloads'][key] == digest(proof), 'PROOF', 'Previously checked proof bytes changed')
    else:
        checker.check(native, proof['proof']['payload']); verified['native_checked'].add(key)
        verified['native_payloads'][key] = digest(proof)
    return q(measured['delta'])


def check_radius(image, references, verified, witnesses, radius, proofs):
    expected = extrema(verified, radius)
    actual = tuple(check_world(image, references, verified, witnesses[direction], radius, proofs)
                   for direction in ('lower', 'upper'))
    require(actual == expected, 'EXTREMA', 'Claimed witness does not attain exact family extrema')
    return actual


def check_affected(nominal, downward, report):
    count = report['minimum_images']
    ordered = sorted(downward.values(), reverse=True)
    if count is None:
        require(nominal > sum(ordered), 'SENSITIVITY', 'An excluding world was omitted')
        return
    require(type(count) is int and count >= 0 and type(report['image_ids']) is list
            and len(report['image_ids']) == count and len(set(report['image_ids'])) == count
            and all(iid in downward for iid in report['image_ids']), 'SENSITIVITY', 'Invalid affected-image subset')
    damage = sum((downward[iid] for iid in report['image_ids']), Fraction(0))
    require(q(report['witness_total']) == nominal - damage <= 0, 'SENSITIVITY', 'Subset does not exclude improvement')
    if count:
        require(sum(ordered[:count - 1]) < nominal, 'SENSITIVITY', 'Claimed image count is not minimum')
        require(q(report['one_fewer_maximum_damage']) == sum(ordered[:count - 1]), 'SENSITIVITY', 'Incorrect lower-bound damage')
    else:
        require(nominal <= 0, 'SENSITIVITY', 'Positive nominal value needs an actual edit')


def check_critical(verified, critical):
    limit = critical['radius_infimum']
    if limit is None:
        lower = sum((extrema(row, Fraction(64))[0] for row in verified.values()), Fraction(0))
        require(lower > 0 and q(critical['lower_total_at_maximum']) == lower,
                'CRITICAL', 'No-reversal claim is false')
        return
    radius = q(limit); require(0 <= radius <= 64, 'CRITICAL', 'Critical radius outside declared domain')
    before = sum((extrema(row, radius, 'before')[0] for row in verified.values()), Fraction(0))
    at = sum((extrema(row, radius)[0] for row in verified.values()), Fraction(0))
    require(q(critical['lower_total_at_infimum']) == at, 'CRITICAL', 'Critical endpoint differs')
    nominal = sum((row['nominal'] for row in verified.values()), Fraction(0))
    if nominal <= 0:
        require(radius == 0 and critical['attained'] is True, 'CRITICAL', 'Nominal exclusion has minimum radius zero')
        return
    require(before > 0 and q(critical['lower_total_before_infimum']) == before,
            'CRITICAL', 'An earlier excluding world exists')
    if critical['attained'] is True:
        require(at <= 0 and q(critical['witness_radius']) == radius, 'CRITICAL', 'Endpoint world is not attained')
    else:
        require(critical['attained'] is False and radius < 64 and at > 0, 'CRITICAL', 'Infimum misreported as unattained')
        after = sum((extrema(row, radius, 'after')[0] for row in verified.values()), Fraction(0))
        require(after <= 0 and q(critical['right_limit_lower_total']) == after, 'CRITICAL', 'No immediate adverse world')
        witness_radius = q(critical['witness_radius'])
        require(radius < witness_radius <= 64 and sum(extrema(row, witness_radius)[0] for row in verified.values()) <= 0,
                'CRITICAL', 'Claimed later radius has no excluding world')


def run(area, run_name='translation-01'):
    area = Path(area).resolve(); started = datetime.now(timezone.utc).isoformat(); tick = time.perf_counter()
    freeze = read(area / 'FREEZE.json')
    for binding in freeze['bindings']:
        require(file_digest(binding['path']) == binding['sha256'], 'FREEZE', 'Frozen source changed')
    comparison = Path(freeze['predecessor_comparison']); visible = read(comparison / 'inputs/visible.json')
    output = area / 'runs' / run_name; results = read(output / 'RESULTS.json')
    require(not results['failures'], 'INCOMPLETE', 'Cannot certify an incomplete analysis as complete')
    require(results['freeze_sha256'] == file_digest(area / 'FREEZE.json') and results['radii'] == list(RADII),
            'FREEZE', 'Result context differs')
    images = {image['id']: image for image in visible['images']}; records = {}; verified = {}; references = {}
    totals = Counter(); seen = set()
    for entry in results['image_records']:
        iid = entry['image_id']; require(iid in images and iid not in seen, 'ALLOCATION', 'Unknown or duplicate image')
        require(entry['path'] == iid + '.json' and file_digest(output / entry['path']) == entry['sha256'], 'BINDING', 'Image bytes differ')
        seen.add(iid); record = read(output / entry['path']); records[iid] = record
        source = comparison / 'oracle' / (iid + '.json'); refs = read(source)['answer']; references[iid] = refs
        require(record['oracle_file_sha256'] == file_digest(source), 'BINDING', 'Wrong oracle source')
        checked = check_partition(images[iid], refs, record); verified[iid] = checked
        require(set(record['radii']) == {str(radius) for radius in RADII}, 'ALLOCATION', 'Missing image/radius row')
        for radius in RADII:
            check_radius(images[iid], refs, checked, record['radii'][str(radius)], Fraction(radius), record['proofs'])
            totals['image_radius_rows'] += 1
        require(checked['native_checked'] == set(record['proofs']), 'PROOF', 'Unverified extra proof')
        totals['native_proofs'] += len(checked['native_checked'])
        for key in ['axes', 'cells', 'matching_states']:
            totals[key] += record[key]
    require(seen == set(images) and len(images) == 64, 'ALLOCATION', 'Missing image')
    cases = {case['id']: case for case in visible['cases']}; assigned = set()
    for row in results['cases']:
        key = row['case_id'], row['radius']
        require(key[0] in cases and key[1] in RADII and key not in assigned, 'ALLOCATION', 'Unknown or repeated case/radius row')
        assigned.add(key); members = cases[key[0]]['images']; radius = Fraction(key[1])
        bounds = [sum((extrema(verified[iid], radius)[i] for iid in members), Fraction(0)) / len(members) for i in (0, 1)]
        nominal = sum((verified[iid]['nominal'] for iid in members), Fraction(0))
        decision = 'supported' if bounds[0] > 0 else 'excluded' if bounds[1] <= 0 else 'unresolved'
        require(row['state'] == 'complete' and row['analysis_failed_images'] == [] and row['bounds'] == list(map(w, bounds))
                and row['decision'] == decision and q(row['nominal_delta']) == nominal / len(members), 'CASE', 'Case interval differs')
        require(row['allocated_images'] == len(members) and row['group'] == cases[key[0]]['group'], 'CASE', 'Case membership differs')
        for direction in ('lower', 'upper'):
            expected = [{'image_id': iid, 'proof_key': records[iid]['radii'][str(key[1])][direction]['proof_key']} for iid in members]
            require(row['worlds'][direction] == expected, 'CASE', 'Composed world membership differs')
            totals['composed_worlds'] += 1
        downward = {iid: verified[iid]['nominal'] - extrema(verified[iid], radius)[0] for iid in members}
        check_affected(nominal, downward, row['minimum_affected'])
    require(assigned == {(case, radius) for case in cases for radius in RADII}, 'ALLOCATION', 'Missing case/radius row')
    critical = results['primary_critical_radius']; check_critical(verified, critical)
    critical_seen = set(); downward = {}
    for entry in results['critical_image_records']:
        iid = entry['image_id']; require(iid in images and iid not in critical_seen, 'ALLOCATION', 'Critical image duplicated')
        require(entry['path'] == 'critical-' + iid + '.json' and file_digest(output / entry['path']) == entry['sha256'], 'BINDING', 'Critical bytes differ')
        critical_seen.add(iid); row = read(output / entry['path'])
        require(row['infimum'] == critical['radius_infimum'] and row['witness_radius'] == critical['witness_radius'],
                'CRITICAL', 'Critical world radius differs')
        check = {**verified[iid], 'native_checked': set(), 'native_payloads': {}}
        check_radius(images[iid], references[iid], check, row['at_infimum'], q(row['infimum']), row['proofs'])
        witness = check_radius(images[iid], references[iid], check, row['at_witness_radius'], q(row['witness_radius']), row['proofs'])
        require(check['native_checked'] == set(row['proofs']), 'PROOF', 'Unverified critical proof')
        totals['native_proofs'] += len(check['native_checked'])
        downward[iid] = verified[iid]['nominal'] - witness[0]
    require(critical_seen == (set(images) if critical['radius_infimum'] is not None else set()), 'ALLOCATION', 'Critical world incomplete')
    if critical_seen:
        check_affected(sum(row['nominal'] for row in verified.values()), downward, critical['minimum_affected_at_witness_radius'])
    require({key: totals[key] for key in results['totals']} == results['totals'], 'ACCOUNTING', 'Search totals differ')
    report = {'artifact_id': 'reiyah.reference-translation.verification', 'version': '0.1.0',
              'started_utc': started, 'finished_utc': datetime.now(timezone.utc).isoformat(), 'seconds': time.perf_counter() - tick,
              'results_sha256': file_digest(output / 'RESULTS.json'), 'verifier_sha256': file_digest(__file__),
              'all_assigned_rows_verified': True, 'images': len(images), 'case_radius_rows': len(assigned),
              'totals': dict(totals), 'critical_radius_verified': True, 'independent_scientific_replication': False}
    put(output / 'VERIFICATION.json', report)
    print(__import__('json').dumps(report), flush=True)


if __name__ == '__main__':
    run(*sys.argv[1:])
