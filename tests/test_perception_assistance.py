"""Full source population, adverse rows, stage separation and forged membership."""
from copy import deepcopy
from decimal import Decimal
from fractions import Fraction
import io
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools import perception_assistance as assistance, perception_assistance_sources as sources
from tools.perception_decision import contract as decision, nuscenes
from tools.perception_inputs.catalog import prediction_index
from tools.perception_observation import package
from tests.test_perception_binding import prepare
from tests.test_perception_geometry import values
from tests.test_perception_inputs import meta_bytes
from tests.test_perception_observation import read, replace, rebind_window, tree
from tests.test_perception_windows import identity_file


def fixture(root):
    observation, request = prepare(root)
    data = values()
    data.update({'category.json': [{'token': 'category', 'name': 'animal', 'description': 'Outside detector taxonomy'}],
                 'attribute.json': [], 'visibility.json': [{'token': '1', 'level': 'low', 'description': 'Source visibility'}],
                 'instance.json': [], 'sample_annotation.json': []})
    for scene in range(2):
        data['instance.json'].append({'token': f'track-{scene}', 'category_token': 'category', 'nbr_annotations': 5,
                                     'first_annotation_token': f'annotation-{scene}-0', 'last_annotation_token': f'annotation-{scene}-4'})
        for i in range(5):
            data['sample_annotation.json'].append({'token': f'annotation-{scene}-{i}', 'sample_token': f'f{scene}-{i}',
                'instance_token': f'track-{scene}', 'attribute_tokens': [], 'visibility_token': '' if i == 0 else '1',
                'translation': [10000, 20, 0], 'size': [1, 2, 3], 'rotation': [1, 0, 0, 0],
                'num_lidar_pts': 0, 'num_radar_pts': 0,
                'prev': f'annotation-{scene}-{i-1}' if i else '', 'next': f'annotation-{scene}-{i+1}' if i < 4 else ''})
    metadata = identity_file(root/'metadata.tgz', meta_bytes(data))
    cat = read(request['catalog']); cat['sources']['metadata'] = metadata
    by_role = {}
    for role, offset in [('base', 0), ('camera', 3)]:
        rows = {}
        for a in cat['anchors']:
            sample = a['sample_token']
            row = {'sample_token': sample, 'detection_name': 'car', 'detection_score': 1,
                   'translation': [10+offset, 20, 0], 'size': [1, 2, 3], 'rotation': [1, 0, 0, 0],
                   'velocity': [0, 0], 'attribute_name': ''}
            rows[sample] = [row, row | {'detection_score': 0}, row | {'translation': [10000, 0, 0]}]
        # One explicitly empty output and one genuinely missing key.
        rows['f0-0'] = []; del rows['f1-4']
        raw = decision.encoded({'meta': {k: False for k in ('use_camera', 'use_lidar', 'use_radar', 'use_map', 'use_external')},
                                'results': rows})
        spec = identity_file(root/(role+'.json'), raw) | {'state': 'observed'}
        cat['sources'][role] = spec
        index, _ = prediction_index(io.BytesIO(raw), spec['sha256'], {a['sample_token'] for a in cat['anchors']})
        for a in cat['anchors']:
            a[role] = index.get(a['sample_token'], {'state': 'missing', 'reason': 'No results key in verified source',
                                                  'source_sha256': spec['sha256']})
        by_role[role] = rows
    replace(request, 'catalog', cat)
    windows = read(observation['window_report'])
    windows['inputs'].update(catalog=request['catalog'], metadata=metadata)
    rebind_window(observation, windows)
    geometry = read(observation['geometry_report']); geometry['inputs'].update(catalog=request['catalog'], metadata=metadata)
    replace(observation, 'geometry_report', geometry)
    case = read(request['comparison']); normals = []
    for i, a in enumerate(case['anchors']):
        sample = windows['windows'][i]['sample_token']
        anchor, normal = nuscenes.normalize_frame(sample_token=sample, anchor_id=a['id'], weight=Fraction(1, 2),
            ego_xy=[10, 20], **{role: {'state': 'observed', 'value': by_role[role][sample]} for role in ('base', 'camera')},
            source_sha256={role: cat['sources'][role]['sha256'] for role in ('base', 'camera')} | {'clock': metadata['sha256']})
        case['anchors'][i] = anchor; normals.append(normal)
    replace(request, 'comparison', case); replace(request, 'normalizations', normals)
    out = root/'observations'; cust = root/'custody.json'
    result = package.build(observation, out, cust)
    request.update(observation_custody=identity_file(cust, cust.read_bytes()),
                   package={'path': str(out), 'seal_sha256': result['seal_sha256']})
    return request, data, cat


class AssistanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.request, self.data, self.catalog = fixture(self.root)

    def reject(self, fn, code):
        with self.assertRaises(decision.Invalid) as caught: fn()
        self.assertEqual(caught.exception.code, code)

    def selection(self):
        manifest = json.loads((Path(self.request['package']['path'])/'manifest.json').read_bytes())
        windows = read(self.request['observation_custody'])['windows']
        chosen, occurrences = sources.selected_frames(self.catalog, windows, manifest)
        return chosen, windows, occurrences

    def metadata(self, data=None, chosen=None, windows=None, occurrences=None):
        if chosen is None: chosen, windows, occurrences = self.selection()
        spec = identity_file(self.root/'changed.tgz', meta_bytes(data or self.data))
        return sources.metadata(spec, chosen, windows, occurrences)

    def test_full_pipeline_unfiltered_rows_neutrality_and_repeat_bytes(self):
        files, context = assistance.materialize(self.request, 'configuration-2')
        self.assertEqual(files, assistance.materialize(self.request, 'configuration-2')[0])
        common = json.loads(files['common/assistance.json'])
        self.assertEqual(context['summary']['distinct_keyframes'], 10)
        self.assertEqual(context['summary']['comparison_anchors'], 2)
        self.assertEqual(context['summary']['annotations'], 10)
        self.assertEqual(context['summary']['prediction_rows'], {'configuration-1': 24, 'configuration-2': 24})
        self.assertEqual(common['frames'][0]['annotations']['value'][0]['visibility'], {'state': 'not_annotated'})
        self.assertEqual(common['frames'][0]['annotations']['value'][0]['category']['name'], 'animal')
        self.assertEqual(common['frames'][1]['predictions']['configuration-1']['value'][1]['detection_score'], '0')
        self.assertEqual(common['frames'][1]['predictions']['configuration-1']['value'][2]['translation'][0], '10000')
        self.assertEqual(common['frames'][0]['predictions']['configuration-1'], {'state': 'observed', 'value': []})
        self.assertEqual(common['frames'][-1]['predictions']['configuration-1']['state'], 'missing')
        for canary in (str(self.root), 'f0-2', 'sample_token', 'source_sha256', 'base:', 'camera:', 'anchor_timestamp_us'):
            self.assertNotIn(canary.encode(), files['common/assistance.json'])
        self.assertEqual(common['status'], 'prepared_not_disclosed')
        self.assertEqual(common['box_time'], 'keyframe_time_only_no_interpolation_or_object_motion_compensation')

    def test_empty_other_frame_cannot_impersonate_nonempty_or_absent_output(self):
        chosen, _, _ = self.selection()
        for target in ('f0-2', 'f1-4'):
            forged = deepcopy(chosen); forged[target]['base'] = deepcopy(forged['f0-0']['base'])
            self.reject(lambda: sources.predictions(self.catalog, forged), 'ASSISTANCE_PREDICTION')

    def test_descriptor_types_and_full_parent_bytes_are_bound(self):
        chosen, _, _ = self.selection()
        forged = deepcopy(chosen); forged['f0-0']['base']['row_count'] = False
        self.reject(lambda: sources.predictions(self.catalog, forged), 'ASSISTANCE_PREDICTION')
        path = Path(self.catalog['sources']['base']['path']); path.write_bytes(path.read_bytes()+b' ')
        self.reject(lambda: sources.predictions(self.catalog, chosen), 'SOURCE_SIZE')

    def test_source_sample_omission_extra_wrong_scene_and_clock_are_rejected(self):
        chosen, windows, occurrences = self.selection()
        for change in ('drop', 'time', 'scene', 'duplicate'):
            data = deepcopy(self.data)
            if change == 'drop': data['sample.json'].pop(0)
            if change == 'time': data['sample.json'][0]['timestamp'] += 1
            if change == 'scene': data['sample.json'][0]['scene_token'] = 'another-scene'
            if change == 'duplicate': data['sample.json'].append(deepcopy(data['sample.json'][0]))
            self.reject(lambda: self.metadata(data, chosen, windows, occurrences),
                        'ASSISTANCE_DUPLICATE' if change == 'duplicate' else 'ASSISTANCE_POPULATION')
        missing = deepcopy(chosen); del missing['f0-0']
        self.reject(lambda: self.metadata(chosen=missing, windows=windows, occurrences=occurrences), 'ASSISTANCE_POPULATION')

    def test_overlapping_windows_share_frames_but_preserve_occurrences(self):
        chosen, windows, _ = self.selection()
        windows[1] = windows[0] | {'window_id': 'window-0002'}
        manifest = {'windows': [{'id': w['window_id'], 'interval_us': [-2000000, 2000000]} for w in windows]}
        selected, occurrences = sources.selected_frames(self.catalog, windows, manifest)
        self.assertEqual(len(selected), 5); self.assertEqual(sum(len(o['keyframes']) for o in occurrences), 10)
        self.assertEqual(occurrences[0]['keyframes'], occurrences[1]['keyframes'])

    def test_temporal_outside_missing_wrong_instance_and_nonreciprocal_links(self):
        chosen, windows, occurrences = self.selection()
        chosen = {k: v for k, v in chosen.items() if k not in ('f0-0', 'f0-4', 'f1-0', 'f1-4')}
        for o in occurrences: o['interval_us'] = [-1000000, 1000000]
        rows, inst, lookups, tokens, _ = self.metadata(chosen=chosen, windows=windows, occurrences=occurrences)
        projected, _ = sources.annotation_rows(chosen, rows, inst, lookups, tokens)
        self.assertEqual(projected['f0-1'][0]['prev'], {'state': 'outside_package'})
        for field, value in [('next', 'missing'), ('instance_token', 'wrong-track'), ('next', '')]:
            data = deepcopy(self.data); data['sample_annotation.json'][0][field] = value
            self.reject(lambda: self.metadata(data, chosen, windows, occurrences), 'ASSISTANCE_JOIN')

    def test_missing_tables_duplicates_and_broken_lookup_never_become_empty(self):
        data = deepcopy(self.data); del data['sample_annotation.json']
        self.reject(lambda: self.metadata(data), 'METADATA_TABLE')
        data = deepcopy(self.data); data['sample_annotation.json'].append(deepcopy(data['sample_annotation.json'][0]))
        self.reject(lambda: self.metadata(data), 'ASSISTANCE_DUPLICATE')
        data = deepcopy(self.data); data['category.json'] = []
        values_ = self.metadata(data); chosen, _, _ = self.selection()
        self.reject(lambda: sources.annotation_rows(chosen, *values_[:4]), 'ASSISTANCE_JOIN')

    def test_invalid_unused_numbers_preserved_without_geometry_promotion(self):
        row = {'translation': [1, 2, Decimal('NaN')], 'size': [1, 2, 3], 'rotation': [0, 0, 0, 0],
               'velocity': [Decimal('Infinity'), 0], 'detection_name': 'car', 'detection_score': Decimal('.25'), 'attribute_name': ''}
        output = sources.prediction_rows({'state': 'observed', 'value': [row]}, 'neutral')
        self.assertEqual(output['value'][0]['translation'][2]['state'], 'nonfinite_source_value')
        self.assertEqual(output['value'][0]['rotation'], ['0']*4)
        self.assertEqual(output['value'][0]['detection_score'], '0.25')
        self.reject(lambda: sources.vector([True, 0, 0], 3), 'ASSISTANCE_NUMBER')

    def test_normalization_receipt_forgery_is_rejected(self):
        chosen, windows, _ = self.selection(); outputs = sources.predictions(self.catalog, chosen)
        normals = read(self.request['normalizations']); normals[0]['trace'][0]['score_eligible'] = False
        self.reject(lambda: assistance.normalize_check(read(self.request['comparison']), normals, self.catalog, outputs, windows),
                    'ASSISTANCE_NORMALIZATION')

    def test_new_global_transform_rejects_forged_content_and_unavailable_matrix(self):
        for malformed, code in [({'state': 'available', 'matrix': 'PRIVATE-SOURCE-CANARY'}, 'OBS_MATRIX'),
                                ({'state': 'unavailable', 'matrix': 'PRIVATE-SOURCE-CANARY'}, 'OBS_SOURCE'),
                                ({'state': 'available'}, 'OBS_SOURCE')]:
            with self.subTest(malformed=malformed):
                record = read(self.request['observation_custody'])
                geometry = read(record['request']['geometry_report'])
                geometry['windows'][0]['nominal_anchor_ego_to_global'] = malformed
                replace(record['request'], 'geometry_report', geometry)
                record['request_sha256'] = hashlib.sha256(decision.encoded(record['request'])).hexdigest()
                replace(self.request, 'observation_custody', record)
                self.reject(lambda: assistance.materialize(self.request, 'configuration-2'), code)

    def test_false_endpoint_cannot_hide_an_outside_predecessor(self):
        chosen, windows, occurrences = self.selection()
        chosen = {k: v for k, v in chosen.items() if k not in ('f0-0', 'f0-4', 'f1-0', 'f1-4')}
        for o in occurrences: o['interval_us'] = [-1000000, 1000000]
        data = deepcopy(self.data); data['sample_annotation.json'][1]['prev'] = ''
        self.reject(lambda: self.metadata(data, chosen, windows, occurrences), 'ASSISTANCE_JOIN')

    def test_instance_endpoint_type_is_a_declared_invalid_input(self):
        data = deepcopy(self.data); data['instance.json'][0]['first_annotation_token'] = []
        self.reject(lambda: self.metadata(data), 'CLOCK_IDENTITY')

    def test_limits_are_checked_during_selection_and_projection(self):
        with patch.object(sources, 'MAX_FRAMES', 1):
            self.reject(self.selection, 'ASSISTANCE_LIMIT')
        with patch.object(sources, 'MAX_SELECTED_BYTES', 1):
            self.reject(self.metadata, 'ASSISTANCE_LIMIT')
        chosen, _, _ = self.selection()
        with patch.object(sources, 'MAX_SELECTED_BYTES', 1):
            self.reject(lambda: sources.predictions(self.catalog, chosen), 'ASSISTANCE_LIMIT')

    def test_output_receipt_last_no_overwrite_and_changed_bytes_rejected(self):
        spec = identity_file(self.root/'request.json', decision.encoded(self.request))
        out = self.root/'prepared'
        result = assistance.run(Path(spec['path']), spec['sha256'], 'configuration-2', out)
        self.assertFalse(result['assisted_evidence_released'])
        receipt = json.loads((out/'PREPARATION.json').read_bytes())
        self.assertFalse(receipt['reference_constraints_admitted'])
        self.reject(lambda: assistance.run(Path(spec['path']), spec['sha256'], 'configuration-2', out), 'OUTPUT_EXISTS')
        files = {k: v for k, v in tree(out).items() if k != 'PREPARATION.json'}
        (out/'PREPARATION.json').unlink()
        path = out/'common/assistance.json'; original = path.read_bytes()
        path.write_bytes(b'X'+original[1:])
        self.reject(lambda: assistance.verify_files(out, files), 'ASSISTANCE_OUTPUT_CHANGED')


if __name__ == '__main__':
    unittest.main()
