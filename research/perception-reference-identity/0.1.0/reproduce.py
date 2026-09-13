"""Replay selected synthetic naming and optional geometry controls, entirely offline.

This is a bounded reproduction, not an admission interface or a human study.
The exact previous compiler is supplied from the named Git commit; every other
production dependency is shared. No files are created by this program.
"""
import argparse
from copy import deepcopy
from fractions import Fraction
import hashlib
import importlib.util
from pathlib import Path
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tests.test_perception_reference import digest, independent_matching, inputs, object_at, world
from tests.test_perception_reference_sharing import geometry_budget_worlds
from tools import perception_reference
from tools.perception_decision import checker, contract, kernel

BASELINE_SHA256 = 'acb2fe1e87e08aeb0c448ffab55322f233786e20a4810422bc209be434649e69'


def fixture(renamed):
    args, sources = inputs(), {}
    for wi in range(64):
        objects = []
        for oi, x in enumerate((0, 3, 30)):
            name = ('world-'+str(wi)+'-' if renamed else '')+'object-'+str(oi)
            obj = object_at(name, x, members=['proposal-'+str(oi)])
            body = {'artifact_id': 'reiyah.synthetic.reference-source', 'version': '0.1.0',
                    'world_id': 'world-'+str(wi),
                    'object': {k: v for k, v in obj.items() if k != 'record_sha256'}}
            obj['record_sha256'] = digest(body)
            sources[obj['record_sha256']] = body
            objects.append(obj)
        entry = world('world-'+str(wi), [objects])
        entry['basis_sha256'] = digest({'synthetic_world': {k: v for k, v in entry.items() if k != 'basis_sha256'}})
        args[0]['worlds'].append(entry)
    return args, sources


def evaluate(module, args):
    before = digest(args)
    compiled, receipt = module.compile_model(*args)
    packet = kernel.produce(compiled)
    with patch.object(kernel, '_matching_certificate', side_effect=AssertionError('Producer called by checker')):
        checker.check(compiled, packet)
    assert digest(args) == before
    summary = {'input_sha256': before,
        'compiler_sha256': hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest(),
        'output_sha256': {k: digest(v) for k, v in [('compiled', compiled), ('compilation', receipt), ('packet', packet)]},
        'states': [a['reference']['state'] for a in compiled['anchors']],
        'graph_nodes': [len(a['reference'].get('objects', [])) for a in compiled['anchors']],
        'geometry_comparisons': receipt['geometry_comparisons_budgeted'],
        'mapping_rows': len(receipt['object_mapping']), 'worlds': len(receipt['world_encodings']),
        'capacity': list(kernel._capacity(compiled)),
        'bounds': [str(contract.rational(packet['result']['bounds'][s])) for s in ('lower', 'upper')]}
    return summary, receipt


def check_originals(args, sources, receipt):
    # Direct original-coordinate partial injections, independent of compiled
    # graphs and both core matching implementations. These are tiny cases only.
    normal = args[2][0]
    positions = {r['detection']['id']: (r['record']['class'],
        tuple(contract.rational(q) for q in r['record']['xy'])) for r in normal['qualified_records']}
    anchor = args[1]['anchors'][0]
    base = [positions[d['id']] for d in anchor['base']['value']]
    added = [positions[d['id']] for d in anchor['additions']['value']]
    fn, fp = [contract.rational(args[1]['loss'][k]) for k in ('false_negative', 'false_positive')]
    for w in args[0]['worlds']:
        objects = [(o['class'], tuple(contract.rational(q) for q in o['xy'])) for o in w['anchors'][0]['objects']]
        m0, m1 = independent_matching(base, objects), independent_matching(base+added, objects)
        assert (m0, m1) == (1, 2)
        loss0 = fn*(len(objects)-m0)+fp*(len(base)-m0)
        loss1 = fn*(len(objects)-m1)+fp*(len(base+added)-m1)
        assert loss0-loss1 == Fraction(1)
    for row in receipt['object_mapping']:
        body = sources[row['record_sha256']]
        assert digest(body) == row['record_sha256']
        assert (body['world_id'], body['object']['id'], body['object']['members']) == (
            row['world_id'], row['object_id'], row['members'])
    assert len(receipt['object_mapping']) == len(sources) == 192


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline-compiler', required=True, type=Path)
    parser.add_argument('--geometry-control', action='store_true', help='Also replay the actual 2,000,000-pair cap control')
    opts = parser.parse_args()
    raw = opts.baseline_compiler.read_bytes()
    if hashlib.sha256(raw).hexdigest() != BASELINE_SHA256:
        parser.error('Baseline compiler bytes differ from selected 61d290b compiler')
    spec = importlib.util.spec_from_file_location('tools.reference_identity_baseline', opts.baseline_compiler)
    baseline = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(baseline)
    results, normalized = {}, []
    for label, renamed in [('stable', False), ('renamed', True)]:
        args, sources = fixture(renamed)
        expected = {'stable': '63571b672fb8ddca31598c44089d66bcd3777dfd4270aba91ae2469fa95ef4a6',
                    'renamed': 'da349ed6563945ad279444e2e0925ff6ffc86ae951e3fe4cbe9248e73c949b49'}
        assert digest(args) == expected[label]
        equivalent = deepcopy(args)
        for w in equivalent[0]['worlds']:
            w.pop('basis_sha256')
            for oi, obj in enumerate(w['anchors'][0]['objects']):
                obj.pop('record_sha256'); obj['id'] = 'local-'+str(oi)
        normalized.append(equivalent)
        results[label] = {}
        for mode, module in [('baseline', baseline), ('current', perception_reference)]:
            summary, receipt = evaluate(module, args)
            check_originals(args, sources, receipt)
            assert summary['bounds'] == (['-1', '1'] if renamed and mode == 'baseline' else ['1', '1'])
            results[label][mode] = summary
    assert normalized[0] == normalized[1]
    assert results['stable']['baseline']['output_sha256'] == results['stable']['current']['output_sha256']
    if opts.geometry_control:
        args = geometry_budget_worlds()
        for value, limit in zip(args, (4 << 20, 4 << 20, 16 << 20, 128 << 20)):
            assert len(contract.encoded(value)) <= limit
        results['geometry'] = {mode: evaluate(module, args)[0]
            for mode, module in [('baseline', baseline), ('current', perception_reference)]}
        assert results['geometry']['baseline']['output_sha256'] == results['geometry']['current']['output_sha256']
        assert results['geometry']['current']['bounds'] == ['-15/16', '1']
    print(contract.encoded({'artifact_id': 'reiyah.perception-reference-identity.reproduction',
        'version': '0.1.0', 'cases': results, 'physical_coverage': 'not_established',
        'human_judgments': 'none', 'scope': 'selected synthetic fixtures only'}).decode(), end='')


if __name__ == '__main__':
    main()
