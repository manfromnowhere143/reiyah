"""Execute the frozen authored reveal protocol, retaining every state and witness."""

import argparse
from collections import Counter
from pathlib import Path
import resource
import time

from binding import bind
from common import write_new
from envelope import solve
from responses import plan
from workflow import run_experiment


def main():
    parser = argparse.ArgumentParser()
    for arg in ("freeze-sha256", "sources", "output", "proofs", "timing"):
        parser.add_argument("--" + arg, required=True)
    args = parser.parse_args()
    started, cpu = time.perf_counter(), resource.getrusage(resource.RUSAGE_SELF)
    cases, oracles = bind(Path(__file__).parent, Path(args.sources), args.freeze_sha256)
    prepared = time.perf_counter()
    results, proofs = [], []
    for case in cases:
        result, witness = run_experiment(case, oracles[case["oracle_id"]], plan, solve)
        results.append(result)
        proofs.append(dict(id=case["id"], stages=witness))
    calculated = time.perf_counter()
    report = dict(
        document_id="reiyah.measurement-resolution.results",
        version="0.1.0",
        freeze_sha256=args.freeze_sha256,
        cases=results,
        final_evidence_counts=dict(
            sorted(Counter(x["final"]["status"] for x in results).items())
        ),
        workflow_counts=dict(
            sorted(Counter(x["workflow_status"] for x in results).items())
        ),
        oracle_calls=sum(x["oracle_calls"] for x in results),
        experiments=len(results),
        evidence_kind="authored conditional mechanism experiments",
        physical_cases=0,
        physical_qualification="unresolved",
        independent_replication=False,
    )
    write_new(args.output, report)
    write_new(
        args.proofs,
        dict(
            document_id="reiyah.measurement-resolution.proofs",
            version="0.1.0",
            freeze_sha256=args.freeze_sha256,
            cases=proofs,
        ),
    )
    finish = resource.getrusage(resource.RUSAGE_SELF)
    write_new(
        args.timing,
        dict(
            arm="analytic_complete_response_sets",
            preparation_seconds=prepared - started,
            calculation_seconds=calculated - prepared,
            process_through_output_seconds=time.perf_counter() - started,
            cpu_seconds=finish.ru_utime + finish.ru_stime - cpu.ru_utime - cpu.ru_stime,
            logical_oracle_calls=report["oracle_calls"],
            all_oracle_records_loaded_for_preparation=len(oracles),
            acquisition_scope="Authored in-memory interpolation only; no physical or human acquisition saving.",
        ),
    )
    print(
        {
            k: report[k]
            for k in (
                "experiments",
                "final_evidence_counts",
                "workflow_counts",
                "oracle_calls",
            )
        }
    )


if __name__ == "__main__":
    main()
