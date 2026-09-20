"""Check actual results with the separate conventional calculation."""

from pathlib import Path
import argparse
from common import Invalid, digest, frozen, keys, load, require, write_new
from reference import check


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze-sha256", required=True)
    parser.add_argument("--results", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        cases = frozen(Path(__file__).resolve().parent, args.freeze_sha256)
        results = load(args.results)
        keys(results, ("document_id", "version", "freeze_sha256", "cases"))
        require(
            results["document_id"] == "reiyah.continuous-envelope.results"
            and results["version"] == "0.1.0"
            and results["freeze_sha256"] == args.freeze_sha256,
            "result_identity",
        )
        require(
            type(results["cases"]) is list and len(results["cases"]) == len(cases),
            "result_membership",
        )
        for case, result in zip(cases, results["cases"]):
            check(case, result)
        write_new(
            args.output,
            {
                "document_id": "reiyah.continuous-envelope.verification",
                "version": "0.1.0",
                "status": "pass",
                "freeze_sha256": args.freeze_sha256,
                "results_sha256": digest(args.results),
                "cases": len(cases),
                "scope": "same_session_separate_arithmetic; not_independent_replication",
            },
        )
        print("separately verified authored cases:", len(cases))
    except (Invalid, OSError) as exc:
        parser.exit(2, str(exc) + "\n")


if __name__ == "__main__":
    main()
