"""Replay the bounded member-order comparison against the selected prior compiler.

Every source and judgment is synthetic. All dependencies are local, and no files
are created. The optional budget control preserves the prior useful fallback.
"""
import argparse
from copy import deepcopy
import hashlib
import importlib.util
from itertools import permutations
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
CANDIDATE = ROOT
sys.path.insert(0, str(CANDIDATE))
from tests.test_perception_reference import digest, inputs, object_at, world
from tests.test_perception_reference_sharing import member_order_budget_worlds
from tools import perception_reference as reference
from tools.perception_decision import contract


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


identity_replay = load('identity_replay', CANDIDATE/'research/perception-reference-identity/0.1.0/reproduce.py')


def fixture(member_order, rational_spelling):
    args, sources = inputs(), {}
    orders = list(permutations(range(3)))
    for wi in range(64):
        objects = []
        for oi, x in enumerate((0, 3, 30)):
            aliases = ['proposal-'+str(oi)+'-'+str(j) for j in range(3)]
            if member_order:
                aliases = [aliases[j] for j in orders[wi % len(orders)]]
            obj = object_at('local-'+str(wi)+'-'+str(oi), x, members=aliases)
            if rational_spelling:
                scale = wi+1
                obj['xy'] = [{'numerator': str(int(q['numerator'])*scale),
                              'denominator': str(int(q['denominator'])*scale)} for q in obj['xy']]
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


def semantic_input(args):
    result = deepcopy(args)
    for w in result[0]['worlds']:
        w.pop('basis_sha256')
        for anchor in w['anchors']:
            for obj in anchor['objects']:
                obj.pop('record_sha256')
                obj['members'].sort()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline-compiler', required=True, type=Path)
    parser.add_argument('--budget-control', action='store_true')
    opts = parser.parse_args()
    expected = '5ad8b6e0e860fe514b04f76db8f11f7453eb63e5b9585b6b186407173eac7b55'
    if hashlib.sha256(opts.baseline_compiler.read_bytes()).hexdigest() != expected:
        parser.error('Baseline compiler differs from selected 2048e3e source bytes')
    baseline = load('tools.reference_equivalence_baseline', opts.baseline_compiler)
    results, semantic = {}, None
    for label, order in [('canonical', False), ('member-order', True)]:
        args, sources = fixture(order, False)
        normalized = semantic_input(args)
        if semantic is None:
            semantic = normalized
        assert normalized == semantic
        results[label] = {}
        for mode, module in [('baseline', baseline), ('current', reference)]:
            summary, receipt = identity_replay.evaluate(module, args)
            identity_replay.check_originals(args, sources, receipt)
            expected_bounds = ['-1', '1'] if label == 'member-order' and mode == 'baseline' else ['1', '1']
            assert summary['bounds'] == expected_bounds
            assert summary['states'] == (['open'] if expected_bounds == ['-1', '1'] else ['finite'])
            results[label][mode] = summary
    assert results['canonical']['baseline']['output_sha256'] == results['canonical']['current']['output_sha256']
    invalid, _ = fixture(False, True)
    for module in (baseline, reference):
        try:
            module.compile_model(*invalid)
        except contract.Invalid as exc:
            assert exc.code == 'INVALID_RATIONAL'
        else:
            raise AssertionError('Unreduced rational input must remain invalid')
    if opts.budget_control:
        args = member_order_budget_worlds()
        for value, limit in zip(args, (4 << 20, 4 << 20, 16 << 20, 128 << 20)):
            assert len(contract.encoded(value)) <= limit
        results['budget-control'] = {}
        for mode, module in [('baseline', baseline), ('current', reference)]:
            summary, _ = identity_replay.evaluate(module, args)
            assert summary['bounds'] == ['0', '1'] and summary['states'] == ['open', 'finite']
            results['budget-control'][mode] = summary
        assert results['budget-control']['baseline']['output_sha256'] == results['budget-control']['current']['output_sha256']
    result = {'artifact_id': 'reiyah.engine.reference-equivalence.replay', 'version': '0.1.0',
        'semantic_input_sha256': digest(semantic), 'results': results,
        'unreduced_rational_control': 'INVALID_RATIONAL in both compilers; numerical-canonicalization proposal withdrawn',
        'source_kind': 'Explicitly synthetic; no human or physical evidence',
        'checker_scope': 'Original-coordinate partial injections on the three-object worlds; shared core checker and prior byte equality on the budget control',
        'shared_trusted_code': 'Normalizer, parser, fixture constructors and input contract. The producer matcher is excluded while the separate core checker runs.'}
    sys.stdout.buffer.write(contract.encoded(result))


if __name__ == '__main__':
    main()
