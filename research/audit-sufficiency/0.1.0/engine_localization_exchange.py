"""Verify this lane's geometric counterexamples through the Engine's localization command.

For each realized case in a localization census result, build the Engine's input
(output_a = base, output_b = base plus retained additions), the Engine's localization request
(decimal-rational coordinates, one radius per reference), and a witness file from the retained
displacement vectors, then run the Engine's `localization` command with the witness as the
candidate. The Engine checks every shift against its radius, recomputes the complete corrected
graph and loss, and reports `refuted_by_displacement` when the criterion is overturned.

Usage: python -B engine_localization_exchange.py ENGINE_SRC_DIR PYTHON UNIT_DIR LOCALIZATION_CENSUS_JSON WORK_DIR OUT_JSON [--limit N]
Record digests are row-canonical (stated); reference_context_sha256 binds the request to the input.
"""
import hashlib
import json
import os
import subprocess
import sys
import time
from fractions import Fraction

engine_src, python, unit_dir, census_path, work, out_path = sys.argv[1:7]
limit = int(sys.argv[sys.argv.index('--limit') + 1]) if '--limit' in sys.argv else None
os.makedirs(work, exist_ok=True)


def rat(v):
    f = Fraction(v) if isinstance(v, str) else Fraction(repr(float(v)))
    return {'numerator': str(f.numerator), 'denominator': str(f.denominator)}


def sha(b):
    return hashlib.sha256(b).hexdigest()


def digest_record(d):
    return sha(json.dumps({'id': d['id'], 'class': d['class'], 'xy': d['xy']}, sort_keys=True).encode())


def build(raw, eps):
    anchors_in, anchors_req = [], []
    for a in raw['anchors']:
        base = [{'id': d['id'], 'record_sha256': digest_record(d)} for d in a['base']['value']]
        adds = [{'id': d['id'], 'record_sha256': digest_record(d)} for d in a['additions']['value']]
        anchors_in.append({'id': a['id'], 'weight': a['weight'],
                           'output_a': {'state': 'observed', 'value': base},
                           'output_b': {'state': 'observed', 'value': base + adds},
                           'reference': {'state': 'finite',
                                         'objects': [{'id': o['id'], 'when': []} for o in a['reference']['objects']],
                                         'edges': [{'detection': e['detection'], 'object': e['object'], 'when': []}
                                                   for e in a['reference']['edges']]}})
        anchors_req.append({'id': a['id'],
                            'detections': [{'id': d['id'], 'record_sha256': digest_record(d), 'class': d['class'],
                                            'xy': [rat(d['xy'][0]), rat(d['xy'][1])]}
                                           for d in a['base']['value'] + a['additions']['value']],
                            'references': [{'id': o['id'], 'record_sha256': digest_record(o), 'class': o['class'],
                                            'xy': [rat(o['xy'][0]), rat(o['xy'][1])], 'radius': rat(eps)}
                                           for o in a['reference']['objects']]})
    context = sha(json.dumps(anchors_req, sort_keys=True).encode())
    case = {'artifact_id': 'reiyah.perception-revision.input', 'version': '0.1.0',
            'comparison_id': raw['comparison_id'], 'input_scope': 'normalized_research_graphs',
            'evidence_kind': 'conditional_reference_graph',
            'assumptions': ['rebuilt census unit; output_b = base plus retained additions; record digests row-canonical'],
            'cohort_id': raw['cohort_id'], 'loss': raw['loss'],
            'model': {'variables': [], 'clauses': [], 'feasible_assignment': []},
            'reference_context_sha256': context, 'anchors': anchors_in}
    request = {'artifact_id': 'reiyah.perception-revision.localization-request', 'version': '0.1.0',
               'comparison_id': raw['comparison_id'], 'coordinate_system': 'shared_planar_metres',
               'family': 'independent_closed_reference_balls', 'matching_rule': 'strict_same_class_center_distance',
               'position_basis': 'benchmark_reference', 'reference_context_sha256': context,
               'threshold': rat('2'), 'anchors': anchors_req}
    return case, request


def engine(case, request, witness, tag):
    paths = {}
    for name, obj in (('input', case), ('request', request), ('witness', witness)):
        if obj is None:
            continue
        data = json.dumps(obj, sort_keys=True, separators=(',', ':')).encode()
        p = os.path.join(work, '%s.%s.json' % (tag, name))
        open(p, 'wb').write(data)
        paths[name] = (p, sha(data))
    out = os.path.join(work, '%s.packet.json' % tag)
    if os.path.exists(out):
        os.unlink(out)
    cmd = [python, '-B', '-m', 'tools.perception_revision', 'localization',
           '--input', paths['input'][0], '--input-sha256', paths['input'][1],
           '--request', paths['request'][0], '--request-sha256', paths['request'][1],
           '--output', out]
    if 'witness' in paths:
        cmd += ['--candidate', paths['witness'][0], '--candidate-sha256', paths['witness'][1]]
    env = {k: v for k, v in os.environ.items() if k != 'PYTHONPATH'}
    r = subprocess.run(cmd, cwd=engine_src, capture_output=True, text=True, env=env, timeout=600)
    try:
        answer = json.loads(r.stdout.strip().splitlines()[-1])
    except Exception:
        answer = {'error': (r.stdout + r.stderr)[-800:]}
    return answer


started = time.perf_counter()
census = json.load(open(census_path))
rows = []
count = 0
for r in census['rows']:
    for eps, e in r['by_epsilon'].items():
        if e.get('status') != 'insufficient_realized' or not e.get('_displacements'):
            continue
        if limit and count >= limit:
            break
        count += 1
        raw = json.load(open(os.path.join(unit_dir, r['unit'] + '.json')))
        case, request = build(raw, eps)
        witness = {'artifact_id': 'reiyah.perception-revision.localization-witness', 'version': '0.1.0',
                   'displacements': [{'anchor': d['anchor'], 'object': d['object'],
                                      'shift': [rat(d['shift'][0]), rat(d['shift'][1])]} for d in e['_displacements']]}
        tag = '%s-e%s' % (r['unit'], eps)
        answer = engine(case, request, witness, tag)
        res = answer.get('result', {})
        rows.append({'unit': r['unit'], 'epsilon': eps, 'displacements': len(witness['displacements']),
                     'engine_robustness': res.get('robustness'), 'engine_witness_value': res.get('witness_value'),
                     'engine_execution': res.get('execution_status'), 'error': answer.get('error'),
                     'lane_achieved_delta': e.get('achieved')})
        print(tag, res.get('robustness'), res.get('witness_value'), answer.get('error', '')[:120] if answer.get('error') else '', flush=True)
summary = {'cases': len(rows),
           'refuted_by_displacement': sum(1 for x in rows if x['engine_robustness'] == 'refuted_by_displacement'),
           'other': [x for x in rows if x['engine_robustness'] != 'refuted_by_displacement'][:20],
           'seconds': round(time.perf_counter() - started, 1), 'rows': rows}
json.dump(summary, open(out_path, 'w'), indent=1)
print(json.dumps({k: v for k, v in summary.items() if k != 'rows'}, indent=1)[:2000])
