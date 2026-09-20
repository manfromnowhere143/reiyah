"""Run all eight bound development candidates without overwriting a prior result."""
import argparse
from collections import Counter
from common import VERSION, frozen_sources, write_new
from adapter import evaluate

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sources", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--freeze-sha256", required=True)
    args = parser.parse_args()
    seeds, rows, freeze = frozen_sources(args.sources, args.freeze_sha256)
    cases = evaluate(seeds, rows)
    result = {"document_id":"reiyah.public-motion.results","version":VERSION,
              "freeze_sha256":freeze,"scope":"recorded_longitudinal_proxy_only",
              "source_rows":len(rows),"cases":cases}
    write_new(args.output, result)
    print(dict(Counter(r["recorded_sample_obligation"] for r in cases)))
if __name__ == "__main__":
    main()
