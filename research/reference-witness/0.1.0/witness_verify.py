"""Check retained geometric worlds independently of the flow search."""
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
import sys
import time

from witness_pool import ROLES, digest, q, w
from witness_run import sources
from witness_search import graph_search
from timing_certificate import check_proof, expected_world
from timing_metadata import file_binding, put, read, require
from timing_verify import check_cases
from axis_certificate import exact_iou, expected_cells, maximum_matching


def independent_pool(image, known, inherited):
    detections = {row['id']: tuple(map(q, row['xyxy'])) for role in ROLES for row in image[role]['value']}
    bases = set(detections.values()) | {tuple(map(q, row['xyxy'])) for row in known}
    bases |= {tuple(map(q, geometry)) for geometry in inherited}
    geometry = set(bases); count = 0
    for base in sorted(bases):
        for axis in (0, 1):
            cells, _ = expected_cells(base, list(detections.values()), axis, image['width'], image['height'])
            count += len(cells)
            for left, right in cells:
                rectangle = list(base); position = (left+right)/2
                rectangle[axis+2] += position-rectangle[axis]; rectangle[axis] = position
                geometry.add(tuple(rectangle))
                require(len(geometry) <= 100000, 'Independent rectangle construction limit')
    representatives = {}; empty = 0
    for rectangle in sorted(geometry):
        neighbors = tuple(key for key in sorted(detections) if exact_iou(detections[key], rectangle) >= Fraction(1, 2))
        if neighbors:
            if neighbors not in representatives: representatives[neighbors] = rectangle
        else:
            empty += 1
    require(len(representatives) <= 4096, 'Independent neighborhood construction limit')
    ordered = sorted(representatives)
    return {'rectangles': [list(map(w, representatives[key])) for key in ordered],
            'neighborhoods': [list(key) for key in ordered], 'base_count': len(bases),
            'axis_sweeps': 2*len(bases), 'axis_cells': count, 'unique_rectangles': len(geometry),
            'empty_neighborhood_rectangles': empty,
            'geometry_sha256': digest([list(map(w, values)) for values in sorted(geometry)]),
            'rectangle_limit': 100000, 'neighborhood_limit': 4096,
            'all_declared_axis_cells_constructed': True, 'all_arbitrary_rectangles_searched': False}


def independent_seeds(image, parent, scope, pool):
    prediction = {row['id']: tuple(map(q, row['xyxy'])) for role in ROLES for row in image[role]['value']}
    lookup = {tuple(values): index for index, values in enumerate(pool['neighborhoods'])}; answer = []
    for direction in ('lower', 'upper'):
        source = parent['searches'][scope]['worlds'][direction]; selected = []
        for index in source['candidate_indices']:
            rectangle = tuple(map(q, parent['candidate_pool']['rectangles'][index]))
            neighborhood = tuple(key for key in sorted(prediction) if exact_iou(prediction[key], rectangle) >= Fraction(1, 2))
            if neighborhood: selected.append(lookup[neighborhood])
        answer.append({'indices': sorted(selected), 'measurement': source['measurement']})
    return answer


def check_search(image, known, unknown, pool, seeds, found):
    predictions = {row['id']: row for role in ROLES for row in image[role]['value']}
    base_edges = {(key, ref['id']) for key, row in predictions.items() for ref in known
                  if exact_iou(list(map(q, row['xyxy'])), list(map(q, ref['xyxy']))) >= Fraction(1, 2)}
    require(found['unknown_ids'] == unknown and found['measurement_limit'] == 50000 and found['reference_limit'] == 128,
            'Search changed census or resource limits')
    replay = graph_search(image, [row['id'] for row in known], base_edges, pool['neighborhoods'], len(unknown), seeds)
    require({key: value for key, value in found.items() if key not in ('seconds', 'unknown_ids')} == replay,
            'Search traversal or charged accounting differs')
    lefts = [{row['id'] for row in image[role]['value']} for role in ROLES]
    for step in found['transcript']:
        indices = step['indices']; ranks = []
        for left in lefts:
            adjacency = {key: {('known', ref) for pred, ref in base_edges if pred == key} for key in left}
            for j, index in enumerate(indices):
                for key in set(pool['neighborhoods'][index]) & left:
                    adjacency[key].add(('optional', j))
            ranks.append(maximum_matching(adjacency))
        expected = {'ranks': ranks, 'delta': w(len(lefts[0])-len(lefts[1])+2*(ranks[1]-ranks[0]))}
        require(step['measurement'] == expected, 'Independent transcript matching differs')
    return len(found['transcript'])


