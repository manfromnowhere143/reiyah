"""Exact world graphs, provenance and conservative boundaries after node sharing."""
from copy import deepcopy
from fractions import Fraction
from itertools import product
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from tools import perception_operands as operands, perception_reference as reference
from tools import perception_reviewed_operands as reviewed
from tools.perception_decision import checker, contract, kernel
from tests.test_perception_reference import digest, independent_matching, inputs, object_at, trap, world, xy

CASES = Path(__file__).resolve().parents[1]/'research/perception-reference-sharing/0.1.0/cases'


def locally_named_worlds(count=64, base_duplicates=1):
    args = inputs(base_duplicates=base_duplicates)
    args[0]['worlds'] = [world('world-'+str(wi), [[
        object_at('local-'+str(wi)+'-'+str(oi), x, members=['proposal-'+str(oi)])
        for oi, x in enumerate((0, 3, 30))]]) for wi in range(count)]
    return args


def geometry_budget_worlds():
    """Actual geometry-cap regression, within each compiler file-size cap."""
    args = inputs(32, base_duplicates=512)
    small = inputs(32, base_duplicates=8)
    args[1]['anchors'][-1], args[2][-1] = small[1]['anchors'][-1], small[2][-1]
    args[0]['inputs'] = {'comparison_sha256': digest(args[1]),
        'normalizations_sha256': digest(args[2]), 'catalog_sha256': digest(args[3])}
    for wi in range(3):
        anchors = [[object_at('w'+str(wi)+'o'+str(oi), 0 if oi < 3 else 30+wi,
                    time=(ai+1)*1_000_000, members=['a'+str(ai)+'p'+str(oi)])
                    for oi in range(45)] for ai in range(31)]
        anchors.append([object_at('last-'+str(oi),
            (0 if oi < 8 else 3 if oi == 8 else 30)+Fraction(wi, 10),
            time=32_000_000, members=['last-proposal-'+str(oi)]) for oi in range(42)])
        args[0]['worlds'].append(world('world-'+str(wi), anchors))
    return args


