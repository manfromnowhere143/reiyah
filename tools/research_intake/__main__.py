"""Explicit local-file CLI for the offline research intake prototype."""
import argparse
import sys

from . import Invalid, assess, canonical, read_record, write_new


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest="action", required=True)
    action = actions.add_parser("assess")
    for name in ("mission", "dossier", "sources"):
        action.add_argument("--" + name, required=True)
    action.add_argument("--output")
    args = parser.parse_args()
    try:
        result = assess(read_record(args.mission), read_record(args.dossier), args.sources)
        if args.output:
            write_new(args.output, result)
        else:
            sys.stdout.buffer.write(canonical(result))
        return 0
    except Invalid as exc:
        sys.stderr.buffer.write(canonical({"status": "invalid", "code": exc.code, "detail": exc.detail}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
