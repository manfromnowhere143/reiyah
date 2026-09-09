"""Geometric counterexamples and independent finite-world loss calculations."""
from copy import deepcopy
from decimal import Decimal
from fractions import Fraction
from itertools import product
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools import perception_reference as reference
from tools.perception_decision import checker, contract, kernel, nuscenes


def digest(value):
    return hashlib.sha256(contract.encoded(value)).hexdigest()


def xy(x, y=0):
    return [contract.wire(Fraction(x)), contract.wire(Fraction(y))]


def declared(state):
    return {'state': state, 'statement': 'Synthetic envelope for a constructed computational test only.',
            'basis_sha256': digest('synthetic basis')}


def object_at(name, x, *, label='car', time=1_000_000, members=None):
    return {'id': name, 'members': members or [name], 'record_sha256': digest([name, str(x), label, time]),
            'state': 'point', 'class': label, 'xy': xy(x), 'timestamp_us': time}


def prediction(sample, x):
    return {'sample_token': sample, 'detection_name': 'car', 'detection_score': Decimal('0.8'),
            'translation': [Decimal(x), 0, 0]}


def inputs(n=1, base=0, camera=3, base_duplicates=1):
    anchors, normals, rows = [], [], []
    source = {'base': 'b'*64, 'camera': 'c'*64, 'clock': 'd'*64}
    for i in range(n):
        sample, name, time = 'sample-'+str(i), 'anchor-'+str(i), 1_000_000+i*1_000_000
        anchor, receipt = nuscenes.normalize_frame(
            sample_token=sample, anchor_id=name, ego_xy=[0, 0], weight=Fraction(1, n),
            base={'state': 'observed', 'value': [prediction(sample, base) for _ in range(base_duplicates)]},
            camera={'state': 'observed', 'value': [prediction(sample, camera)]}, source_sha256=source)
        anchors.append(anchor);normals.append(receipt)
        rows.append({'sample_token': sample, 'anchor_timestamp_us': time,
                     'nominal_ego_xy': {'state': 'observed', 'timestamp_us': time, 'value': xy(0)}})
    case = {'artifact_id': 'reiyah.perception-decision.input', 'version': '0.1.0', 'comparison_id': 'synthetic-comparison',
            'input_scope': 'normalized_research_graphs', 'evidence_kind': 'synthetic', 'cohort_id': 'synthetic-cohort',
            'assumptions': ['Constructed point-reference test, not physical observations.'],
            'loss': {'false_negative': contract.wire(Fraction(1)), 'false_positive': contract.wire(Fraction(1)),
                     'tolerance': contract.wire(Fraction(1, 10))},
            'model': {'variables': [], 'clauses': []}, 'anchors': anchors}
    catalog = {'artifact_id': 'reiyah.perception-inputs.catalog', 'version': '0.1.0', 'anchors': rows,
               'sources': {('metadata' if k == 'clock' else k): {'state': 'observed', 'sha256': v} for k, v in source.items()}}
    spec = {'artifact_id': 'reiyah.perception-reference.input', 'version': '0.1.0', 'coordinate_frame': 'nominal_global_xy',
            'inputs': {'comparison_sha256': digest(case), 'normalizations_sha256': digest(normals), 'catalog_sha256': digest(catalog)},
            'joint_coverage': declared('assumed_complete'), 'worlds': []}
    return spec, case, normals, catalog


def world(name, per_anchor):
    return {'id': name, 'basis_sha256': digest(name), 'anchors': [
        {'anchor_id': 'anchor-'+str(i), 'unlisted_objects': declared('excluded_by_assumption'), 'objects': objs}
        for i, objs in enumerate(per_anchor)]}


def trap(n=1):
    args = inputs(n)
    args[0]['worlds'] = [world('absent', [[object_at('known', Fraction(3, 2), time=(i+1)*1_000_000)] for i in range(n)]),
                         world('present', [[object_at('known', Fraction(3, 2), time=(i+1)*1_000_000),
                                            object_at('disputed', -1, time=(i+1)*1_000_000)] for i in range(n)])]
    return args