def check_image(record, parent, image, contracts, cache):
    detail = record['refinement']; known = parent['known_references']
    require(detail['selected_contracts'] == contracts and set(detail['contracts']) == set(contracts), 'Selected component omitted')
    require({key: value for key, value in record.items() if key not in ('proofs', 'contracts', 'refinement')}
            == {key: value for key, value in parent.items() if key not in ('proofs', 'contracts')}, 'Inherited evidence changed')
    require(all(record['proofs'].get(key) == value for key, value in parent['proofs'].items()), 'Inherited native proof changed')
    needs_pool = any(parent['contracts'][contract]['unknown_count'] for contract in contracts)
    if needs_pool and detail['pool_error'] is None:
        require(detail['pool'] == independent_pool(image, known, parent['candidate_pool']['rectangles']),
                'Exact threshold pool or neighborhood coverage differs')
    elif not needs_pool:
        require(detail['pool'] is None and detail['pool_error'] is None, 'Unnecessary pool for exact inherited world')
    used = set(parent['proofs']); expected_contracts = deepcopy(parent['contracts']); failures = {}; measurements = 0
    for contract in contracts:
        value = detail['contracts'][contract]; scope = contract.removesuffix('_partial')
        unknown = parent[scope+'_unknown_instances']; original = parent['contracts'][contract]
        require(unknown is not None and original['state'] == 'available', 'Refinement used an unavailable census')
        if not unknown:
            require(value == {'state': 'inherited_exact', 'reason': 'zero_unknown_instances'}, 'Zero-unknown component changed')
            continue
        if value['state'] == 'search_incomplete':
            require(type(value['error']) is str and value['error'], 'Failure lacks its cause')
            failures[contract] = value['error']; continue
        require(value['state'] == 'complete' and detail['pool_error'] is None, 'Unknown refinement state')
        pool = detail['pool']; seeds = independent_seeds(image, parent, scope, pool)
        require(value['seeds'] == seeds, 'Inherited seed assignment differs')
        reused = value['reused_from']
        if reused is None:
            measurements += check_search(image, known, unknown, pool, seeds, value['search'])
        else:
            require(reused in contracts and contracts.index(reused) < contracts.index(contract)
                    and parent[reused.removesuffix('_partial')+'_unknown_instances'] == unknown
                    and value['search'] == detail['contracts'][reused]['search'], 'Invalid search reuse')
        keys = []; improved = []; searched = []
        require(value['search']['bounds'] == original['bounds'], 'Universal bounds changed')
        for endpoint, world in enumerate(value['search']['worlds']):
            references = expected_world(known, unknown, world['indices'], pool['rectangles'])
            key = digest({'image_id': image['id'], 'references': references}); searched.append(key); used.add(key)
            measured = check_proof(key, record['proofs'][key], image, references, cache)
            require(measured == world['measurement'], 'Retained world and search ranks differ')
            better = q(measured['delta']) < q(original['attained'][endpoint]) if endpoint == 0 else q(measured['delta']) > q(original['attained'][endpoint])
            improved.append(better); keys.append(key if better else original['proof_keys'][endpoint])
        require(value['searched_proof_keys'] == searched and value['improved_endpoints'] == improved, 'Witness selection differs')
        expected_contracts[contract] = {**original, 'proof_keys': keys,
            'attained': [record['proofs'][key]['measurement']['delta'] for key in keys]}
    require(record['contracts'] == expected_contracts and detail['failures'] == failures, 'Contract changed outside its refined endpoints')
    require(set(record['proofs']) == used, 'Unexplained or missing proof')
    # Independently recheck inherited endpoint proofs too. The prior projection
    # source verification is inherited by exact bytes, not silently rerun.
    for key, proof in record['proofs'].items():
        check_proof(key, proof, image, proof['references'], cache)
    return failures, measurements


