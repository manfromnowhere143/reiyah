"""Verify all assigned planar results and every justified bracket update."""
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
import sys
import time

from planar_certificate import check_basis, check_search, q, require, w
from planar_run import file_digest, put, read

RADII = (0, 1, 2, 4, 8, 16, 32, 64)


def key_for(radius):
    radius = Fraction(radius)
    return 'r' + str(radius.numerator) + '_' + str(radius.denominator)


def check_case(row, case, records, radius):
    members = case['images']; size = len(members)
    require(row['case_id'] == case['id'] and row['group'] == case['group']
            and q(row['radius']) == radius and row['allocated_images'] == size, 'CASE', 'Wrong case identity')
    failed = [iid for iid in members if records[iid]['state'] == 'analysis_incomplete']
    require(row['analysis_failed_images'] == failed, 'CASE', 'Failure membership changed')
    if failed:
        require(row['state'] == 'analysis_incomplete'
                and all(row[key] is None for key in ('universal_bounds', 'attained_bounds', 'nominal_delta',
                    'exact_extrema', 'decision', 'unresolved_reason', 'worlds')), 'INCOMPLETE', 'Failure became an outcome')
        return 'analysis_incomplete'
    lower = upper = found_lower = found_upper = nominal = Fraction(0)
    for iid in members:
        value = records[iid]
        lower += q(value['universal_bounds'][0]); upper += q(value['universal_bounds'][1])
        found_lower += q(value['attained_bounds'][0]); found_upper += q(value['attained_bounds'][1])
        nominal += value['nominal_delta']
    expected_decision = 'supported' if lower > 0 else 'excluded' if upper <= 0 else 'unresolved'
    expected_reason = None
    if expected_decision == 'unresolved':
        expected_reason = 'opposite_worlds' if found_lower <= 0 < found_upper else 'bound_gap'
    require(row['state'] == 'complete' and row['universal_bounds'] == [w(lower / size), w(upper / size)]
            and row['attained_bounds'] == [w(found_lower / size), w(found_upper / size)]
            and q(row['nominal_delta']) == nominal / size and row['decision'] == expected_decision
            and row['unresolved_reason'] == expected_reason
            and row['exact_extrema'] is (lower == found_lower and upper == found_upper), 'CASE', 'Case outcome differs')
    require(set(row['worlds']) == {'lower', 'upper'}, 'CASE', 'Missing composed world')
    for direction in ('lower', 'upper'):
        expected = [{'image_id': iid, 'proof_key': records[iid]['witnesses'][direction]['proof_key']} for iid in members]
        require(row['worlds'][direction] == expected, 'CASE', 'Composed world membership differs')
    return expected_decision


def check_bracket(report, primary, batches):
    lower, upper = Fraction(0), Fraction(8)
    require(report['initial'] == [w(lower), w(upper)] and report['maximum_steps'] == 8
            and len(report['steps']) <= 8 and len(report['initial_rows']) == 2, 'BRACKET', 'Initial bracket or cap differs')
    for radius, row in zip((lower, upper), report['initial_rows']):
        check_case(row, primary, batches[key_for(radius)], radius)
    first, second = report['initial_rows']
    if any(row['state'] != 'complete' for row in (first, second)):
        require(report['state'] == 'analysis_incomplete' and report['steps'] == [], 'BRACKET', 'Incomplete initial bracket continued')
    elif q(first['universal_bounds'][0]) <= 0 or q(second['attained_bounds'][0]) > 0:
        require(report['state'] == 'initial_bracket_not_established' and report['steps'] == [],
                'BRACKET', 'Unsupported initial bracket continued')
    else:
        known = {key_for(radius) for radius in RADII}; stopped = False
        require(bool(report['steps']), 'BRACKET', 'Established bracket not pursued')
        for index, step in enumerate(report['steps']):
            midpoint = (lower + upper) / 2; key = key_for(midpoint)
            require(not stopped and step['step'] == index and step['before'] == [w(lower), w(upper)]
                    and q(step['midpoint']) == midpoint and step['reused_radius'] is (key in known),
                    'BRACKET', 'Bisection order, midpoint or reuse differs')
            require(key in batches, 'BRACKET', 'Missing midpoint evidence')
            check_case(step['row'], primary, batches[key], midpoint); row = step['row']; known.add(key)
            if row['state'] == 'analysis_incomplete':
                expected = 'analysis_incomplete'; stopped = True
            elif q(row['universal_bounds'][0]) > 0:
                expected = 'supported'; lower = midpoint
            elif q(row['attained_bounds'][0]) <= 0:
                expected = 'attained_excluding_world'; upper = midpoint
            else:
                expected = 'bound_gap'; stopped = True
            require(step['outcome'] == expected and step['after'] == [w(lower), w(upper)],
                    'BRACKET', 'Unsupported bracket update')
            if stopped:
                require(report['state'] == expected and index == len(report['steps']) - 1, 'BRACKET', 'Search continued across a gap')
        if not stopped:
            require(len(report['steps']) == 8 and report['state'] == 'step_limit', 'BRACKET', 'Premature step-limit claim')
    require(report['final'] == [w(lower), w(upper)], 'BRACKET', 'Final bracket differs')
    return lower, upper


