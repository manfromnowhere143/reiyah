"""Source-identity adversaries independent of Blender; no review records."""
from copy import deepcopy
from pathlib import Path
import struct
import tempfile
import unittest

from tools import perception_viewer as v


class ViewerTests(unittest.TestCase):
    def setUp(self):
        self.points = [(1., -0., 3., 4., 5.), (-6., 7., 8., 9., 10.), (11., 12., 13., 14., 15.)]
        self.body = b''.join(struct.pack('<5f', *p) for p in self.points)
        self.ply = v.ply_header(3) + self.body
        self.binding = {'artifact_id': 'reiyah.perception-viewer.binding', 'version': '0.1.0',
                        'package_seal_sha256': '1'*64, 'capture_id': 'capture-000001',
                        'asset': {'byte_size': len(self.ply), 'sha256': v.sha(self.ply)}, 'point_count': 3}
        self.rows = [(i, *p) for i, p in enumerate(self.points)]

    def rejects(self, code, fn, *args):
        with self.assertRaises(v.Invalid) as ctx:
            fn(*args)
        self.assertEqual(ctx.exception.code, code)

    def test_fixed_profile_body_and_binding(self):
        self.assertEqual(v.parse_binding(v.encoded(self.binding)), self.binding)
        self.assertEqual(v.point_body(self.ply, self.binding), self.body)

    def test_pure_reorder_returns_original_indices(self):
        rows = [self.rows[2], self.rows[0], self.rows[1]]
        self.assertEqual(v.verify_rows(self.body, rows, [2, 0], v.IDENTITY), [0, 2])

    def test_all_five_fields_reject_one_float32_ulp_change(self):
        for field in range(5):
            with self.subTest(field=field):
                rows = [list(r) for r in self.rows]
                bits = struct.unpack('<I', struct.pack('<f', rows[2][1+field]))[0]
                rows[2][1+field] = struct.unpack('<f', struct.pack('<I', bits+1))[0]
                # Mutate an UNSELECTED row; the whole source still must be intact.
                self.rejects('VIEW_FIELDS', v.verify_rows, self.body, rows, [0], v.IDENTITY)

    def test_negative_zero_is_not_coerced(self):
        rows = [list(r) for r in self.rows]; rows[0][2] = 0.
        self.rejects('VIEW_FIELDS', v.verify_rows, self.body, rows, [0], v.IDENTITY)

    def test_nonfinite_or_unrepresentable_field(self):
        for value in (float('inf'), float('nan'), 1e100):
            rows = [list(r) for r in self.rows]; rows[0][1] = value
            self.rejects('VIEW_FIELDS', v.verify_rows, self.body, rows, [0], v.IDENTITY)

    def test_duplicate_outside_boolean_or_missing_index(self):
        for index in (1, -1, 3, True, 0.):
            rows = [list(r) for r in self.rows]; rows[0][0] = index
            self.rejects('VIEW_INDEX', v.verify_rows, self.body, rows, [0], v.IDENTITY)
        self.rejects('VIEW_INDEX', v.verify_rows, self.body, self.rows[:-1], [0], v.IDENTITY)

    def test_swapped_index_without_record_reorder(self):
        rows = [list(r) for r in self.rows]; rows[0][0], rows[1][0] = 1, 0
        self.rejects('VIEW_FIELDS', v.verify_rows, self.body, rows, [0], v.IDENTITY)

    def test_selection_is_a_set_of_original_integer_positions(self):
        for selected in ([True], [0, 0], [-1], [3], [1.0], '0'):
            self.rejects('VIEW_SELECTION', v.verify_rows, self.body, self.rows, selected, v.IDENTITY)

    def test_transform_changes_fail(self):
        matrix = deepcopy(v.IDENTITY); matrix[0][3] = 1e-9
        self.rejects('VIEW_TRANSFORM', v.verify_rows, self.body, self.rows, [0], matrix)

    def test_binding_unknown_missing_duplicate_and_float_fields(self):
        for change in ({'annotation': 'car'}, {'point_count': True}, {'capture_id': '../private'},
                       {'point_count': 0}, {'version': '0.2.0'}, {'package_seal_sha256': 'bad'}):
            b = deepcopy(self.binding); b.update(change)
            self.rejects('VIEW_BINDING', v.parse_binding, v.encoded(b))
        b = deepcopy(self.binding); del b['asset']
        self.rejects('VIEW_BINDING', v.parse_binding, v.encoded(b))
        raw = v.encoded(self.binding).replace(b'"point_count": 3', b'"point_count": 3.0')
        self.rejects('VIEW_BINDING', v.parse_binding, raw)
        self.rejects('VIEW_BINDING', v.parse_binding, b'{"a":1,"a":2}')

    def test_declared_count_and_size_must_agree(self):
        for n in (4, v.MAX_POINTS+1):
            b = deepcopy(self.binding); b['point_count'] = n
            self.rejects('VIEW_BINDING', v.parse_binding, v.encoded(b))
        self.rejects('VIEW_BINDING', v.parse_binding, b' '*4097)

    def test_changed_ply_profile_rejected_even_when_rehashed(self):
        data = self.ply.replace(b'property float ring', b'property float time')
        b = deepcopy(self.binding); b['asset'] = {'byte_size': len(data), 'sha256': v.sha(data)}
        self.rejects('VIEW_PLY', v.point_body, data, b)

    def test_nonfinite_source_rejected_even_when_rehashed(self):
        data = v.ply_header(3)+struct.pack('<f', float('inf'))+self.body[4:]
        b = deepcopy(self.binding); b['asset']['sha256'] = v.sha(data)
        self.rejects('VIEW_PLY', v.point_body, data, b)

    def test_external_binding_defeats_self_rehashed_source(self):
        self.rejects('VIEW_BOUND', v.point_body, self.ply[:-1]+b'!', self.binding)
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)/'input'; p.write_bytes(self.ply)
            self.assertEqual(v.read_bound(p, len(self.ply), v.sha(self.ply), 4096), self.ply)
            p.write_bytes(self.ply+b'!')
            self.rejects('VIEW_BOUND', v.read_bound, p, len(self.ply), v.sha(self.ply), 4096)

    def test_empty_selection_is_not_an_empty_reference(self):
        # Core validates the absence of selection; extract must separately refuse
        # to create a report. The native Blender probe exercises that rejection.
        self.assertEqual(v.verify_rows(self.body, self.rows, [], v.IDENTITY), [])


if __name__ == '__main__':
    unittest.main()
