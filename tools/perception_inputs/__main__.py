"""Verify source bytes and write one private clock-derived input catalog."""
import argparse
import hashlib
from pathlib import Path
import sys

from tools.perception_decision.cli import atomic_write
from tools.perception_decision.contract import Invalid, encoded, load
from .catalog import build
from .source_io import require


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', type=Path, required=True)
    parser.add_argument('--request-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        request = load(args.request, args.request_sha256, validate_input=False)
        tools_root = Path(__file__).resolve().parent.parent
        code = sorted([*tools_root.glob('perception_inputs/*.py'), *tools_root.glob('perception_decision/*.py')])
        identities = [[str(p.relative_to(tools_root)), hashlib.sha256(p.read_bytes()).hexdigest()] for p in code]
        catalog = build(request)
        require(identities == [[str(p.relative_to(tools_root)), hashlib.sha256(p.read_bytes()).hexdigest()] for p in code],
                'SOURCE_CODE_CHANGED', 'Implementation files changed during ingestion')
        catalog['request_file_sha256'] = args.request_sha256
        catalog['source_identities'] = identities
        catalog['implementation_sha256'] = hashlib.sha256(encoded(identities)).hexdigest()
        data = encoded(catalog)
        require(len(data) <= 128 << 20, 'CATALOG_SIZE', 'Catalog exceeds its byte limit; no anchors are clipped')
        atomic_write(args.output, data)
        result = {'output': str(args.output), 'sha256': hashlib.sha256(data).hexdigest(),
                  'byte_size': len(data), 'summary': catalog['summary']}
    except Invalid as exc:
        sys.stderr.buffer.write(encoded({'status': 'invalid', **exc.diagnostic()}))
        return 2
    except OSError as exc:
        sys.stderr.buffer.write(encoded({'status': 'invalid', 'code': 'IO_ERROR', 'detail': str(exc)}))
        return 2
    sys.stdout.buffer.write(encoded(result))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