class ReferenceSharingTests(unittest.TestCase):
    def checked(self, args):
        before = deepcopy(args)
        compiled, receipt = reference.compile_model(*args)
        packet = kernel.produce(compiled)
        with patch.object(kernel, '_matching_certificate', side_effect=AssertionError('Producer called by checker')):
            checker.check(compiled, packet)
        self.assertEqual(args, before)
        self.assertEqual(receipt['reference_semantic_sha256'], digest(args[0]))
        if any(o['id'].startswith('shared:') for a in compiled['anchors'] for o in a['reference'].get('objects', [])):
            states, work = kernel._capacity(compiled)
            self.assertLessEqual(states, contract.MAX_WORLDS)
            self.assertLessEqual(work, contract.MAX_WORK)
        return compiled, receipt, packet

    def exact_worlds(self, args):
        """Use original coordinates and partial injections, not compiler edge construction."""
        compiled, receipt, packet = self.checked(args)
        spec, original, normals, catalog = args
        self.assertTrue(all(a['reference']['state'] == 'finite' for a in compiled['anchors']))
        self.assertEqual([w['world_id'] for w in receipt['world_encodings']], [w['id'] for w in spec['worlds']])
        self.assertEqual(len(packet['proof']['worlds']), len(spec['worlds']))
        normal = {r['anchor_id']: r for r in normals}
        clocks = {r['sample_token']: r for r in catalog['anchors']}
        proofs = {tuple(w['assignment']): {a['anchor']: a for a in w['anchors']} for w in packet['proof']['worlds']}
        fn, fp = [contract.rational(original['loss'][k]) for k in ('false_negative', 'false_positive')]
        totals, mapping_count = [], 0
        for source, encoding in zip(spec['worlds'], receipt['world_encodings']):
            assignment = {q['variable']: q['value'] for q in encoding['when']}
            proof = proofs[tuple(assignment[v] for v in compiled['model']['variables'])]
            references = {e['anchor_id']: e for e in source['anchors']}
            total = Fraction(0)
            for anchor in compiled['anchors']:
                name = anchor['id']; row = normal[name]
                clock = clocks[row['sample_token']]
                ego = [contract.rational(q) for q in clock['nominal_ego_xy']['value']]
                sources = {o['id']: o for o in references[name]['objects'] if o['class'] != 'outside_target'
                           and sum((contract.rational(q)-e)**2 for q, e in zip(o['xy'], ego)) <= 2500}
                source_points = {o['id']: (o['class'], tuple(contract.rational(q) for q in o['xy'])) for o in sources.values()}
                self.assertTrue(all(o['timestamp_us'] == clock['anchor_timestamp_us'] for o in sources.values()))
                mappings = [m for m in receipt['object_mapping'] if m['world_id'] == source['id'] and m['anchor_id'] == name]
                names = {m['graph_id']: m['object_id'] for m in mappings}
                self.assertEqual(len(names), len(sources)); self.assertEqual(len(mappings), len(sources))
                mapping_count += len(mappings)
                for m in mappings:
                    self.assertEqual(m['record_sha256'], sources[m['object_id']]['record_sha256'])
                    self.assertEqual(m['members'], sources[m['object_id']]['members'])
                ref = anchor['reference']
                active = lambda r: all(assignment[q['variable']] == q['value'] for q in r['when'])
                objects = {o['id'] for o in ref['objects'] if active(o)}
                self.assertEqual({names[o] for o in objects}, set(sources))
                records = {r['detection']['id']: (r['record']['class'], tuple(contract.rational(q) for q in r['record']['xy']))
                           for r in row['qualified_records']}
                selected = [r['id'] for role in ('base', 'additions') for r in anchor[role]['value']]
                expected_edges = {(d, o) for d in selected for o, (label, point) in source_points.items()
                                  if records[d][0] == label and sum((a-b)**2 for a, b in zip(records[d][1], point)) < 4}
                actual_edges = {(e['detection'], names[e['object']]) for e in ref['edges'] if e['object'] in objects and active(e)}
                self.assertEqual(actual_edges, expected_edges)
                base = [records[r['id']] for r in anchor['base']['value']]
                full = base+[records[r['id']] for r in anchor['additions']['value']]
                m0, m1 = independent_matching(base, list(source_points.values())), independent_matching(full, list(source_points.values()))
                self.assertEqual(len(proof[name]['base']['matching']), m0)
                self.assertEqual(len(proof[name]['augmented']['matching']), m1)
                loss0 = fn*(len(sources)-m0)+fp*(len(base)-m0)
                loss1 = fn*(len(sources)-m1)+fp*(len(full)-m1)
                total += contract.rational(anchor['weight'])*(loss0-loss1)
            totals.append(total)
        self.assertEqual(mapping_count, len(receipt['object_mapping']))
        self.assertEqual([contract.rational(packet['result']['bounds'][s]) for s in ('lower', 'upper')], [min(totals), max(totals)])
        return compiled, receipt, packet, totals

    def test_small_seventeen_world_comparison_reaches_its_conditional_decision(self):
        args = json.loads((CASES/'seventeen-worlds.json').read_bytes())
        compiled, receipt, packet, totals = self.exact_worlds(args)
        self.assertEqual(totals, [Fraction(1, 2) if i % 2 == 0 else Fraction(3, 2) for i in range(17)])
        self.assertEqual(packet['result']['decision']['preference'], 'prefer_augmented')
        self.assertEqual(receipt['geometry_comparisons_budgeted'], 74)
        self.assertEqual(len(receipt['object_mapping']), 161)
        self.assertEqual([len(a['reference']['objects']) for a in compiled['anchors']], [8, 25])
        self.assertEqual(packet['result']['physical_coverage'], 'not_established')

    def test_original_repeated_65_case_fits_while_retaining_both_worlds(self):
        args = json.loads((CASES/'historical-repeated-65.json').read_bytes())
        compiled, receipt, packet, totals = self.exact_worlds(args)
        self.assertEqual(totals, [-1, -1])
        self.assertEqual(len(compiled['anchors'][0]['reference']['objects']), 65)
        self.assertEqual(len(receipt['object_mapping']), 130)
        self.assertEqual(receipt['geometry_comparisons_budgeted'], 130)
        self.assertEqual(packet['result']['decision']['preference'], 'prefer_base')

    def test_source_records_stay_separate_when_graph_object_is_shared(self):
        args = trap()
        for i, w in enumerate(args[0]['worlds']):
            w['anchors'][0]['objects'][0]['record_sha256'] = digest(['distinct-world-source', i])
        compiled, receipt, _, _ = self.exact_worlds(args)
        known = [m for m in receipt['object_mapping'] if m['object_id'] == 'known']
        self.assertEqual(len({m['graph_id'] for m in known}), 1)
        self.assertEqual(len({m['record_sha256'] for m in known}), 2)
        self.assertEqual(len(compiled['anchors'][0]['reference']['objects']), 2)

    def test_sharing_does_not_replace_a_mixed_bound_with_global_resource_fallback(self):
        args = inputs(2, base_duplicates=128)
        small = inputs(2)
        args[1]['anchors'][1], args[2][1] = small[1]['anchors'][1], small[2][1]
        args[0]['inputs'] = {'comparison_sha256': digest(args[1]), 'normalizations_sha256': digest(args[2]),
                             'catalog_sha256': digest(args[3])}
        objects = [object_at('object-'+str(i), 10) for i in range(128)]
        args[0]['worlds'] = [world('world-'+str(i), [deepcopy(objects), [object_at('known', 3, time=2_000_000)]]) for i in range(64)]
        compiled, receipt, packet = self.checked(args)
        self.assertEqual([a['reference']['state'] for a in compiled['anchors']], ['open', 'finite'])
        self.assertEqual(packet['result']['execution_status'], 'succeeded')
        self.assertEqual([contract.rational(packet['result']['bounds'][s]) for s in ('lower', 'upper')], [0, 1])
        self.assertEqual(kernel._capacity(compiled), (64, 124096))
        # Exact pre-change compiled bytes: preserve this stronger mixed result.
        self.assertEqual(digest(compiled), '5c5a5c3a6a76ad481ca79b2ed913617d21b1c5e22de1bc1b2c644230b24d5365')
        self.assertEqual(len(receipt['object_mapping']), 8256)

    def test_equal_edges_do_not_merge_different_declared_objects(self):
        variants = [lambda o: o.update(members=['other-proposal']),
                    lambda o: o.update(xy=xy(Fraction(8, 5))), lambda o: o.update(**{'class': 'truck'}),
                    lambda o: o.update(members=['two', 'one'])]
        for change in variants:
            with self.subTest(change=variants.index(change)):
                args = inputs(); first = object_at('known', Fraction(3, 2), members=['one', 'two'])
                second = deepcopy(first); change(second)
                args[0]['worlds'] = [world('one', [[first]]), world('two', [[second]])]
                compiled, _, _, _ = self.exact_worlds(args)
                self.assertEqual(len(compiled['anchors'][0]['reference']['objects']), 2)
                self.assertTrue(all(o['when'] for o in compiled['anchors'][0]['reference']['objects']))

    def test_local_object_names_do_not_prevent_exact_member_sharing(self):
        # Local names and record digests remain distinct in provenance; all
        # geometric worlds are checked against original-coordinate injections.
        args = locally_named_worlds()
        compiled, receipt, packet, totals = self.exact_worlds(args)
        self.assertEqual(totals, [1]*64)
        self.assertEqual(len(compiled['anchors'][0]['reference']['objects']), 3)
        self.assertEqual(receipt['geometry_comparisons_budgeted'], 6)
        self.assertEqual(len({m['object_id'] for m in receipt['object_mapping']}), 192)
        self.assertEqual(len({m['record_sha256'] for m in receipt['object_mapping']}), 192)
        self.assertEqual(packet['result']['decision']['preference'], 'prefer_augmented')

    def test_renamed_objects_preserve_an_adverse_last_world(self):
        args = locally_named_worlds()
        args[0]['worlds'][-1]['anchors'][0]['objects'][1]['xy'] = xy(6)
        compiled, receipt, _, totals = self.exact_worlds(args)
        self.assertEqual(totals, [1]*63+[-1])
        self.assertEqual(len(compiled['anchors'][0]['reference']['objects']), 66)
        self.assertEqual(len(receipt['object_mapping']), 192)

    def test_coincident_objects_with_distinct_members_stay_distinct(self):
        args = locally_named_worlds(3, base_duplicates=2)
        for w in args[0]['worlds']:
            objects = w['anchors'][0]['objects']
            objects[1]['xy'], objects[2]['xy'] = xy(0), xy(3)
        compiled, _, packet, totals = self.exact_worlds(args)
        self.assertEqual(totals, [1, 1, 1])
        self.assertEqual(len(compiled['anchors'][0]['reference']['objects']), 3)
        self.assertEqual(len(compiled['model']['clauses']), 1)  # Unused fourth code stays excluded.
        for w in packet['proof']['worlds']:
            self.assertEqual(len(w['anchors'][0]['base']['matching']), 2)
            self.assertEqual(len(w['anchors'][0]['augmented']['matching']), 3)

    def test_reused_local_names_follow_the_correct_world_member(self):
        args = locally_named_worlds(3)
        for wi, w in enumerate(args[0]['worlds']):
            for oi, obj in enumerate(w['anchors'][0]['objects']):
                obj['id'] = 'local-'+str((wi+oi) % 3)
        _, receipt, _, totals = self.exact_worlds(args)
        self.assertEqual(totals, [1, 1, 1])
        local_zero = [m for m in receipt['object_mapping'] if m['object_id'] == 'local-0']
        self.assertEqual(len({m['graph_id'] for m in local_zero}), 3)
        self.assertEqual(len({tuple(m['members']) for m in local_zero}), 3)

    def test_local_names_preserve_joint_anchor_constraints(self):
        args = json.loads((CASES/'seventeen-worlds.json').read_bytes())
        for wi, w in enumerate(args[0]['worlds']):
            for ai, anchor in enumerate(w['anchors']):
                for oi, obj in enumerate(anchor['objects']):
                    obj['id'] = 'local-'+str(wi)+'-'+str(ai)+'-'+str(oi)
                    obj['record_sha256'] = digest(['synthetic renamed record', obj])
        compiled, receipt, _, totals = self.exact_worlds(args)
        self.assertEqual(totals, [Fraction(1, 2) if i % 2 == 0 else Fraction(3, 2) for i in range(17)])
        self.assertEqual([len(a['reference']['objects']) for a in compiled['anchors']], [8, 25])
        self.assertEqual(len(receipt['object_mapping']), 161)

    def test_expanded_sharing_budget_retains_the_previous_plan(self):
        # Broader sharing makes the heavy anchor too costly under the global
        # preflight. Discarding every shared node also loses the small anchor.
        # The previous plan must survive, including exact original report bytes.
        args = inputs(2, base_duplicates=128)
        small = inputs(2)
        args[1]['anchors'][1], args[2][1] = small[1]['anchors'][1], small[2][1]
        args[0]['inputs'] = {'comparison_sha256': digest(args[1]),
            'normalizations_sha256': digest(args[2]), 'catalog_sha256': digest(args[3])}
        for wi in range(64):
            heavy = [object_at('world-'+str(wi)+'-object-'+str(i), 0,
                     members=['heavy-proposal-'+str(i)]) for i in range(128)]
            light = [object_at('light-'+str(i), x, time=2_000_000,
                     members=['light-proposal-'+str(i)]) for i, x in enumerate((0, 3, 30))]
            args[0]['worlds'].append(world('world-'+str(wi), [heavy, light]))
        compiled, receipt, packet = self.checked(args)
        self.assertEqual([a['reference']['state'] for a in compiled['anchors']], ['open', 'finite'])
        self.assertEqual([contract.rational(packet['result']['bounds'][s]) for s in ('lower', 'upper')], [0, 1])
        self.assertEqual(kernel._capacity(compiled), (64, 5056))
        self.assertEqual(len(receipt['object_mapping']), 8384)
        self.assertEqual(digest(compiled), '510811e4a60397a223d21295eb1d3460f99cb898a013f47718e8b75e19747e44')
        self.assertEqual(digest(receipt), '351f5c57af43c75a2f7cb82c3215f01daac6403d8bb23a4d34941beb02eef830')
        self.assertEqual(digest(packet), '69808f59197ccd1891e903a11b207037a9435b37df7f9ca36dd639cd3ef44e6a')

    def test_dense_graph_at_adjacent_sharing_budget_boundary(self):
        # Seven predictions connect to every active object on anchor 0. The
        # single addition on anchor 1 has no edge. Direct deltas are +1/-1,
        # so equal weights give zero in all 64 worlds. The first representation
        # fits; the next must retain the ordinary mixed [-1,0] enclosure.
        for stable_count, bounds, capacity in [(56, [0, 0], 1_994_176),
                                                (57, [-1, 0], 58_304)]:
            with self.subTest(stable_objects=stable_count):
                args = inputs(2, base_duplicates=6)
                small = inputs(2, base_duplicates=0)
                args[1]['anchors'][1], args[2][1] = small[1]['anchors'][1], small[2][1]
                args[0]['inputs'] = {'comparison_sha256': digest(args[1]),
                    'normalizations_sha256': digest(args[2]), 'catalog_sha256': digest(args[3])}
                stable = [object_at('invariant-'+str(i), Fraction(3, 2)) for i in range(stable_count)]
                args[0]['worlds'] = [world('world-'+str(i), [
                    deepcopy(stable)+[object_at('varying', Fraction(1500+i, 1000))],
                    [object_at('unmatched', 30, time=2_000_000)]]) for i in range(64)]
                compiled, receipt, packet = self.checked(args)
                self.assertEqual(packet['result']['execution_status'], 'succeeded')
                self.assertEqual([contract.rational(packet['result']['bounds'][s])
                                  for s in ('lower', 'upper')], bounds)
                self.assertEqual(kernel._capacity(compiled), (64, capacity))
                self.assertEqual(len(receipt['world_encodings']), 64)
                self.assertEqual(len(receipt['object_mapping']), 64*(stable_count+2))
                if stable_count == 56:
                    self.assertEqual([len(a['reference']['objects']) for a in compiled['anchors']], [120, 1])
                    for w in packet['proof']['worlds']:
                        first, second = w['anchors']
                        self.assertEqual([len(first[r]['matching']) for r in ('base', 'augmented')], [6, 7])
                        self.assertEqual([len(second[r]['matching']) for r in ('base', 'augmented')], [0, 0])
                else:
                    self.assertEqual([a['reference']['state'] for a in compiled['anchors']], ['open', 'finite'])

    def test_expanded_geometry_budget_retains_the_last_finite_anchor(self):
        # Heavy anchors remain open, but wider sharing lets them consume more
        # geometry before their graph caps stop emission. Evaluator work alone
        # misses this. Preserve the old plan instead of starving the last anchor.
        args = geometry_budget_worlds()
        for value, limit in zip(args, (4 << 20, 4 << 20, 16 << 20, 128 << 20)):
            self.assertLessEqual(len(contract.encoded(value)), limit)
        compiled, receipt, packet = self.checked(args)
        self.assertEqual([a['reference']['state'] for a in compiled['anchors']], ['open']*31+['finite'])
        self.assertEqual([contract.rational(packet['result']['bounds'][s]) for s in ('lower', 'upper')],
                         [Fraction(-15, 16), 1])
        self.assertEqual(receipt['geometry_comparisons_budgeted'], 748575)
        self.assertEqual(kernel._capacity(compiled), (4, 52548))
        self.assertEqual(len(receipt['object_mapping']), 4311)
        self.assertEqual(digest(compiled), 'e1709913ecee38679d12fc1b53a9f385d8fdf443ba31431ed8e6c0b686d9c89a')
        self.assertEqual(digest(receipt), 'ecbd0fb540427a23b3691c3fff7541ec09d94717cf0142b2728ae8d4d9bcc563')
        self.assertEqual(digest(packet), 'bcdb235527da49300e8f698b4abd6a05d64aef65448ac34e5b9a0cae05658c00')

    def test_absence_and_geometry_patterns_preserve_each_world_graph(self):
        # Every three-world pattern of absence, matching competition, class and range.
        choices = [None, ('car', Fraction(3, 2)), ('car', -1), ('truck', -1), ('car', 51)]
        for pattern in product(choices, repeat=3):
            args = inputs()
            for i, choice in enumerate(pattern):
                objects = [object_at('stable', 0)]
                if choice is not None:
                    label, point = choice; objects.append(object_at('varying', point, label=label))
                args[0]['worlds'].append(world('world-'+str(i), [objects]))
            self.exact_worlds(args)

    def test_reordering_worlds_anchors_and_objects_preserves_provenance_and_values(self):
        args = trap(2)
        args[0]['worlds'][0]['anchors'][1]['objects'].append(object_at('disputed', -1, time=2_000_000))
        args[0]['worlds'][1]['anchors'][1]['objects'].pop()
        args[0]['worlds'].reverse()
        for w in args[0]['worlds']:
            w['anchors'].reverse()
            for a in w['anchors']: a['objects'].reverse()
        _, _, _, totals = self.exact_worlds(args)
        self.assertEqual(totals, [0, 0])

    def test_late_unknowns_still_open_the_entire_affected_anchor(self):
        for change in [lambda e: e.update(unlisted_objects={'state': 'unknown', 'reason': 'Later coverage is unresolved'}),
                       lambda e: e['objects'][0].update(timestamp_us=999999),
                       lambda e: e.update(objects=[{'id': 'known', 'members': ['known'], 'record_sha256': 'f'*64,
                                                   'state': 'unresolved', 'reason': 'Later geometry is unknown'}])]:
            args = trap(); change(args[0]['worlds'][-1]['anchors'][0])
            compiled, receipt, packet = self.checked(args)
            self.assertEqual(compiled['anchors'][0]['reference']['state'], 'open')
            self.assertTrue(receipt['open_reasons']['anchor-0'])
            self.assertEqual([contract.rational(packet['result']['bounds'][s]) for s in ('lower', 'upper')], [-1, 1])

    def test_late_malformed_records_cannot_be_skipped_after_early_unknowns(self):
        for change, code in [(lambda o: o.update(record_sha256='bad'), 'REFERENCE_BINDING'),
                             (lambda o: o.update(xy=[True, 0]), 'REFERENCE_FIELDS'),
                             (lambda o: o.update(members=['same', 'same']), 'REFERENCE_ALIAS'),
                             (lambda o: o.update(**{'class': 'car_typo'}), 'REFERENCE_CLASS')]:
            args = trap(); args[0]['joint_coverage'] = {'state': 'unknown', 'reason': 'No complete closure'}
            change(args[0]['worlds'][-1]['anchors'][0]['objects'][0])
            with self.subTest(code=code), self.assertRaises(contract.Invalid) as caught:
                reference.compile_model(*args)
            self.assertEqual(caught.exception.code, code)

    def test_common_projection_rejects_lost_shared_object_even_when_loss_bounds_agree(self):
        args = json.loads((CASES/'seventeen-worlds.json').read_bytes())
        compiled, receipt, packet = self.checked(args)
        neutral_open, _, mappings = operands.project(args[1], args[2],
            [{'anchor_id': 'anchor-'+str(i), 'sample_token': 'sample-'+str(i), 'window_id': 'window-'+str(i)} for i in range(2)],
            {'sample-'+str(i): {'frame_id': 'frame-'+str(i)} for i in range(2)},
            {'base': 'configuration-2', 'camera': 'configuration-1'})
        neutral = reviewed.project(compiled, neutral_open, mappings)
        self.assertEqual(neutral['model'], compiled['model'])
        self.assertEqual(kernel.produce(neutral)['result'], packet['result'])
        changed = deepcopy(neutral)
        isolated = next(m['graph_id'] for m in receipt['object_mapping'] if m['anchor_id'] == 'anchor-0' and m['object_id'] == 'stable-2')
        target = next(o for o in changed['anchors'][0]['reference']['objects'] if o['id'] == isolated)
        target['when'] = deepcopy(receipt['world_encodings'][0]['when'])
        # Removing the same missed object from both configurations leaves delta unchanged.
        self.assertEqual(kernel.produce(changed)['result'], packet['result'])
        with self.assertRaises(contract.Invalid) as caught:
            reviewed.check_projection(compiled, changed, neutral_open, mappings)
        self.assertEqual(caught.exception.code, 'REVIEWED_SEMANTICS')


if __name__ == '__main__':
    unittest.main()
