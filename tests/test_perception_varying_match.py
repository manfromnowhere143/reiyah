"""A sealed constructed case through geometry and the existing common projection.

No admission or reviewer is manufactured. The geometric baseline enumerates
partial injections without the compiler's graphs or the producer's matcher.
"""
from copy import deepcopy
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from tools import perception_operands as operands, perception_reference as reference
from tools import perception_reviewed_operands as reviewed
from tools.perception_decision import checker, contract, kernel
from tests.test_perception_reference import digest, independent_matching, inputs, world, xy


CASE = Path(__file__).resolve().parents[1]/'research/perception-varying-match/0.1.0/case.json'
CASE_SHA256 = '655b0afaecc89bd6544ae59c6f842705713e17e6924447d5c09742276a324194'
POSITIONS = {
    'none': {'k': (Fraction(3, 2), 0)},
    'c_only': {'k': (0, 0), 'dC': (3, 0)},
    'b_only': {'k': (0, 0), 'dB': (3, 0)},
    'a_and_c': {'k': (0, 0), 'dA': (0, 1), 'dC': (0, -1)},
}
DETECTIONS = {'b0': ('car', (0, 0)), 'c0': ('car', (3, 0))}


def scenario():
    """A test realization of the selected graph, not an importer for Fable cases."""
    raw = CASE.read_bytes()
    if hashlib.sha256(raw).hexdigest() != CASE_SHA256:
        raise AssertionError('The selected constructed case changed')
    selected = json.loads(raw)
    spec, open_case, normals, catalog = inputs()
    classes = {o['id']: o['class'] for o in selected['anchors'][0]['objects']}
    for entry in selected['joint_worlds']:
        wid = entry['world_id']
        objects = []
        for oid in entry['per_anchor']['A']['objects_present']:
            obj = {'id': oid, 'members': [oid], 'state': 'point', 'class': classes[oid],
                   'xy': xy(*POSITIONS[wid][oid]), 'timestamp_us': 1_000_000}
            obj['record_sha256'] = digest(obj)
            objects.append(obj)
        spec['worlds'].append(world(wid, [objects]))
    compiled, receipt = reference.compile_model(spec, open_case, normals, catalog)
    neutral_open, _, mappings = operands.project(open_case, normals,
        [{'anchor_id': 'anchor-0', 'sample_token': 'sample-0', 'window_id': 'window-0001'}],
        {'sample-0': {'frame_id': 'frame-0001'}},
        {'base': 'configuration-2', 'camera': 'configuration-1'})
    neutral = reviewed.project(compiled, neutral_open, mappings)
    return selected, spec, normals, compiled, receipt, neutral_open, mappings, neutral


def checked_world_deltas(case, receipt):
    """Use the separately checked witness counts, keyed by explicit world identity."""
    contract.validate(case)
    packet = kernel.produce(case)
    with patch.object(kernel, '_matching_certificate', side_effect=AssertionError('Producer matcher called by checker')):
        checker.check(case, packet)
    by_assignment = {tuple(row['assignment']): row['anchors'][0] for row in packet['proof']['worlds']}
    fn, fp = (contract.rational(case['loss'][k]) for k in ('false_negative', 'false_positive'))
    anchor = case['anchors'][0]
    result = {}
    for encoding in receipt['world_encodings']:
        env = {lit['variable']: lit['value'] for lit in encoding['when']}
        row = by_assignment[tuple(env[v] for v in case['model']['variables'])]
        gain = len(row['augmented']['matching'])-len(row['base']['matching'])
        result[encoding['world_id']] = contract.rational(anchor['weight'])*(
            (fn+fp)*gain-fp*len(anchor['additions']['value']))
    return result, packet['result']


