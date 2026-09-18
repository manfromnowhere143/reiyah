"""Refine every retained timing bound gap without changing its input family."""
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
import sys
import time

from witness_pool import build_pool, q, seed_indices
from witness_search import search
from timing_bounds import CONTRACTS, case_rows, certify
from timing_metadata import file_binding, put, read, require


def allocation(parent):
    gaps = [row for row in parent['cases'] if row['evidence'] == 'bound_gap']
    pairs = sorted({(iid, row['contract']) for row in gaps for iid in row['membership']})
    require(all(contract in ('current_partial', 'union_partial') for _, contract in pairs),
            'Gap allocation contains a nonpartial contract')
    return gaps, pairs


def refine(image, parent, contracts):
    tick = time.perf_counter(); result = deepcopy(parent); refinements = {}; failures = {}
    known = parent['known_references']; pool = None; pool_error = None
    if any(parent['contracts'][name]['unknown_count'] for name in contracts):
        try:
            pool = build_pool(image, known, parent['candidate_pool']['rectangles'])
        except Exception as exc:
            pool_error = type(exc).__name__+': '+str(exc)
    reused = {}
    for contract in contracts:
        scope = contract.removesuffix('_partial'); original = parent['contracts'][contract]
        unknown = parent[scope+'_unknown_instances']
        require(original['state'] == 'available' and unknown is not None, 'Target contract is unavailable')
        if not unknown:
            refinements[contract] = {'state': 'inherited_exact', 'reason': 'zero_unknown_instances'}
            continue
        if pool_error is not None:
            failures[contract] = pool_error
            refinements[contract] = {'state': 'search_incomplete', 'error': pool_error}
            continue
        try:
            seeds = seed_indices(image, parent, scope, pool); key = tuple(unknown)
            if key in reused:
                other, found = reused[key]
            else:
                other = None; found = search(image, known, unknown, pool, seeds); reused[key] = (contract, found)
            require(found['known'] == parent['known_only_measurement'] and found['bounds'] == original['bounds'],
                    'Refinement changed known evidence or universal bounds')
            chosen = []; improvement = []; searched_proofs = []; pending_proofs = deepcopy(result['proofs'])
            for endpoint, world in enumerate(found['worlds']):
                proof_key = certify(image, known, unknown, world['indices'], pool['rectangles'], pending_proofs)
                require(pending_proofs[proof_key]['measurement'] == world['measurement'], 'Search and native proof disagree')
                searched_proofs.append(proof_key)
                improved = q(world['measurement']['delta']) < q(original['attained'][endpoint]) if endpoint == 0 else q(world['measurement']['delta']) > q(original['attained'][endpoint])
                improvement.append(improved)
                chosen.append(proof_key if improved else original['proof_keys'][endpoint])
            result['proofs'] = pending_proofs
            result['contracts'][contract] = {**original, 'proof_keys': chosen,
                'attained': [result['proofs'][key]['measurement']['delta'] for key in chosen]}
            refinements[contract] = {'state': 'complete', 'seeds': seeds, 'search': found,
                'reused_from': other, 'searched_proof_keys': searched_proofs, 'improved_endpoints': improvement}
        except Exception as exc:
            error = type(exc).__name__+': '+str(exc); failures[contract] = error
            refinements[contract] = {'state': 'search_incomplete', 'error': error}
            result['contracts'][contract] = deepcopy(original)
    result['refinement'] = {'selected_contracts': contracts, 'pool': pool, 'pool_error': pool_error,
                            'contracts': refinements, 'failures': failures, 'seconds': time.perf_counter()-tick}
    return result


def sources(area):
    freeze_path = area/'FREEZE.json'; freeze = read(freeze_path)
    for binding in freeze['bindings']:
        require(file_binding(binding['path']) == binding, 'Frozen source or implementation changed')
    parent_path = Path(freeze['parent_results']); parent = read(parent_path)
    verification = read(freeze['parent_verification'])
    require(verification['results_sha256'] == file_binding(parent_path)['sha256']
            and verification['all_assigned_rows_accounted_for'] and verification['all_complete_rows_verified']
            and verification['all_images_complete'], 'Parent results lack their completed verification')
    visible = read(freeze['visible']); gaps, pairs = allocation(parent)
    require(freeze['targets'] == [list(pair) for pair in pairs]
            and freeze['gap_cases'] == [[row['case_id'], row['contract']] for row in gaps], 'Frozen gap allocation differs')
    return freeze, parent, visible, gaps, pairs


def run(area, run_name='witness-01'):
    area = Path(area).resolve(); tick = time.perf_counter(); started = datetime.now(timezone.utc).isoformat()
    freeze, parent, visible, gaps, pairs = sources(area)
    require(len(pairs) == 14 and len(gaps) == 7 and len(visible['images']) == 64 and len(visible['cases']) == 73,
            'Actual declared allocation differs')
    output = area/'runs'/run_name; output.mkdir(parents=True)
    images = {image['id']: image for image in visible['images']}; records = {}; bindings = []; failures = {}
    for entry in parent['image_records']:
        iid = entry['image_id']; source = {key: entry[key] for key in ('path', 'bytes', 'sha256')}
        require(file_binding(entry['path']) == source and iid not in records, 'Parent image identity changed or repeated')
        original = read(entry['path']); contracts = [contract for key, contract in pairs if key == iid]
        if contracts:
            record = refine(images[iid], original, contracts); record['refinement']['parent_source'] = source
            path = output/(iid+'.json'); put(path, record)
            failures.update({iid+':'+key: value for key, value in record['refinement']['failures'].items()})
            binding = {'image_id': iid, **file_binding(path), 'state': 'refined'}
        else:
            record = original; binding = {**entry, 'state': 'inherited'}
        records[iid] = record; bindings.append(binding)
    require(set(records) == set(images), 'Image allocation omitted')
    rows = case_rows(visible['cases'], records)
    require(len(rows) == 292, 'Case allocation omitted')
    by_key = {(row['case_id'], row['contract']): row for row in parent['cases']}
    for row in rows:
        old = by_key[row['case_id'], row['contract']]
        require(all(row[name] == old[name] for name in ('membership', 'bounds', 'blocked_images', 'state', 'decision')),
                'Refinement changed universal decisions or available inputs')
    counts = {name: dict(Counter(row['evidence'] for row in rows if row['contract'] == name and row['state'] == 'available'))
              for name in CONTRACTS}
    result = {'artifact_id': 'reiyah.reference-witness.results', 'version': '0.1.0', 'status': 'exploratory',
        'started_utc': started, 'finished_utc': datetime.now(timezone.utc).isoformat(), 'seconds': time.perf_counter()-tick,
        'freeze_sha256': file_binding(area/'FREEZE.json')['sha256'], 'parent_source': file_binding(freeze['parent_results']),
        'allocated_images': 64, 'allocated_cases': 73, 'allocated_case_contract_rows': 292,
        'selected_pairs': [list(pair) for pair in pairs], 'selected_gap_cases': freeze['gap_cases'],
        'image_records': bindings, 'cases': rows, 'evidence_counts': counts, 'failures': failures,
        'human_seconds': None, 'economic_cost': None, 'new_image_reads': 0, 'model_inference_calls': 0,
        'reserved_outcomes_accessed': 0, 'independent_scientific_replication': False}
    put(output/'RESULTS.json', result)
    print(__import__('json').dumps({'evidence_counts': counts, 'failures': failures, 'seconds': result['seconds']}), flush=True)


if __name__ == '__main__':
    run(*sys.argv[1:])
