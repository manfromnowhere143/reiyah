"""Verify inherited extrema, direct weighted worlds and every continuum cell."""
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
import sys
import time

from trade_certificate import check_cells, check_component, evaluate, linear_world, outcome
from trade_math import POLICY, SHARES, require, validate_policy
from trade_run import put
from trade_sources import digest, families, file_digest, load_sources, q, read, w


def check_incomplete(row, case, family):
    require(row['state'] == 'analysis_incomplete' and type(row['error']) is str and row['error']
            and row['source'] is None and row['continuum'] is None, 'Incomplete row claims usable evidence')
    require(row['case_id'] == case['id'] and row['family'] == family['id'] and row['group'] == case['group']
            and row['allocated_images'] == len(case['images']) and row['complete_case_membership'] == case['images'],
            'Incomplete row changes its allocation')
    require(len(row['grid']) == len(SHARES), 'Incomplete row omits a displayed setting')
    for entry, p in zip(row['grid'], SHARES):
        require(q(entry['share']) == p and entry['bounds'] is None and entry['decision'] is None
                and entry['opposite_worlds'] is None, 'Missing evidence became a weighted outcome')


def check_row(row, case, family, contexts, pool, verified):
    members = case['images']; size = len(members)
    require(row['state'] == 'complete' and row['case_id'] == case['id'] and row['group'] == case['group']
            and row['family'] == family['id'] and row['allocated_images'] == size
            and row['complete_case_membership'] == members, 'Case identity or full membership differs')
    source = row['source']; count_difference = Fraction(sum(contexts[iid]['count_difference'] for iid in members), size)
    require(q(source['count_difference']) == count_difference and len(source['worlds']) == 2, 'Count context or world pair differs')
    expected_unit = []
    centers = {iid: verified[contexts[iid]['nominal']]['unit'] for iid in members}
    for index in (0, 1):
        if family['kind'] == 'one_edit_global':
            changes = [q(contexts[iid]['families'][family['id']]['unit_bounds'][index]) - centers[iid] for iid in members]
            adjustment = min([Fraction(0)] + changes) if index == 0 else max([Fraction(0)] + changes)
            expected_unit.append((sum(centers.values()) + adjustment) / size)
        else:
            expected_unit.append(sum((q(contexts[iid]['families'][family['id']]['unit_bounds'][index]) for iid in members), Fraction(0)) / size)
        edited = 0
        for component, iid in zip(source['worlds'][index], members):
            key = component['component']; require(key in pool and component['image_id'] == iid, 'Unknown or misassigned world')
            expected_key = contexts[iid]['families'][family['id']]['worlds'][index]
            if family['kind'] == 'one_edit_global':
                require(key in (contexts[iid]['nominal'], expected_key), 'Global edit substitutes another source family')
                edited += int(pool[key]['world'] != contexts[iid]['original'])
            else:
                require(key == expected_key, 'World does not belong to the declared source extremum')
        if family['kind'] == 'one_edit_global':
            require(edited <= 1, 'Global reference-edit budget exceeded')
    require(source['unit_bounds'] == list(map(w, expected_unit)), 'Inherited universal enclosure differs')
    functions = [linear_world(world, verified, members) for world in source['worlds']]
    require(evaluate(functions, Fraction(1, 2)) == tuple(value / 2 for value in expected_unit)
            and all(slope == -count_difference for _, slope in functions), 'Direct world counts contradict affine transfer')
    require(len(row['grid']) == len(SHARES), 'Missing displayed share')
    for entry, p in zip(row['grid'], SHARES):
        require(q(entry['share']) == p, 'Displayed shares changed order or membership')
        expected = evaluate(functions, p); state = outcome(expected)
        require(entry['bounds'] == list(map(w, expected)) and entry['decision'] == state
                and entry['opposite_worlds'] is (state == 'unresolved'), 'Weighted grid decision or attained worlds differ')
        if p == 1:
            require(entry['ratio_kind'] == 'miss_only' and entry['miss_fp_ratio'] is None, 'Miss-only endpoint misrepresented')
        else:
            require(entry['ratio_kind'] == 'finite' and q(entry['miss_fp_ratio']) == p / (1-p), 'Penalty ratio differs')
    return check_cells(row['continuum'], functions)


