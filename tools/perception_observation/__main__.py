"""Build or check an offline observation package, using separate custody."""
import argparse
from pathlib import Path
import sys

from tools.perception_decision.contract import Invalid, encoded, load
from . import package


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    subs = p.add_subparsers(dest='command', required=True)
    build = subs.add_parser('build')
    build.add_argument('--request', type=Path, required=True)
    build.add_argument('--request-sha256', required=True)
    build.add_argument('--output', type=Path, required=True)
    build.add_argument('--custody', type=Path, required=True)
    verify = subs.add_parser('verify')
    verify.add_argument('--package', type=Path, required=True)
    verify.add_argument('--seal-sha256', required=True)
    args = p.parse_args(argv)
    try:
        if args.command == 'build':
            request = load(args.request, args.request_sha256, validate_input=False)
            result = package.build(request, args.output, args.custody)
        else:
            result = package.verify(args.package, args.seal_sha256)
        sys.stdout.buffer.write(encoded(result))
        return 0
    except Invalid as exc:
        sys.stderr.buffer.write(encoded({'status': 'invalid', **exc.diagnostic()}))
    except OSError as exc:
        sys.stderr.buffer.write(encoded({'status': 'invalid', 'code': 'IO_ERROR', 'detail': str(exc)}))
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
