"""Cross-implementation agreement: the Engine's kernel and checker versus this package.

For every rebuilt census unit, emit a strict-schema Engine input (coordinates and classes
stripped; detection record digests are row-canonical SHA-256 of the qualified row, not the
Engine's byte-span digests), run the Engine producer and its separate certificate checker as
exported from main, and compare the exact bounds with this package's decision. Then apply the
split-level deletion witness of one pair through the Engine and confirm the split verdict.

Usage: python -B engine_agreement.py ENGINE_SRC_DIR UNIT_DIR CENSUS_RESULTS_JSON SPLIT_JSON OUT_JSON [--witness-pair base addition]
ENGINE_SRC_DIR must contain tools/perception_decision/*.py and research/perception-decision/0.1.0/input.schema.json
exactly as committed on the Engine commit named in the output.
"""
import hashlib
import json
import os
import sys
import time
from fractions import Fraction

engine_src = sys.argv[1]
sys.path.insert(0, engine_src)
from tools.perception_decision.kernel import produce      # noqa: E402
from tools.perception_decision.checker import check        # noqa: E402
from tools.perception_decision.contract import load, encoded  # noqa: E402

unit_dir, census_path, split_path, out_path = sys.argv[2:6]
witness_pair = None
if '--witness-pair' in sys.argv:
    i = sys.argv.index('--witness-pair')
    witness_pair = (sys.argv[i + 1], sys.argv[i + 2])


def strict(raw):
    def det(d):
        return {'id': d['id'], 'record_sha256': hashlib.sha256(
            json.dumps({'id': d['id'], 'class': d['class'], 'xy': d['xy']}, sort_keys=True).encode()).hexdigest()}
    return {'artifact_id': 'reiyah.perception-decision.input', 'version': '0.1.0',
            'comparison_id': raw['comparison_id'], 'input_scope': 'normalized_research_graphs',
            'evidence_kind': 'conditional_reference_graph',
            'assumptions': ['rebuilt census unit; record digests are row-canonical, not byte spans'],
            'cohort_id': raw['cohort_id'], 'loss': raw['loss'],
            'model': {'variables': [], 'clauses': [], 'feasible_assignment': []},
            'anchors': [{'id': a['id'], 'weight': a['weight'],
                         'base': {'state': 'observed', 'value': [det(d) for d in a['base']['value']]},
                         'additions': {'state': 'observed', 'value': [det(d) for d in a['additions']['value']]},
                         'reference': {'state': 'finite',
                                       'objects': [{'id': o['id'], 'when': []} for o in a['reference']['objects']],
                                       'edges': [{'detection': e['detection'], 'object': e['object'], 'when': []}
                                                 for e in a['reference']['edges']]}}
                        for a in raw['anchors']]}


def engine_bounds(case_dict):
    data = encoded(case_dict)
    digest = hashlib.sha256(data).hexdigest()
    tmp = os.path.join(os.environ.get('TMPDIR', '/tmp'), 'engine-agreement-%s.json' % digest[:16])
    with open(tmp, 'wb') as f:
        f.write(data)
    case = load(tmp, digest)
    payload = produce(case)
    check(case, payload)
    os.unlink(tmp)
    r = payload['result']
    return (Fraction(int(r['bounds']['lower']['numerator']), int(r['bounds']['lower']['denominator'])),
            Fraction(int(r['bounds']['upper']['numerator']), int(r['bounds']['upper']['denominator'])),
            r['decision']['improvement_criterion'], r['execution_status'], r['enclosure_kind'])


started = time.perf_counter()
census = {r['unit']: r for r in json.load(open(census_path))['rows']}
files = sorted(f for f in os.listdir(unit_dir) if f.endswith('.json') and f != 'INDEX.json')
agree = 0
disagree = []
kinds = {}
for f in files:
    raw = json.load(open(os.path.join(unit_dir, f)))
    lo, hi, crit, status, kind = engine_bounds(strict(raw))
    kinds[kind] = kinds.get(kind, 0) + 1
    mine = Fraction(census[raw['comparison_id']]['delta'])
    mine_crit = census[raw['comparison_id']]['criterion']
    ok = (lo == hi == mine) and (crit == ('supported' if mine_crit == 'supported' else 'excluded'))
    if ok:
        agree += 1
    else:
        disagree.append({'unit': raw['comparison_id'], 'engine': [str(lo), str(hi), crit, status, kind], 'here': [str(mine), mine_crit]})
print('units', len(files), 'agree', agree, 'disagree', len(disagree), round(time.perf_counter() - started, 1), 's', flush=True)

witness = None
if witness_pair:
    split = json.load(open(split_path))
    key = '%s -> +%s' % witness_pair
    row = split[key]
    n = row['scenes']
    # rebuild the split-level witness: largest per-deletion steps first from the additive pools
    from sufficiency import Case
    steps = []
    for f in files:
        raw = json.load(open(os.path.join(unit_dir, f)))
        if not f.startswith('%s__%s__' % witness_pair):
            continue
        case = Case(raw)
        for a in case.anchors:
            g = a.gain()
            base_set = set(a.base)
            for o in a.objects_with_edge:
                if any(d in base_set for d in a.object_edges[o]):
                    continue
                if g - a.gain(frozenset([o])) == 1:
                    steps.append((Fraction(2, len(case.anchors) * n), f, a.id, o))
    steps.sort(key=lambda t: -t[0])
    k = row['deletions_to_overturn']
    chosen = steps[:k]
    by_file = {}
    for _, f, aid, o in chosen:
        by_file.setdefault(f, set()).add((aid, o))
    total_before = Fraction(0)
    total_after = Fraction(0)
    for f in files:
        if not f.startswith('%s__%s__' % witness_pair):
            continue
        raw = json.load(open(os.path.join(unit_dir, f)))
        lo, hi, _, _, _ = engine_bounds(strict(raw))
        total_before += lo / n
        gone = by_file.get(f, set())
        if gone:
            for a in raw['anchors']:
                g = {o for aid, o in gone if aid == a['id']}
                a['reference']['objects'] = [o for o in a['reference']['objects'] if o['id'] not in g]
                a['reference']['edges'] = [e for e in a['reference']['edges'] if e['object'] not in g]
        lo2, hi2, _, _, _ = engine_bounds(strict(raw))
        total_after += lo2 / n
    witness = {'pair': key, 'deletions': k, 'split_delta_before_engine': str(total_before),
               'split_delta_after_engine': str(total_after), 'tolerance': '1/10',
               'overturned_by_engine': total_after <= Fraction(1, 10),
               'split_delta_before_package': row['split_delta']}
    print('witness', witness, flush=True)

json.dump({'engine_units': len(files), 'agree': agree, 'disagree': disagree[:20], 'disagree_count': len(disagree),
           'enclosure_kinds': kinds, 'witness': witness, 'seconds': round(time.perf_counter() - started, 1),
           'note': 'Engine kernel and checker imported from the exported main sources; record digests row-canonical'},
          open(out_path, 'w'), indent=1)
