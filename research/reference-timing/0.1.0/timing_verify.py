"""Verify full temporal allocation, source geometry, bounds and attained worlds."""
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
import sys
import time

from timing_bounds import CONTRACTS, digest, q, w
from timing_certificate import (check_alternate_edges, check_pool, check_proof, check_search,
                                expected_world, independent_bounds, known_from_source, matching)
from timing_metadata import file_binding, put, read, require
from timing_source_certificate import check_source_image


def check_changes(record, projection, original):
    old = {row['id']: row for row in original}; counts = Counter(); paired = []
    current_ids = {'reference:'+row['annotation_token'] for row in projection['objects']}
    require(set(old) <= current_ids, 'Original eligible reference is outside the admitted current census')
    for row in projection['objects']:
        key = 'reference:'+row['annotation_token']; present = key in old
        if row['state'] == 'unavailable':
            counts['originally_eligible_unassessed' if present else 'originally_ineligible_unassessed'] += 1
        elif row['projection']['eligibility'] == 'eligible':
            counts['stayed_eligible' if present else 'entered_eligibility'] += 1
            if present:
                errors = [abs(q(a)-Fraction(str(b))) for a, b in zip(old[key]['xyxy'], row['projection']['xyxy'])]
                paired.append({'annotation_token': row['annotation_token'], 'maximum_coordinate_change': w(max(errors)),
                               'coordinate_changes': list(map(w, errors))})
        else:
            counts['left_eligibility' if present else 'stayed_ineligible'] += 1
    maximum = max((q(row['maximum_coordinate_change']) for row in paired), default=None)
    expected = {'counts': dict(counts), 'paired_changes': paired,
                'maximum_coordinate_change': w(maximum) if maximum is not None else None}
    require(record['projection_changes'] == expected, 'Eligibility transition or displacement accounting differs')


def check_image_record(record, image, projection, source, original, original_nominal, cache):
    require(record['image_id'] == image['id'] and record['state'] == 'complete', 'Image result state differs')
    known = known_from_source(source)
    require(record['known_references'] == known and record['current_unknown_instances'] == source['current_unknown']
            and record['union_unknown_instances'] == source['union_unknown'], 'Known geometry or unknown census differs')
    check_alternate_edges(image, known, source); check_pool(image, record['candidate_pool'])
    require(record['original_nominal'] == original_nominal == matching(image, original), 'Inherited nominal comparison differs')
    check_changes(record, projection, original)
    pool = record['candidate_pool']['rectangles']; proofs = record['proofs']; used = set()
    key = record['known_proof_key']; used.add(key)
    nominal = check_proof(key, proofs[key], image, known, cache)
    require(record['known_only_measurement'] == nominal, 'Known-only world differs')
    require(set(record['contracts']) == set(CONTRACTS), 'Missing reference contract')
    expected_search_scopes = {'current'} | ({'union'} if source['union_unknown'] is not None else set())
    require(set(record['searches']) == set(record['search_reuse']) == expected_search_scopes, 'Search membership differs')
    require(record['search_reuse']['current'] is None, 'Current search has an invalid reuse source')
    for scope, unknown in [('current', source['current_unknown']), ('union', source['union_unknown'])]:
        strict, partial = record['contracts'][scope+'_strict'], record['contracts'][scope+'_partial']
        if unknown is None:
            for value in (strict, partial):
                require(value == {'state': 'input_blocked', 'reason': 'preceding_census_unavailable',
                                  'bounds': None, 'attained': None, 'proof_keys': None}, 'Missing union census became complete')
            continue
        if unknown:
            require(strict == {'state': 'input_blocked', 'reason': 'motion_unavailable_for_census_instances',
                               'bounds': None, 'attained': None, 'proof_keys': None}, 'Strict model silently filled missing motion')
        else:
            require(strict == {'state': 'available', 'unknown_count': 0,
                               'bounds': [nominal['delta'], nominal['delta']], 'attained': [nominal['delta'], nominal['delta']],
                               'proof_keys': [key, key]}, 'Complete point-model comparison differs')
        found = record['searches'][scope]
        if scope == 'union':
            expected_reuse = 'current' if unknown == source['current_unknown'] else None
            require(record['search_reuse']['union'] == expected_reuse, 'Search reuse claim differs')
            if expected_reuse is not None:
                require(found == record['searches']['current'], 'Reused search bytes differ')
        bounds = check_search(found, image, known, unknown, pool)
        expected_keys = []; attained = []
        for direction in ('lower', 'upper'):
            world = found['worlds'][direction]; references = expected_world(known, unknown, world['candidate_indices'], pool)
            proof_key = digest({'image_id': image['id'], 'references': references}); expected_keys.append(proof_key); used.add(proof_key)
            measured = check_proof(proof_key, proofs[proof_key], image, references, cache)
            require(measured == world['measurement'], 'Search endpoint and independently checked world differ')
            attained.append(measured['delta'])
        require(partial == {'state': 'available', 'unknown_count': len(unknown), 'bounds': bounds,
                            'attained': attained, 'proof_keys': expected_keys}, 'Partial reference contract differs')
        require(q(bounds[0]) <= q(attained[0]) <= q(nominal['delta']) <= q(attained[1]) <= q(bounds[1]),
                'Attained values violate enclosure or known-only world')
    require(set(proofs) == used, 'Unexplained or missing native proof')
    return {'known_references': len(known), 'current_unknown_instances': len(source['current_unknown']),
            'union_unknown_instances': len(source['union_unknown']) if source['union_unknown'] is not None else None,
            'proofs': len(used)}


