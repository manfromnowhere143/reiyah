"""Synthetic timing and projection controls, including source SDK agreement."""
from copy import deepcopy
from fractions import Fraction
import math
import random
import unittest

from timing_geometry import alternate_motion, close_coordinates, close_motion, eligible, hull, clip, project, rotation
from timing_model import bracket, car_census, project_current, sdk_motion, sdk_project


def fixture():
    current = {'token': 'a1', 'sample_token': 's1', 'instance_token': 'car0', 'prev': 'a0', 'next': '',
               'translation': [2, 0, 20], 'size': [2, 4, 2], 'rotation': [1, 0, 0, 0],
               'visibility_token': '4', 'attribute_tokens': [], 'num_lidar_pts': 1, 'num_radar_pts': 0}
    previous = {**deepcopy(current), 'token': 'a0', 'sample_token': 's0', 'prev': '', 'next': 'a1', 'translation': [0, 0, 20]}
    sample = {'token': 's1', 'prev': 's0', 'next': '', 'timestamp': 1_000_000, 'scene_token': 'scene'}
    previous_sample = {'token': 's0', 'prev': '', 'next': 's1', 'timestamp': 500_000, 'scene_token': 'scene'}
    sd = {'token': 'cam', 'sample_token': 's1', 'calibrated_sensor_token': 'cal', 'ego_pose_token': 'pose',
          'width': 1600, 'height': 900, 'timestamp': 950_000, 'filename': 'synthetic.jpg', 'is_key_frame': True}
    pose = {'token': 'pose', 'translation': [0, 0, 0], 'rotation': [1, 0, 0, 0]}
    calibration = {'token': 'cal', 'translation': [0, 0, 0], 'rotation': [1, 0, 0, 0],
                   'camera_intrinsic': [[1000, 0, 800], [0, 1000, 450], [0, 0, 1]]}
    selected = {'sample': {'s1': sample}, 'sample_data': {'cam': sd}, 'sample_annotation': {'a1': current},
                'category': {'car': {'name': 'vehicle.car'}}, 'instance': {'car0': {'category_token': 'car'}},
                'calibrated_sensor': {'cal': calibration}, 'ego_pose': {'pose': pose}}
    preceding = {'sample': {'s0': previous_sample}, 'sample_annotation': {'a0': previous},
                 'instance': {'car0': {'category_token': 'car'}}}
    return selected, preceding, sd, current, previous, sample, previous_sample