class VaryingMatchTests(unittest.TestCase):
    def setUp(self):
        (self.selected, self.spec, self.normals, self.compiled, self.receipt,
         self.neutral_open, self.mappings, self.neutral) = scenario()

    def test_all_world_graphs_and_full_losses_survive_geometry_and_common_projection(self):
        self.assertEqual(set(POSITIONS), {w['world_id'] for w in self.selected['joint_worlds']})
        self.assertEqual(self.compiled['model'], self.neutral['model'])
        self.assertEqual(self.receipt['joint_world_count'], 4)
        self.assertEqual(len(self.compiled['model']['variables']), 2)
        self.assertEqual(self.compiled['model']['clauses'], [])
        self.assertEqual(self.compiled['loss'], self.neutral['loss'])
        self.assertEqual({k: Fraction(v) for k, v in self.selected['loss'].items()},
                         {k: contract.rational(v) for k, v in self.neutral['loss'].items()})
        self.assertEqual(contract.rational(self.neutral['anchors'][0]['weight']),
                         Fraction(self.selected['anchors'][0]['weight']))
        normalized = {r['detection']['id']: (r['record']['class'],
            tuple(contract.rational(q) for q in r['record']['xy'])) for r in self.normals[0]['qualified_records']}
        self.assertEqual(normalized, {'base:0': DETECTIONS['b0'], 'camera:0': DETECTIONS['c0']})
        for role, expected in [('base', 'base:0'), ('additions', 'camera:0')]:
            self.assertEqual([n['id'] for n in self.compiled['anchors'][0][role]['value']], [expected])
        graph_names = {m['graph_id']: m['object_id'] for m in self.receipt['object_mapping']}
        inverse = {m['neutral']['id']: m['original']['id'] for m in self.mappings[0]['detections']}
        original_names = {'base:0': 'b0', 'camera:0': 'c0'}
        direct = {}
        for selected_world, encoding in zip(self.selected['joint_worlds'], self.receipt['world_encodings']):
            wid = selected_world['world_id']
            self.assertEqual(encoding['world_id'], wid)
            expected = selected_world['per_anchor']['A']
            positions = POSITIONS[wid]
            self.assertEqual(set(positions), set(expected['objects_present']))
            geometry_edges = {(d, o) for d, (label, p) in DETECTIONS.items() for o, q in positions.items()
                              if label == 'car' and sum((x-y)**2 for x, y in zip(p, q)) < 4}
            self.assertEqual(geometry_edges, {tuple(e) for e in expected['edges']})
            env = {lit['variable']: lit['value'] for lit in encoding['when']}
            def enabled(guard):
                return all(env[lit['variable']] is lit['value'] for lit in guard)
            for case, rename in [(self.compiled, original_names),
                                 (self.neutral, {k: original_names[v] for k, v in inverse.items()})]:
                ref = case['anchors'][0]['reference']
                present = {o['id'] for o in ref['objects'] if enabled(o['when'])}
                self.assertEqual({graph_names[o] for o in present}, set(expected['objects_present']))
                edges = {(rename[e['detection']], graph_names[e['object']]) for e in ref['edges']
                         if e['object'] in present and enabled(e['when'])}
                self.assertEqual(edges, geometry_edges)
            objects = [('car', tuple(p)) for p in positions.values()]
            base, full = [DETECTIONS['b0']], list(DETECTIONS.values())
            m0, m1 = independent_matching(base, objects), independent_matching(full, objects)
            loss0 = len(objects)-m0+len(base)-m0
            loss1 = len(objects)-m1+len(full)-m1
            direct[wid] = loss0-loss1
        self.assertEqual(direct, {'none': -1, 'c_only': 1, 'b_only': 1, 'a_and_c': -1})
        for case in (self.compiled, self.neutral):
            deltas, result = checked_world_deltas(case, self.receipt)
            self.assertEqual(deltas, direct)
            self.assertEqual([contract.rational(result['bounds'][s]) for s in ('lower', 'upper')], [-1, 1])
            self.assertEqual(result['enclosure_kind'], 'exact_for_finite_model')
            self.assertEqual(result['reference_scope'], 'synthetic')
            self.assertEqual(result['physical_coverage'], 'not_established')

    def assert_semantic_rejection(self, changed, expected_deltas):
        before, result = checked_world_deltas(self.neutral, self.receipt)
        after, changed_result = checked_world_deltas(changed, self.receipt)
        self.assertNotEqual(before, after)
        self.assertEqual(after, expected_deltas)
        # Even the entire aggregate result agrees, with valid certificates for each input.
        self.assertEqual(result, changed_result)
        with self.assertRaises(contract.Invalid) as caught:
            reviewed.check_projection(self.compiled, changed, self.neutral_open, self.mappings)
        self.assertEqual(caught.exception.code, 'REVIEWED_SEMANTICS')

    def test_changed_matching_competition_rejected_despite_identical_aggregate_result(self):
        changed = deepcopy(self.neutral)
        target = next(m['graph_id'] for m in self.receipt['object_mapping']
                      if m['world_id'] == 'a_and_c' and m['object_id'] == 'dC')
        edge = next(e for e in changed['anchors'][0]['reference']['edges'] if e['object'] == target)
        edge['detection'] = changed['anchors'][0]['additions']['value'][0]['id']
        self.assert_semantic_rejection(changed, {'none': -1, 'c_only': 1, 'b_only': 1, 'a_and_c': 1})

    def test_swapped_world_conditions_rejected_despite_identical_aggregate_result(self):
        changed = deepcopy(self.neutral)
        encodings = {r['world_id']: r['when'] for r in self.receipt['world_encodings']}
        for obj in changed['anchors'][0]['reference']['objects']:
            if obj['when'] == encodings['c_only']:
                obj['when'] = deepcopy(encodings['a_and_c'])
            elif obj['when'] == encodings['a_and_c']:
                obj['when'] = deepcopy(encodings['c_only'])
        self.assert_semantic_rejection(changed, {'none': -1, 'c_only': -1, 'b_only': 1, 'a_and_c': 1})


if __name__ == '__main__':
    unittest.main()
