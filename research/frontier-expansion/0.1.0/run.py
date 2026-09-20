"""Execute all frozen authored cases; this is a development study."""
import argparse,json
from pathlib import Path
from format import load_json,digest
from contract import evaluate
from binding import verify_freeze
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",required=True)
    args=parser.parse_args()
    root=Path(__file__).resolve().parent
    freeze=verify_freeze(root)
    allocation=load_json(root/"allocation.json")
    rows=[evaluate(entry["case"]) for entry in allocation["cases"]]
    result={"document_id":"reiyah.frontier-expansion.results","version":"0.1.0",
            "freeze_sha256":freeze,"allocation_sha256":digest(allocation),"cases":rows}
    Path(args.output).write_text(json.dumps(result,indent=2)+"\n")
    from collections import Counter
    print(json.dumps({"cases":len(rows),"worlds":sum(len(r["worlds"]) for r in rows),
                      "statuses":dict(Counter(r["status"] for r in rows))},sort_keys=True))
if __name__=="__main__":main()
