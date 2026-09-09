"""Resolve nominal spatial and time operands for source-bound observation windows."""
import argparse
import hashlib
from importlib.metadata import version
from pathlib import Path
import platform
import sys

from tools.perception_decision.cli import atomic_write
from tools.perception_decision.contract import Invalid, encoded, load
from tools.perception_inputs.source_io import require
from .bind import build


def runtime():
    return {'python': platform.python_version(), 'platform': sys.platform, 'jsonschema': version('jsonschema')}


def code_identities():
    root = Path(__file__).resolve().parent.parent
    return [[str(p.relative_to(root)), hashlib.sha256(p.read_bytes()).hexdigest()]
            for folder in ('perception_geometry', 'perception_windows', 'perception_inputs', 'perception_decision')
            for p in sorted((root/folder).glob('*.py'))]


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--request', type=Path, required=True); p.add_argument('--request-sha256', required=True)
    p.add_argument('--output', type=Path, required=True); args = p.parse_args(argv)
    try:
        require(not args.output.exists(), 'OUTPUT_EXISTS', 'Output identity is already consumed')
        request = load(args.request, args.request_sha256, validate_input=False)
        code, environment = code_identities(), runtime()
        result = build(request)
        require(code == code_identities() and environment == runtime(), 'GEOMETRY_CODE_CHANGED',
                'Implementation or runtime identity changed during assessment')
        result.update(source_identities=code, runtime=environment, request_file_sha256=args.request_sha256)
        data = encoded(result)
        require(len(data) <= 128 << 20, 'GEOMETRY_OUTPUT_SIZE', 'Report exceeds limit; no capture is clipped')
        atomic_write(args.output, data)
        sys.stdout.buffer.write(encoded({'output': str(args.output), 'sha256': hashlib.sha256(data).hexdigest(),
                                        'byte_size': len(data), 'summary': result['summary']}))
        return 0
    except Invalid as exc:
        sys.stderr.buffer.write(encoded({'status': 'invalid', **exc.diagnostic()}))
    except OSError as exc:
        sys.stderr.buffer.write(encoded({'status': 'invalid', 'code': 'IO_ERROR', 'detail': str(exc)}))
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