class TimingTests(unittest.TestCase):
    def compare(self, change=None):
        selected, preceding, sd, current, previous, sample, previous_sample = fixture()
        if change:
            change(selected, current, previous)
        context = bracket(current, previous, sample, previous_sample, sd['timestamp'])
        first = sdk_motion(current, previous, context)
        second = alternate_motion(current, previous, context['amount'], context['kind'])
        projected = sdk_project(selected, sd, current, first)
        alternative = project(second, selected['ego_pose']['pose'], selected['calibrated_sensor']['cal'])
        close_coordinates(projected['xyxy'], alternative)
        return context, first, projected, alternative

    def test_linear_center_and_scalar_projection(self):
        context, modeled, projected, _ = self.compare()
        self.assertEqual(Fraction(context['amount']), Fraction(9, 10))
        self.assertAlmostEqual(modeled['translation'][0], 1.8)
        self.assertEqual(projected['eligibility'], 'eligible')

    def test_changing_orientation(self):
        def change(selected, current, previous):
            current['rotation'] = [math.sqrt(.5), 0, 0, math.sqrt(.5)]
        self.compare(change)

    def test_antipodal_quaternion(self):
        def change(selected, current, previous):
            previous['rotation'] = [-1, 0, 0, 0]
        self.compare(change)

    def test_near_equal_quaternion_linear_branch(self):
        def change(selected, current, previous):
            current['rotation'] = [math.cos(.0001), math.sin(.0001), 0, 0]
        self.compare(change)

    def test_camera_pose_and_calibration_transforms(self):
        def change(selected, current, previous):
            selected['ego_pose']['pose'].update(translation=[2, -1, .4], rotation=[math.cos(.2), 0, 0, math.sin(.2)])
            selected['calibrated_sensor']['cal'].update(translation=[.3, .2, .1], rotation=[math.cos(.1), math.sin(.1), 0, 0])
        self.compare(change)

    def test_canvas_clipping(self):
        def change(selected, current, previous):
            current['translation'] = [15, 0, 20]; previous['translation'] = [15, 0, 20]
        _, _, projected, _ = self.compare(change)
        self.assertEqual(projected['xyxy'][2], 1600)

    def test_behind_camera_is_modeled_ineligibility(self):
        def change(selected, current, previous):
            current['translation'] = [0, 0, -20]; previous['translation'] = [0, 0, -20]
        _, _, projected, _ = self.compare(change)
        self.assertEqual(projected['eligibility'], 'outside_canvas'); self.assertIsNone(projected['xyxy'])

    def test_small_height_is_modeled_ineligibility(self):
        def change(selected, current, previous):
            current['translation'] = [0, 0, 100]; previous['translation'] = [0, 0, 100]
        _, _, projected, _ = self.compare(change)
        self.assertEqual(projected['eligibility'], 'height_below_25')

    def test_missing_previous_instance_is_not_static_or_empty(self):
        selected, _, sd, current, _, _, previous_sample = fixture()
        value = project_current(selected, sd, current, None, previous_sample)
        self.assertEqual(value['state'], 'unavailable'); self.assertIsNone(value['projection']); self.assertIsNone(value['modeled'])

    def test_current_time_does_not_require_previous_track(self):
        selected, _, sd, current, _, sample, _ = fixture(); sd['timestamp'] = sample['timestamp']
        value = project_current(selected, sd, current, None, None)
        self.assertEqual(value['state'], 'modeled'); self.assertEqual(value['context']['kind'], 'current_time')

    def test_missing_preceding_sample_retained(self):
        selected, _, sd, current, previous, _, _ = fixture()
        value = project_current(selected, sd, current, previous, None)
        self.assertEqual(value['reason'], 'missing_preceding_sample')

    def test_no_timestamp_clamping(self):
        _, _, sd, current, previous, sample, previous_sample = fixture()
        for time in (499_999, 1_000_001):
            value = bracket(current, previous, sample, previous_sample, time)
            self.assertEqual(value['reason'], 'camera_timestamp_outside_bracket')

    def test_bracket_span_limit(self):
        _, _, sd, current, previous, sample, previous_sample = fixture(); previous_sample['timestamp'] = -500_001
        self.assertEqual(bracket(current, previous, sample, previous_sample, sd['timestamp'])['reason'], 'invalid_or_excessive_sample_span')

    def test_nonreciprocal_instance_link_is_unavailable(self):
        _, _, sd, current, previous, sample, previous_sample = fixture(); previous['next'] = 'someone_else'
        self.assertEqual(bracket(current, previous, sample, previous_sample, sd['timestamp'])['reason'], 'inconsistent_instance_or_sample_links')

    def test_current_census_precedes_visibility_and_size(self):
        selected, preceding, _, current, _, _, _ = fixture(); current['translation'][2] = -500; current['size'] = [.01, .01, .01]
        current_cars, previous_cars, _ = car_census(selected, preceding, 's1')
        self.assertEqual(set(current_cars), {'car0'}); self.assertEqual(set(previous_cars), {'car0'})

    def test_invalid_dimensions_are_unavailable(self):
        selected, _, sd, current, previous, _, previous_sample = fixture(); current['size'][0] = 0
        value = project_current(selected, sd, current, previous, previous_sample)
        self.assertEqual(value['state'], 'unavailable'); self.assertEqual(value['reason'], 'invalid_motion_or_projection')

    def test_zero_quaternion_is_unavailable(self):
        selected, _, sd, current, previous, _, previous_sample = fixture(); previous['rotation'] = [0, 0, 0, 0]
        self.assertEqual(project_current(selected, sd, current, previous, previous_sample)['state'], 'unavailable')

    def test_unknown_visibility_is_unavailable_not_outside_canvas(self):
        selected, _, sd, current, previous, _, previous_sample = fixture(); current['visibility_token'] = 'unmeasured'
        value = project_current(selected, sd, current, previous, previous_sample)
        self.assertEqual(value['state'], 'unavailable'); self.assertIsNone(value['projection'])

    def test_duplicate_current_instance_rejected(self):
        selected, preceding, _, current, _, _, _ = fixture(); extra = deepcopy(current); extra['token'] = 'duplicate'
        selected['sample_annotation']['duplicate'] = extra
        with self.assertRaisesRegex(ValueError, 'Duplicate current'):
            car_census(selected, preceding, 's1')

    def test_projection_tolerance_does_not_override_eligibility(self):
        with self.assertRaisesRegex(ValueError, 'eligibility'):
            close_coordinates([0, 0, 20, 25], [0, 0, 20, 24.99999999])

    def test_quaternion_sign_preserves_rotation(self):
        self.assertEqual(rotation([1, 0, 0, 0]), rotation([-1, 0, 0, 0]))

    def test_hull_and_clipping_cover_crossing_without_inside_corners(self):
        polygon = hull([(-2, 1), (3, 1), (3, 2), (-2, 2)])
        result = clip(polygon, 1, 3)
        self.assertEqual(set(result), {(0, 1), (1, 1), (1, 2), (0, 2)})

    def test_seeded_three_axis_rotations_and_partial_depth(self):
        rng = random.Random(78319)
        for index in range(64):
            def change(selected, current, previous):
                for annotation in (current, previous):
                    annotation['rotation'] = [rng.uniform(-1, 1) for _ in range(4)]
                    annotation['translation'] = [rng.uniform(-12, 12), rng.uniform(-5, 5), rng.uniform(-3, 30)]
                    annotation['size'] = [rng.uniform(.5, 3), rng.uniform(1, 6), rng.uniform(.5, 4)]
                selected['ego_pose']['pose']['rotation'] = [1, .05, -.03, .08]
                selected['calibrated_sensor']['cal']['rotation'] = [1, -.04, .02, -.05]
            with self.subTest(case=index):
                self.compare(change)

    def test_publisher_module_source_is_restored(self):
        from nuscenes.scripts import export_2d_annotations_as_json as publisher
        sentinel = object(); absent = object(); inherited = getattr(publisher, 'nusc', absent)
        publisher.nusc = sentinel
        try:
            self.compare()
            self.assertIs(publisher.nusc, sentinel)
        finally:
            if inherited is absent:
                del publisher.nusc
            else:
                publisher.nusc = inherited

    def test_bad_center_and_rotation_fail_numerical_check(self):
        first = {'translation': [0, 0, 0], 'rotation': [1, 0, 0, 0], 'size': [1, 2, 3]}
        other = deepcopy(first); other['translation'][0] = 1e-5
        with self.assertRaisesRegex(ValueError, 'centers'):
            close_motion(first, other)
        other = deepcopy(first); other['rotation'] = [math.sqrt(.5), math.sqrt(.5), 0, 0]
        with self.assertRaisesRegex(ValueError, 'orientations'):
            close_motion(first, other)


if __name__ == '__main__':
    unittest.main()