def run(area, run_name='trade-01'):
    area = Path(area).resolve(); tick = time.perf_counter(); started = datetime.now(timezone.utc).isoformat()
    freeze_path = area / 'FREEZE.json'; freeze = read(freeze_path); validate_policy(freeze['policy'])
    allowed = {}
    for binding in freeze['bindings']:
        require(file_digest(binding['path']) == binding['sha256'], 'Frozen source or implementation changed')
        allowed[binding['path']] = binding['sha256']
    output = area / 'runs' / run_name; results_path = output / 'RESULTS.json'; results = read(results_path)
    require(results['freeze_sha256'] == file_digest(freeze_path) and results['policy'] == POLICY
            and results['shares'] == list(map(w, SHARES)) and results['families'] == families(), 'Result policy differs')
    visible = read(Path(freeze['predecessor_comparison']) / 'inputs/visible.json')
    cases = {case['id']: case for case in visible['cases']}; family_map = {family['id']: family for family in families()}
    require(len(cases) == 73 and len(visible['images']) == 64 and len(family_map) == 19, 'Wrong allocation')
    cache = {'sources': {}, 'counts': {}, 'native': set()}; verified = {}; totals = Counter(); decisions = Counter()
    source = results['source_admission']; nominal_counts = None
    if source['state'] == 'complete':
        source_visible, contexts, expected_pool = load_sources(freeze)
        require(source_visible == visible and file_digest(output / 'COMPONENTS.json') == source['components_sha256']
                and file_digest(output / 'CONTEXTS.json') == source['contexts_sha256'], 'Admitted source bytes changed')
        pool = read(output / 'COMPONENTS.json')
        require(pool == expected_pool and read(output / 'CONTEXTS.json') == contexts and len(pool) == source['components'],
                'Source selection or component context differs')
        for key, component in pool.items():
            iid = component['image_id']; require(iid in contexts, 'Unknown component image')
            expected_key = digest({'subject_sha256': component['subject_sha256'], 'world': component['world'], 'source': component['source']})
            require(key == expected_key, 'Source alias identity differs')
            verified[key] = {'image_id': iid, **check_component(contexts[iid]['image'], contexts[iid]['original'], component, cache, allowed)}
        nominal_counts = {role: {name: 0 for name in ('predictions', 'references', 'matches', 'false_positives', 'misses')}
                          for role in ('output_a', 'output_b')}
        for context in contexts.values():
            counts = verified[context['nominal']]['counts']
            for index, role in enumerate(nominal_counts):
                for name in nominal_counts[role]: nominal_counts[role][name] += counts[index][name]
    else:
        require(source['state'] == 'analysis_incomplete' and type(source['error']) is str and source['error'],
                'Invalid source-admission state')
    require(results['nominal_counts'] == nominal_counts, 'Nominal aggregate FP/FN counts differ')
    seen = set(); failures = []
    for row in results['rows']:
        key = row['case_id'], row['family']
        require(key[0] in cases and key[1] in family_map and key not in seen, 'Unknown or duplicate case/family row')
        seen.add(key); case, family = cases[key[0]], family_map[key[1]]
        if row['state'] == 'analysis_incomplete':
            check_incomplete(row, case, family); totals['incomplete_case_family_rows'] += 1
            failures.append({'case_id': key[0], 'family': key[1], 'error': row['error']})
        else:
            require(source['state'] == 'complete', 'Source admission failure became a completed result')
            totals['continuum_cells'] += check_row(row, case, family, contexts, pool, verified)
            totals['complete_case_family_rows'] += 1
            for entry in row['grid']: decisions[entry['decision']] += 1
        totals['displayed_rows'] += len(row['grid'])
    require(seen == {(case, family) for case in cases for family in family_map}, 'Assigned case/family row omitted')
    require(results['failures'] == failures and results['case_family_rows'] == len(seen) == 1387
            and results['displayed_rows'] == totals['displayed_rows'] == 12483
            and results['continuum_cells'] == totals['continuum_cells']
            and results['allocated_images'] == 64 and results['allocated_cases'] == 73, 'Result accounting differs')
    totals['source_components'] = len(verified); totals['unique_world_matchings'] = len(cache['counts'])
    totals['unique_native_proofs_checked'] = len(cache['native'])
    report = {'artifact_id': 'reiyah.loss-tradeoff.verification', 'version': '0.1.0',
              'started_utc': started, 'finished_utc': datetime.now(timezone.utc).isoformat(), 'seconds': time.perf_counter() - tick,
              'results_sha256': file_digest(results_path), 'verifier_sha256': file_digest(__file__),
              'all_assigned_rows_accounted_for': True, 'all_complete_rows_verified': True, 'totals': dict(totals),
              'displayed_decisions': dict(decisions), 'nominal_counts': nominal_counts,
              'independent_scientific_replication': False}
    put(output / 'VERIFICATION.json', report)
    print(__import__('json').dumps(report), flush=True)


if __name__ == '__main__':
    run(*sys.argv[1:])
