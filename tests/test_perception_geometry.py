"""Geometry orientation, source population, unavailable states and temporal boundaries."""
from copy import deepcopy
from decimal import Decimal
from fractions import Fraction
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from tools.perception_decision.contract import Invalid, encoded, rational
from tools.perception_geometry import algebra, bind
from tools.perception_geometry import __main__ as cli
from tools.perception_windows import __main__ as windows
from tests.test_perception_windows import identity_file, make_request, scene_fixture


def values():
    result = scene_fixture()
    for r in result['calibrated_sensor.json']:
        r.update(translation=[1, 2, 3], rotation=[1, 0, 0, 0],
                 camera_intrinsic=[] if r['sensor_token'] == 'sensor-LIDAR_TOP' else [[800, 0, 2], [0, 810, 1], [0, 0, 1]])
    result['ego_pose.json'] = [{'token': 'pose-'+s['token'], 'timestamp': s['timestamp'],
                               'translation': [10, 20, 30], 'rotation': [1, 0, 0, 0]}
                              for s in result['sample.json']]
    return result


def request(root, tables=None):
    (root/'raw').mkdir()
    req = make_request(root, values() if tables is None else tables)
    report = windows.build(req)
    return {'artifact_id': 'reiyah.perception-geometry.request', 'version': '0.1.0',
            'window_report': identity_file(root/'windows.json', encoded(report)),
            'catalog': req['catalog'], 'metadata': req['metadata']}


def change_window(req, change):
    path = Path(req['window_report']['path'])
    doc = json.loads(path.read_bytes()); change(doc)
    req['window_report'] = identity_file(path, encoded(doc))


def point(matrix, p):
    return tuple(sum(matrix[i][j]*p[j] for j in range(3)) + matrix[i][3] for i in range(3))


def hamilton(a, b):
    # Separate Hamilton product, used only by the test oracle. No rotation matrix.
    w, x, y, z = a; s, u, v, t = b
    return (w*s-x*u-y*v-z*t, w*u+x*s+y*t-z*v,
            w*v-x*t+y*s+z*u, w*t+x*v-y*u+z*s)


def rotate_point(q, p):
    q = tuple(Fraction(v) for v in q)
    s = sum(v*v for v in q)
    return tuple(v/s for v in hamilton(hamilton(q, (0, *p)), (q[0], -q[1], -q[2], -q[3]))[1:])


