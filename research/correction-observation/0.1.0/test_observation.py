"""Targeted scientific controls; generated fixtures contain no third-party records."""
from copy import deepcopy
from fractions import Fraction
from itertools import product
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from common import (FAMILIES, checker, conventional_measure, decision, digest, edit_interval,
                    flow_rank, interval, native_graph, native_measure, open_interval, q, ranking,
                    subject, validate_event, validate_rows, w)
from prepare import project


def rectangle(name, x=0):
    xyxy = [w(x), w(0), w(x + 10), w(30)]
    return {'id': name, 'record_sha256': digest([name, xyxy]), 'xyxy': xyxy}


def image(name='image-00', a=(), b=(), original=(), ordinal=0):
    return {'id': name, 'ordinal': ordinal, 'policy_sha256': '0' * 64,
            'output_a': {'state': 'observed', 'value': list(a)},
            'output_b': {'state': 'observed', 'value': list(b)}, 'original_reference': list(original)}


def brute_rank(left, right, edges):
    left = list(left)
    def recurse(i, used):
        if i == len(left):
            return 0
        return max([recurse(i+1, used)] + [1 + recurse(i+1, used | {r})
                   for r in right if r not in used and (left[i], r) in edges])
    return recurse(0, set())


class ObservationControls(unittest.TestCase):
    def test_independent_flow_matches_brute_all_three_by_three_graphs(self):
        pairs = [(d, r) for d in range(3) for r in range(3)]
        for bits in product((False, True), repeat=9):
            edges = {pair for pair, active in zip(pairs, bits) if active}
            self.assertEqual(flow_rank(range(3), range(3), edges), brute_rank(range(3), range(3), edges))

    def test_one_edit_bounds_exhaustive_graphs(self):
        im = image(a=[rectangle('a0'), rectangle('a1')], b=[rectangle('b0'), rectangle('b1')])
        nodes = range(4); old_refs = (0, 1)
        pairs = [(d, r) for d in nodes for r in old_refs]
        worlds = 0; tight_replacement = False
        for bits in product((False, True), repeat=8):
            edges = {p for p, yes in zip(pairs, bits) if yes}
            ma = brute_rank((0, 1), old_refs, edges); mb = brute_rank((2, 3), old_refs, edges)
            delta = 2 * (mb - ma)
            bounds = edit_interval(im, {'ranks': [ma, mb], 'delta': w(delta)})
            variants = [('delete', tuple(r for r in old_refs if r != removed),
                         {(d, r) for d, r in edges if r != removed}) for removed in old_refs]
            for new_bits in product((False, True), repeat=4):
                added = {(d, 2) for d, yes in zip(nodes, new_bits) if yes}
                variants.append(('insert', (0, 1, 2), edges | added))
                for removed in old_refs:
                    variants.append(('replace', tuple(r for r in old_refs if r != removed) + (2,),
                                     {(d, r) for d, r in edges if r != removed} | added))
            for kind, refs, changed in variants:
                actual = 2 * (brute_rank((2, 3), refs, changed) - brute_rank((0, 1), refs, changed))
                self.assertLessEqual(bounds[0], actual); self.assertLessEqual(actual, bounds[1])
                self.assertLessEqual(abs(actual-delta), 4 if kind == 'replace' else 2)
                tight_replacement |= kind == 'replace' and abs(actual-delta) == 4
                worlds += 1
        self.assertEqual(worlds, 12800)
        self.assertTrue(tight_replacement, 'Replacement is not an addition-only perturbation')

    def test_geometric_replacement_can_change_delta_by_four(self):
        im = image(a=[rectangle('a', 0)], b=[rectangle('b', 100)])
        before, after = [rectangle('old', 0)], [rectangle('new', 100)]
        left, right = conventional_measure(im, before), conventional_measure(im, after)
        self.assertEqual((q(left['delta']), q(right['delta'])), (-2, 2))
        self.assertEqual(edit_interval(im, left), (-2, 2))
        for refs in [[], before, after, before + after]:
            measured = native_measure(im, refs)
            self.assertEqual(measured['ranks'], conventional_measure(im, refs)['ranks'])
            self.assertEqual(measured['delta'], conventional_measure(im, refs)['delta'])

    def test_pooled_and_per_image_error_are_different_obligations(self):
        aa = image(a=[rectangle('a')], b=[rectangle('b', 100)])
        bb = image('image-01', a=[rectangle('c')], b=[rectangle('d', 100)], ordinal=1)
        measured = {im['id']: conventional_measure(im, [rectangle('r', 100)]) for im in [aa, bb]}
        self.assertEqual(interval([aa, bb], measured, 'exact_publisher'), (2, 2))
        self.assertEqual(interval([aa, bb], measured, 'one_edit_per_image'), (-2, 2))
        self.assertEqual(interval([aa, bb], measured, 'one_edit_global'), (0, 2))
        for changed_index in [0, 1]:
            for refs in [[], [rectangle('r', 0)], [rectangle('r', 100)], [rectangle('r', 100), rectangle('s')]]:
                actual = sum(q(conventional_measure(im, refs if i == changed_index else [rectangle('r', 100)])['delta'])
                             for i, im in enumerate([aa, bb])) / 2
                self.assertLessEqual(0, actual); self.assertLessEqual(actual, 2)

    def test_empty_is_known_but_missing_is_not_empty(self):
        empty = image()
        for family in FAMILIES:
            self.assertEqual(interval([empty], {}, family), (0, 0))
            self.assertEqual(decision(interval([empty], {}, family)), 'excluded')
        missing = deepcopy(empty); missing['output_b'] = {'state': 'unknown', 'reason': 'unjoined'}
        self.assertIsNone(interval([empty, missing], {}, 'exact_publisher'))
        self.assertEqual(ranking([missing], 'width'), [])
        with self.assertRaises(ValueError):
            open_interval(missing)

    def test_strict_threshold(self):
        self.assertEqual(decision((0, 0)), 'excluded')
        self.assertEqual(decision((0, 1)), 'unresolved')
        self.assertEqual(decision((Fraction(1, 1000), 1)), 'supported')

    def test_hidden_alternatives_cannot_affect_visible_projection(self):
        im = image(a=[rectangle('a')], b=[rectangle('b', 100)], original=[rectangle('r')])
        source = {'anchors': [{'output_a': im['output_a'], 'output_b': im['output_b'],
                              'reference': {'state': 'alternatives', 'before': im['original_reference'], 'after': []}}]}
        one, answer = project(source, 0, '0'*64)
        altered = deepcopy(source); altered['anchors'][0]['reference']['after'] = [rectangle('secret', 100)]
        two, changed_answer = project(altered, 0, '0'*64)
        self.assertNotEqual(answer, changed_answer)
        self.assertEqual(one, two); self.assertEqual(subject(one), subject(two))
        for policy in ['width', 'prior_margin']:
            self.assertEqual(ranking([one], policy), ranking([two], policy))

    def test_worker_initial_request_needs_no_oracle(self):
        with tempfile.TemporaryDirectory() as tmp:
            im = image(a=[rectangle('a')], b=[rectangle('b', 100)], original=[rectangle('r')])
            path = Path(tmp)/'visible.json'
            path.write_text(json.dumps({'images': [im], 'cases': [{'id': 'single', 'group': 'singleton', 'images': [im['id']]}]}))
            proc = subprocess.Popen([sys.executable, '-B', str(Path(__file__).with_name('experiment.py')),
                                     '--worker', str(path), 'C'], stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            try:
                frames = [json.loads(proc.stdout.readline()) for _ in range(3)]
                self.assertEqual([f['type'] for f in frames], ['begin', 'checkpoint', 'query'])
                self.assertEqual(frames[-1]['request']['subject_sha256'], subject(im))
            finally:
                proc.terminate(); proc.communicate(timeout=5)

    def test_query_subject_sequence_and_precision_rejections(self):
        request = {'case_id': 'single', 'arm': 'A', 'family': 'one_edit_global', 'sequence': 1,
                   'image_id': 'image-00', 'subject_sha256': '0'*64, 'precision': 'whole_image_reference', 'method_version': '0.1.0'}
        event = {'request': request, 'answer': [], 'source_sha256': '1'*64,
                 'basis': 'published_correction_replay', 'residual': 'one_edit_global',
                 'requested_utc': 'test', 'returned_utc': 'test',
                 'cost': {'observation_units': 1, 'human_seconds': None}}
        event['evidence_sha256'] = digest(event)
        self.assertEqual(validate_event(event, request), [])
        for key in request:
            wrong = deepcopy(request); wrong[key] = 2 if key == 'sequence' else 'different'
            with self.assertRaises(ValueError):
                validate_event(event, wrong)
        wrong = deepcopy(event); wrong['answer'] = [rectangle('unrecorded')]
        with self.assertRaises(ValueError): validate_event(wrong, request)
        wrong = deepcopy(event); wrong['residual'] = 'exact_publisher'
        wrong['evidence_sha256'] = digest({k:v for k,v in wrong.items() if k != 'evidence_sha256'})
        with self.assertRaises(ValueError): validate_event(wrong, request)

    def test_wrong_native_proof_is_rejected(self):
        im = image(a=[rectangle('a')], b=[rectangle('b', 100)])
        graph = native_graph(im, [rectangle('r', 100)])
        measured = native_measure(im, [rectangle('r', 100)])
        bad = deepcopy(measured['payload'])
        bad['proof']['worlds'][0]['anchors'][0]['output_b']['matching'] = []
        with self.assertRaises(Exception): checker.check(graph, bad)
        stale_graph = native_graph(im, [rectangle('r', 0)])
        with self.assertRaises(Exception): checker.check(stale_graph, measured['payload'])

    def test_invalid_operands_and_unsupported_family_fail(self):
        im = image()
        with self.assertRaises(ValueError): interval([im], {}, 'silent_imputation')
        bad = rectangle('bad'); bad['xyxy'][2] = w(0)
        with self.assertRaises(Exception): validate_rows([bad])
        with self.assertRaises(ValueError): validate_rows([rectangle('dup'), rectangle('dup')])
        different = rectangle('a', 100)
        with self.assertRaises(ValueError): open_interval(image(a=[rectangle('a')], b=[different]))
        with self.assertRaises(ValueError): edit_interval(im, {'ranks': [0, 0], 'delta': w(1)})


if __name__ == '__main__':
    unittest.main()
