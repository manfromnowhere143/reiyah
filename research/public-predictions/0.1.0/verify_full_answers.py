"""Check achieved worlds and query-floor optimality without trusting search.

The source record, admissible edit, conventional matching and native proof
are checked for each retained component. Optimality uses a separate
cardinality-bound calculation, rather than calling the floor solver.
"""
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys
import time

from admission import digest, encoded, require
from compare_math import (FAMILIES, checker, conventional_measure, decision, graph, interval,
                          linked, measure, open_interval, q, validate_canvas, validate_rows, w, wire_interval)
from geometric_worlds import alter


def file_digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def put(path, value):
    with Path(path).open('xb') as handle:
        handle.write(encoded(value))


def verify_floor(images, measurements, family, floor):
    bounds = interval(images, measurements, family); outcome = decision(bounds)
    require(floor['decision'] == outcome and floor['full_bounds'] == wire_interval(bounds), 'FLOOR', 'Full decision differs')
    if outcome in ('unresolved', 'input_blocked'):
        require(floor['minimum_queries'] is None and floor['sufficient_subset'] is None,
                'FLOOR', 'Unresolved or blocked case has no sufficient finite subset')
        return {'minimum_queries': None, 'optimality_checked': False}
    count, chosen = floor['minimum_queries'], floor['sufficient_subset']
    ids = {image['id'] for image in images}
    require(type(count) is int and count >= 0 and len(chosen) == count and len(set(chosen)) == count
            and set(chosen) <= ids, 'FLOOR', 'Invalid sufficient subset')
    subset_bounds = interval(images, {iid: measurements[iid] for iid in chosen}, family)
    require(decision(subset_bounds) == outcome and floor['subset_bounds'] == wire_interval(subset_bounds),
            'FLOOR', 'Reported subset is not sufficient')
    if count == 0:
        return {'minimum_queries': 0, 'optimality_checked': True}
    threshold = sum(open_interval(image)[1] for image in images)
    gains = []
    for image in images:
        radius = open_interval(image)[1]
        if radius == 0:
            continue
        measured = measurements[image['id']]
        center = q(measured['nominal']['delta']); lo, hi = map(q, measured['edit_bounds'])
        if outcome == 'supported':
            gain = radius + (lo if family == 'one_edit_per_image' else center)
            penalty = center - lo if family == 'one_edit_global' else Fraction(0)
        else:
            gain = radius - (hi if family == 'one_edit_per_image' else center)
            penalty = hi - center if family == 'one_edit_global' else Fraction(0)
        gains.append((gain, penalty))
    # Every (count-1)-answer subset has a maximum penalty in this finite list.
    # At that penalty, the largest allowed gains bound its possible progress.
    # If even that bound cannot certify, fewer queries cannot suffice.
    possible_penalties = {Fraction(0)} | {penalty for _, penalty in gains}
    upper_progress = max(sum(sorted((gain for gain, penalty in gains if penalty <= limit), reverse=True)[:count - 1]) - limit
                         for limit in possible_penalties)
    impossible = upper_progress <= threshold if outcome == 'supported' else upper_progress < threshold
    require(impossible, 'FLOOR', 'Claimed minimum is not proved by the cardinality bound')
    return {'minimum_queries': count, 'optimality_checked': True, 'one_fewer_queries_progress_upper': w(upper_progress),
            'required_threshold': w(threshold), 'strict_progress_required': outcome == 'supported'}


def verify_component(image, references, record):
    nominal = measure(image, references, 'one_edit_per_image', 'conventional')
    for key in ('nominal', 'edit_bounds', 'deletion_bases'):
        require(record['nominal'][key] == nominal[key], 'NOMINAL', 'Full-answer measurement differs')
    checked = {'nominal': q(nominal['nominal']['delta']), 'native_proofs': 0}
    if record['search_state'] != 'complete':
        require(record['search_state'] == 'incomplete' and record['error'], 'SEARCH', 'Missing search failure state')
        return checked
    search = record['search']
    require(search['all_rectangles_exhaustively_searched'] is False and search['axis_cells_exhaustively_searched'] is True,
            'SEARCH', 'Finite search scope changed')
    for direction in ('lower', 'upper'):
        witness = search['witnesses'][direction]
        world = alter(references, witness['edit']); validate_rows(world); validate_canvas(world, image)
        require(world == witness['altered_references'], 'WORLD', 'Retained world differs from its stated edit')
        measured = conventional_measure(image, world)
        require(measured == witness['measurement'], 'MATCHING', 'Adverse geometric matching differs')
        compiled = graph(image, world); proof = witness['native_proof']
        require(proof['graph_sha256'] == digest(compiled), 'PROOF', 'Adverse graph binding differs')
        checker.check(compiled, proof['payload']); checked['native_proofs'] += 1
        require(proof['payload']['result']['bounds']['lower'] == measured['delta']
                and proof['payload']['result']['bounds']['upper'] == measured['delta'], 'PROOF', 'Adverse checked value differs')
        delta = q(measured['delta']); checked[direction] = delta
        require(q(nominal['edit_bounds'][0]) <= delta <= q(nominal['edit_bounds'][1]), 'BOUND', 'Witness violates universal edit bound')
        require(delta <= checked['nominal'] if direction == 'lower' else delta >= checked['nominal'],
                'WORLD', 'Retained extremum is worse than its own unedited alternative')
    return checked