def check_cases(rows, cases, records):
    lookup = {case['id']: case for case in cases}; seen = set(); decisions = {name: Counter() for name in CONTRACTS}
    evidence = Counter()
    for row in rows:
        key = row['case_id'], row['contract']; require(key not in seen and key[0] in lookup and key[1] in CONTRACTS,
                                                    'Repeated or unknown case/contract row')
        seen.add(key); case = lookup[key[0]]; members = case['images']; contract = key[1]
        require(row['group'] == case['group'] and row['membership'] == members and row['allocated_images'] == len(members),
                'Case silently replaced its full allocation')
        blocked = [iid for iid in members if records[iid]['contracts'][contract]['state'] != 'available']
        require(row['blocked_images'] == blocked, 'Blocked membership differs')
        if blocked:
            require(row['state'] == 'input_blocked' and row['decision'] == 'input_blocked'
                    and all(row[name] is None for name in ('bounds', 'attained', 'evidence', 'worlds')), 'Missing input became a decision')
        else:
            bounds = []; attained = []; worlds = []
            for endpoint in (0, 1):
                bounds.append(sum((q(records[iid]['contracts'][contract]['bounds'][endpoint]) for iid in members), Fraction(0))/len(members))
                attained.append(sum((q(records[iid]['contracts'][contract]['attained'][endpoint]) for iid in members), Fraction(0))/len(members))
                worlds.append([{'image_id': iid, 'proof_key': records[iid]['contracts'][contract]['proof_keys'][endpoint]} for iid in members])
            decision = 'supported' if bounds[0] > 0 else 'excluded' if bounds[1] <= 0 else 'unresolved'
            basis = 'universal_bound' if decision != 'unresolved' else 'opposite_worlds' if attained[0] <= 0 < attained[1] else 'bound_gap'
            require(row['state'] == 'available' and row['bounds'] == list(map(w, bounds)) and row['attained'] == list(map(w, attained))
                    and row['decision'] == decision and row['evidence'] == basis and row['worlds'] == worlds, 'Case arithmetic or evidence differs')
            evidence[basis] += 1
        decisions[contract][row['decision']] += 1
    require(seen == {(case, contract) for case in lookup for contract in CONTRACTS}, 'Assigned case/contract row omitted')
    return {key: dict(value) for key, value in decisions.items()}, dict(evidence)


