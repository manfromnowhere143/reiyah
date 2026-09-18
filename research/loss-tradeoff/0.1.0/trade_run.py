"""Run the frozen weighted-loss derivation without selector or inference calls."""
from datetime import datetime, timezone
from fractions import Fraction
import json
from pathlib import Path
import sys
import time

from trade_math import POLICY, SHARES, bounds, decision, partition, penalty_ratio, require, validate_policy
from trade_sources import compose, families, file_digest, load_sources, q, read, w


def put(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, sort_keys=True, separators=(',', ':'), allow_nan=False); stream.write('\n')


def build_case(case, family, contexts, pool):
    source = compose(case, family, contexts, pool)
    unit = tuple(map(q, source['unit_bounds'])); count_difference = q(source['count_difference'])
    grid = []
    for p in SHARES:
        interval = bounds(unit, count_difference, p); outcome = decision(interval)
        grid.append({'share': w(p), 'miss_fp_ratio': None if penalty_ratio(p) is None else w(penalty_ratio(p)),
                     'ratio_kind': 'miss_only' if p == 1 else 'finite', 'bounds': list(map(w, interval)),
                     'decision': outcome, 'opposite_worlds': outcome == 'unresolved'})
    continuum = []
    for cell in partition(unit, count_difference):
        continuum.append({key: w(value) if isinstance(value, Fraction) else list(map(w, value)) if key == 'bounds' else value
                          for key, value in cell.items()})
    return {'case_id': case['id'], 'group': case['group'], 'family': family['id'], 'state': 'complete',
            'allocated_images': len(case['images']), 'complete_case_membership': case['images'],
            'source': source, 'grid': grid, 'continuum': continuum}


def incomplete_case(case, family, error):
    return {'case_id': case['id'], 'group': case['group'], 'family': family['id'], 'state': 'analysis_incomplete',
            'allocated_images': len(case['images']), 'complete_case_membership': case['images'], 'error': error,
            'source': None, 'continuum': None,
            'grid': [{'share': w(p), 'bounds': None, 'decision': None, 'opposite_worlds': None} for p in SHARES]}


def run(area, run_name='trade-01'):
    area = Path(area).resolve(); started = datetime.now(timezone.utc).isoformat(); tick = time.perf_counter()
    freeze_path = area / 'FREEZE.json'; freeze = read(freeze_path); validate_policy(freeze['policy'])
    require(freeze['shares'] == list(map(w, SHARES)) and freeze['families'] == families()
            and freeze['actual_weighted_outcomes_before_freeze'] is False, 'Frozen weighted plan differs')
    for binding in freeze['bindings']:
        require(file_digest(binding['path']) == binding['sha256'], 'Frozen source or implementation changed')
    visible = read(Path(freeze['predecessor_comparison']) / 'inputs/visible.json')
    require(len(visible['images']) == 64 and len(visible['cases']) == 73, 'Wrong allocated population')
    output = area / 'runs' / run_name; output.mkdir(parents=True)
    source_tick = time.perf_counter(); source_error = None; source_counts = None
    try:
        source_visible, contexts, pool = load_sources(freeze)
        require(source_visible == visible, 'Source population changed')
        put(output / 'COMPONENTS.json', pool); put(output / 'CONTEXTS.json', contexts)
        source_counts = {role: {'predictions': 0, 'references': 0, 'matches': 0, 'false_positives': 0, 'misses': 0}
                         for role in ('output_a', 'output_b')}
        for context in contexts.values():
            component = pool[context['nominal']]
            for index, role in enumerate(source_counts):
                n, t, m = component['prediction_counts'][index], component['reference_count'], component['measurement']['ranks'][index]
                for key, value in [('predictions', n), ('references', t), ('matches', m), ('false_positives', n-m), ('misses', t-m)]:
                    source_counts[role][key] += value
        source_state = {'state': 'complete', 'components': len(pool), 'components_sha256': file_digest(output / 'COMPONENTS.json'),
                        'contexts_sha256': file_digest(output / 'CONTEXTS.json')}
    except Exception as exc:
        source_error = type(exc).__name__ + ': ' + str(exc)
        source_state = {'state': 'analysis_incomplete', 'error': source_error}; put(output / 'SOURCE_FAILURE.json', source_state)
    source_state['seconds'] = time.perf_counter() - source_tick
    rows, failures = [], []
    for case in visible['cases']:
        for family in families():
            if source_error:
                row = incomplete_case(case, family, source_error)
            else:
                try:
                    row = build_case(case, family, contexts, pool)
                except Exception as exc:
                    row = incomplete_case(case, family, type(exc).__name__ + ': ' + str(exc))
            rows.append(row)
            if row['state'] == 'analysis_incomplete':
                failures.append({'case_id': row['case_id'], 'family': row['family'], 'error': row['error']})
    require(len(rows) == 1387 and sum(len(row['grid']) for row in rows) == 12483, 'Incomplete assigned rows')
    results = {'artifact_id': 'reiyah.loss-tradeoff.results', 'version': '0.1.0', 'status': 'exploratory',
               'started_utc': started, 'finished_utc': datetime.now(timezone.utc).isoformat(), 'seconds': time.perf_counter() - tick,
               'freeze_sha256': file_digest(freeze_path), 'policy': POLICY, 'shares': list(map(w, SHARES)), 'families': families(),
               'allocated_images': 64, 'allocated_cases': 73, 'case_family_rows': 1387, 'displayed_rows': 12483,
               'rows': rows, 'failures': failures, 'source_admission': source_state, 'nominal_counts': source_counts,
               'continuum_cells': sum(len(row['continuum'] or []) for row in rows),
               'new_geometry_searches': 0, 'model_inference_calls': 0, 'reserved_outcomes_accessed': 0,
               'human_seconds': None, 'economic_cost': None, 'independent_scientific_replication': False}
    put(output / 'RESULTS.json', results)
    print(json.dumps({'rows': len(rows), 'failures': len(failures), 'source_admission': source_state,
                      'continuum_cells': results['continuum_cells'], 'seconds': results['seconds']}), flush=True)


if __name__ == '__main__':
    run(*sys.argv[1:])
