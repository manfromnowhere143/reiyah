"""Bounded development workflow. Each arm executes in its own measured process."""

import argparse
import resource
import time

from adapter import all_cases
from binding import verify
from common import write_new
from workflow import run


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", choices=("reiyah", "conventional"), required=True)
    parser.add_argument("--sources")
    parser.add_argument("--output", required=True)
    parser.add_argument("--proofs", required=True)
    parser.add_argument("--timing", required=True)
    args = parser.parse_args()
    freeze = verify()
    if args.arm == "reiyah":
        import native as engine
    else:
        import conventional as engine
    rows = all_cases(args.sources)
    start, cpu = time.perf_counter(), resource.getrusage(resource.RUSAGE_SELF)
    results, proofs = [], []
    for row in rows:
        result, proof = run(row, engine, args.arm)
        results.append(result)
        proofs.append(proof)
    finish, cpu1 = time.perf_counter(), resource.getrusage(resource.RUSAGE_SELF)
    write_new(
        args.output,
        dict(
            document_id="reiyah.grid-fidelity.workflow",
            version="0.1.0",
            arm=args.arm,
            freeze_sha256=freeze,
            results=results,
        ),
    )
    write_new(
        args.proofs,
        dict(
            document_id="reiyah.grid-fidelity.proofs",
            version="0.1.0",
            arm=args.arm,
            freeze_sha256=freeze,
            proofs=proofs,
        ),
    )
    timing = dict(
        arm=args.arm,
        workflows=len(rows),
        workflow_wall_seconds=finish - start,
        self_user_cpu_seconds=cpu1.ru_utime - cpu.ru_utime,
        self_system_cpu_seconds=cpu1.ru_stime - cpu.ru_stime,
        scope="All declared solver, query, partition and witness operations; input preparation, source validation, serialization and external checking excluded. One fixed-order run; not a general speed benchmark.",
    )
    write_new(args.timing, timing)
    print(
        dict(
            arm=args.arm,
            cases=len(rows),
            oracle_calls=sum(x["oracle_calls"] for x in results),
            timing=timing,
        )
    )


if __name__ == "__main__":
    main()