def run(area, run_name='planar-01'):
    area = Path(area).resolve(); tick = time.perf_counter(); started = datetime.now(timezone.utc).isoformat()
    freeze_path = area / 'FREEZE.json'; freeze = read(freeze_path)
    for binding in freeze['bindings']:
        require(file_digest(binding['path']) == binding['sha256'], 'FREEZE', 'Frozen bytes changed')
    comparison = Path(freeze['predecessor_comparison']); axes = Path(freeze['axis_run'])
    visible = read(comparison / 'inputs/visible.json'); images = {row['id']: row for row in visible['images']}
    cases = {row['id']: row for row in visible['cases']}; primary = [row for row in visible['cases'] if row['group'] == 'primary']
    require(len(images) == len(visible['images']) == 64 and len(cases) == len(visible['cases']) == 73
            and len(primary) == 1 and primary[0]['images'] == list(images), 'ALLOCATION', 'Frozen population differs')
    output = area / 'runs' / run_name; results = read(output / 'RESULTS.json')
    require(results['freeze_sha256'] == file_digest(freeze_path) and results['radii'] == list(RADII)
            and results['allocated_images'] == 64 and results['allocated_cases'] == 73
            and results['allocated_case_radius_rows'] == 584, 'FREEZE', 'Result allocation differs')
    checked, references, failed_preparation = {}, {}, set(); seen = set(); totals = Counter()
    for entry in results['preparation_entries']:
        iid = entry['image_id']; require(iid in images and iid not in seen, 'ALLOCATION', 'Repeated or unknown preparation')
        seen.add(iid); require(entry['path'] == 'basis-' + iid + '.json'
            and file_digest(output / entry['path']) == entry['sha256'], 'BINDING', 'Preparation bytes changed')
        record = read(output / entry['path']); require(record['image_id'] == iid, 'BINDING', 'Preparation image changed')
        references[iid] = read(comparison / 'oracle' / (iid + '.json'))['answer']
        if record['state'] == 'analysis_incomplete':
            require(type(record['error']) is str and record['error'], 'INCOMPLETE', 'Failure requires a reason')
            failed_preparation.add(iid); continue
        require(record['state'] == 'complete' and record['oracle_sha256'] == file_digest(comparison / 'oracle' / (iid + '.json'))
                and record['axis_record_sha256'] == file_digest(axes / (iid + '.json')), 'BINDING', 'Wrong source input')
        checked[iid] = check_basis(images[iid], references[iid], record['basis']); totals['prepared_images'] += 1
    require(seen == set(images), 'ALLOCATION', 'Missing prepared image')
    expected_order = [key_for(radius) for radius in RADII]
    for step in results['primary_bracket']['steps']:
        key = key_for(q(step['midpoint']))
        if key not in expected_order:
            expected_order.append(key)
    require(results['batch_order'] == expected_order and set(results['batches']) == set(expected_order),
            'ALLOCATION', 'Extra or omitted radius batch')
    batches = {}; seen_proofs = {iid: set() for iid in images}; cost_proofs = set()
    for key in expected_order:
        batch = results['batches'][key]; radius = q(batch['radius'])
        require(key_for(radius) == key, 'RADIUS', 'Batch key differs'); records = {}; row_seen = set()
        for entry in batch['records']:
            iid = entry['image_id']; require(iid in images and iid not in row_seen, 'ALLOCATION', 'Repeated or unknown radius member')
            row_seen.add(iid); require(q(entry['radius']) == radius and entry['path'] == key + '-' + iid + '.json'
                and file_digest(output / entry['path']) == entry['sha256'], 'BINDING', 'Wrong radius record bytes')
            record = read(output / entry['path']); records[iid] = record; totals['image_radius_rows'] += 1
            require(record['image_id'] == iid and q(record['radius']) == radius, 'BINDING', 'Radius record context differs')
            if record['state'] == 'analysis_incomplete':
                require(type(record['error']) is str and record['error'], 'INCOMPLETE', 'Failure requires a reason')
                continue
            require(iid not in failed_preparation, 'INCOMPLETE', 'Failed preparation became an outcome')
            require(record['limits'] == {'maximum_regions': 2048, 'maximum_depth': 24}, 'LIMIT', 'Actual run limit differs')
            verified = check_search(images[iid], references[iid], checked[iid], record, radius)
            totals['complete_image_radius_rows'] += 1; totals['regions'] += verified['regions']
            totals['bound_gap_image_radius_rows'] += int(not verified['exact'])
            totals['unresolved_regions'] += verified['unresolved_regions']
            # Producer always evaluates lower, then upper; shared worlds have one paid proof.
            expected_new, expected_reused = [], []
            for direction in ('lower', 'upper'):
                proof_key = record['witnesses'][direction]['proof_key']
                if proof_key in seen_proofs[iid]:
                    expected_reused.append(proof_key)
                else:
                    expected_new.append(proof_key); seen_proofs[iid].add(proof_key); cost_proofs.add((iid, proof_key))
            require(record['new_native_proofs'] == expected_new and record['reused_native_proofs'] == expected_reused,
                    'ACCOUNTING', 'Repeated proof charged as new or new proof omitted')
        require(row_seen == set(images), 'ALLOCATION', 'Missing image/radius record'); batches[key] = records
    totals['native_proofs'] = len(cost_proofs); assigned = set(); decisions = Counter()
    for row in results['cases']:
        cid, radius = row['case_id'], q(row['radius']); key = cid, radius
        require(cid in cases and radius in RADII and key not in assigned, 'ALLOCATION', 'Unknown or repeated assigned row')
        assigned.add(key); outcome = check_case(row, cases[cid], batches[key_for(radius)], radius); decisions[outcome] += 1
        if outcome == 'unresolved':
            decisions[row['unresolved_reason']] += 1
        if outcome != 'analysis_incomplete':
            totals['composed_worlds'] += 2
    require(assigned == {(cid, Fraction(radius)) for cid in cases for radius in RADII}, 'ALLOCATION', 'Missing assigned row')
    bracket = check_bracket(results['primary_bracket'], primary[0], batches)
    require(results['totals'] == {key: totals[key] for key in results['totals']}, 'ACCOUNTING', 'Result totals differ')
    report = {'artifact_id': 'reiyah.translation-2d.verification', 'version': '0.1.0',
              'started_utc': started, 'finished_utc': datetime.now(timezone.utc).isoformat(), 'seconds': time.perf_counter() - tick,
              'results_sha256': file_digest(output / 'RESULTS.json'), 'verifier_sha256': file_digest(__file__),
              'all_assigned_rows_accounted_for': True, 'all_complete_rows_verified': True,
              'images': len(images), 'case_radius_rows': len(assigned), 'totals': dict(totals), 'decisions': dict(decisions),
              'bracket_verified': list(map(w, bracket)), 'independent_scientific_replication': False}
    put(output / 'VERIFICATION.json', report)
    print(__import__('json').dumps(report), flush=True)


if __name__ == '__main__':
    run(*sys.argv[1:])
