"""Retrospective floors and adversarial reference worlds for the frozen run."""
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys
import time

from admission import digest, encoded, require
from certificate_floor import minimum_certificate
from compare_math import ARMS, FAMILIES, decision, interval, linked, measure, q, w, wire_interval
from geometric_worlds import alter, search_image


def file_digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def put(path, value):
    with Path(path).open('xb') as handle:
        handle.write(encoded(value))


def compose(members, records, family, direction):
    """Choose checked component worlds within the case's declared edit budget."""
    require(family in ('one_edit_per_image', 'one_edit_global') and direction in ('lower', 'upper'),
            'FAMILY', 'Adverse composition requires a declared residual family')
    nominal = {image['id']: q(records[image['id']]['nominal']['nominal']['delta']) for image in members}
    effects = []
    for image in members:
        record = records[image['id']]
        if record['search_state'] == 'complete':
            witness = record['search']['witnesses'][direction]
            change = q(witness['measurement']['delta']) - nominal[image['id']]
            if change != 0:
                require((change < 0) == (direction == 'lower'), 'WORLD', 'Extremum moved in the wrong direction')
                effects.append((image['id'], change))
    if family == 'one_edit_global' and effects:
        effects = [min(effects, key=lambda item: (item[1], item[0])) if direction == 'lower'
                   else max(effects, key=lambda item: (item[1], item[0]))]
    total = sum(nominal.values()) + sum(change for _, change in effects)
    return {'direction': direction, 'delta': w(total / len(members)),
        'decision': 'supported' if total > 0 else 'excluded',
        'edited_images': [{'image_id': iid, 'witness': direction, 'delta_change': w(change)} for iid, change in effects],
        'complete_case_membership': [image['id'] for image in members],
        'remaining_images_use_nominal_reference': True}


def minimal_primary_edits(members, records):
    """At most one edit per image; universal lower and constructive upper counts."""
    nominal = sum(q(records[image['id']]['nominal']['nominal']['delta']) for image in members)
    if nominal <= 0:
        return {'nominal_total_delta': w(nominal), 'lower_bound': 0, 'upper_bound': 0, 'exact': True,
                'witness': [], 'reason': 'Nominal strict improvement is already excluded.'}
    sound, achieved = [], []
    for image in members:
        record = records[image['id']]; center = q(record['nominal']['nominal']['delta'])
        sound.append((center - q(record['nominal']['edit_bounds'][0]), image['id']))
        if record['search_state'] == 'complete':
            achieved.append((center - q(record['search']['witnesses']['lower']['measurement']['delta']), image['id']))
    def reach(values):
        total = Fraction(0); chosen = []
        for improvement, iid in sorted(values, key=lambda item: (-item[0], item[1])):
            require(improvement >= 0, 'BOUND', 'Downward change cannot be negative')
            if improvement == 0:
                continue
            total += improvement; chosen.append({'image_id': iid, 'downward_change': w(improvement), 'witness': 'lower'})
            if total >= nominal:
                return len(chosen), chosen, nominal - total
        return None, None, None
    lower, _, _ = reach(sound); upper, edits, total = reach(achieved)
    require(upper is None or (lower is not None and lower <= upper), 'BOUND', 'Achieved edit count violates universal lower bound')
    return {'nominal_total_delta': w(nominal), 'lower_bound': lower, 'upper_bound': upper,
        'exact': lower is not None and lower == upper, 'witness': edits,
        'witness_total_delta': None if total is None else w(total),
        'scope': 'At most one arbitrary eligible rectangle edit per affected image; not an empirical error rate.'}


def case_rows(visible, records, actual):
    by_id = {image['id']: image for image in visible['images']}
    measurements = {iid: record['nominal'] for iid, record in records.items() if 'nominal' in record}
    rows = []
    for case in visible['cases']:
        members = [by_id[iid] for iid in case['images']]
        for family in FAMILIES:
            bounds = interval(members, measurements, family); outcome = decision(bounds)
            floor = minimum_certificate(members, measurements, family)
            row = {'case_id': case['id'], 'group': case['group'], 'family': family, 'decision': outcome,
                'bounds': wire_interval(bounds), 'certificate_floor': floor,
                'actual_queries': {arm: actual[(arm, family, case['id'])]['queries'] for arm in ARMS}}
            for arm in ARMS:
                scored = actual[(arm, family, case['id'])]
                if scored['decision'] in ('supported', 'excluded'):
                    require(scored['decision'] == outcome and floor['minimum_queries'] <= scored['queries'],
                            'BOUND', 'Post-analysis contradicts a scored certified decision or query floor')
            if outcome != 'input_blocked':
                nominal_total = sum(q(records[image['id']]['nominal']['nominal']['delta']) for image in members)
                nominal_decision = 'supported' if nominal_total > 0 else 'excluded'
                row['nominal_delta'] = w(nominal_total / len(members)); row['nominal_decision'] = nominal_decision
                if family != 'exact_projection':
                    worlds = {direction: compose(members, records, family, direction) for direction in ('lower', 'upper')}
                    row['worlds'] = worlds
                    row['opposite_decisions_witnessed'] = {world['decision'] for world in worlds.values()} == {'supported', 'excluded'}
                    row['search_incomplete_images'] = [image['id'] for image in members if records[image['id']]['search_state'] != 'complete']
                    row['unresolved_kind'] = ('admitted_opposite_decision_worlds' if row['opposite_decisions_witnessed'] else
                        'search_incomplete' if row['search_incomplete_images'] else 'remaining_bound_geometry_gap') if outcome == 'unresolved' else None
                    for world in worlds.values():
                        require(bounds[0] <= q(world['delta']) <= bounds[1], 'BOUND', 'Composed world violates the full-case envelope')
            rows.append(row)
    return rows