def independent_matching(detections, objects):
    """Enumerate partial injections directly from positions, without compiler graphs."""
    def search(i, used):
        if i == len(detections):
            return 0
        best = search(i+1, used)
        label, point = detections[i]
        for j, (kind, location) in enumerate(objects):
            if j not in used and kind == label and sum((a-b)**2 for a, b in zip(point, location)) < 4:
                best = max(best, 1+search(i+1, used | {j}))
        return best
    return search(0, set())


class ReferenceTests(unittest.TestCase):
    def rejected(self, fn, code):
        with self.assertRaises(contract.Invalid) as raised:
            fn()
        self.assertEqual(raised.exception.code, code)

    def checked(self, args):
        compiled, receipt = reference.compile_model(*args)
        packet = kernel.produce(compiled)
        checker.check(compiled, packet)
        return compiled, receipt, packet['result']

    def interval(self, result):
        return tuple(contract.rational(result['bounds'][side]) for side in ('lower', 'upper'))

    def test_matching_path_through_base_neighbor_survives_geometric_compilation(self):
        args = trap();before = deepcopy(args)
        compiled, receipt, result = self.checked(args)
        self.assertEqual(self.interval(result), (-1, 1))
        self.assertEqual(result['physical_coverage'], 'not_established')
        self.assertEqual(result['decision']['preference'], 'unresolved')
        self.assertEqual(receipt['joint_world_count'], 2)
        self.assertEqual(args, before)
        self.assertEqual(sum(e['detection'] == 'base:0' for e in compiled['anchors'][0]['reference']['edges']), 3)

    def test_joint_choice_is_not_replaced_by_independent_anchor_choices(self):
        args = trap(2)
        args[0]['worlds'][0]['anchors'][1]['objects'].append(object_at('disputed', -1, time=2_000_000))
        args[0]['worlds'][1]['anchors'][1]['objects'].pop()
        _, receipt, result = self.checked(args)
        self.assertEqual(self.interval(result), (0, 0))
        self.assertEqual(len(receipt['choice_variables']), 1)
        self.assertEqual(result['decision']['preference'], 'equivalent_within_tolerance')

    def test_strict_distance_and_inclusive_range_use_exact_rationals(self):
        epsilon = Fraction(1, 10**18)
        for location, wanted in [(-2, -1), (-2+epsilon, 1)]:
            args = inputs();args[0]['worlds'] = [world('only', [[object_at('known', Fraction(3, 2)), object_at('disputed', location)]])]
            self.assertEqual(self.interval(self.checked(args)[2]), (wanted, wanted))
        for location, wanted in [(50, 1), (50+epsilon, -1)]:
            args = inputs(base=47, camera=50);args[0]['worlds'] = [world('only', [[object_at('boundary', location)]])]
            self.assertEqual(self.interval(self.checked(args)[2]), (wanted, wanted))

    def test_class_and_alias_alternatives_remain_joint_world_hypotheses(self):
        args = trap();args[0]['worlds'][0]['anchors'][0]['objects'][0]['members'] = ['proposal-a', 'proposal-b']
        objs = args[0]['worlds'][1]['anchors'][0]['objects']
        objs[0]['members'] = ['proposal-a'];objs[1]['members'] = ['proposal-b']
        self.assertEqual(self.interval(self.checked(args)[2]), (-1, 1))
        objs[1]['class'] = 'truck'
        self.assertEqual(self.interval(self.checked(args)[2]), (-1, -1))
        objs[1]['members'] = ['proposal-a']
        self.rejected(lambda: reference.compile_model(*args), 'REFERENCE_ALIAS')

    def test_unknown_coverage_or_object_geometry_keeps_reference_open(self):
        changes = [lambda a: a[0].update(joint_coverage={'state': 'unknown', 'reason': 'Unenumerated joint alternatives'}),
                   lambda a: a[0]['worlds'][0]['anchors'][0].update(unlisted_objects={'state': 'unknown', 'reason': 'Not exhaustively observed'}),
                   lambda a: a[0]['worlds'][0]['anchors'][0].update(objects=[
                       {'id': 'unknown', 'members': ['proposal'], 'record_sha256': 'e'*64, 'state': 'unresolved', 'reason': 'Geometry unclear'}]),
                   lambda a: a[0]['worlds'][0]['anchors'][0]['objects'][0].update(timestamp_us=999999)]
        for change in changes:
            args = trap();change(args);compiled, receipt, result = self.checked(args)
            self.assertEqual(compiled['anchors'][0]['reference']['state'], 'open')
            self.assertTrue(receipt['open_reasons']['anchor-0'])
            self.assertEqual(self.interval(result), (-1, 1))
            self.assertEqual(result['enclosure_kind'], 'conservative_open_reference')

    def test_unused_binary_encodings_do_not_add_phantom_worlds(self):
        for n in (1, 2, 3, 5, 64):
            args = inputs();args[0]['worlds'] = [world('world-'+str(i), [[]]) for i in range(n)]
            compiled, receipt, result = self.checked(args)
            packet = kernel.produce(compiled)
            self.assertEqual(len(packet['proof']['worlds']), n)
            self.assertEqual(self.interval(result), (-1, -1))
            self.assertEqual(receipt['joint_world_count'], n)

    def test_compilation_resource_limit_preserves_open_bound_without_clipping(self):
        args = inputs();objects = [object_at('object-'+str(i), 0) for i in range(65)]
        args[0]['worlds'] = [world('one', [deepcopy(objects)]), world('two', [deepcopy(objects)])]
        compiled, receipt, result = self.checked(args)
        self.assertEqual(receipt['joint_world_count'], 2)
        self.assertEqual(compiled['anchors'][0]['reference']['state'], 'open')
        self.assertIn('compiled_graph_exceeds_core_resource_scope', receipt['open_reasons']['anchor-0'])
        self.assertEqual(self.interval(result), (-1, 1))
        args[0]['worlds'] *= 33
        self.rejected(lambda: reference.compile_model(*args), 'REFERENCE_SIZE')

    def test_dense_edges_and_geometry_work_stop_with_an_open_reference(self):
        args = inputs(base_duplicates=70)
        args[0]['worlds'] = [world('dense', [[object_at('o'+str(i), Fraction(3, 2)) for i in range(30)]])]
        compiled, receipt, result = self.checked(args)
        self.assertEqual(compiled['anchors'][0]['reference']['state'], 'open')
        self.assertEqual(self.interval(result), (-1, 1))
        with patch.object(reference, 'MAX_GEOMETRY_COMPARISONS', 2):
            compiled, receipt, result = self.checked(trap())
        self.assertEqual(compiled['anchors'][0]['reference']['state'], 'open')
        self.assertIn('reference_geometry_work_limit', receipt['open_reasons']['anchor-0'])
        self.assertLessEqual(receipt['geometry_comparisons_budgeted'], 2)

    def test_missing_predictions_stay_blocked_after_reference_compilation(self):
        args = trap()
        anchor = args[1]['anchors'][0]
        anchor['base'] = {'state': 'unmeasured', 'reason': 'Base output unavailable'}
        anchor['additions'] = {'state': 'unknown', 'reason': 'Cannot determine suppression without base'}
        args[2][0]['normalized_anchor_sha256'] = digest(anchor)
        _, receipt, result = self.checked(args)
        self.assertEqual(result['execution_status'], 'input_blocked')
        self.assertIsNone(result['bounds'])
        self.assertIn('required_predictions_unavailable', receipt['open_reasons']['anchor-0'])

    def test_every_world_uses_exactly_the_common_population(self):
        for alteration in [lambda s: s['worlds'][0].update(anchors=[]),
                           lambda s: s['worlds'][0]['anchors'].append(deepcopy(s['worlds'][0]['anchors'][0])),
                           lambda s: s['worlds'][0]['anchors'][0].update(anchor_id='other')]:
            args = trap();alteration(args[0])
            with self.assertRaises(contract.Invalid):reference.compile_model(*args)
        args = trap();args[0]['worlds'][1]['id'] = args[0]['worlds'][0]['id']
        self.rejected(lambda: reference.compile_model(*args), 'REFERENCE_IDENTITY')

    def test_malformed_classes_coordinates_and_coverage_are_rejected(self):
        for change, code in [
            (lambda s: s['worlds'][0]['anchors'][0]['objects'][0].update(**{'class': 'car_typo'}), 'REFERENCE_CLASS'),
            (lambda s: s['worlds'][0]['anchors'][0]['objects'][0].update(xy=[True, 0]), 'REFERENCE_FIELDS'),
            (lambda s: s['worlds'][0]['anchors'][0]['objects'][0]['xy'][0].update(denominator='0'), 'REFERENCE_NUMBER'),
            (lambda s: s['joint_coverage'].update(state='independently_verified'), 'REFERENCE_COVERAGE'),
            (lambda s: s.update(extra=True), 'REFERENCE_FIELDS')]:
            args = trap();change(args[0]);self.rejected(lambda: reference.compile_model(*args), code)

    def test_changed_upstream_operands_or_geometric_records_cannot_be_reused(self):
        for change, code in [
            (lambda a: a[2][0].update(normalized_anchor_sha256='0'*64), 'REFERENCE_BINDING'),
            (lambda a: a[2][0]['qualified_records'][0]['record'].update(xy=xy(100)), 'REFERENCE_BINDING'),
            (lambda a: a[3]['sources']['metadata'].update(sha256='0'*64), 'REFERENCE_BINDING'),
            (lambda a: a[3]['anchors'][0]['nominal_ego_xy'].update(value=xy(1)), 'REFERENCE_POSE'),
            (lambda a: a[2].append(deepcopy(a[2][0])), 'REFERENCE_BINDING'),
            (lambda a: a[3]['anchors'].append(deepcopy(a[3]['anchors'][0])), 'REFERENCE_BINDING')]:
            args = trap();change(args);self.rejected(lambda: reference.compile_model(*args), code)

    def test_preexisting_reference_constraints_cannot_be_replaced_silently(self):
        args = trap();args[1]['model'] = {'variables': ['old'], 'clauses': []}
        self.rejected(lambda: reference.compile_model(*args), 'REFERENCE_PRECONDITION')

    def test_hash_bound_file_entry_point_rejects_parent_changes(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder);spec, case, normals, catalog = trap()
            paths = {k: root/(k+'.json') for k in ['reference', 'comparison', 'normalizations', 'catalog']}
            for k, value in [('reference', spec), ('comparison', case), ('normalizations', normals), ('catalog', catalog)]:
                paths[k].write_bytes(contract.encoded(value))
            kwargs = {k+'_path': v for k, v in paths.items()};kwargs['reference_sha256'] = digest(spec)
            compiled, receipt = reference.compile_files(**kwargs)
            self.assertEqual(receipt['compiled_input_sha256'], digest(compiled))
            for k in paths:
                before = paths[k].read_bytes();paths[k].write_bytes(before+b' ')
                self.rejected(lambda: reference.compile_files(**kwargs), 'INPUT_DIGEST_MISMATCH')
                paths[k].write_bytes(before)
            real_read = Path.read_bytes
            reads = 0
            def changed_source(path):
                nonlocal reads
                data = real_read(path)
                if path == Path(reference.__file__):
                    reads += 1
                    if reads > 1:
                        return data+b'changed'
                return data
            with patch.object(Path, 'read_bytes', changed_source):
                self.rejected(lambda: reference.compile_files(**kwargs), 'REFERENCE_SOURCE_CHANGED')

    def test_enclosures_match_independent_geometric_partial_injections(self):
        locations = [-1, Fraction(3, 2), 3, 51]
        for left, right in product(locations, repeat=2):
            args = inputs();worlds, expected = [], []
            for i, label in enumerate(['car', 'truck', 'outside_target']):
                objs = [object_at('one', left), object_at('two', right, label=label)]
                worlds.append(world('w'+str(i), [objs]))
                admitted = [(o['class'], tuple(contract.rational(q) for q in o['xy'])) for o in objs
                            if o['class'] != 'outside_target' and sum(contract.rational(q)**2 for q in o['xy']) <= 2500]
                base = [('car', (Fraction(0), Fraction(0)))];augmented = base+[('car', (Fraction(3), Fraction(0)))]
                # Compute both full losses, including the common target population.
                m0, m1 = independent_matching(base, admitted), independent_matching(augmented, admitted)
                loss0 = len(admitted)-m0+len(base)-m0
                loss1 = len(admitted)-m1+len(augmented)-m1
                expected.append(loss0-loss1)
            args[0]['worlds'] = worlds
            self.assertEqual(self.interval(self.checked(args)[2]), (min(expected), max(expected)))


if __name__ == '__main__':
    unittest.main()