def verify_composition(images, checked, family, world):
    ids = [image['id'] for image in images]
    require(world['complete_case_membership'] == ids and world['remaining_images_use_nominal_reference'] is True,
            'WORLD', 'Composed world drops or changes case members')
    edits = world['edited_images']; edited = {row['image_id']: row for row in edits}
    require(len(edited) == len(edits) and set(edited) <= set(ids), 'WORLD', 'Repeated or out-of-case edited image')
    require(family == 'one_edit_per_image' or (family == 'one_edit_global' and len(edits) <= 1),
            'WORLD', 'Composed world exceeds its edit budget')
    total = Fraction(0)
    for iid in ids:
        component = checked[iid]; value = component['nominal']
        if iid in edited:
            edit = edited[iid]; direction = edit['witness']
            require(direction == world['direction'] and direction in component, 'WORLD', 'Unverified component substituted')
            value = component[direction]
            require(q(edit['delta_change']) == value - component['nominal'], 'WORLD', 'Component change differs')
        total += value
    require(world['delta'] == w(total / len(ids)) and world['decision'] == ('supported' if total > 0 else 'excluded'),
            'WORLD', 'Composed decision differs from its checked component worlds')
    return total / len(ids)


def verify_edit_threshold(images, records, checked, result):
    ids = [image['id'] for image in images]; nominal = sum(checked[iid]['nominal'] for iid in ids)
    require(result['nominal_total_delta'] == w(nominal), 'SENSITIVITY', 'Nominal total differs')
    if nominal <= 0:
        require(result['lower_bound'] == result['upper_bound'] == 0 and result['exact'] is True,
                'SENSITIVITY', 'Nominal exclusion needs no edit')
        return {'exact': True, 'minimum_affected_images': 0}
    damage = sorted((checked[iid]['nominal'] - q(records[iid]['nominal']['edit_bounds'][0]) for iid in ids), reverse=True)
    lower, upper = result['lower_bound'], result['upper_bound']
    if lower is None:
        require(sum(damage) < nominal and upper is None and result['exact'] is False,
                'SENSITIVITY', 'Claimed robustness exceeds the sound damage bound')
        return {'exact': False, 'exclusion_impossible_under_supplied_bounds': True}
    require(type(lower) is int and 1 <= lower <= len(ids), 'SENSITIVITY', 'Invalid lower edit count')
    require(sum(damage[:lower - 1]) < nominal <= sum(damage[:lower]),
            'SENSITIVITY', 'Universal minimum-edit lower bound is not established')
    if upper is not None:
        edits = result['witness']; chosen = {row['image_id']: row for row in edits}
        require(type(upper) is int and len(edits) == len(chosen) == upper and set(chosen) <= set(ids),
                'SENSITIVITY', 'Reversal witness changes an invalid set of images')
        total = nominal
        for iid, edit in chosen.items():
            require(edit['witness'] == 'lower' and 'lower' in checked[iid], 'SENSITIVITY', 'Missing checked adverse component')
            change = checked[iid]['nominal'] - checked[iid]['lower']
            require(change > 0 and edit['downward_change'] == w(change), 'SENSITIVITY', 'Adverse contribution differs')
            total -= change
        require(total <= 0 and result['witness_total_delta'] == w(total) and lower <= upper,
                'SENSITIVITY', 'Retained witness does not exclude strict improvement')
    require(result['exact'] == (upper is not None and lower == upper), 'SENSITIVITY', 'A bound gap is not an exact threshold')
    return {'exact': result['exact'], 'minimum_affected_images': lower if result['exact'] else None,
            'maximum_damage_with_one_fewer_images': w(sum(damage[:lower - 1])),
            'nominal_total_delta': w(nominal)}


