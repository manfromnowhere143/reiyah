"""Selection is explicit; source identities are derived without changing the stage."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tools import perception_viewer as viewer, perception_viewer_preparation as preparation
from tools.perception_decision.contract import Invalid
from tools.perception_observation import package
from tests.test_perception_observation import fixture, read, tree


class ViewerPreparationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.request = fixture(self.root)
        self.package = self.root/'Source Package'
        delivery = package.build(self.request, self.package, self.root/'custody.json')
        self.seal = delivery['seal_sha256']
        self.manifest = json.loads((self.package/'manifest.json').read_bytes())
        self.lidar = next(r for r in self.manifest['captures'] if r['channel'] == 'LIDAR_TOP')
        self.output = self.root/'binding with spaces.json'

    def bind(self, **kw):
        args = dict(package=self.package, expected_seal=self.seal,
                    capture_id=self.lidar['id'], output=self.output)
        args.update(kw)
        return preparation.bind(**args)

    def rejected(self, code, **kw):
        source = kw.get('package', self.package)
        before = tree(source)
        with self.assertRaises(Invalid) as caught:
            self.bind(**kw)
        self.assertEqual(caught.exception.code, code)
        self.assertEqual(tree(source), before)
        self.assertFalse(self.output.exists())

    def test_correct_manual_binding_bytes_and_native_arguments(self):
        before = tree(self.package)
        result = self.bind()
        # The baseline reads the original disclosed bytes, not the helper's
        # field-derivation code. The synthetic source has exactly two records.
        asset = self.package/self.lidar['evidence']['asset']['filename']
        raw = asset.read_bytes()
        manual = {'artifact_id': 'reiyah.perception-viewer.binding', 'version': '0.1.0',
                  'package_seal_sha256': self.seal, 'capture_id': self.lidar['id'],
                  'asset': {'byte_size': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()},
                  'point_count': 2}
        expected = (json.dumps(manual, sort_keys=True, indent=2)+'\n').encode()
        self.assertEqual(self.output.read_bytes(), expected)
        self.assertEqual(viewer.point_body(raw, viewer.parse_binding(expected)), raw[-40:])
        self.assertEqual(result['viewer_source_arguments'],
                         ['--binding', str(self.output.resolve()), '--binding-sha256', hashlib.sha256(expected).hexdigest(),
                          '--package', str(self.package.resolve()), '--asset', str(asset.resolve())])
        self.assertEqual(result['interactive_observation'], 'not_established')
        self.assertEqual(result['reference_judgment'], 'not_created')
        self.assertEqual(tree(self.package), before)
        other = self.root/'other.json'
        self.bind(output=other)
        self.assertEqual(other.read_bytes(), expected)

    def test_explicit_capture_and_modality_are_required(self):
        for capture in (None, True, '../capture-000001', 'capture-999999'):
            with self.subTest(capture=capture):
                self.rejected('VIEW_CAPTURE', capture_id=capture)
        camera = next(r for r in self.manifest['captures'] if r['channel'] == 'CAM_FRONT')
        self.rejected('VIEW_MODALITY', capture_id=camera['id'])

    def test_missing_point_source_is_never_empty_observation(self):
        # Build a valid disclosure retaining a missing source, rather than
        # silently changing the manifest beneath an existing seal.
        first = read(self.request['inventory'])['assets'][0]
        self.assertTrue(first['filename'].endswith('.pcd.bin'))
        (self.root/'raw'/first['filename']).unlink()
        missing = self.root/'Missing Package'
        delivery = package.build(self.request, missing, self.root/'missing-custody.json')
        m = json.loads((missing/'manifest.json').read_bytes())
        row = next(r for r in m['captures'] if r['evidence']['state'] == 'missing')
        self.rejected('VIEW_UNAVAILABLE', package=missing, expected_seal=delivery['seal_sha256'], capture_id=row['id'])

    def test_wrong_expected_seal_is_refused(self):
        self.rejected('OBS_FILE_IDENTITY', expected_seal='0'*64)

    def test_selected_and_unrelated_asset_substitution_are_refused(self):
        for row in (self.lidar, next(r for r in self.manifest['captures'] if r['channel'] == 'CAM_FRONT')):
            path = self.package/row['evidence']['asset']['filename']
            original = path.read_bytes()
            with self.subTest(capture=row['id']):
                path.write_bytes(original[:-1] + bytes([original[-1] ^ 1]))
                self.rejected('OBS_FILE_IDENTITY')
                path.write_bytes(original)

    def test_unlisted_source_file_is_refused(self):
        (self.package/'extra.json').write_text('{}')
        self.rejected('OBS_FILE_SET')

    def test_existing_file_directory_and_symlink_are_preserved(self):
        other = self.root/'occupied'
        other.write_bytes(b'unchanged')
        directory = self.root/'directory'; directory.mkdir()
        link = self.root/'link'; link.symlink_to(other)
        for target in (other, directory, link):
            with self.subTest(target=target):
                self.rejected('OUTPUT_EXISTS', output=target)
        self.assertEqual(other.read_bytes(), b'unchanged')
        self.assertTrue(link.is_symlink())

    def test_outputs_inside_source_or_symlink_alias_are_refused(self):
        link = self.root/'alias'; link.symlink_to(self.package, target_is_directory=True)
        checkout = Path(preparation.__file__).resolve().parents[1]
        for parent in (self.package, self.package/'assets', link, link/'assets', checkout):
            with self.subTest(parent=parent):
                target = parent/'viewer-binding-must-not-exist.json'
                self.assertFalse(os.path.lexists(target))
                self.rejected('VIEW_OUTPUT', output=target)
                self.assertFalse(os.path.lexists(target))

    def test_case_alias_cannot_hide_output_inside_package(self):
        alias = self.package.with_name(self.package.name.swapcase())
        if not alias.exists() or not alias.samefile(self.package):
            self.skipTest('Host filesystem does not resolve this case alias')
        self.rejected('VIEW_OUTPUT', output=alias/'binding.json')

    def test_cli_produces_machine_readable_result_and_rejects_reuse(self):
        argv = [sys.executable, '-B', '-m', 'tools.perception_viewer_preparation',
                '--package', str(self.package), '--package-seal-sha256', self.seal,
                '--capture', self.lidar['id'], '--output', str(self.output)]
        first = subprocess.run(argv, capture_output=True, check=True)
        self.assertEqual(json.loads(first.stdout)['state'], 'binding_prepared')
        original = self.output.read_bytes()
        second = subprocess.run(argv, capture_output=True)
        self.assertEqual(second.returncode, 2)
        self.assertEqual(json.loads(second.stderr)['code'], 'OUTPUT_EXISTS')
        self.assertEqual(self.output.read_bytes(), original)


if __name__ == '__main__':
    unittest.main()
