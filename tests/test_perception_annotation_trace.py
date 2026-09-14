"""Source-identity and joint-deletion traps for the offline trace example."""
from copy import deepcopy
from decimal import Decimal
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from tools import perception_annotations as adapter
from tools.perception_decision import contract
from tests.test_perception_annotations import annotation, fixture, source

SCRIPT = Path(__file__).resolve().parents[1]/'research/perception-annotation-trace/0.1.0/replay.py'
SPEC = importlib.util.spec_from_file_location('annotation_trace_example', SCRIPT)
trace = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(trace)


def prepared(root, redundant=False):
    def change(tables):
        tables['category.json'][0]['description'] = 'été'
        if redundant:
            tables['sample_annotation.json'].insert(2, annotation('redundant', -1))
    request, _ = fixture(root, change=change)
    docs = adapter.build(request)
    for role in ('catalog', 'normalizations', 'renamings'):
        docs[role] = json.loads(Path(request['inputs'][role]['path']).read_bytes())
    core = docs['comparison.json']; a = core['anchors'][0]
    reference = docs['reference.json']['worlds'][0]['anchors'][0]['objects']
    mappings = docs['compilation.json']['object_mapping']
    docs['source_map'] = {'core_comparison_sha256': trace.digest(core), 'mappings': [
        {**m, 'neutral_anchor_id': a['id'], 'reference_object': reference[i]} for i, m in enumerate(mappings)]}
    docs['renamings']['renamings'][0]['sample_token'] = 'sample-0'
    docs['case'] = {'loss': {k: str(contract.rational(v)) for k, v in core['loss'].items()},
        'anchors': [{'id': a['id'], 'weight': '1', 'reference_state': 'finite',
                     'objects': [{'id': x['id'], 'class': 'car'} for x in a['reference']['objects']],
                     'base_detections': [{'id': x['id'], 'class': 'car'} for x in a['base']['value']],
                     'added_detections': [{'id': x['id'], 'class': 'car'} for x in a['additions']['value']]}],
        'joint_worlds': [{'world_id': 'benchmark-labels', 'per_anchor': {a['id']: {
            'objects_present': [x['id'] for x in a['reference']['objects']],
            'edges': [[e['detection'], e['object']] for e in a['reference']['edges']]}}}]}
    targets = [{'anchor_id': a['id'], 'world_id': 'benchmark-labels', 'local_index': i,
                'graph_id': x['id'], 'class': 'car'} for i, x in enumerate(a['reference']['objects'])]
    return docs, targets


def group(indices, delta, criterion, preference):
    return {'target_indices': indices, 'expected_delta': delta,
            'expected_criterion': criterion, 'expected_preference': preference}


class AnnotationTraceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def reject(self, code, fn):
        with self.assertRaises(contract.Invalid) as raised:
            fn()
        self.assertEqual(raised.exception.code, code)

    def test_joint_deletion_survives_when_both_individual_deletions_are_absorbed(self):
        docs, targets = prepared(self.root, redundant=True)
        trace.check_case(docs)
        groups = [group([1], '1', 'supported', 'prefer_augmented'),
                  group([2], '1', 'supported', 'prefer_augmented'),
                  group([1, 2], '-1', 'excluded', 'prefer_base'),
                  group([0], '-1', 'excluded', 'prefer_base')]
        results = trace.evaluate_groups(docs, targets, groups)
        self.assertEqual([contract.rational(r['result']['bounds']['lower']) for r in results], [1, 1, -1, -1])

    def test_original_utf8_record_bytes_indices_and_zero_point_metadata_preserved(self):
        docs, targets = prepared(self.root)
        resolved = [trace.resolve(docs, t) for t in targets]
        out = self.root/'out'; out.mkdir(); (out/'records').mkdir()
        trace.original_annotations(docs, resolved, out)
        self.assertEqual([t['annotation']['num_lidar_pts'] for t in resolved], [0, 0])
        for t in resolved:
            for entry in t['original_records'].values():
                raw = Path(entry['extracted_path']).read_bytes()
                self.assertEqual(trace.sha(raw), entry['binding']['sha256'])
        self.assertEqual(resolved[0]['original_records']['annotation']['binding']['row_index'], 0)
        self.assertIn('été', Path(resolved[0]['original_records']['category']['extracted_path']).read_text())

    def test_local_index_is_not_graph_suffix_or_boolean(self):
        docs, targets = prepared(self.root)
        for value in (True, -1, 2):
            bad = {**targets[0], 'local_index': value}
            self.reject('TRACE_INDEX', lambda: trace.resolve(docs, bad))
        self.reject('TRACE_INDEX', lambda: trace.resolve(docs, {**targets[0], 'graph_id': targets[1]['graph_id']}))

    def test_world_anchor_and_full_source_mapping_required(self):
        docs, targets = prepared(self.root)
        for key in ('world_id', 'anchor_id'):
            self.reject('TRACE_JOIN', lambda: trace.resolve(docs, {**targets[0], key: 'other'}))
        changed = deepcopy(docs)
        changed['source_map']['mappings'].append(deepcopy(changed['source_map']['mappings'][0]))
        self.reject('TRACE_JOIN', lambda: trace.resolve(changed, targets[0]))
        changed = deepcopy(docs)
        changed['source_map']['mappings'][0]['record_sha256'] = '0'*64
        self.reject('TRACE_MAPPING', lambda: trace.resolve(changed, targets[0]))

    def test_wrong_original_index_rejected_even_when_literal_hash_is_unchanged(self):
        docs, targets = prepared(self.root)
        resolved = [trace.resolve(docs, targets[0])]
        resolved[0]['annotation']['annotation_source']['row_index'] = 1
        out = self.root/'out'; out.mkdir(); (out/'records').mkdir()
        self.reject('TRACE_ROW', lambda: trace.original_annotations(docs, resolved, out))

    def test_wrong_case_and_open_reference_are_distinct(self):
        docs, _ = prepared(self.root)
        changed = deepcopy(docs); changed['source_map']['core_comparison_sha256'] = '0'*64
        self.reject('TRACE_CASE', lambda: trace.check_case(changed))
        changed = deepcopy(docs); changed['case']['anchors'][0]['reference_state'] = 'open'
        self.reject('TRACE_SCOPE', lambda: trace.check_case(changed))

    def test_unselected_exported_classes_must_match_sources(self):
        docs, _ = prepared(self.root)
        for role in ('base_detections', 'added_detections', 'objects'):
            changed = deepcopy(docs)
            changed['case']['anchors'][0][role][0]['class'] = 'pedestrian'
            self.reject('TRACE_CASE', lambda: trace.check_case(changed))

    def test_group_cannot_claim_individual_flip_or_repeat_a_target(self):
        docs, targets = prepared(self.root, redundant=True)
        self.reject('TRACE_WITNESS', lambda: trace.evaluate_groups(docs, targets,
            [group([1], '-1', 'excluded', 'prefer_base')]))
        self.reject('TRACE_INDEX', lambda: trace.evaluate_groups(docs, targets,
            [group([1, 1], '-1', 'excluded', 'prefer_base')]))
        self.reject('TRACE_SELECTION', lambda: trace.evaluate_groups(docs, targets,
            [group([1], '1', 'supported', 'prefer_augmented')]))

    def test_unknown_target_fields_do_not_become_human_observation(self):
        docs, targets = prepared(self.root)
        self.reject('TRACE_FIELDS', lambda: trace.resolve(docs, {**targets[0], 'human_verified': True}))

    def test_relative_capture_escape_is_refused(self):
        self.reject('TRACE_PATH', lambda: trace.file_spec(self.root,
            {'filename': '../other.jpg', 'byte_size': 1, 'sha256': '0'*64}))

    def test_research_cost_decimal_is_not_an_engine_operand(self):
        spec = source(self.root, 'report.json', b'{"cost_seconds":0.0083}')
        self.assertEqual(trace.source_document(spec)['cost_seconds'], Decimal('0.0083'))
        self.reject('INVALID_NUMBER', lambda: trace.document(spec))
        duplicate = source(self.root, 'duplicate.json', b'{"cost_seconds":0.0083,"cost_seconds":0}')
        self.reject('SOURCE_JSON', lambda: trace.source_document(duplicate))


if __name__ == '__main__':
    unittest.main()
