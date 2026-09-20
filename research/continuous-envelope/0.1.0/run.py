"""Replay frozen authored cases; no private source or network dependency."""

from pathlib import Path
import argparse
from common import Invalid, frozen, write_new
from producer import solve


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze-sha256", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        cases = frozen(Path(__file__).resolve().parent, args.freeze_sha256)
        results = [solve(case) for case in cases]
        write_new(
            args.output,
            {
                "document_id": "reiyah.continuous-envelope.results",
                "version": "0.1.0",
                "freeze_sha256": args.freeze_sha256,
                "cases": results,
            },
        )
        print("authored conditional cases:", len(results))
    except (Invalid, OSError) as exc:
        parser.exit(2, str(exc) + "\n")


if __name__ == "__main__":
    main()
