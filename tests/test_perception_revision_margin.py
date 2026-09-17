"""Deletion-margin controls against exhaustive partial injections and deletions."""
from copy import deepcopy
from fractions import Fraction
import hashlib
from itertools import combinations, product
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from test_perception_revision import direct_delta, finite, ratio
from tools.perception_revision import contract, margin, margin_checker

ROOT = Path(__file__).resolve().parents[1]


def subsets(values):
    return (set(c) for k in range(len(values) + 1) for c in combinations(values, k))


class DeletionMarginTests(unittest.TestCase):
    def evaluate(self, case):
        contract.validate(case)
        payload = margin.produce(case)
        self.assertEqual(margin_checker.check(case, payload), payload['result'])
        return payload

    def test_exhaustive_replacement_graphs_and_all_deletions(self):
        calculations = 0
        for aa, bb in [(['a'], ['b', 'c']), (['a', 'b'], ['a', 'b', 'c']),
                       (['a', 'b'], ['a', 'b']), (['a', 'b'], [])]:
            for no in range(4):
                objects = ['o' + str(i) for i in range(no)]
                choices = list(product(sorted(set(aa + bb)), objects))
                for mask in range(1 << len(choices)):
                    edges = {e for i, e in enumerate(choices) if mask & (1 << i)}
                    case = finite(aa, bb, objects, edges)
                    contract.validate(case)
                    aid = case['anchors'][0]['id']
                    for fn, fp in [(1, 1), (3, 0), (Fraction(1, 3), 2)]:
                        case['loss'].update(false_negative=ratio(fn), false_positive=ratio(fp), tolerance=ratio(0))
                        payload = margin.produce(case)
                        result = margin_checker.check(case, payload)
                        baseline = direct_delta(case)
                        self.assertEqual(contract.rational(result['baseline_delta']), baseline)
                        pool = {p['object'] for p in payload['proof']['pool']}
                        eligible = {o for o in objects if not any((a, o) in edges for a in aa)
                                    and baseline - direct_delta(case, {(aid, o)}) == fn + fp}
                        self.assertEqual(pool, eligible)
                        adverse_sizes = []
                        for removed in subsets(objects):
                            observed = direct_delta(case, {(aid, o) for o in removed})
                            self.assertGreaterEqual(observed, baseline - len(removed) * (fn + fp))
                            if removed <= pool:
                                self.assertEqual(observed, baseline - len(removed) * (fn + fp))
                            if observed <= 0:
                                adverse_sizes.append(len(removed))
                            calculations += 1
                        if result['minimum_adverse_deletions'] is not None:
                            self.assertEqual(result['minimum_adverse_deletions'], min(adverse_sizes))
                        elif adverse_sizes:
                            self.assertGreaterEqual(min(adverse_sizes), result['deletion_lower_bound'])
        # Two three-detection and two two-detection populations, three losses,
        # every edge subset and every reference-deletion subset.
        self.assertEqual(calculations, 3 * sum(2 * (2 ** (3 * n) + 2 ** (2 * n)) * 2 ** n for n in range(4)))

    def test_global_budget_strict_threshold_and_audit_distinction(self):
        case = finite([], ['b1', 'b2'], ['o1', 'o2'], {('b1', 'o1'), ('b2', 'o2')})
        other = deepcopy(case['anchors'][0]); other['id'] = 'second'
        case['anchors'].append(other)
        for a in case['anchors']:
            a['weight'] = ratio(1, 2)
        case['loss']['tolerance'] = ratio(1)
        payload = self.evaluate(case); result = payload['result']
        self.assertEqual(result['minimum_adverse_deletions'], 1)
        self.assertEqual(result['necessary_confirmations'], 4)
        self.assertEqual(contract.rational(result['witness_delta']), 1)
        # Confirming the one-member witness leaves three different adverse singletons.
        confirmed = {(p['anchor'], p['object']) for p in payload['proof']['witness']}
        labels = [(a['id'], o['id']) for a in case['anchors'] for o in a['reference']['objects']]
        for a, o in set(labels) - confirmed:
            self.assertEqual(direct_delta(case, {(a, o)}), 1)
        for confirmed_count in range(4):
            for confirmed in combinations(labels, confirmed_count):
                self.assertTrue(any(direct_delta(case, {item}) <= 1 for item in set(labels) - set(confirmed)))

    def test_matching_ambiguity_does_not_make_a_matched_object_essential(self):
        case = finite([], ['b'], ['x', 'y'], {('b', 'x'), ('b', 'y')})
        result = self.evaluate(case)['result']
        self.assertEqual(result['pool_size'], 0)
        self.assertEqual(result['margin_status'], 'lower_bound_only')
        self.assertIsNone(result['minimum_adverse_deletions'])
        self.assertEqual(direct_delta(case, {(case['anchors'][0]['id'], 'x')}), 1)

    def test_reject_forged_proofs_results_and_input_rebinding(self):
        case = finite([], ['b1', 'b2'], ['o1', 'o2'], {('b1', 'o1'), ('b2', 'o2')})
        payload = self.evaluate(case)
        mutations = []
        for key, value in [('minimum_adverse_deletions', 0), ('pool_size', 0),
                           ('necessary_confirmations', 0), ('audit_sufficiency', 'supported'),
                           ('physical_coverage', 'established')]:
            forged = deepcopy(payload); forged['result'][key] = value; mutations.append(forged)
        forged = deepcopy(payload); forged['proof']['anchors'].clear(); mutations.append(forged)
        forged = deepcopy(payload); forged['proof']['pool'].append(forged['proof']['pool'][0]); mutations.append(forged)
        forged = deepcopy(payload); forged['proof']['pool'][0]['object'] = 'foreign'; mutations.append(forged)
        forged = deepcopy(payload); forged['proof']['witness'].clear(); mutations.append(forged)
        forged = deepcopy(payload); forged['proof']['anchors'][0]['output_b']['cover']['objects'].clear(); mutations.append(forged)
        forged = deepcopy(payload); forged['proof']['anchors'][0]['output_b']['matching'][0][1] = 'foreign'; mutations.append(forged)
        for forged in mutations:
            with self.assertRaises(contract.Invalid):
                margin_checker.check(case, forged)
        changed = deepcopy(case)
        changed['anchors'][0]['reference']['edges'].pop()
        with self.assertRaises(contract.Invalid):
            margin_checker.check(changed, payload)
        with patch.object(margin, 'produce', side_effect=AssertionError('producer called')), \
                patch.object(margin, '_matching_certificate', side_effect=AssertionError('matcher called')):
            self.assertEqual(margin_checker.check(case, payload), payload['result'])

    def test_unknown_open_joint_weight_and_zero_loss_scope(self):
        original = finite([], ['b'], ['o'], {('b', 'o')})
        cases = []
        case = deepcopy(original); case['anchors'][0]['output_b'] = {'state': 'unknown', 'reason': 'unavailable control'}; cases.append((case, 'input_blocked'))
        case = deepcopy(original); case['anchors'][0]['reference'] = {'state': 'open', 'reason': 'unbounded control'}; cases.append((case, 'unsupported_scope'))
        case = deepcopy(original); case['model']['variables'] = ['v']; cases.append((case, 'unsupported_scope'))
        case = deepcopy(original); case['model']['clauses'] = [[]]; cases.append((case, 'unsupported_scope'))
        case = deepcopy(original); case['loss'].update(false_negative=ratio(0), false_positive=ratio(0)); cases.append((case, 'unsupported_scope'))
        case = deepcopy(original); other = deepcopy(case['anchors'][0]); other.update(id='other', weight=ratio(2, 3))
        case['anchors'][0]['weight'] = ratio(1, 3); case['anchors'].append(other); cases.append((case, 'unsupported_scope'))
        for case, status in cases:
            payload = self.evaluate(case)
            self.assertEqual(payload['result']['execution_status'], status)
            self.assertEqual(payload['result']['model_status'], 'not_checked')
            forged = deepcopy(payload); forged['result']['minimum_adverse_deletions'] = 1
            with self.assertRaises(contract.Invalid):
                margin_checker.check(case, forged)
        with patch('tools.perception_revision.margin_contract.MAX_WORK', 1):
            self.assertEqual(self.evaluate(original)['result']['execution_status'], 'resource_limited')

    def test_cli_packet_and_digest_binding(self):
        case = finite([], ['b'], ['o'], {('b', 'o')})
        with tempfile.TemporaryDirectory() as tmp:
            inp, out = Path(tmp) / 'input.json', Path(tmp) / 'packet.json'
            inp.write_bytes(contract.encoded(case))
            digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
            prefix = [sys.executable, '-B', '-m', 'tools.perception_revision']
            operands = ['--input', str(inp), '--input-sha256', digest(inp)]
            produced = subprocess.run(prefix + ['deletion-margin', *operands, '--output', str(out)], cwd=ROOT, capture_output=True)
            self.assertEqual(produced.returncode, 0, produced.stderr)
            verified = subprocess.run(prefix + ['verify-deletion-margin', *operands, '--packet', str(out), '--packet-sha256', digest(out)], cwd=ROOT, capture_output=True)
            self.assertEqual(verified.returncode, 0, verified.stderr)
            packet = json.loads(out.read_bytes()); packet['artifact_id'] = 'reiyah.perception-revision.packet'
            out.write_bytes(contract.encoded(packet))
            rejected = subprocess.run(prefix + ['verify-deletion-margin', *operands, '--packet', str(out), '--packet-sha256', digest(out)], cwd=ROOT, capture_output=True)
            self.assertEqual(rejected.returncode, 2)
            self.assertEqual(json.loads(rejected.stderr)['code'], 'PACKET_BINDING')


if __name__ == '__main__':
    unittest.main()