class GeometryTests(unittest.TestCase):
    def rejected(self, call, code):
        with self.assertRaises(Invalid) as caught:
            call()
        self.assertEqual(caught.exception.code, code)

    def test_landmark_and_noncommuting_transform_order(self):
        sensor = algebra.rigid([1, 2, 3], [0, 1, 0, 0])
        ego = algebra.rigid([10, 20, 30], [Decimal('.5')]*4)
        joint = algebra.multiply(ego, sensor)
        self.assertEqual(point(joint, (4, 5, 6)), (7, 25, 27))
        self.assertNotEqual(point(algebra.multiply(sensor, ego), (4, 5, 6)), (7, 25, 27))
        self.assertEqual(point(algebra.inverse(joint), (7, 25, 27)), (4, 5, 6))

    def test_hamilton_oracle_axes_and_exact_inverse(self):
        qs = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1],
              [Decimal('.5')]*4, [Decimal('.6'), Decimal('.8'), 0, 0],
              [Decimal('1.0000004'), 0, 0, 0]]
        for q in qs:
            transform = algebra.rigid([1, -2, 3], q)
            for p in ((0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1), (2, -7, 11)):
                expected = tuple(a+b for a, b in zip(rotate_point(q, p), (1, -2, 3)))
                self.assertEqual(point(transform, p), expected)
                self.assertEqual(point(algebra.inverse(transform), expected), p)
            self.assertEqual(algebra.multiply(transform, algebra.inverse(transform)), algebra.rigid([0, 0, 0], [1, 0, 0, 0]))

    def test_quaternion_sign_and_declared_norm_screen(self):
        q = [Decimal('.5')]*4
        self.assertEqual(algebra.rotation(q), algebra.rotation([-v for v in q]))
        for q in ([0]*4, [2, 0, 0, 0], [Decimal('1.000001'), 0, 0, 0]):
            self.rejected(lambda: algebra.rotation(q), 'GEOMETRY_QUATERNION')

    def test_numeric_boundaries_reject_nan_infinity_bool_and_binary_float(self):
        for bad in (Decimal('NaN'), Decimal('Infinity'), Decimal('-Infinity'), True, 1.0, '1', Decimal('1e100'), Decimal('1e-33')):
            for field in ('translation', 'rotation'):
                r = {'translation': [0, 0, 0], 'rotation': [1, 0, 0, 0]}; r[field][0] = bad
                result, matrix = bind.rigid_record(r)
                self.assertEqual(result['state'], 'invalid'); self.assertIsNone(matrix)
                self.assertEqual(result['diagnostic']['code'], 'ADAPTER_NUMBER')

    def test_intrinsic_form_and_separate_missingness(self):
        good = {'camera_intrinsic': [[100, 2, 50], [0, 120, 40], [0, 0, 1]]}
        self.assertEqual(bind.intrinsic_record(good, 'CAM_FRONT')['state'], 'available')
        for k in ([[0, 0, 2], [0, 3, 1], [0, 0, 1]], [[1, 0, 2], [0, 3, 1], [0, 1, 1]],
                  [[True, 0, 2], [0, 3, 1], [0, 0, 1]], []):
            self.assertEqual(bind.intrinsic_record({'camera_intrinsic': k}, 'CAM_FRONT')['state'], 'invalid')
        self.assertEqual(bind.intrinsic_record({}, 'CAM_FRONT')['state'], 'missing')
        self.assertEqual(bind.intrinsic_record({}, 'LIDAR_TOP')['state'], 'not_applicable')

    def test_full_pipeline_keeps_geometry_separate_from_raw_and_physical_validity(self):
        with tempfile.TemporaryDirectory() as name:
            result = bind.build(request(Path(name)))
        self.assertEqual(result['summary']['distinct_captures'], 70)
        self.assertEqual(result['summary']['nominal_global_transform_states'], {'available': 70})
        self.assertEqual(result['summary']['relative_transform_states'], {'available': 70})
        self.assertEqual(result['summary']['recorded_time_relations'], {'equal': 14, 'different': 56})
        self.assertEqual(result['uncertainty']['object_motion'], 'unmeasured')
        self.assertEqual(result['reference_review_readiness'], 'not_established')
        self.assertFalse(result['raw_payloads_reopened'])
        self.assertIsNone(result['selected_study_cohort'])
        for r in result['captures'].values():
            self.assertEqual(r['prior_payload_state'], 'not_checked')
            self.assertEqual(r['prior_custody_state'], 'not_listed')
            m = [[rational(v) for v in row] for row in r['nominal_sensor_to_global']['matrix']]
            self.assertEqual(point(m, (0, 0, 0)), (11, 22, 33))

    def test_absent_pose_keeps_all_captures_and_blocks_anchor_transform(self):
        v = values(); v['ego_pose.json'] = [r for r in v['ego_pose.json'] if r['token'] != 'pose-f0-2']
        with tempfile.TemporaryDirectory() as name:
            r = bind.build(request(Path(name), v))
        self.assertEqual(r['summary']['nominal_global_transform_states'], {'available': 63, 'unavailable': 7})
        self.assertEqual(r['summary']['relative_transform_states'], {'available': 35, 'unavailable': 35})
        self.assertEqual(r['ego_poses']['pose-f0-2']['rigid']['state'], 'missing')
        self.assertTrue(all(c['nominal_sensor_to_anchor_ego']['matrix'] is None for c in r['windows'][0]['captures']))

    def test_pose_offset_one_microsecond_is_not_rounded_or_interpolated(self):
        v = values(); v['ego_pose.json'][2]['timestamp'] += 1
        with tempfile.TemporaryDirectory() as name:
            r = bind.build(request(Path(name), v))
        self.assertEqual(r['summary']['pose_time_states'], {'aligned': 63, 'mismatch': 7})
        row = r['captures']['CAM_FRONT-f0-2']
        self.assertEqual(row['pose_time']['pose_minus_capture_us'], 1)
        self.assertIsNone(row['nominal_sensor_to_global']['matrix'])
        self.assertEqual(row['nominal_sensor_to_global']['reasons'], ['pose_time_mismatch'])

    def test_bad_pose_time_and_nan_pose_are_invalid_operands_not_negative_findings(self):
        v = values(); v['ego_pose.json'][0]['timestamp'] = True
        v['ego_pose.json'][1]['rotation'][0] = float('nan')
        with tempfile.TemporaryDirectory() as name:
            # Deliberately produce a legacy nonfinite source literal. The normal
            # artifact writer correctly refuses to emit it, including in fixtures.
            with patch('tests.test_perception_inputs.encoded', lambda rows: json.dumps(rows, allow_nan=True).encode()):
                req = request(Path(name), v)
            r = bind.build(req)
        self.assertEqual(r['ego_poses']['pose-f0-0']['time']['state'], 'invalid')
        self.assertEqual(r['ego_poses']['pose-f0-1']['rigid']['state'], 'invalid')
        self.assertEqual(r['summary']['nominal_global_transform_states']['unavailable'], 14)
        self.assertIsNone(r['captures']['CAM_FRONT-f0-1']['nominal_global_to_sensor']['matrix'])

    def test_missing_calibration_fields_preserve_missing_state(self):
        v = values(); del v['calibrated_sensor.json'][1]['translation']
        with tempfile.TemporaryDirectory() as name:
            r = bind.build(request(Path(name), v))
        self.assertEqual(r['calibrations']['cal-CAM_FRONT']['rigid'], {'state': 'missing', 'missing_fields': ['translation']})
        self.assertEqual(r['summary']['nominal_global_transform_states']['unavailable'], 10)

    def test_invalid_camera_intrinsic_does_not_invent_invalid_rigid_transform(self):
        v = values(); v['calibrated_sensor.json'][1]['camera_intrinsic'][0][0] = -1
        with tempfile.TemporaryDirectory() as name:
            r = bind.build(request(Path(name), v))
        self.assertEqual(r['calibrations']['cal-CAM_FRONT']['intrinsic']['state'], 'invalid')
        self.assertEqual(r['summary']['nominal_global_transform_states'], {'available': 70})

    def test_duplicate_requested_pose_rejects_without_partial_join(self):
        v = values(); v['ego_pose.json'].append(deepcopy(v['ego_pose.json'][0]))
        with tempfile.TemporaryDirectory() as name:
            req = request(Path(name), v)
            self.rejected(lambda: bind.build(req), 'GEOMETRY_JOIN')

    def test_missing_and_reordered_capture_population_rejected_against_source(self):
        for edit in (lambda r: r['windows'][0]['channels']['CAM_FRONT']['captures'].pop(),
                     lambda r: r['windows'][0]['channels']['CAM_FRONT']['captures'].reverse(),
                     lambda r: r['windows'][0]['channels']['CAM_FRONT']['captures'][0].update(ego_pose_token='wrong'),
                     lambda r: r['windows'][0].update(anchor_timestamp_us=True)):
            with tempfile.TemporaryDirectory() as name:
                req = request(Path(name)); change_window(req, edit)
                self.rejected(lambda: bind.build(req), 'GEOMETRY_WINDOW_BINDING')

    def test_boolean_identity_in_structural_match_is_explicit(self):
        self.assertFalse(bind.matches({'count': True}, {'count': 1}))
        self.assertFalse(bind.matches({'state': 1}, {'state': True}))
        self.assertTrue(bind.matches({'state': True}, {'state': True}))

    def test_empty_window_population_has_no_zero_support_success(self):
        with tempfile.TemporaryDirectory() as name:
            req = request(Path(name)); change_window(req, lambda r: r.update(windows=[]))
            self.rejected(lambda: bind.build(req), 'GEOMETRY_WINDOW')

    def test_nonfinite_generated_window_artifact_is_rejected_before_use(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name); req = request(root)
            p = Path(req['window_report']['path']); raw = p.read_bytes()
            raw = raw.replace(b'"capture_count":5', b'"capture_count":NaN', 1)
            self.assertIn(b'"capture_count":NaN', raw)
            req['window_report'] = identity_file(p, raw)
            self.rejected(lambda: bind.build(req), 'INVALID_NUMBER')

    def test_distinct_capture_limit_refuses_truncation(self):
        with tempfile.TemporaryDirectory() as name:
            req = request(Path(name))
            with patch.object(bind, 'MAX_CAPTURES', 69):
                self.rejected(lambda: bind.build(req), 'GEOMETRY_LIMIT')

    def test_bad_prior_state_and_unknown_channel_rejected(self):
        for edit, code in ((lambda r: r['windows'][0]['channels']['CAM_FRONT']['captures'][0]['payload'].update(payload_state=False), 'GEOMETRY_PAYLOAD_STATE'),
                           (lambda r: r['windows'][0]['channels']['CAM_FRONT']['captures'][0]['payload'].update(payload_state='decoded'), 'GEOMETRY_PAYLOAD_STATE'),
                           (lambda r: r['windows'][0]['channels'].update(UNKNOWN={}), 'GEOMETRY_WINDOW')):
            with tempfile.TemporaryDirectory() as name:
                req = request(Path(name)); change_window(req, edit)
                self.rejected(lambda: bind.build(req), code)

    def test_request_is_closed_and_source_hashes_must_agree(self):
        with tempfile.TemporaryDirectory() as name:
            req = request(Path(name))
            self.rejected(lambda: bind.build({**req, 'assume_static_objects': True}), 'GEOMETRY_REQUEST')
            bad = deepcopy(req); bad['metadata']['sha256'] = '0'*64
            self.rejected(lambda: bind.build(bad), 'GEOMETRY_BINDING')
            bad = deepcopy(req); bad['window_report']['sha256'] = '0'*64
            self.rejected(lambda: bind.build(bad), 'SOURCE_DIGEST')
            change_window(req, lambda r: r['metadata_tables']['sample_data.json'].update(sha256='0'*64))
            self.rejected(lambda: bind.build(req), 'GEOMETRY_BINDING')

    def test_missing_calibration_row_is_join_failure_not_silently_reduced_population(self):
        v = values(); v['calibrated_sensor.json'].pop()
        with tempfile.TemporaryDirectory() as name:
            # The window producer itself rejects an unresolved capture calibration.
            self.rejected(lambda: request(Path(name), v), 'WINDOW_METADATA')

    def test_cli_success_then_refuses_output_reuse_and_code_change(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name); req = request(root); path = root/'request.json'; path.write_bytes(encoded(req))
            digest = hashlib.sha256(path.read_bytes()).hexdigest(); out = root/'report.json'
            argv = [sys.executable, '-B', '-m', 'tools.perception_geometry', '--request', str(path),
                    '--request-sha256', digest, '--output', str(out)]
            first = subprocess.run(argv, capture_output=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            data = out.read_bytes()
            self.assertEqual(json.loads(first.stdout)['sha256'], hashlib.sha256(data).hexdigest())
            second = subprocess.run(argv, capture_output=True)
            self.assertEqual(second.returncode, 2); self.assertEqual(json.loads(second.stderr)['code'], 'OUTPUT_EXISTS')
            self.assertEqual(out.read_bytes(), data)
            changed = root/'changed.json'
            with patch.object(cli, 'code_identities', side_effect=[['first'], ['changed']]), patch.object(sys, 'stderr', type('Sink', (), {'buffer': io.BytesIO()})()):
                self.assertEqual(cli.main(argv[4:-1]+[str(changed)]), 2)
            self.assertFalse(changed.exists())


if __name__ == '__main__':
    unittest.main()
