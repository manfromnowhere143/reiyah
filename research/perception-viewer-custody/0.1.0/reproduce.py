#!/usr/bin/env python3
"""Native output-custody probes on synthetic observations; no human review.

The protected run supplies the added explicit package-location argument. Both
runs use the same separately verified package/binding/asset and output cases.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import subprocess
import sys
import tempfile
import time


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False)+'\n').encode()


def identity(data):
    return {'byte_size': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def source_identity(root):
    paths = set(root.glob('tools/perception*.py'))
    paths.update(p for d in root.glob('tools/perception_*') if d.is_dir() for p in d.glob('*.py'))
    paths.update(root.glob('tests/test_perception*.py'))
    for name in ('rehearsal', 'assistance', 'operands', 'reviewed-operands', 'discovery', 'observation'):
        paths.update(p for p in (root/'research'/('perception-'+name)/'0.1.0').rglob('*') if p.is_file())
    rows = [{'path': p.relative_to(root).as_posix(), **identity(p.read_bytes())} for p in sorted(paths)]
    return rows, identity(encoded(rows))['sha256']


def inventory(root):
    return [{'path': p.relative_to(root).as_posix(), **identity(p.read_bytes())}
            for p in sorted(root.rglob('*')) if p.is_file()]


def main(args):
    source = Path(args.source_root).resolve()
    rows, digest = source_identity(source)
    assert digest == args.source_sha256, (digest, args.source_sha256)
    blender = Path(args.blender).resolve()
    binary = identity(blender.read_bytes())
    assert binary['sha256'] == args.blender_sha256
    output = Path(args.output).resolve(); output.mkdir()
    (output/'SOURCE_BINDINGS.json').write_bytes(encoded({'files': rows, 'source_sha256': digest}))
    sys.path.insert(0, str(source))
    from tests.test_perception_observation import fixture
    from tools.perception_observation import package
    from tools.perception_decision.contract import Invalid
    from tools import perception_viewer as viewer
    results = []
    flags = [str(blender), '--background', '--factory-startup', '--disable-autoexec', '--python-exit-code', '2']

    def run(name, argv):
        dest = output/name; dest.mkdir()
        start = time.monotonic(); when = datetime.now(timezone.utc).isoformat()
        with (dest/'stdout.txt').open('wb') as stdout, (dest/'stderr.txt').open('wb') as stderr:
            proc = subprocess.run(argv, stdout=stdout, stderr=stderr, env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
        receipt = {'argv': argv, 'started_utc': when, 'elapsed_seconds': time.monotonic()-start,
                   'exit_code': proc.returncode,
                   'child_max_rss_bytes_macos_cumulative': resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,
                   'streams': {p.name: identity(p.read_bytes()) for p in (dest/'stdout.txt', dest/'stderr.txt')}}
        (dest/'receipt.json').write_bytes(encoded(receipt))
        messages = []
        for p in (dest/'stdout.txt', dest/'stderr.txt'):
            for line in p.read_text(errors='replace').splitlines():
                try: messages.append(json.loads(line))
                except json.JSONDecodeError: pass
        codes = [m['code'] for m in messages if type(m) is dict and m.get('state') == 'invalid']
        return proc.returncode, codes

    with tempfile.TemporaryDirectory(prefix='reiyah-viewer-custody-') as td:
        root = Path(td); request = fixture(root)
        pristine = root/'pristine'; result = package.build(request, pristine, root/'custody.json')
        seal = result['seal_sha256']; package.verify(pristine, seal)
        manifest = json.loads((pristine/'manifest.json').read_bytes())
        row = next(r for r in manifest['captures'] if r['channel'] == 'LIDAR_TOP' and r['evidence']['state'] == 'delivered')
        evidence = row['evidence']; asset = pristine/evidence['asset']['filename']
        binding = {'artifact_id': 'reiyah.perception-viewer.binding', 'version': '0.1.0',
                   'package_seal_sha256': seal, 'capture_id': row['id'],
                   'asset': {k: evidence['asset'][k] for k in ('byte_size', 'sha256')},
                   'point_count': evidence['point_count']}
        raw_binding = encoded(binding); binding_path = root/'binding.json'; binding_path.write_bytes(raw_binding)
        binding_sha = identity(raw_binding)['sha256']
        (output/'binding.json').write_bytes(raw_binding)
        body = asset.read_bytes().split(b'end_header\n', 1)[1]
        original = next(r for r in json.loads((root/'custody.json').read_bytes())['captures'] if r['capture_id'] == row['id'])
        assert body == (root/'raw'/original['source']['filename']).read_bytes()

        def command(action, package_path, dest, scene=None):
            argv = flags+['--python', str(source/'tools/perception_viewer.py'), '--', action,
                '--binding', str(binding_path), '--binding-sha256', binding_sha,
                '--asset', str(package_path/evidence['asset']['filename']), '--output', str(dest)]
            if args.expect == 'protected': argv += ['--package', str(package_path)]
            if scene is not None:
                b = scene.read_bytes()
                argv += ['--scene', str(scene), '--scene-sha256', identity(b)['sha256'], '--scene-bytes', str(len(b))]
            return argv

        opening = root/'opening'
        assert run('private-prepare', command('prepare', pristine, opening))[0] == 0
        scene = opening/(row['id']+'.blend'); selected = root/'programmatic-selection.blend'
        selector = root/'select.py'
        selector.write_text('import bpy\nfrom pathlib import Path\nimport sys\n'
            'source, scene, target = sys.argv[sys.argv.index("--")+1:]\n'
            'sys.path.insert(0, source)\nfrom tools import perception_viewer as v\nv.runtime()\n'
            'assert bpy.ops.wm.open_mainfile(filepath=scene, load_ui=False, use_scripts=False)=={"FINISHED"}\n'
            'obj=bpy.context.scene.objects[0]\nbpy.ops.object.mode_set(mode="OBJECT")\n'
            'for p in obj.data.vertices: p.select=(obj.data.attributes[v.INDEX].data[p.index].value==1)\n'
            'bpy.context.preferences.filepaths.save_version=0\n'
            'assert not Path(target).exists()\n'
            'assert bpy.ops.wm.save_as_mainfile(filepath=target)=={"FINISHED"}\n')
        (output/'select-programmatically.py').write_bytes(selector.read_bytes())
        assert run('programmatic-select', flags+['--python', str(selector), '--', str(source), str(scene), str(selected)])[0] == 0
        private_report = root/'private-selection.json'
        assert run('private-extract', command('extract', pristine, private_report, selected))[0] == 0
        report = json.loads(private_report.read_bytes())
        assert report['point_indices'] == [1]
        assert report['records'] == [{'point_index': 1, 'raw_byte_offset': 20,
            'ply_byte_offset': len(asset.read_bytes())-len(body)+20, 'float32_le_hex': body[20:40].hex()}]
        assert report['human_review'] == 'not_established' and report['reference_judgment'] == 'not_created'
        package.verify(pristine, seal)
        (output/'private-selection.json').write_bytes(private_report.read_bytes())
        for action in ('prepare', 'extract'):
            for spelling in ('root', 'assets', 'symlink', 'case_alias'):
                name = action+'-'+spelling
                case_root = root/name; case_root.mkdir()
                observation = case_root/'package'; shutil.copytree(pristine, observation)
                if spelling == 'root': parent = observation
                elif spelling == 'assets': parent = observation/'assets'
                elif spelling == 'symlink':
                    parent = case_root/'package-link'; parent.symlink_to(observation, target_is_directory=True)
                else:
                    parent = case_root/'PACKAGE'
                    if not parent.exists() or not parent.samefile(observation):
                        results.append({'case': name, 'state': 'skipped_case_sensitive_filesystem'}); continue
                dest = parent/('opening' if action == 'prepare' else 'selection.json')
                before = inventory(observation)
                assert package.verify(observation, seal)['disclosure_verified']
                code, diagnostics = run(name, command(action, observation, dest, selected if action == 'extract' else None))
                after = inventory(observation)
                try: package.verify(observation, seal); verification = 'verified'
                except Invalid as exc: verification = exc.code
                expected = args.expect == 'protected'
                assert (code != 0 and diagnostics == ['VIEW_OUTPUT'] and before == after and verification == 'verified') if expected else (code == 0 and before != after and verification == 'OBS_FILE_SET'), (name, code, diagnostics, verification)
                (output/name/'before-inventory.json').write_bytes(encoded(before))
                (output/name/'after-inventory.json').write_bytes(encoded(after))
                results.append({'case': name, 'state': 'rejected' if expected else 'contaminated',
                    'exit_code': code, 'diagnostics': diagnostics, 'source_unchanged': before == after,
                    'verification': verification, 'added_files': len(after)-len(before)})
        summary = {'artifact_id': 'reiyah.viewer-custody.reproduction', 'version': '0.1.0',
            'source_sha256': digest, 'blender': binary, 'expected_state': args.expect,
            'cases': results, 'controls': {'private_prepare': 'pass', 'private_extract': 'pass',
                'exact_original_record_indices': [1], 'pristine_package_preserved': True},
            'package_seal_sha256': seal, 'binding_sha256': binding_sha,
            'selection_origin': 'programmatically_constructed_synthetic_fixture',
            'interactive_observation': False, 'human_reference_records_created': 0}
        (output/'RESULTS.json').write_bytes(encoded(summary))
    assert source_identity(source)[1] == digest
    print(json.dumps({'cases': len(results), 'expected_state': args.expect,
                      'results': identity((output/'RESULTS.json').read_bytes())}, sort_keys=True))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('source-root', 'source-sha256', 'blender', 'blender-sha256', 'output'):
        p.add_argument('--'+name, required=True)
    p.add_argument('--expect', choices=('vulnerable', 'protected'), required=True)
    main(p.parse_args())
