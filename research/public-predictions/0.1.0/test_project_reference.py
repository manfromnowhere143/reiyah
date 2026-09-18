"""Synthetic source-join and projection-admission controls; no dataset access."""
import copy
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from admission import Rejected
from project_reference import TABLES, classify_projection, collect, qualify


class ProjectionControls(unittest.TestCase):
    def setUp(self):
        self.area = tempfile.TemporaryDirectory(); self.addCleanup(self.area.cleanup)
        path = Path(self.area.name) / 'already-bound-image'; path.write_bytes(b'fixture image bytes')
        calibration = {'token': 'calibration', 'sensor_token': 'sensor', 'camera_intrinsic': [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
                       'rotation': [1, 0, 0, 0], 'translation': [0, 0, 0]}
        pose = {'token': 'pose', 'timestamp': 110, 'rotation': [1, 0, 0, 0], 'translation': [0, 0, 0]}
        self.image = {'id': 'image-00', 'sensor_sample_token': 'camera', 'width': 1600, 'height': 900,
            'image_path': str(path), 'bytes': path.stat().st_size,
            'image_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'evidence': {'calibration': calibration, 'ego_pose': pose, 'relative_asset_path': 'samples/CAM_FRONT/a.jpg',
                         'sensor_timestamp_us': 110}}
        self.tables = {name: {} for name in TABLES}
        self.tables.update(ego_pose={'pose': pose}, calibrated_sensor={'calibration': calibration},
            sensor={'sensor': {'token': 'sensor', 'modality': 'camera', 'channel': 'CAM_FRONT'}},
            category={'car-category': {'token': 'car-category', 'name': 'vehicle.car'}},
            instance={'instance': {'token': 'instance', 'category_token': 'car-category'}},
            scene={'scene': {'token': 'scene'}},
            sample={'sample': {'token': 'sample', 'scene_token': 'scene', 'timestamp': 100}},
            sample_data={'camera': {'token': 'camera', 'sample_token': 'sample', 'calibrated_sensor_token': 'calibration',
                'ego_pose_token': 'pose', 'is_key_frame': True, 'width': 1600, 'height': 900, 'timestamp': 110,
                'filename': 'samples/CAM_FRONT/a.jpg'}},
            sample_annotation={'annotation': {'token': 'annotation', 'sample_token': 'sample', 'instance_token': 'instance'}})

    def stream(self, tables=None, order=TABLES):
        tables = self.tables if tables is None else tables
        return [(name + '.json', row) for name in order for row in tables[name].values()]

    def projection(self, token='annotation', category='vehicle.car', coordinates=None):
        return {'sample_annotation_token': token, 'sample_data_token': 'camera', 'category_name': category,
                'bbox_corners': [1, 2, 80, 100] if coordinates is None else coordinates}

    def test_join_preserves_sample_time_difference_and_complete_annotation_membership(self):
        with patch('project_reference.metadata', return_value=self.stream()):
            tables, counts = collect('unused', [self.image])
        joined, sources = qualify(tables, [self.image])
        self.assertEqual(joined['sample']['sample']['anns'], ['annotation'])
        self.assertEqual(joined['sample_annotation']['annotation']['category_name'], 'vehicle.car')
        self.assertEqual(sources[0]['camera_minus_sample_us'], 10)
        self.assertFalse(sources[0]['annotation_time_interpolation'])
        self.assertNotIn('anns', tables['sample']['sample'])
        self.assertEqual(counts['sample_annotation'], 1)

    def test_missing_selected_image_is_not_empty(self):
        tables = copy.deepcopy(self.tables); tables['sample_data'] = {}
        with patch('project_reference.metadata', return_value=self.stream(tables)):
            with self.assertRaises(Rejected):
                collect('unused', [self.image])

    def test_dependent_table_before_image_join_is_rejected(self):
        order = ('sample_annotation',) + tuple(name for name in TABLES if name != 'sample_annotation')
        with patch('project_reference.metadata', return_value=self.stream(order=order)):
            with self.assertRaises(Rejected):
                collect('unused', [self.image])

    def test_duplicate_selected_record_is_rejected(self):
        rows = self.stream(); rows.insert(1, rows[0])
        with patch('project_reference.metadata', return_value=rows):
            with self.assertRaises(Rejected):
                collect('unused', [self.image])

    def test_pose_calibration_dimensions_and_camera_identity_are_bound(self):
        changes = [('ego_pose', 'pose', 'timestamp', 111),
                   ('calibrated_sensor', 'calibration', 'translation', [1, 0, 0]),
                   ('sample_data', 'camera', 'width', 1599),
                   ('sample_data', 'camera', 'timestamp', 111),
                   ('sample_data', 'camera', 'is_key_frame', False),
                   ('sensor', 'sensor', 'channel', 'CAM_BACK')]
        for table, key, field, value in changes:
            with self.subTest(field=field):
                tables = copy.deepcopy(self.tables); tables[table][key][field] = value
                with self.assertRaises(Rejected):
                    qualify(tables, [self.image])

    def test_image_bytes_are_bound(self):
        Path(self.image['image_path']).write_bytes(b'changed')
        with self.assertRaises(Rejected):
            qualify(self.tables, [self.image])

    def test_explicit_empty_projection_is_a_valid_empty_answer(self):
        self.assertEqual(classify_projection([], self.image), ([], []))

    def test_exclusions_keep_source_records_and_reasons(self):
        rows = [self.projection(), self.projection('truck', 'vehicle.truck'),
                self.projection('short', coordinates=[1, 2, 80, 26])]
        eligible, excluded = classify_projection(rows, self.image)
        self.assertEqual(len(eligible), 1)
        self.assertEqual([row['reason'] for row in excluded], ['category_outside_car', 'height_below_25'])
        self.assertEqual(excluded[0]['record'], rows[1])
        at_boundary, _ = classify_projection([self.projection(coordinates=[1, 2, 80, 27])], self.image)
        self.assertEqual(len(at_boundary), 1)

    def test_invalid_geometry_and_wrong_image_are_not_empty(self):
        for coordinates in ([1, 2, 1, 100], [-1, 2, 80, 100], [1, 2, 1601, 100], [1, 2, 80, float('nan')]):
            with self.subTest(coordinates=coordinates):
                with self.assertRaises(Rejected):
                    classify_projection([self.projection(coordinates=coordinates)], self.image)
        row = self.projection(); row['sample_data_token'] = 'different'
        with self.assertRaises(Rejected):
            classify_projection([row], self.image)

    def test_height_cutoff_uses_declared_exact_decimal_coordinates(self):
        # Binary subtraction rounds to 25.0, but the declared JSON decimals
        # differ by slightly less than 25. The metric must not switch domains.
        rows, excluded = classify_projection([self.projection(coordinates=[1, 10.000000000000002, 80, 35.0])], self.image)
        self.assertEqual(rows, [])
        self.assertEqual(excluded[0]['reason'], 'height_below_25')

    def test_duplicate_annotation_is_rejected(self):
        with self.assertRaises(Rejected):
            classify_projection([self.projection(), self.projection()], self.image)


if __name__ == '__main__':
    unittest.main()
