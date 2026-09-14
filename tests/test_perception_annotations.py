"""Synthetic boundary/custody tests; no generated row is a human observation."""
from copy import deepcopy
from fractions import Fraction
import hashlib
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch

from tools import perception_annotations as adapter
from tools.perception_decision import checker, contract, kernel
from tests.test_perception_reference import inputs, xy


def source(root, name, data):
    path = root/name
    path.write_bytes(data)
    return {'path': str(path), 'byte_size': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def annotation(name, x, *, sample='sample-0'):
    return {'token': name, 'sample_token': sample, 'instance_token': 'instance',
            'attribute_tokens': [], 'visibility_token': '', 'translation': [x, 0, 0],
            'size': [1, 1, 1], 'rotation': [1, 0, 0, 0], 'prev': '', 'next': '',
            'num_lidar_pts': 0, 'num_radar_pts': 0}


def fixture(root, *, change=None):
    tables = {
        'sample.json': [{'token': 'sample-0', 'scene_token': 'scene', 'timestamp': 1000000, 'prev': '', 'next': ''},
                        {'token': 'context', 'scene_token': 'scene', 'timestamp': 2000000, 'prev': '', 'next': ''}],
        'sample_annotation.json': [annotation('known', 1.5), annotation('new', -1),
                                   annotation('context-label', 3, sample='context')],
        'instance.json': [{'token': 'instance', 'category_token': 'category', 'first_annotation_token': 'known',
                           'last_annotation_token': 'new', 'nbr_annotations': 3}],
        'category.json': [{'token': 'category', 'name': 'vehicle.car', 'description': 'Synthetic test category'}],
    }
    if change:
        change(tables)
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode='w:gz') as archive:
        for name, rows in tables.items():
            data = json.dumps(rows, ensure_ascii=False).encode()
            member = tarfile.TarInfo('v1.0-trainval/'+name)
            member.size = len(data)
            archive.addfile(member, io.BytesIO(data))
    metadata = source(root, 'metadata.tgz', raw.getvalue())
    _, case, normals, catalog = inputs()
    normals[0]['source_sha256']['clock'] = metadata['sha256']
    catalog['sources']['metadata'] = metadata
    catalog['anchors'][0]['scene_token'] = 'scene'
    mappings = [{'original_anchor_id': 'anchor-0', 'neutral_anchor_id': 'anchor-0',
                 'detections': [{'original': row['detection'], 'neutral': row['detection']}
                                for row in normals[0]['qualified_records']]}]
    docs = {'comparison': case, 'normalizations': normals, 'catalog': catalog,
            'common_comparison': deepcopy(case), 'renamings': {'renamings': mappings}}
    selected = {role: source(root, role+'.json', contract.encoded(doc)) for role, doc in docs.items()}
    selected['metadata'] = metadata
    return {'artifact_id': 'reiyah.perception-annotations.request', 'version': '0.1.0',
            'policy': adapter.POLICY, 'inputs': selected}, tables


class AnnotationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def reject(self, code, function):
        with self.assertRaises(contract.Invalid) as caught:
            function()
        self.assertEqual(caught.exception.code, code)

    def test_source_bound_competition_zero_point_retention_and_no_human_admission(self):
        request, _ = fixture(self.root)
        before = {k: Path(v['path']).read_bytes() for k, v in request['inputs'].items()}
        with patch('tools.perception_admission.build', side_effect=AssertionError('Human admission called')):
            files = adapter.build(request)
        result = files['RESULT.json']
        self.assertEqual(result['admitted_human_readings'], 0)
        self.assertFalse(result['original_reference_changed'])
        self.assertEqual(result['source_annotation_count'], 2)
        self.assertEqual(result['annotation_rows_scanned'], 3)
        self.assertEqual(result['anchors'][0]['included_annotations'], 2)
        self.assertEqual([contract.rational(result['result']['bounds'][k]) for k in ('lower', 'upper')], [1, 1])
        self.assertEqual(files['comparison.json']['evidence_kind'], 'synthetic')
        with patch.object(kernel, '_matching_certificate', side_effect=AssertionError('Producer called')):
            checker.check(files['comparison.json'], files['decision-payload.json'])
        self.assertEqual(before, {k: Path(v['path']).read_bytes() for k, v in request['inputs'].items()})

    def test_row_offsets_point_to_literal_original_bytes(self):
        request, _ = fixture(self.root, change=lambda t: t['category.json'][0].update(description='été'))
        files = adapter.build(request)
        with tarfile.open(request['inputs']['metadata']['path']) as archive:
            for row in files['annotations.json']:
                selections = [('sample_annotation.json', row['annotation_source']),
                              ('sample.json', row['sample']['source']),
                              ('instance.json', row['instance']['source']),
                              ('category.json', row['category']['source'])]
                for table, binding in selections:
                    data = archive.extractfile('v1.0-trainval/'+table).read()
                    piece = data[binding['byte_offset']:binding['byte_offset']+binding['byte_size']]
                    self.assertEqual(hashlib.sha256(piece).hexdigest(), binding['sha256'])
                    self.assertEqual(json.loads(piece), json.loads(data)[binding['row_index']])

    def test_only_actual_empty_annotation_table_is_observed_empty(self):
        request, _ = fixture(self.root, change=lambda t: t.update({'sample_annotation.json': []}))
        result = adapter.build(request)['RESULT.json']
        self.assertEqual(result['source_annotation_count'], 0)
        self.assertEqual(contract.rational(result['result']['bounds']['lower']), -1)
        self.assertEqual(result['anchors'][0]['reference_state'], 'finite')
        Path(request['inputs']['metadata']['path']).unlink()
        with self.assertRaises(FileNotFoundError):
            adapter.build(request)

    def test_original_source_digest_mismatch_rejected(self):
        request, _ = fixture(self.root)
        path = Path(request['inputs']['metadata']['path'])
        data = path.read_bytes()
        path.write_bytes(bytes([data[0] ^ 1])+data[1:])
        self.reject('SOURCE_DIGEST', lambda: adapter.build(request))

    def test_unknown_policy_and_fields_rejected(self):
        request, _ = fixture(self.root)
        bad = deepcopy(request)
        bad['policy'] = 'benchmark_is_physical_truth'
        self.reject('ANNOTATION_POLICY', lambda: adapter.build(bad))
        bad = deepcopy(request)
        bad['admitted_human_readings'] = 2
        self.reject('ANNOTATION_FIELDS', lambda: adapter.build(bad))

    def test_duplicate_annotation_and_missing_class_join_rejected(self):
        for name, change, code in [
            ('duplicate', lambda t: t['sample_annotation.json'].append(t['sample_annotation.json'][0]), 'ANNOTATION_DUPLICATE'),
            ('category', lambda t: t.update({'category.json': []}), 'ANNOTATION_CATEGORY'),
            ('instance', lambda t: t.update({'instance.json': []}), 'ANNOTATION_INSTANCE')]:
            with self.subTest(name=name):
                root = self.root/name
                root.mkdir()
                request, _ = fixture(root, change=change)
                self.reject(code, lambda: adapter.build(request))

    def test_wrong_time_and_scene_rejected(self):
        for field, value, code in [('timestamp', 1000001, 'ANNOTATION_TIME'), ('scene_token', 'other', 'ANNOTATION_SAMPLE')]:
            root = self.root/field
            root.mkdir()
            request, _ = fixture(root, change=lambda t: t['sample.json'][0].update({field: value}))
            self.reject(code, lambda: adapter.build(request))

    def test_malformed_selected_geometry_is_not_silently_dropped(self):
        request, _ = fixture(self.root, change=lambda t: t['sample_annotation.json'][0].update(translation=[float('nan'), 0, 0]))
        self.reject('ADAPTER_NUMBER', lambda: adapter.build(request))

    def test_range_boundary_and_unmapped_categories_have_explicit_dispositions(self):
        request, _ = fixture(self.root)
        files = adapter.build(request)
        wanted = {'sample-0': {'anchor_id': 'anchor-0', 'ego': (Fraction(0), Fraction(0)), 'time': 1000000}}
        rows = [deepcopy(files['annotations.json'][0]) for _ in range(3)]
        for row, name, x in zip(rows, ('boundary', 'outside', 'unmapped'), (Fraction(50), Fraction(50)+Fraction(1, 10**18), Fraction(0))):
            row['annotation_token'] = name
            row['translation'] = xy(x)+[contract.wire(Fraction(0))]
        rows[2]['category']['record']['name'] = 'human.pedestrian.stroller'
        spec, dispositions = adapter.model_from_annotations(rows, wanted, files['reference.json']['inputs'], 'b'*64)
        self.assertEqual([r['disposition'] for r in dispositions], ['included', 'outside_nominal_50m', 'unmapped_category'])
        self.assertEqual([o['id'] for o in spec['worlds'][0]['anchors'][0]['objects']], ['boundary'])

    def test_object_limit_fails_without_clipping(self):
        request, _ = fixture(self.root, change=lambda t: t.update({'sample_annotation.json': [annotation('object-'+str(i), 0) for i in range(129)]}))
        self.reject('ANNOTATION_LIMIT', lambda: adapter.build(request))

    def test_different_neutral_prediction_bytes_rejected(self):
        request, _ = fixture(self.root)
        case = json.loads(Path(request['inputs']['common_comparison']['path']).read_bytes())
        case['anchors'][0]['base']['value'][0]['record_sha256'] = 'a'*64
        request['inputs']['common_comparison'] = source(self.root, 'forged-common.json', contract.encoded(case))
        self.reject('REVIEWED_MAPPING', lambda: adapter.build(request))

    def test_output_reuse_and_input_directory_alias_rejected(self):
        source_root = self.root/'sources'
        source_root.mkdir()
        request, _ = fixture(source_root)
        spec = source(self.root, 'request.json', contract.encoded(request))
        output = self.root/'result'
        adapter.run(Path(spec['path']), spec['sha256'], output)
        before = {p.name: p.read_bytes() for p in output.iterdir()}
        self.reject('ANNOTATION_OUTPUT', lambda: adapter.run(Path(spec['path']), spec['sha256'], output))
        alias = self.root/'alias'
        alias.symlink_to(source_root, target_is_directory=True)
        self.reject('ANNOTATION_OUTPUT', lambda: adapter.run(Path(spec['path']), spec['sha256'], alias/'result'))
        self.assertEqual(before, {p.name: p.read_bytes() for p in output.iterdir()})


if __name__ == '__main__':
    unittest.main()
