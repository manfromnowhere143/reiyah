"""Check that altered source, witness rows and aggregate claims are rejected."""
import argparse
import copy
import json
from pathlib import Path
import tempfile

from verify import verify


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--rows", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    args = parser.parse_args()
    verify(args.data, args.rows, args.result)
    original_rows = json.loads(args.rows.read_bytes())
    original_result = json.loads(args.result.read_bytes())
    cases = []
    with tempfile.TemporaryDirectory(prefix="reiyah-reviewer-rejections-") as temporary:
        root = Path(temporary)
        for name in ("source", "missing_row", "duplicate_row", "raw_outcome", "count_bound",
                     "witness", "Hall_obstruction", "repeat_flag", "aggregate_primary",
                     "boolean_count", "floating_count"):
            rows = copy.deepcopy(original_rows)
            result = copy.deepcopy(original_result)
            data_path = args.data
            if name == "source":
                data_path = root / "wrong_source.json"
                data_path.write_text("{}\n")
            elif name == "missing_row":
                rows.pop()
            elif name == "duplicate_row":
                rows.append(copy.deepcopy(rows[0]))
            elif name == "raw_outcome":
                rows[0]["raw_outcome"] = "forged_class"
            elif name == "count_bound":
                next(iter(rows[0]["class_count_bounds"].values()))["upper"] += 1
            elif name == "witness":
                next(iter(rows[0]["outcome_witnesses"].values()))[0] = "forged_class"
            elif name == "Hall_obstruction":
                subject = next(r for r in rows if r["no_majority_obstruction"] is not None)
                subject["no_majority_obstruction"]["forced_group_indices"] = []
            elif name == "repeat_flag":
                rows[0]["repeated_id"] = not rows[0]["repeated_id"]
            elif name == "aggregate_primary":
                result["procedures"]["proposed"]["raw_outcome_not_invariant"] += 1
            elif name == "boolean_count":
                bound = next(b for r in rows for b in r["class_count_bounds"].values()
                             if b["lower"] == 0)
                bound["lower"] = False
            elif name == "floating_count":
                result["procedures"]["proposed"]["raw_ordinary_majority_can_switch_ordinary_class"] = 0.0
            row_path, result_path = root / "rows.json", root / "result.json"
            row_path.write_text(json.dumps(rows))
            result_path.write_text(json.dumps(result))
            try:
                verify(data_path, row_path, result_path)
            except ValueError as error:
                cases.append({"case": name, "rejected": True, "reason": str(error)})
            else:
                raise AssertionError("Mutation accepted: " + name)
    print(json.dumps({"artifact_id": "reiyah.reviewer-identity-sensitivity.rejections",
                      "version": "0.1.0", "status": "pass", "cases": cases}, indent=2))


if __name__ == "__main__":
    main()
