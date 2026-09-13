"""Source-identity adversaries independent of Blender; no review records."""
from copy import deepcopy
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

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

    def source_context(self, root):
        package = root/'package'; (package/'assets').mkdir(parents=True)
        # Context-only fixture: these seal bytes are NOT a valid observation
        # package. Full package verification remains an explicit prior step.
        seal = b'{"synthetic_context_only":true}\n'
        (package/'SEAL.json').write_bytes(seal)
        asset = package/'assets'/('capture-000001.ply'); asset.write_bytes(self.ply)
        binding = deepcopy(self.binding); binding['package_seal_sha256'] = v.sha(seal)
        raw = v.encoded(binding); binding_path = root/'binding.json'; binding_path.write_bytes(raw)
        return package, asset, binding, binding_path, v.sha(raw)

    def test_package_context_requires_selected_file_not_just_identical_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); package, asset, binding, _, _ = self.source_context(root)
            self.assertTrue(v.package_source(package, asset, binding).samefile(package))
            for copy in (root/'copied.ply', package/'assets'/'capture-000002.ply'):
                copy.write_bytes(asset.read_bytes())
                self.rejects('VIEW_PACKAGE', v.package_source, package, copy, binding)
            other = root/'other'; (other/'assets').mkdir(parents=True)
            (other/'SEAL.json').write_bytes((package/'SEAL.json').read_bytes())
            (other/'assets'/'capture-000001.ply').write_bytes(asset.read_bytes())
            self.rejects('VIEW_PACKAGE', v.package_source, other, asset, binding)

    def test_wrong_package_seal_rejected_without_output(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); package, asset, binding, _, _ = self.source_context(root)
            (package/'SEAL.json').write_bytes(b'{"other":true}\n')
            self.rejects('VIEW_BOUND', v.package_source, package, asset, binding)

    def test_output_rejects_package_root_assets_and_filesystem_aliases(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); package, _, _, _, _ = self.source_context(root)
            link = root/'package-link'; link.symlink_to(package, target_is_directory=True)
            for parent in (package, package/'assets', link):
                self.rejects('VIEW_OUTPUT', v.private_output, parent/'new', package)
            case = root/'PACKAGE'
            if case.exists() and case.samefile(package):
                self.rejects('VIEW_OUTPUT', v.private_output, case/'new', package)
            else:
                # Native reproduction also reports this platform limitation.
                self.skipTest('Case aliases unavailable; preceding root/assets/symlink cases passed')

    def test_cli_rejects_source_checkout_output_before_native_preparation(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); package, asset, _, binding, digest = self.source_context(root)
            output = Path(v.__file__).resolve().parents[1]/'viewer-forbidden-output'
            argv = ['prepare', '--package', str(package), '--binding', str(binding),
                    '--binding-sha256', digest, '--asset', str(asset), '--output', str(output)]
            with patch.object(v, 'prepare', side_effect=AssertionError('Native preparation reached')):
                self.rejects('VIEW_OUTPUT', v.main, argv)
            self.assertFalse(output.exists())

    def test_cli_pins_private_destination_before_parent_symlink_retarget(self):
        for action in ('prepare', 'extract'):
            with self.subTest(action=action), tempfile.TemporaryDirectory() as td:
                root = Path(td); package, asset, _, binding, digest = self.source_context(root)
                private = root/'private'; private.mkdir()
                link = root/'output-link'; link.symlink_to(private, target_is_directory=True)
                argv = [action, '--package', str(package), '--binding', str(binding),
                        '--binding-sha256', digest, '--asset', str(asset), '--output', str(link/'new')]

                def retarget(*args):
                    link.unlink(); link.symlink_to(package, target_is_directory=True)
                    if action == 'prepare':
                        # Stand-in isolates path custody; the separate native
                        # reproduction checks actual Blender save/extraction.
                        dest = args[-1]; self.assertEqual(dest, private.resolve()/'new')
                        dest.mkdir(); return dest
                    return {'point_indices': [1]}

                if action == 'extract':
                    scene = root/'synthetic.blend'; scene.write_bytes(b'context-only')
                    argv += ['--scene', str(scene), '--scene-bytes', str(scene.stat().st_size),
                             '--scene-sha256', v.sha(scene.read_bytes())]
                with patch.object(v, action, side_effect=retarget), patch.object(v, 'runtime', return_value={}), patch('builtins.print'):
                    v.main(argv)
                self.assertTrue((private/'new').exists())
                self.assertFalse((package/'new').exists())


if __name__ == '__main__':
    unittest.main()