def run(area, run_name='analysis-01'):
    area = Path(area).resolve(); output = area / 'runs' / run_name
    started, tick = datetime.now(timezone.utc).isoformat(), time.perf_counter()
    freeze = json.loads((area / 'ANALYSIS_FREEZE.json').read_text())
    for binding in freeze['bindings']:
        require(file_digest(binding['path']) == binding['sha256'], 'FREEZE', 'Analysis input changed')
    result_path = output / 'RESULTS.json'; result = json.loads(result_path.read_text())
    require(result['analysis_freeze_sha256'] == file_digest(area / 'ANALYSIS_FREEZE.json'), 'FREEZE', 'Analysis freeze differs')
    visible = json.loads((area / 'inputs/visible.json').read_text()); images = {image['id']: image for image in visible['images']}
    records, checked, totals = {}, {}, Counter()
    require(len(result['image_records']) == len(images) == 64, 'ALLOCATION', 'Analysis image allocation differs')
    for entry in result['image_records']:
        iid = entry['image_id']
        require(iid in images and iid not in records and entry['path'] == iid + '.json', 'ALLOCATION', 'Unknown/repeated image record')
        require(file_digest(output / entry['path']) == entry['sha256'], 'BINDING', 'Image analysis bytes changed')
        record = json.loads((output / entry['path']).read_text()); records[iid] = record
        require(record['image_id'] == iid, 'BINDING', 'Record image differs')
        if linked(images[iid]):
            oracle = json.loads((area / 'oracle' / (iid + '.json')).read_text())
            require(oracle['subject_sha256'] == digest(images[iid]), 'SOURCE', 'Analysis oracle subject differs')
            checked[iid] = verify_component(images[iid], oracle['answer'], record)
            totals['native_proofs'] += checked[iid]['native_proofs']
    require(set(records) == set(images), 'ALLOCATION', 'Assigned image omitted')
    measurements = {iid: record['nominal'] for iid, record in records.items() if 'nominal' in record}
    cases = {case['id']: case for case in visible['cases']}; seen, floors = set(), []
    for row in result['cases']:
        key = (row['family'], row['case_id'])
        require(key not in seen and key[0] in FAMILIES and key[1] in cases, 'ALLOCATION', 'Unknown/repeated analysis case')
        seen.add(key); members = [images[iid] for iid in cases[key[1]]['images']]
        full = interval(members, measurements, row['family'])
        require(row['bounds'] == wire_interval(full) and row['decision'] == decision(full), 'BOUND', 'Full case decision differs')
        floors.append({'case_id': row['case_id'], 'family': row['family'],
                       **verify_floor(members, measurements, row['family'], row['certificate_floor'])})
        if row['decision'] != 'input_blocked':
            nominal = sum(checked[image['id']]['nominal'] for image in members) / len(members)
            require(row['nominal_delta'] == w(nominal) and row['nominal_decision'] == ('supported' if nominal > 0 else 'excluded'),
                    'BOUND', 'Full nominal decision differs')
            if row['family'] != 'exact_projection':
                outcomes = set()
                for direction in ('lower', 'upper'):
                    world = row['worlds'][direction]
                    require(world['direction'] == direction, 'WORLD', 'World direction differs')
                    delta = verify_composition(members, checked, row['family'], world)
                    require(full[0] <= delta <= full[1], 'BOUND', 'World falls outside its universal case bound')
                    outcomes.add('supported' if delta > 0 else 'excluded'); totals['composed_worlds'] += 1
                opposite = outcomes == {'supported', 'excluded'}
                require(row['opposite_decisions_witnessed'] == opposite, 'WORLD', 'Opposite-decision assertion differs')
                if row['decision'] == 'unresolved' and opposite:
                    require(row['unresolved_kind'] == 'admitted_opposite_decision_worlds', 'WORLD', 'Information limit relabeled')
                    totals['unresolved_pairs_with_opposite_worlds'] += 1
    require(seen == {(family, case) for family in FAMILIES for case in cases}, 'ALLOCATION', 'Assigned analysis row omitted')
    primary = next(case for case in cases.values() if case['group'] == 'primary')
    sensitivity = verify_edit_threshold([images[iid] for iid in primary['images']], records, checked,
                                        result['primary_edit_sensitivity'])
    exact_extrema = {direction: sum(record['search_state'] == 'complete' and
        checked[iid][direction] == q(record['nominal']['edit_bounds'][0 if direction == 'lower' else 1])
        for iid, record in records.items()) for direction in ('lower', 'upper')}
    report = {'artifact_id': 'reiyah.public-predictions.full-answer-verification', 'version': '0.1.0',
        'started_utc': started, 'finished_utc': datetime.now(timezone.utc).isoformat(), 'seconds': time.perf_counter() - tick,
        'results_sha256': file_digest(result_path), 'verifier_sha256': file_digest(__file__),
        'images': len(records), 'case_family_rows': len(seen), 'totals': dict(totals), 'floors': floors,
        'achieved_universal_extrema_images': exact_extrema, 'primary_edit_sensitivity_check': sensitivity,
        'all_assigned_rows_verified': True, 'independent_scientific_replication': False}
    put(output / 'VERIFICATION.json', report)
    print(json.dumps({'images': len(records), 'rows': len(seen), 'totals': dict(totals),
                      'extrema': exact_extrema, 'sensitivity': sensitivity, 'seconds': report['seconds']}), flush=True)


if __name__ == '__main__':
    run(*sys.argv[1:])