def run(area, run_name='analysis-01'):
    area = Path(area).resolve(); started, tick = datetime.now(timezone.utc).isoformat(), time.perf_counter()
    freeze_path = area / 'ANALYSIS_FREEZE.json'; freeze = json.loads(freeze_path.read_text())
    for binding in freeze['bindings']:
        require(file_digest(binding['path']) == binding['sha256'], 'FREEZE', 'Analysis input or implementation changed')
    output = area / 'runs' / run_name; output.mkdir()
    visible = json.loads((area / 'inputs/visible.json').read_text())
    scored = json.loads((area / 'runs/assay-02/RESULTS.json').read_text())
    actual = {(entry['result']['arm'], entry['result']['family'], entry['result']['case_id']): entry['result'] for entry in scored['rows']}
    records, access, failures = {}, [], []
    for image in visible['images']:
        iid = image['id']; image_tick = time.perf_counter()
        if not linked(image):
            record = {'image_id': iid, 'search_state': 'input_blocked'}
        else:
            path = area / 'oracle' / (iid + '.json'); answer = json.loads(path.read_text())
            require(answer['subject_sha256'] == digest(image), 'SOURCE', 'Oracle applicability changed')
            access.append({'image_id': iid, 'source_file_sha256': file_digest(path),
                'accessed_utc': datetime.now(timezone.utc).isoformat(), 'purpose': 'retrospective_full_answer_analysis',
                'human_seconds': None})
            try:
                search = search_image(image, answer['answer'])
                record = {'image_id': iid, 'search_state': 'complete', 'nominal': search['nominal'], 'search': search}
            except Exception as exc:
                failure = type(exc).__name__ + ': ' + str(exc); failures.append({'image_id': iid, 'error': failure})
                # Preserve the complete allocation and retain usable nominal
                # bounds if the bounded geometric search alone failed.
                nominal = measure(image, answer['answer'], 'one_edit_per_image', 'conventional')
                record = {'image_id': iid, 'search_state': 'incomplete', 'error': failure, 'nominal': nominal}
        record['seconds'] = time.perf_counter() - image_tick
        put(output / (iid + '.json'), record); records[iid] = record
        print(json.dumps({'image_id': iid, 'state': record['search_state'], 'seconds': record['seconds'],
                          'candidates': record.get('search', {}).get('candidate_rectangles')}), flush=True)
    put(output / 'ANSWER_ACCESS.json', access)
    cases = case_rows(visible, records, actual)
    primary = next(case for case in visible['cases'] if case['group'] == 'primary')
    primary_images = [image for image in visible['images'] if image['id'] in primary['images']]
    sensitivity = minimal_primary_edits(primary_images, records) if all(linked(image) for image in primary_images) else None
    totals = {key: sum(record.get('search', {}).get(key, 0) for record in records.values())
              for key in ('candidate_rectangles', 'candidate_bases', 'neighborhoods', 'base_candidate_evaluations')}
    result = {'artifact_id': 'reiyah.public-predictions.full-answer-results', 'version': '0.1.0',
        'started_utc': started, 'finished_utc': datetime.now(timezone.utc).isoformat(), 'seconds': time.perf_counter() - tick,
        'analysis_freeze_sha256': file_digest(freeze_path), 'scored_results_sha256': file_digest(area / 'runs/assay-02/RESULTS.json'),
        'allocated_images': len(visible['images']), 'case_family_rows': len(cases), 'answer_files_read': len(access),
        'image_records': [{'image_id': iid, 'path': iid + '.json', 'sha256': file_digest(output / (iid + '.json'))} for iid in records],
        'search_failures': failures, 'search_totals': totals, 'cases': cases, 'primary_edit_sensitivity': sensitivity,
        'unresolved_kinds': dict(Counter(row.get('unresolved_kind') for row in cases if row['decision'] == 'unresolved')),
        'human_seconds': None, 'economic_cost': None, 'all_four_dimensional_rectangles_searched': False}
    put(output / 'RESULTS.json', result)
    print(json.dumps({'rows': len(cases), 'search_totals': totals, 'search_failures': failures,
                      'unresolved_kinds': result['unresolved_kinds'], 'seconds': result['seconds']}), flush=True)


if __name__ == '__main__':
    run(*sys.argv[1:])
