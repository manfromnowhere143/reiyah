"""Replay four exposed intake controls, not a scientific efficacy experiment."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tools.research_intake import assess, read_record


def main():
    folder = Path(__file__).resolve().parent
    cases = read_record(folder / "cases.json")
    results = []
    for case in cases["cases"]:
        result = assess(read_record(folder / case["mission"]),
                        read_record(folder / case["dossier"]), ROOT)
        if result["status"] != case["expected_status"]:
            raise RuntimeError(f"Unexpected status for {case['id']}: {result['status']}")
        if any(result["boundaries"][key] for key in (
            "semantic_entailment_verified", "observation_validity_verified",
            "scientific_support_established", "build_authorized", "reopening_authorized"
        )):
            raise RuntimeError("A structural check acquired unsupported authority")
        results.append({"case": case["id"], "status": result["status"],
                        "mission_sha256": result["mission_sha256"],
                        "dossier_sha256": result["dossier_sha256"],
                        "missing": result["missing"],
                        "incompatible_assumptions": result["incompatible_assumptions"]})
    print(json.dumps({"artifact_id": "reiyah.decision-research.development-result",
                      "version": "0.1.0", "efficacy_test": False,
                      "cases": results}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
