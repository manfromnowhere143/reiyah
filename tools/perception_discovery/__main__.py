"""Draft, seal and inspect unassisted discovery custody; no phase-2 release."""
import argparse
from pathlib import Path
import sys

from tools.perception_decision.contract import Invalid, encoded
from . import custody


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);subs=p.add_subparsers(dest='command',required=True)
    for name in ('draft','seal','verify','pair'):
        sub=subs.add_parser(name)
        sub.add_argument('--package',type=Path,required=True);sub.add_argument('--package-seal-sha256',required=True)
        if name=='draft':
            sub.add_argument('--record-id',required=True);sub.add_argument('--output',type=Path,required=True)
        elif name=='pair':
            sub.add_argument('--first',type=Path,required=True);sub.add_argument('--first-sha256',required=True)
            sub.add_argument('--second',type=Path,required=True);sub.add_argument('--second-sha256',required=True)
        else:
            sub.add_argument('--record',type=Path,required=True);sub.add_argument('--record-sha256',required=True)
            if name=='seal':sub.add_argument('--output',type=Path,required=True)
    a=p.parse_args(argv)
    try:
        if a.command=='draft':result=custody.make_draft(a.package,a.package_seal_sha256,a.record_id,a.output)
        elif a.command=='seal':result=custody.seal_record(a.record,a.record_sha256,a.package,a.package_seal_sha256,a.output)
        elif a.command=='verify':result=custody.verify_record(a.record,a.record_sha256,a.package,a.package_seal_sha256)
        else:result=custody.verify_pair(a.first,a.first_sha256,a.second,a.second_sha256,a.package,a.package_seal_sha256)
        sys.stdout.buffer.write(encoded(result));return 0
    except Invalid as exc:
        sys.stderr.buffer.write(encoded({'status':'invalid',**exc.diagnostic()}))
    except OSError as exc:
        sys.stderr.buffer.write(encoded({'status':'invalid','code':'IO_ERROR','detail':str(exc)}))
    return 2


if __name__=='__main__':
    raise SystemExit(main())