def run(area, projection_name='projection-01', run_name='timing-01'):
    area = Path(area).resolve(); started = datetime.now(timezone.utc).isoformat(); tick = time.perf_counter()
    freeze_path = area/'FREEZE.json'; freeze = read(freeze_path)
    for row in freeze['bindings']:
        require(file_binding(row['path']) == row, 'Frozen input or code changed')
    comparison = Path(freeze['predecessor_comparison']); visible = read(comparison/'inputs/visible.json')
    images = {image['id']: image for image in visible['images']}
    selected, preceding = read(freeze['selected_metadata']), read(freeze['preceding_metadata'])
    applicability = {row['image_id']: row for row in read(freeze['applicability'])}
    output = area/'runs'/run_name; result_path = output/'RESULTS.json'; result = read(result_path)
    projection_path = area/'runs'/projection_name/'RESULTS.json'; projected = read(projection_path)
    require(result['freeze_sha256'] == projected['freeze_sha256'] == file_binding(freeze_path)['sha256']
            and result['projection_source'] == file_binding(projection_path), 'Result source binding differs')
    require(len(images) == 64 and len(visible['cases']) == 73 and result['allocated_images'] == 64
            and result['allocated_cases'] == 73 and result['allocated_case_contract_rows'] == 292
            and result['contracts'] == list(CONTRACTS), 'Result allocation differs')
    projected_records = {row['image_id']: row for row in projected['image_records']}
    require(len(projected['image_records']) == len(result['image_records']) == 64
            and set(projected_records) == set(images) == set(applicability), 'Projection or result membership differs')
    require(all(image['image_sha256'] == applicability[iid]['image_sha256'] for iid, image in images.items()),
            'Prediction/projection image byte identity differs')
    records = {}; source_totals = Counter(); numerical = Counter(); totals = Counter(); failures = {}
    cache = {'native': set(), 'native_check_seconds': 0.0}
    for entry in result['image_records']:
        iid = entry['image_id']; require(iid in images and iid not in records, 'Unknown or repeated result image')
        require(file_binding(entry['path']) == {key: entry[key] for key in ('path', 'sha256', 'bytes')}, 'Image result bytes changed')
        record = read(entry['path']); records[iid] = record; source_entry = projected_records[iid]
        require(record['projection_source'] == source_entry
                and file_binding(source_entry['path']) == {key: source_entry[key] for key in ('path', 'sha256', 'bytes')},
                'Image projection source changed')
        projection = read(source_entry['path'])
        oracle = comparison/'oracle'/(iid+'.json'); baseline = comparison/'runs/analysis-01'/(iid+'.json')
        require(record['original_reference_source'] == file_binding(oracle) and record['original_nominal_source'] == file_binding(baseline),
                'Original source identity differs')
        if record['state'] == 'analysis_incomplete':
            require(type(record['error']) is str and record['error'] and record['contracts'] == {
                name: {'state': 'input_blocked', 'reason': 'analysis_incomplete', 'bounds': None,
                       'attained': None, 'proof_keys': None} for name in CONTRACTS}, 'Incomplete analysis claims results')
            failures[iid] = record['error']; totals['incomplete_images_retained'] += 1
            continue
        source = check_source_image(projection, applicability[iid], selected, preceding)
        counts = check_image_record(record, images[iid], projection, source, read(oracle)['answer'], read(baseline)['nominal']['nominal'], cache)
        totals['complete_images_verified'] += 1
        for key, value in counts.items():
            if value is not None: totals[key] += value
        source_totals.update(source['counts'])
        for key, value in source['numerical'].items():
            if key.startswith('maximum_'): numerical[key] = max(numerical[key], value)
            else: numerical[key] += value
    require(set(records) == set(images) and result['failures'] == failures, 'Failed image omitted or relabeled')
    decisions, evidence = check_cases(result['cases'], visible['cases'], records)
    require(result['decision_counts'] == decisions, 'Aggregate decision counts differ')
    report = {'artifact_id': 'reiyah.reference-timing.verification', 'version': '0.1.0',
              'started_utc': started, 'finished_utc': datetime.now(timezone.utc).isoformat(), 'seconds': time.perf_counter()-tick,
              'results_sha256': file_binding(result_path)['sha256'], 'verifier_sha256': file_binding(__file__)['sha256'],
              'all_assigned_rows_accounted_for': True, 'all_complete_rows_verified': True,
              'all_images_complete': not failures, 'totals': dict(totals), 'source_object_counts': dict(source_totals),
              'numerical_diagnostics': dict(numerical), 'decisions': decisions, 'case_evidence': evidence,
              'unique_native_proofs_checked': len(cache['native']), 'native_check_seconds': cache['native_check_seconds'],
              'incomplete_images': failures, 'independent_scientific_replication': False,
              'human_seconds': None, 'economic_cost': None}
    put(output/'VERIFICATION.json', report)
    print(__import__('json').dumps(report), flush=True)


if __name__ == '__main__':
    run(*sys.argv[1:])
