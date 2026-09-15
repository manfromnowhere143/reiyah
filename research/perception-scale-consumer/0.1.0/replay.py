"""Replay the retained small consumer counterexamples, without repairing Fable."""
from argparse import ArgumentParser
from copy import deepcopy
from fractions import Fraction
import hashlib
import importlib.util
from itertools import combinations, product
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from tools.perception_decision import checker, contract, kernel


def exhaustive(left, objects, edges):
    """Enumerate partial injections; no augmenting-path matcher is shared."""
    assert len(left) <= 2 and len(objects) <= 3
    best = 0
    for assignment in product([None] + objects, repeat=len(left)):
        used = [o for o in assignment if o is not None]
        if len(used) != len(set(used)):
            continue
        if all(o is None or (d, o) in edges for d, o in zip(left, assignment)):
            best = max(best, len(used))
    return best


def run(module):
    expected = json.loads((HERE / 'result.json').read_text())
    module_bytes = module.read_bytes()
    assert hashlib.sha256(module_bytes).hexdigest() == expected['source']['module_sha256']
    spec = importlib.util.spec_from_file_location('selected_fable_scale', module)
    fable = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fable)
    case = json.loads((HERE / 'case.json').read_text())
    pose = {'translation': [0, 0, 0], 'rotation': [1, 0, 0, 0]}

    def raw(x, score=0.9):
        return {'detection_name': 'car', 'detection_score': score, 'translation': [x, 0, 0]}

    base = fable.qualify([raw(0)], pose)
    added = fable.suppress(base, fable.qualify([raw(3)], pose))
    assert len(base) == len(added) == 1
    objects = [{'c': 'car', 'x': x, 'y': 0} for x in (1.1, 1.5, 1.9)]
    frame = fable.Frame(objects, base, added)
    assert frame.adj_all == {0: [0, 1, 2], 1: [0, 1, 2]}
    rows = []
    for size in range(4):
        for dropped in combinations(range(3), size):
            changed = deepcopy(case)
            removed = {'o' + str(i) for i in dropped}
            a = changed['anchors'][0]
            a['reference']['objects'] = [o for o in a['reference']['objects'] if o['id'] not in removed]
            a['reference']['edges'] = [e for e in a['reference']['edges'] if e['object'] not in removed]
            names = [o['id'] for o in a['reference']['objects']]
            edges = {(e['detection'], e['object']) for e in a['reference']['edges']}
            tp_base = exhaustive(['base-1'], names, edges)
            tp_all = exhaustive(['base-1', 'added-1'], names, edges)
            direct = 2 * (tp_all - tp_base) - 1
            contract.validate(changed)
            result = checker.check(changed, kernel.produce(changed))
            assert result['bounds'] == {'lower': contract.wire(Fraction(direct)), 'upper': contract.wire(Fraction(direct))}
            assert fable.decide([fable.Frame([objects[i] for i in range(3) if i not in dropped], base, added)]) == direct
            rows.append({'removed': list(dropped), 'delta': direct})
    assert min(len(r['removed']) for r in rows if Fraction(r['delta']) <= Fraction(1, 10)) == 2
    assert fable.unit([frame]) == expected['joint_deletion']['fable_return']

    good = fable.Frame([{'c': 'car', 'x': 3, 'y': 0}], base, added)
    assert fable.unit([good, None]) == fable.unit([good]) == expected['missing_frame']['fable_return']
    missing = deepcopy(case)
    first = missing['anchors'][0]
    first['weight'] = contract.wire(Fraction(1, 2))
    second = deepcopy(first)
    second['id'] = 'missing-anchor'
    for key in ('base', 'additions'):
        second[key] = {'state': 'missing', 'reason': 'declared frame not supplied'}
    second['reference'] = {'state': 'open', 'reason': 'reference not supplied'}
    missing['anchors'].append(second)
    contract.validate(missing)
    missing_result = checker.check(missing, kernel.produce(missing))
    assert missing_result['execution_status'] == 'input_blocked' and missing_result['bounds'] is None
    for row in (raw(3, float('nan')), raw(3, float('inf')), raw(3, True), raw(float('nan'))):
        assert len(fable.qualify([row], pose)) == 1
    assert not fable.qualify([raw(3, .29)], pose)
    assert not fable.qualify([raw(51)], pose)
    return {'status': 'reproduced', 'source_module_sha256': expected['source']['module_sha256'],
            'subsets': rows, 'floor': 1, 'minimum': 2, 'missing_frame_silently_dropped': True,
            'malformed_rows_retained': 4, 'engine_missing_input': 'input_blocked',
            'scope': 'synthetic consumer controls; no actual pilot witness rechecked'}


if __name__ == '__main__':
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('--fable-module', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(run(args.fable_module), sort_keys=True, indent=2))
