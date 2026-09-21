"""Run the prespecified Reiyah residual experiment; full trace remains private."""

import argparse
from pathlib import Path
import resource
import time

from binding import bind
from common import write_new
from decode import decode, population, select
from experiment import run_segment, segments


def main():
    parser = argparse.ArgumentParser()
    for arg in (
        "freeze-sha256",
        "sources",
        "vendor",
        "output",
        "proofs",
        "decoded",
        "timing",
    ):
        parser.add_argument("--" + arg, required=True)
    args = parser.parse_args()
    tick = time.perf_counter()
    cpu = resource.getrusage(resource.RUSAGE_SELF)
    data = bind(Path(__file__).parent, args.sources, args.vendor, args.freeze_sha256)
    rows = decode(data)
    selection = select(rows)
    write_new(
        args.decoded,
        dict(
            document_id="reiyah.navigation-measurement.decoded",
            version="0.1.0",
            rows=rows,
            selection=None if selection is None else [r["index"] for r in selection],
            population=population(rows),
        ),
    )
    prepared = time.perf_counter()
    reports, proofs = [], []
    if selection is not None:
        for segment in segments(selection):
            result, witness = run_segment(segment, "reiyah")
            reports.append(result)
            proofs.append(dict(id=segment["id"], stages=witness))
    calculated = time.perf_counter()
    report = dict(
        document_id="reiyah.navigation-measurement.reiyah",
        version="0.1.0",
        freeze_sha256=args.freeze_sha256,
        status="calculated_binding_pending" if selection else "blocked_no_eligible_run",
        source_population=population(rows),
        selection=None if selection is None else [r["index"] for r in selection],
        dependent_segments=reports,
        total_oracle_calls=sum(r["oracle_calls"] for r in reports),
        family="Conservative residual-rate relaxation; not the tight original-velocity family.",
        physical_qualification="unresolved",
        physical_cases=0,
    )
    write_new(args.output, report)
    write_new(
        args.proofs,
        dict(
            document_id="reiyah.navigation-measurement.proofs",
            version="0.1.0",
            freeze_sha256=args.freeze_sha256,
            segments=proofs,
        ),
    )
    end = resource.getrusage(resource.RUSAGE_SELF)
    write_new(
        args.timing,
        dict(
            arm="reiyah_residual",
            preparation_seconds=prepared - tick,
            calculation_seconds=calculated - prepared,
            process_through_output_seconds=time.perf_counter() - tick,
            cpu_seconds=end.ru_utime + end.ru_stime - cpu.ru_utime - cpu.ru_stime,
            source_bytes_loaded=len(data),
            original_packets_decoded=len(rows),
            logical_queries=report["total_oracle_calls"],
            acquisition_savings="not measured; full fixed prefix acquired and parsed",
        ),
    )
    print(
        dict(
            status=report["status"],
            population=report["source_population"],
            segments=len(reports),
            logical_queries=report["total_oracle_calls"],
        )
    )


if __name__ == "__main__":
    main()
