"""Execute the frozen planar stress family, retaining failed and bounded rows."""
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys
import time

from planar_search import MAX_DEPTH, MAX_REGIONS, RADII, prepare, q, require, search, w


def read(path):
    return json.loads(Path(path).read_text())


def put(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, sort_keys=True, separators=(',', ':'), allow_nan=False)
        stream.write('\n')


def file_digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def radius_key(radius):
    radius = Fraction(radius)
    return f'r{radius.numerator}_{radius.denominator}'


def case_row(case, records, radius):
    failed = [iid for iid in case['images'] if records[iid]['state'] == 'analysis_incomplete']
    base = {'case_id': case['id'], 'group': case['group'], 'radius': w(Fraction(radius)),
            'allocated_images': len(case['images']), 'analysis_failed_images': failed}
    if failed:
        return {**base, 'state': 'analysis_incomplete', 'universal_bounds': None, 'attained_bounds': None,
                'nominal_delta': None, 'exact_extrema': None, 'decision': None, 'unresolved_reason': None, 'worlds': None}
    members = case['images']; size = len(members)
    universal = [sum((q(records[iid]['universal_bounds'][i]) for iid in members), Fraction(0)) / size for i in (0, 1)]
    attained = [sum((q(records[iid]['attained_bounds'][i]) for iid in members), Fraction(0)) / size for i in (0, 1)]
    decision = 'supported' if universal[0] > 0 else 'excluded' if universal[1] <= 0 else 'unresolved'
    reason = ('opposite_worlds' if attained[0] <= 0 < attained[1] else 'bound_gap') if decision == 'unresolved' else None
    return {**base, 'state': 'complete', 'universal_bounds': list(map(w, universal)),
            'attained_bounds': list(map(w, attained)), 'exact_extrema': universal == attained,
            'nominal_delta': w(sum((Fraction(records[iid]['nominal_delta']) for iid in members), Fraction(0)) / size),
            'decision': decision, 'unresolved_reason': reason,
            'worlds': {direction: [{'image_id': iid, 'proof_key': records[iid]['witnesses'][direction]['proof_key']}
                                   for iid in members] for direction in ('lower', 'upper')}}


def bracket_step(lower, upper, row):
    lower, upper = Fraction(lower), Fraction(upper); midpoint = (lower + upper) / 2
    require(lower < upper and q(row['radius']) == midpoint, 'BRACKET', 'Wrong bisection midpoint')
    if row['state'] == 'analysis_incomplete':
        return lower, upper, 'analysis_incomplete'
    if q(row['universal_bounds'][0]) > 0:
        return midpoint, upper, 'supported'
    if q(row['attained_bounds'][0]) <= 0:
        return lower, midpoint, 'attained_excluding_world'
    return lower, upper, 'bound_gap'


