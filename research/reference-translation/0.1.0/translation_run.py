"""Run the frozen localized-translation follow-up, retaining every allocation."""
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys
import time

from translation_search import (RADII, checked_extrema, decision, digest, enumerate_image, minimum_affected,
                                primary_critical_radius, q, require, w)


def file_digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def put(path, value):
    with Path(path).open('x') as output:
        json.dump(value, output, sort_keys=True, separators=(',', ':'), allow_nan=False)
        output.write('\n')


def case_rows(visible, records, failures):
    output = []
    for case in visible['cases']:
        members = case['images']
        failed = [iid for iid in members if iid in failures]
        for radius in RADII:
            base = {'case_id': case['id'], 'group': case['group'], 'radius': radius,
                    'allocated_images': len(members), 'analysis_failed_images': failed}
            if failed:
                output.append({**base, 'state': 'analysis_incomplete', 'bounds': None,
                               'decision': None, 'nominal_delta': None, 'minimum_affected': None})
                continue
            nominal = sum((q(records[iid]['nominal']['delta']) for iid in members), Fraction(0))
            lower = sum((q(records[iid]['radii'][str(radius)]['lower']['delta']) for iid in members), Fraction(0))
            upper = sum((q(records[iid]['radii'][str(radius)]['upper']['delta']) for iid in members), Fraction(0))
            downward = {iid: q(records[iid]['nominal']['delta']) - q(records[iid]['radii'][str(radius)]['lower']['delta'])
                        for iid in members}
            output.append({**base, 'state': 'complete', 'bounds': [w(lower / len(members)), w(upper / len(members))],
                           'decision': decision((lower, upper)), 'nominal_delta': w(nominal / len(members)),
                           'minimum_affected': minimum_affected(nominal, downward),
                           'worlds': {direction: [{'image_id': iid,
                                'proof_key': records[iid]['radii'][str(radius)][direction]['proof_key']}
                                for iid in members] for direction in ('lower', 'upper')}})
    return output


def run(area, run_name='translation-01'):
    area = Path(area).resolve(); started = datetime.now(timezone.utc).isoformat(); tick = time.perf_counter()
    freeze_path = area / 'FREEZE.json'; freeze = read(freeze_path)
    require(freeze['radii'] == list(RADII), 'PLAN', 'Frozen radii differ')
    require(not freeze['actual_translation_search_before_freeze'], 'PLAN', 'New search was not frozen before execution')
    for binding in freeze['bindings']:
        require(file_digest(binding['path']) == binding['sha256'], 'FREEZE', 'Frozen input or implementation changed')
    comparison = Path(freeze['predecessor_comparison'])
    visible = read(comparison / 'inputs/visible.json')
    require(len(visible['images']) == 64 and len(visible['cases']) == 73, 'ALLOCATION', 'Frozen population differs')
    require(len({image['id'] for image in visible['images']}) == 64, 'ALLOCATION', 'Repeated image')
    output = area / 'runs' / run_name; output.mkdir(parents=True)
    records, failures, answers = {}, {}, {}
    images = {image['id']: image for image in visible['images']}
    for image in visible['images']:
        iid = image['id']; image_tick = time.perf_counter()
        try:
            source = comparison / 'oracle' / (iid + '.json'); answer = read(source)['answer']; answers[iid] = answer
            value = enumerate_image(image, answer); proofs = {}
            value['radii'] = {str(radius): checked_extrema(image, answer, value, radius, proofs) for radius in RADII}
            value['proofs'] = proofs; value['oracle_file_sha256'] = file_digest(source)
            value['state'] = 'complete'; value['image_elapsed_seconds'] = time.perf_counter() - image_tick
            records[iid] = value
            put(output / (iid + '.json'), value)
            print(json.dumps({'image': iid, 'state': 'complete', 'cells': value['cells'],
                              'matching_states': value['matching_states'], 'proofs': len(proofs)}), flush=True)
        except Exception as exc:
            failure = {'image_id': iid, 'state': 'analysis_incomplete',
                       'error': type(exc).__name__ + ': ' + str(exc),
                       'seconds': time.perf_counter() - image_tick}
            failures[iid] = failure; put(output / (iid + '.json'), failure)
            print(json.dumps(failure), flush=True)
    cases = case_rows(visible, records, failures)
    critical = {'state': 'analysis_incomplete', 'failed_images': sorted(failures)} if failures else primary_critical_radius(records)
    critical_rows = []
    if not failures and critical['radius_infimum'] is not None:
        critical_tick = time.perf_counter()
        infimum, witness_radius = q(critical['radius_infimum']), q(critical['witness_radius'])
        downward = {}; nominal = Fraction(0)
        for iid, image in images.items():
            proofs = {}
            at = checked_extrema(image, answers[iid], records[iid], infimum, proofs)
            witness = checked_extrema(image, answers[iid], records[iid], witness_radius, proofs)
            nominal += q(records[iid]['nominal']['delta'])
            downward[iid] = q(records[iid]['nominal']['delta']) - q(witness['lower']['delta'])
            value = {'image_id': iid, 'infimum': w(infimum), 'witness_radius': w(witness_radius),
                     'at_infimum': at, 'at_witness_radius': witness, 'proofs': proofs}
            path = 'critical-' + iid + '.json'; put(output / path, value)
            critical_rows.append({'image_id': iid, 'path': path, 'sha256': file_digest(output / path)})
        critical['minimum_affected_at_witness_radius'] = minimum_affected(nominal, downward)
        critical['extra_witness_seconds'] = time.perf_counter() - critical_tick
    require(len(cases) == 73 * len(RADII), 'ALLOCATION', 'Missing assigned case/radius row')
    result = {'artifact_id': 'reiyah.reference-translation.results', 'version': '0.1.0', 'status': 'exploratory',
              'started_utc': started, 'finished_utc': datetime.now(timezone.utc).isoformat(),
              'seconds': time.perf_counter() - tick, 'freeze_sha256': file_digest(freeze_path),
              'allocated_images': 64, 'allocated_cases': 73, 'allocated_case_radius_rows': len(cases),
              'radii': list(RADII), 'cases': cases, 'failures': failures, 'primary_critical_radius': critical,
              'critical_image_records': critical_rows,
              'image_records': [{'image_id': iid, 'path': iid + '.json', 'sha256': file_digest(output / (iid + '.json'))}
                                for iid in images],
              'totals': {key: sum(value[key] for value in records.values()) for key in ['axes', 'cells', 'matching_states']},
              'native_proofs_fixed_radii': sum(len(value['proofs']) for value in records.values()),
              'human_seconds': None, 'economic_cost': None, 'model_inference_calls': 0,
              'reserved_outcomes_accessed': 0, 'independent_scientific_replication': False,
              'scope': 'Exact extrema for the declared one-reference one-axis family; no empirical error rate.'}
    put(output / 'RESULTS.json', result)
    print(json.dumps({'rows': len(cases), 'failures': list(failures), 'totals': result['totals'],
                      'critical_radius': critical, 'seconds': result['seconds']}), flush=True)


if __name__ == '__main__':
    run(*sys.argv[1:])
