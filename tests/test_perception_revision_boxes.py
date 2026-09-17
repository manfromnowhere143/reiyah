"""Geometry and exclusivity controls for qualified rectangle operands."""
from copy import deepcopy
from fractions import Fraction
import hashlib
from itertools import product
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from tools.perception_revision import boxes, checker, contract, kernel

ROOT = Path(__file__).resolve().parents[1]


def q(value):
    return contract.wire(Fraction(value))


def box(name, coordinates):
    return {'id': name, 'record_sha256': hashlib.sha256(name.encode()).hexdigest(),
            'xyxy': [q(v) for v in coordinates]}


def example():
    return {
        'artifact_id': 'reiyah.perception-revision.box-alternatives', 'version': '0.1.0',
        'coordinate_system': 'continuous_xyxy_pixels', 'comparison_id': 'box-control',
        'cohort_id': 'image-control', 'evidence_kind': 'synthetic',
        'assumptions': ['Hypothetical finite alternatives; no physical truth.'],
        'loss': {k: q(v) for k, v in (('false_negative', 1), ('false_positive', 1), ('tolerance', 0))},
        'iou_threshold': q('1/2'), 'model': {'variables': ['corrected'], 'clauses': []},
        'anchors': [{
            'id': 'image', 'weight': q(1),
            'output_a': {'state': 'observed', 'value': [box('a', (0, 0, 2, 2))]},
            'output_b': {'state': 'observed', 'value': [box('b', (4, 0, 6, 2))]},
            'reference': {'state': 'alternatives', 'variable': 'corrected',
                          'before': [box('object', (0, 0, 2, 2))],
                          'after': [box('object', (4, 0, 6, 2))]}}]}


