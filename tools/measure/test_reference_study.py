"""Scientific counterexamples for sampling, geometry, uncertainty and review custody."""
import copy
import itertools
import json
import math
import pathlib
import tempfile
import unittest

import numpy as np

import reference_study as study
from reference_study_analysis import consensus_bounds, two_stage_bounds, stratified_srs_bounds

ROOT = pathlib.Path(__file__).resolve().parents[2]


class GeometryTests(unittest.TestCase):
    def test_known_nonidentity_sensor_and_ego_rotation(self):
        q = [math.sqrt(.5), 0, 0, math.sqrt(.5)]
        # Sensor origin [1,0,0] rotated into ego's world y axis; double z-rotation.
        ego = {'rotation': q, 'translation': [10, 20, 0]}
        calib = {'rotation': q, 'translation': [1, 0, 0]}
        np.testing.assert_allclose(study.global_to_sensor([8, 21, 3], ego, calib), [2, 0, 3], atol=1e-12)

    def test_scalar_first_quaternion_and_bad_norm(self):
        np.testing.assert_allclose(study.rotation_wxyz([0, 1, 0, 0]), np.diag([1, -1, -1]))
        with self.assertRaises(ValueError): study.rotation_wxyz([2, 0, 0, 0])

    def test_negative_depth_cannot_be_visible(self):
        k = [[100, 0, 50], [0, 100, 50], [0, 0, 1]]
        self.assertEqual(study.camera_projection([0, 0, -1], k, 100, 100)['state'], 'behind_camera')
        self.assertEqual(study.camera_projection([0, 0, 2], k, 100, 100)['pixel_xy'], [50, 50])
        self.assertEqual(study.camera_projection([1, 0, 2], k, 100, 100)['state'], 'outside_image')

    def test_missing_empty_and_nonfinite_lidar_are_distinct_from_valid_observation(self):
        from reference_study_packets import asset_state
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d) / 'scan.bin'
            self.assertEqual(asset_state(p, 'LIDAR_TOP')['state'], 'missing')
            p.write_bytes(b'')
            self.assertEqual(asset_state(p, 'LIDAR_TOP')['state'], 'sensor_invalid')
            np.array([1, 2, float('nan'), 4, 5], dtype='<f4').tofile(p)
            self.assertEqual(asset_state(p, 'LIDAR_TOP')['state'], 'sensor_invalid')
            np.array([1, 2, 3, 4, 5], dtype='<f4').tofile(p)
            self.assertEqual(asset_state(p, 'LIDAR_TOP')['state'], 'available')

    def test_asset_cannot_escape_root(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            for name in ('../secret', '/etc/passwd', 'samples/../../secret'):
                with self.assertRaises(ValueError): study.safe_asset(root, name)
            (root / 'samples').symlink_to('/tmp', target_is_directory=True)
            with self.assertRaises(ValueError): study.safe_asset(root, 'samples/outside')


class PopulationTests(unittest.TestCase):
    def test_four_disjoint_strata_and_empty_lidar(self):
        labels, _, _ = study.strata_for([[0, 0], [10, 0], [20, 0], [30, 0]],
                                       [[20, 0]], [[0, 0]], [[0, 0], [10, 0]], 2)
        self.assertEqual(labels, list(study.STRATA))
        labels, _, _ = study.strata_for([[20, 0]], [], [[0, 0]], [[0, 0]], 2)
        self.assertEqual(labels, [study.STRATA[3]])
        with self.assertRaises(ValueError): study.strata_for([[0, 0]], [], [[0, 0]], [], 2)

    def test_selection_invariant_to_input_order_and_domain_separated(self):
        key = bytes(range(32)); identities = [str(i) for i in range(100)]
        self.assertEqual(study.choose(key, 'scene', identities, 10), study.choose(key, 'scene', identities[::-1], 10))
        self.assertNotEqual(study.choose(key, 'scene', identities, 10), study.choose(key, 'case', identities, 10))

    def test_json_rejects_nonfinite_and_duplicate_keys(self):
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d) / 'input.json'
            for text in ('{"a":NaN}', '{"a":1,"a":2}'):
                p.write_text(text)
                with self.assertRaises(ValueError): study.read_json(p)

    def test_ht_unbiased_by_exhausting_unequal_scene_sampling(self):
        # Two unequal scenes, sample one scene then one detection: exact expectation.
        population = [[0, 1], [1, 1, 1, 0]]
        estimates, probabilities = [], []
        for scene, values in enumerate(population):
            for j, y in enumerate(values):
                cells = [{'population_n': len(v), 'selected': i == scene,
                          'case_ids': ['x'] if i == scene else []} for i, v in enumerate(population)]
                result = two_stage_bounds(cells, {'x': (y, y)})
                estimates.append(result['point_estimate']); probabilities.append(.5 / len(values))
                self.assertLessEqual(result['confidence_set'][0], 4 / 6)
                self.assertGreaterEqual(result['confidence_set'][1], 4 / 6)
        self.assertAlmostEqual(sum(e*p for e, p in zip(estimates, probabilities)), 4 / 6)
        self.assertGreater(max(estimates), 1, 'HT estimates must not be silently clipped')

    def test_unreviewed_and_disagreement_do_not_shrink_denominator(self):
        cells = [{'population_n': 3, 'selected': True, 'case_ids': ['a', 'b', 'c']}]
        result = two_stage_bounds(cells, {'a': (1, 1), 'b': (0, 0)})
        np.testing.assert_allclose(result['confidence_set'], [1 / 3, 2 / 3])
        self.assertIsNone(result['point_estimate'])
        self.assertEqual(result['sampled_n'], 3)
        all_missing = two_stage_bounds(cells, {})
        self.assertEqual(all_missing['confidence_set'], [0, 1])

    def test_missing_selected_cell_and_duplicate_case_rejected(self):
        for cells in ([{'population_n': 2, 'selected': True, 'case_ids': []}],
                      [{'population_n': 2, 'selected': True, 'case_ids': ['a', 'a']}]):
            with self.assertRaises(ValueError): two_stage_bounds(cells, {})

    def test_srs_randomization_bound_coverage_by_exact_hypergeometric_enumeration(self):
        # Exact distribution for every possible binary finite population of size 100.
        # This exercises concentration without treating repeated physical scenes as IID.
        N, n = 100, 60
        ids = [str(i) for i in range(n)]
        for positives in range(N + 1):
            covered = 0.
            for k in range(max(0, n - (N - positives)), min(n, positives) + 1):
                outcomes = {str(i): (int(i < k), int(i < k)) for i in range(n)}
                ci = stratified_srs_bounds(N, ids, outcomes)['confidence_set']
                mass = math.comb(positives, k) * math.comb(N - positives, n - k) / math.comb(N, n)
                if ci[0] <= positives / N <= ci[1]: covered += mass
            self.assertGreaterEqual(covered, .9875 - 1e-12)

    def test_srs_unknown_mass_and_scene_clustering_do_not_become_zero(self):
        ids = [str(i) for i in range(60)]
        missing = stratified_srs_bounds(1000, ids, {})
        self.assertEqual(missing['confidence_set'], [0, 1])
        observed = {i: (1, 1) for i in ids[:30]}
        half = stratified_srs_bounds(1000, ids, observed)
        self.assertEqual(half['support_upper_estimate'], 1)
        self.assertGreater(half['confidence_set'][0], 0)
        self.assertIsNone(half['point_estimate'])


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.schema = study.read_json(ROOT / 'research/reference-study/0.1.0/review.schema.json')
        self.packet = {'case_id': 'a'*24, 'protocol_sha256': 'b'*64,
                       'evidence': [{'evidence_id': '+0:CAM_FRONT', 'asset_sha256': 'c'*64, 'state': 'available'}]}
        self.review = {'artifact_id': 'reiyah.reference-study.review.0.1.0', 'version': '0.1.0',
                       'case_id': 'a'*24, 'protocol_sha256': 'b'*64, 'reviewer_id': 'r1',
                       'reviewed_at_utc': '2026-09-07T00:00:00Z', 'outcome': 'supported', 'validity': 'usable',
                       'evidence': [{'evidence_id': '+0:CAM_FRONT', 'asset_sha256': 'c'*64}],
                       'reason': 'test fixture', 'timing_assessment': 'test', 'visibility_assessment': 'test'}

    def test_two_reviewers_required_and_disagreement_retained(self):
        self.assertEqual(consensus_bounds([self.review], self.packet, self.schema), (0, 1))
        second = dict(self.review, reviewer_id='r2')
        self.assertEqual(consensus_bounds([self.review, second], self.packet, self.schema), (1, 1))
        second['outcome'] = 'inconsistent'
        self.assertEqual(consensus_bounds([self.review, second], self.packet, self.schema), (0, 1))

    def test_repeated_identity_unknown_property_wrong_case_rejected(self):
        import jsonschema
        with self.assertRaises(ValueError): consensus_bounds([self.review, self.review], self.packet, self.schema)
        for field, value in [('extra_authority', True), ('case_id', 'd'*24)]:
            altered = dict(self.review, **{field: value})
            with self.assertRaises((ValueError, jsonschema.ValidationError)):
                consensus_bounds([altered], self.packet, self.schema)

    def test_missing_changed_or_uncited_evidence_cannot_support_judgment(self):
        for change in ('hash', 'missing', 'uncited', 'abstained'):
            packet, review = copy.deepcopy(self.packet), copy.deepcopy(self.review)
            if change == 'hash': review['evidence'][0]['asset_sha256'] = 'd'*64
            if change == 'missing': packet['evidence'][0]['state'] = 'missing'
            if change == 'uncited': review['evidence'] = []
            if change == 'abstained': review['validity'] = 'abstained'
            with self.assertRaises(ValueError): consensus_bounds([review], packet, self.schema)


if __name__ == '__main__':
    unittest.main()