def run(area, run_name='planar-01'):
    area = Path(area).resolve(); started = datetime.now(timezone.utc).isoformat(); tick = time.perf_counter()
    freeze_path = area / 'FREEZE.json'; freeze = read(freeze_path)
    require(freeze['radii'] == list(RADII) and freeze['maximum_regions_per_image_radius'] == MAX_REGIONS
            and freeze['maximum_depth'] == MAX_DEPTH and freeze['maximum_bisection_steps'] == 8
            and freeze['actual_planar_search_before_freeze'] is False, 'PLAN', 'Frozen plan differs')
    for binding in freeze['bindings']:
        require(file_digest(binding['path']) == binding['sha256'], 'FREEZE', 'Frozen bytes changed')
    comparison = Path(freeze['predecessor_comparison']); axes = Path(freeze['axis_run'])
    visible = read(comparison / 'inputs/visible.json'); images = {row['id']: row for row in visible['images']}
    require(len(visible['images']) == len(images) == 64 and len(visible['cases']) == 73, 'ALLOCATION', 'Wrong population')
    primary = [case for case in visible['cases'] if case['group'] == 'primary']
    require(len(primary) == 1 and primary[0]['images'] == list(images), 'ALLOCATION', 'Wrong primary membership')
    primary = primary[0]; output = area / 'runs' / run_name; output.mkdir(parents=True)
    answers, bases, prep_failures, caches, seeds = {}, {}, {}, {}, {}
    preparation_entries = []
    for iid, image in images.items():
        image_tick = time.perf_counter(); source = comparison / 'oracle' / (iid + '.json')
        try:
            answers[iid] = read(source)['answer']; bases[iid] = prepare(image, answers[iid]); caches[iid] = {}
            axis_record = read(axes / (iid + '.json'))
            require(axis_record['subject_sha256'] == bases[iid]['subject_sha256']
                    and axis_record['reference_sha256'] == bases[iid]['reference_sha256'], 'SEED', 'Axis source differs')
            seeds[iid] = axis_record
            value = {'image_id': iid, 'state': 'complete', 'basis': bases[iid],
                     'oracle_sha256': file_digest(source), 'axis_record_sha256': file_digest(axes / (iid + '.json')),
                     'seconds': time.perf_counter() - image_tick}
        except Exception as exc:
            value = {'image_id': iid, 'state': 'analysis_incomplete', 'error': type(exc).__name__ + ': ' + str(exc),
                     'seconds': time.perf_counter() - image_tick}; prep_failures[iid] = value
        path = 'basis-' + iid + '.json'; put(output / path, value)
        preparation_entries.append({'image_id': iid, 'path': path, 'sha256': file_digest(output / path)})
    by_radius, batches, entries = {}, {}, []

    def evaluate(radius):
        radius = Fraction(radius); key = radius_key(radius)
        if key in by_radius:
            return by_radius[key], True
        batch_tick = time.perf_counter(); records, batch_entries = {}, []
        for iid, image in images.items():
            image_tick = time.perf_counter()
            if iid in prep_failures:
                value = {**prep_failures[iid], 'radius': w(radius), 'inherited_preparation_failure': True}
            else:
                try:
                    prior = seeds[iid]['radii'][str(radius.numerator)] if radius.denominator == 1 and radius.numerator in RADII else None
                    axis_witnesses = [prior[direction] for direction in ('lower', 'upper')] if prior else None
                    value = search(image, answers[iid], bases[iid], radius, axis_witnesses=axis_witnesses, native_cache=caches[iid])
                except Exception as exc:
                    value = {'image_id': iid, 'radius': w(radius), 'state': 'analysis_incomplete',
                             'error': type(exc).__name__ + ': ' + str(exc), 'seconds': time.perf_counter() - image_tick}
            path = key + '-' + iid + '.json'; put(output / path, value); records[iid] = value
            entry = {'image_id': iid, 'radius': w(radius), 'path': path, 'sha256': file_digest(output / path)}
            batch_entries.append(entry); entries.append(entry)
        by_radius[key] = records
        batches[key] = {'radius': w(radius), 'records': batch_entries, 'seconds': time.perf_counter() - batch_tick}
        print(json.dumps({'radius': w(radius), 'complete_images': sum(v['state'] != 'analysis_incomplete' for v in records.values()),
                          'bound_gap_images': sum(v['state'] == 'bounded_with_gap' for v in records.values()),
                          'regions': sum(len(v.get('nodes', [])) for v in records.values()),
                          'seconds': batches[key]['seconds']}), flush=True)
        return records, False

    cases = []
    for radius in RADII:
        records, _ = evaluate(radius)
        cases.extend(case_row(case, records, radius) for case in visible['cases'])
    lower, upper = Fraction(0), Fraction(8); steps = []
    initial_low = case_row(primary, by_radius[radius_key(lower)], lower)
    initial_high = case_row(primary, by_radius[radius_key(upper)], upper)
    if initial_low['state'] != 'complete' or initial_high['state'] != 'complete':
        bracket_state = 'analysis_incomplete'
    elif q(initial_low['universal_bounds'][0]) <= 0 or q(initial_high['attained_bounds'][0]) > 0:
        bracket_state = 'initial_bracket_not_established'
    else:
        bracket_state = 'step_limit'
        for index in range(8):
            midpoint = (lower + upper) / 2; records, reused = evaluate(midpoint)
            row = case_row(primary, records, midpoint); before = [w(lower), w(upper)]
            lower, upper, outcome = bracket_step(lower, upper, row)
            steps.append({'step': index, 'before': before, 'midpoint': w(midpoint), 'reused_radius': reused,
                          'row': row, 'outcome': outcome, 'after': [w(lower), w(upper)]})
            if outcome in ('bound_gap', 'analysis_incomplete'):
                bracket_state = outcome; break
    bracket = {'state': bracket_state, 'initial': [w(Fraction(0)), w(Fraction(8))],
               'initial_rows': [initial_low, initial_high], 'steps': steps, 'final': [w(lower), w(upper)],
               'maximum_steps': 8, 'claim': 'Bracket between a universally supported radius and an attained excluding radius; not an exact infimum.'}
    totals = {'prepared_images': len(bases) - len(set(bases) & set(prep_failures)), 'image_radius_rows': len(entries),
              'complete_image_radius_rows': sum(v['state'] != 'analysis_incomplete' for rows in by_radius.values() for v in rows.values()),
              'bound_gap_image_radius_rows': sum(v['state'] == 'bounded_with_gap' for rows in by_radius.values() for v in rows.values()),
              'regions': sum(len(v.get('nodes', [])) for rows in by_radius.values() for v in rows.values()),
              'native_proofs': sum(len(cache) for cache in caches.values())}
    result = {'artifact_id': 'reiyah.translation-2d.results', 'version': '0.1.0', 'status': 'exploratory',
              'started_utc': started, 'finished_utc': datetime.now(timezone.utc).isoformat(), 'seconds': time.perf_counter() - tick,
              'freeze_sha256': file_digest(freeze_path), 'radii': list(RADII), 'allocated_images': 64,
              'allocated_cases': 73, 'allocated_case_radius_rows': 584, 'cases': cases, 'primary_bracket': bracket,
              'preparation_entries': preparation_entries, 'batches': batches, 'batch_order': list(batches), 'totals': totals,
              'human_seconds': None, 'economic_cost': None, 'model_inference_calls': 0, 'reserved_outcomes_accessed': 0,
              'independent_scientific_replication': False}
    put(output / 'RESULTS.json', result)
    print(json.dumps({'totals': totals, 'bracket_state': bracket_state, 'bracket': bracket['final'],
                      'seconds': result['seconds']}), flush=True)


if __name__ == '__main__':
    run(*sys.argv[1:])
