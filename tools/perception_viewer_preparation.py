"""Derive the existing native viewer binding from a verified observation package.

The coordinator selects the expected package seal and capture. This command
prepares source arguments only; it does not launch a viewer or create a review.
"""
import argparse
import os
from pathlib import Path
import re
import sys

from tools import perception_viewer as viewer
from tools.perception_decision.cli import atomic_write
from tools.perception_decision.contract import Invalid
from tools.perception_discovery.custody import manifest
from tools.perception_inputs.source_io import private_output_path, require


def bind(package, expected_seal, capture_id, output):
    require(type(capture_id) is str and re.fullmatch('capture-[0-9]{6}', capture_id),
            'VIEW_CAPTURE', 'Require an explicit neutral capture identifier')
    package = Path(package).resolve(strict=True)
    output = private_output_path(output, (package, Path(__file__).resolve().parents[1]),
                                 'VIEW_OUTPUT', 'Binding must remain outside the package and source checkout')
    require(not os.path.lexists(output), 'OUTPUT_EXISTS', 'Binding output already exists')
    # Full disclosure verification, then a fresh hash-bound manifest read. No
    # source identities are learned from an unverified manifest or asset path.
    m = manifest(package, expected_seal)
    row = next((r for r in m['captures'] if r['id'] == capture_id), None)
    require(row is not None, 'VIEW_CAPTURE', 'Capture is not in the selected package')
    require(row['channel'] == 'LIDAR_TOP', 'VIEW_MODALITY', 'Native point binding requires LIDAR_TOP')
    evidence = row['evidence']
    require(evidence['state'] == 'delivered', 'VIEW_UNAVAILABLE',
            'Capture has no delivered point asset; no observation is inferred')
    binding = {'artifact_id': 'reiyah.perception-viewer.binding', 'version': viewer.VERSION,
               'package_seal_sha256': expected_seal, 'capture_id': capture_id,
               'asset': {k: evidence['asset'][k] for k in ('byte_size', 'sha256')},
               'point_count': evidence['point_count']}
    data = viewer.encoded(binding)
    viewer.parse_binding(data)  # Apply the native adapter's existing bounds/profile.
    binding_sha = viewer.sha(data)
    source_arguments = ['--binding', str(output), '--binding-sha256', binding_sha,
                        '--package', str(package), '--asset', str(package/evidence['asset']['filename'])]
    atomic_write(output, data)
    return {'artifact_id': 'reiyah.perception-viewer.preparation', 'version': '0.1.0',
            'state': 'binding_prepared', 'binding_sha256': binding_sha,
            'binding_byte_size': len(data), 'capture_id': capture_id,
            'viewer_source_arguments': source_arguments,
            'interactive_observation': 'not_established', 'human_review': 'not_established',
            'reference_judgment': 'not_created'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', required=True)
    parser.add_argument('--package-seal-sha256', required=True)
    parser.add_argument('--capture', required=True)
    parser.add_argument('--output', required=True, help='New binding file outside all source directories')
    args = parser.parse_args(argv)
    try:
        result = bind(args.package, args.package_seal_sha256, args.capture, args.output)
        sys.stdout.buffer.write(viewer.encoded(result))
        return 0
    except (Invalid, viewer.Invalid, OSError, ValueError) as exc:
        sys.stderr.write(viewer.encoded({'state': 'invalid', 'code': getattr(exc, 'code', 'VIEW_IO'),
                                        'detail': str(exc)}).decode())
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
