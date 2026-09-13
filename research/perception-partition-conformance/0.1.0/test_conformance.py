"""Independent partition coverage and deliberate faults in the new audit."""
from copy import deepcopy
from itertools import product
import unittest

import reproduce as audit

SEPARATE = audit.PARTITIONS.index(((0,), (1,), (2,), (3,)))
MERGED = audit.PARTITIONS.index(((0, 1, 2, 3),))


def specimen(recipe=(SEPARATE, MERGED, 0, 0, 0, 0)):
    return audit.run_case(audit.RECIPES.index(recipe))[1]


def inspect(payload):
    return audit.inspect(payload['inputs'], payload['synthetic_source_records'],
                         payload['compiled'], payload['compilation'], payload['checked_packet'])


def recertify(payload):
    payload['compilation']['compiled_input_sha256'] = audit.digest(payload['compiled'])
    payload['checked_packet'] = audit.kernel.produce(payload['compiled'])
    audit.checker.check(payload['compiled'], payload['checked_packet'])


class ConformanceTests(unittest.TestCase):
    def test_partitions_equal_independent_label_word_enumeration(self):
        expected = set()
        for labels in product(range(4), repeat=4):
            blocks = tuple(tuple(i for i, value in enumerate(labels) if value == label) for label in sorted(set(labels)))
            expected.add(tuple(sorted(blocks)))
        self.assertEqual(len(expected), 15)
        self.assertEqual(set(audit.PARTITIONS), expected)
        self.assertEqual(len(audit.PARTITIONS), len(set(audit.PARTITIONS)))
        self.assertEqual(len(audit.RECIPES), 5400)

    def test_swapped_original_world_partitions_remain_joint(self):
        payload = specimen()
        graphs, _ = inspect(payload)
        self.assertEqual([row['weighted_delta'] for row in graphs], ['0', '0'])
        self.assertEqual({a['delta'] for row in graphs for a in row['anchors']}, {'-1', '1'})
        self.assertEqual([str(audit.number(payload['checked_packet']['result']['bounds'][key])) for key in ('lower', 'upper')], ['0', '0'])
        changed = specimen((SEPARATE, MERGED, 0, 0, 0, 1))
        self.assertEqual([str(audit.number(changed['checked_packet']['result']['bounds'][key])) for key in ('lower', 'upper')], ['-1/3', '1/3'])

    def test_forged_compiled_weights_fail_despite_valid_core_packet(self):
        payload = specimen()
        for ai, weight in enumerate((audit.Fraction(1, 3), audit.Fraction(2, 3))):
            payload['compiled']['anchors'][ai]['weight'] = audit.wire(weight)
        recertify(payload)
        with self.assertRaisesRegex(AssertionError, '^ORIGINAL_OPERANDS$'):
            inspect(payload)

    def test_forged_tolerance_fails_even_when_loss_is_unchanged(self):
        payload = specimen()
        payload['compiled']['loss']['tolerance'] = audit.wire(0)
        recertify(payload)
        with self.assertRaisesRegex(AssertionError, '^ORIGINAL_OPERANDS$'):
            inspect(payload)

    def test_missing_edge_fails_even_when_matching_sizes_are_unchanged(self):
        payload = specimen((SEPARATE, SEPARATE, 0, 0, 0, 0))
        original_bounds = deepcopy(payload['checked_packet']['result']['bounds'])
        payload['compiled']['anchors'][0]['reference']['edges'].pop()
        recertify(payload)
        self.assertEqual(payload['checked_packet']['result']['bounds'], original_bounds)
        with self.assertRaisesRegex(AssertionError, '^EXACT_ORIGINAL_EDGES$'):
            inspect(payload)

    def test_member_order_rewrite_is_detected(self):
        payload = specimen((MERGED, MERGED, 0, 0, 1, 0))
        payload['compilation']['object_mapping'][0]['members'].reverse()
        with self.assertRaisesRegex(AssertionError, '^ORDERED_PROVENANCE$'):
            inspect(payload)

    def test_equal_graphs_do_not_certify_shared_group_identity(self):
        left = audit.PARTITIONS.index(((0, 1), (2, 3)))
        right = audit.PARTITIONS.index(((0, 3), (1, 2)))
        payload = specimen((left, right, 0, 0, 1, 0))
        original_bounds = deepcopy(payload['checked_packet']['result']['bounds'])
        for anchor in payload['compiled']['anchors']:
            anchor['reference']['objects'] = [{'id': f'unsafe:{i}', 'when': []} for i in range(2)]
            anchor['reference']['edges'] = [{'detection': d['id'], 'object': f'unsafe:{i}', 'when': []}
                for d in anchor['base']['value'] + anchor['additions']['value'] for i in range(2)]
        for mapping in payload['compilation']['object_mapping']:
            mapping['graph_id'] = 'unsafe:' + mapping['object_id'].split('-')[-1]
        recertify(payload)
        self.assertEqual(payload['checked_packet']['result']['bounds'], original_bounds)
        with self.assertRaisesRegex(AssertionError, '^SHARED_NODE_IDENTITY$'):
            inspect(payload)

    def test_joint_coverage_unknown_remains_open(self):
        args, _ = audit.make_case(0)
        args[0]['joint_coverage'] = {'state': 'unknown', 'reason': 'Synthetic missing coverage control; no assumption of completeness.'}
        compiled, receipt = audit.reference.compile_model(*args)
        packet = audit.kernel.produce(compiled)
        audit.checker.check(compiled, packet)
        self.assertEqual([a['reference']['state'] for a in compiled['anchors']], ['open', 'open'])
        self.assertEqual([str(audit.number(packet['result']['bounds'][key])) for key in ('lower', 'upper')], ['-1', '1'])
        self.assertEqual(packet['result']['physical_coverage'], 'not_established')
        self.assertEqual(receipt['mapping_scope'], 'proposed_graph_nodes_before_any_open_reference_fallback')


if __name__ == '__main__':
    unittest.main()