def run(area, run_name='witness-01'):
    area = Path(area).resolve(); tick = time.perf_counter(); started = datetime.now(timezone.utc).isoformat()
    freeze, parent, visible, gaps, pairs = sources(area)
    output = area/'runs'/run_name; path = output/'RESULTS.json'; result = read(path)
    require(result['freeze_sha256'] == file_binding(area/'FREEZE.json')['sha256']
            and result['parent_source'] == file_binding(freeze['parent_results']), 'Result source binding differs')
    require(result['selected_pairs'] == [list(pair) for pair in pairs] and result['selected_gap_cases'] == freeze['gap_cases'],
            'Result omits a selected gap')
    require([result[name] for name in ('allocated_images', 'allocated_cases', 'allocated_case_contract_rows')] == [64, 73, 292],
            'Result allocation differs')
    images = {row['id']: row for row in visible['images']}; parent_entries = {row['image_id']: row for row in parent['image_records']}
    records = {}; failures = {}; measurements = 0; cache = {'native': set(), 'native_check_seconds': 0.0}
    for entry in result['image_records']:
        iid = entry['image_id']; require(iid in images and iid not in records, 'Repeated or unknown image')
        source = parent_entries[iid]; parent_binding = {key: source[key] for key in ('path', 'bytes', 'sha256')}
        require(file_binding(entry['path']) == {key: entry[key] for key in ('path', 'bytes', 'sha256')}
                and file_binding(source['path']) == parent_binding, 'Result or parent image bytes changed')
        parent_record = read(source['path']); record = read(entry['path']); records[iid] = record
        contracts = [contract for key, contract in pairs if key == iid]
        if contracts:
            require(entry['state'] == 'refined' and record['refinement']['parent_source'] == parent_binding,
                    'Refined image provenance differs')
            found, count = check_image(record, parent_record, images[iid], contracts, cache)
            failures.update({iid+':'+key: value for key, value in found.items()}); measurements += count
        else:
            require(entry == {**source, 'state': 'inherited'} and record == parent_record, 'Untargeted component changed')
            for key, proof in record['proofs'].items():
                check_proof(key, proof, images[iid], proof['references'], cache)
    require(set(records) == set(images) and result['failures'] == failures, 'Missing image or failed search')
    decisions, evidence = check_cases(result['cases'], visible['cases'], records)
    old_rows = {(row['case_id'], row['contract']): row for row in parent['cases']}
    for row in result['cases']:
        original = old_rows[row['case_id'], row['contract']]
        require(all(row[key] == original[key] for key in ('bounds', 'decision', 'membership', 'blocked_images', 'state')),
                'Search changed universal decision or missing input')
        if row['attained'] is not None:
            require(q(row['attained'][0]) <= q(original['attained'][0])
                    and q(row['attained'][1]) >= q(original['attained'][1]), 'Search lost a previous attained world')
    counts = {name: dict(Counter(row['evidence'] for row in result['cases'] if row['contract'] == name and row['state'] == 'available'))
              for name in parent['contracts']}
    require(result['evidence_counts'] == counts, 'Aggregate evidence counts differ')
    report = {'artifact_id': 'reiyah.reference-witness.verification', 'version': '0.1.0',
        'started_utc': started, 'finished_utc': datetime.now(timezone.utc).isoformat(), 'seconds': time.perf_counter()-tick,
        'results_sha256': file_binding(path)['sha256'], 'verifier_sha256': file_binding(__file__)['sha256'],
        'all_assigned_rows_accounted_for': True, 'all_complete_rows_verified': True,
        'universal_decisions_unchanged': decisions == parent['decision_counts'], 'case_evidence': evidence,
        'unique_flow_measurements_checked': measurements, 'unique_native_proofs_checked': len(cache['native']),
        'native_check_seconds': cache['native_check_seconds'], 'retained_search_failures': failures,
        'independent_scientific_replication': False, 'human_seconds': None, 'economic_cost': None}
    require(report['universal_decisions_unchanged'], 'Decision count changed')
    put(output/'VERIFICATION.json', report); print(__import__('json').dumps(report), flush=True)


if __name__ == '__main__':
    run(*sys.argv[1:])