class BoxAlternativeTests(unittest.TestCase):
    def checked(self, source):
        case = boxes.compile_alternatives(source)
        payload = kernel.produce(case)
        self.assertEqual(checker.check(case, payload), payload['result'])
        return case, payload

    def test_whole_set_geometry_replacement_never_counts_both_versions(self):
        case, packet = self.checked(example())
        self.assertEqual(packet['result']['bounds'], {'lower': q(-2), 'upper': q(2)})
        for _, env in contract.worlds(case['model']):
            present, _ = contract.graph(case['anchors'][0], env)
            self.assertEqual(len(present), 1)
        self.assertEqual(packet['result']['decision']['preference'], 'unresolved')

    def test_insertion_can_overturn_deletion_only_verdict(self):
        source = example()
        source['anchors'][0]['output_b']['value'] = []
        source['anchors'][0]['reference']['before'] = []
        source['anchors'][0]['reference']['after'] = [box('new', (0, 0, 2, 2))]
        _, packet = self.checked(source)
        self.assertEqual(packet['result']['bounds'], {'lower': q(-1), 'upper': q(1)})
        source['model']['clauses'] = [[{'variable': 'corrected', 'value': False}]]
        _, old = self.checked(source)
        self.assertEqual(old['result']['decision']['improvement_criterion'], 'supported')
        source['model']['clauses'] = [[{'variable': 'corrected', 'value': True}]]
        _, new = self.checked(source)
        self.assertEqual(new['result']['decision']['preference'], 'prefer_a')

    def test_joint_choice_across_anchors_is_preserved(self):
        source = example()
        second = deepcopy(source['anchors'][0])
        second['id'] = 'second'
        second['output_a'], second['output_b'] = second['output_b'], second['output_a']
        source['anchors'].append(second)
        for a in source['anchors']:
            a['weight'] = q('1/2')
        _, packet = self.checked(source)
        self.assertEqual(packet['result']['bounds'], {'lower': q(0), 'upper': q(0)})
        source['model']['variables'].append('independent')
        second['reference']['variable'] = 'independent'
        _, independent = self.checked(source)
        self.assertEqual(independent['result']['bounds'], {'lower': q(-2), 'upper': q(2)})

    def test_empty_missing_and_open_are_distinct(self):
        source = example()
        for a in source['anchors']:
            a['output_a']['value'] = []
            a['output_b']['value'] = []
            a['reference']['before'] = []
            a['reference']['after'] = []
        _, empty = self.checked(source)
        self.assertEqual(empty['result']['bounds'], {'lower': q(0), 'upper': q(0)})
        source['anchors'][0]['output_b'] = {'state': 'unknown', 'reason': 'No source join'}
        _, blocked = self.checked(source)
        self.assertEqual(blocked['result']['execution_status'], 'input_blocked')
        self.assertIsNone(blocked['result']['bounds'])
        source = example()
        source['anchors'][0]['reference'] = {'state': 'open', 'reason': 'Unqualified reference'}
        _, opened = self.checked(source)
        self.assertEqual(opened['result']['enclosure_kind'], 'conservative_open_reference')

    def test_exact_iou_boundary_and_touching_boxes(self):
        # Intersection 2, union 4: equality is admitted, then a tiny movement excludes.
        a = (Fraction(0), Fraction(0), Fraction(3), Fraction(1))
        self.assertTrue(boxes.overlap(a, (Fraction(1), Fraction(0), Fraction(4), Fraction(1)), Fraction(1, 2)))
        self.assertFalse(boxes.overlap(a, (Fraction(1) + Fraction(1, 10**20), Fraction(0),
                                           Fraction(4) + Fraction(1, 10**20), Fraction(1)), Fraction(1, 2)))
        self.assertFalse(boxes.overlap(a, (Fraction(3), Fraction(0), Fraction(4), Fraction(1)), Fraction(1, 2)))

    def test_many_geometry_edges_against_integer_cross_products(self):
        coords = [(x, y, x+w, y+h) for x, y, w, h in product(range(2), range(2), (1, 2), (1, 2))]
        checks = 0
        for aa, bb, threshold in product(coords, coords, (Fraction(1, 3), Fraction(1, 2), Fraction(1))):
            iw = max(0, min(aa[2], bb[2]) - max(aa[0], bb[0]))
            ih = max(0, min(aa[3], bb[3]) - max(aa[1], bb[1]))
            area = (aa[2]-aa[0])*(aa[3]-aa[1]) + (bb[2]-bb[0])*(bb[3]-bb[1])
            expected = iw*ih*threshold.denominator >= (area-iw*ih)*threshold.numerator
            self.assertEqual(boxes.overlap(tuple(map(Fraction, aa)), tuple(map(Fraction, bb)), threshold), expected)
            checks += 1
        self.assertEqual(checks, 768)

    def test_geometry_and_schema_rejections(self):
        changes = [
            lambda s: s.update(extra=True),
            lambda s: s.update(coordinate_system='metres'),
            lambda s: s.update(iou_threshold=q(0)),
            lambda s: s.update(iou_threshold=q(2)),
            lambda s: s['anchors'][0]['output_a']['value'][0]['xyxy'].__setitem__(2, q(0)),
            lambda s: s['anchors'][0]['output_a']['value'][0]['xyxy'].__setitem__(2, q(10_000_001)),
            lambda s: s['anchors'][0]['output_a']['value'][0]['xyxy'].__setitem__(2, 2.0),
            lambda s: s['anchors'][0]['reference'].update(variable='unknown'),
            lambda s: s['anchors'][0]['reference']['before'].append(deepcopy(s['anchors'][0]['reference']['before'][0])),
            lambda s: s['model']['variables'].append('corrected'),
        ]
        for change in changes:
            source = example()
            change(source)
            with self.subTest(change=change), self.assertRaises(contract.Invalid):
                boxes.compile_alternatives(source)

    def test_shared_output_requires_geometry_equality(self):
        source = example()
        source['anchors'][0]['output_b'] = deepcopy(source['anchors'][0]['output_a'])
        _, packet = self.checked(source)
        self.assertEqual(packet['result']['bounds'], {'lower': q(0), 'upper': q(0)})
        source['anchors'][0]['output_b']['value'][0]['xyxy'][2] = q(3)
        with self.assertRaisesRegex(contract.Invalid, 'inconsistent'):
            boxes.compile_alternatives(source)

    def test_resource_boundary_and_checker_rejects_omitted_world(self):
        with patch.object(boxes, 'MAX_WORK', 0), self.assertRaises(contract.Invalid):
            boxes.compile_alternatives(example())
        case, packet = self.checked(example())
        packet['proof']['worlds'].pop()
        with self.assertRaises(contract.Invalid):
            checker.check(case, packet)

    def test_cli_source_digest_binding_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'boxes.json'
            target = root / 'graph.json'
            source.write_bytes(contract.encoded(example()))
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            argv = [sys.executable, '-B', '-m', 'tools.perception_revision', 'from-box-alternatives',
                    '--input', str(source), '--input-sha256', digest, '--output', str(target)]
            result = subprocess.run(argv, cwd=ROOT, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            contract.load(target, hashlib.sha256(target.read_bytes()).hexdigest())
            self.assertNotEqual(subprocess.run(argv, cwd=ROOT, capture_output=True).returncode, 0)
            argv[argv.index(digest)] = '0' * 64
            self.assertNotEqual(subprocess.run(argv, cwd=ROOT, capture_output=True).returncode, 0)


if __name__ == '__main__':
    unittest.main()
