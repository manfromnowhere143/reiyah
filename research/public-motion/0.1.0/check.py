"""Derive each expectation from source rows using the separate reference."""
import argparse
from common import VERSION, canonical, digest, frozen_sources, load, require, write_new
from reference import evaluate_reference

def verify(seeds, rows, result, freeze):
    expected = {"document_id":"reiyah.public-motion.results","version":VERSION,
                "freeze_sha256":freeze,"scope":"recorded_longitudinal_proxy_only",
                "source_rows":len(rows),"cases":evaluate_reference(seeds,rows)}
    require(result == expected, "result_mismatch")

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--sources",required=True)
    parser.add_argument("--results",required=True)
    parser.add_argument("--output",required=True)
    parser.add_argument("--freeze-sha256",required=True)
    args=parser.parse_args()
    seeds,rows,freeze=frozen_sources(args.sources,args.freeze_sha256)
    result=load(args.results)
    verify(seeds,rows,result,freeze)
    receipt={"document_id":"reiyah.public-motion.verification","version":VERSION,
             "freeze_sha256":freeze,"result_sha256":digest(canonical(result)),
             "cases_checked":len(result["cases"]),"all_equal_to_conventional":True,
             "independent_replication":False,"shared_component":"strict JSON/source-shape and byte-binding gate only"}
    write_new(args.output,receipt)
    print(receipt)
if __name__ == "__main__":
    main()
