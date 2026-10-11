"""Prove that the checker rejects score, membership, type and adapter failures."""
import argparse
import copy
import importlib.util
import json
from pathlib import Path
import tempfile


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(source, result_path):
    here = Path(__file__).resolve().parent
    producer = load("empty_output_producer", here / "reproduce.py")
    verifier = load("empty_output_verifier", here / "verify.py")
    result = json.loads(Path(result_path).read_text())
    controls = {}

    def rejected(label, call):
        try:
            call()
        except ValueError as exc:
            controls[label] = {"status": "rejected", "reason": str(exc)}
        else:
            raise ValueError("alteration accepted: " + label)

    mutations = {}
    value = copy.deepcopy(result)
    value["primary"]["A"][0]["corrected"]["AUSRC"] = 1.0
    mutations["wrong_score"] = value
    value = copy.deepcopy(result)
    value["primary"]["A"][0]["corrected"]["total_gt"] = 1
    mutations["wrong_denominator"] = value
    value = copy.deepcopy(result)
    value["presence_subsets"][0]["corrected"]["AUSRC"] = False
    mutations["boolean_score"] = value
    value = copy.deepcopy(result)
    value["primary"]["A"][0]["workers"] = True
    mutations["boolean_worker_count"] = value
    value = copy.deepcopy(result)
    value["presence_subsets"].pop()
    mutations["missing_subset"] = value

    with tempfile.TemporaryDirectory(prefix="reiyah-empty-output-controls-") as temporary:
        root = Path(temporary)
        for label, value in mutations.items():
            path = root / (label + ".json")
            path.write_text(json.dumps(value))
            rejected(label, lambda: verifier.verify(path))
        altered_source = root / "altered-source.py"
        altered_source.write_bytes(Path(source).read_bytes() + b"\n")
        rejected("source_byte_change", lambda: producer.native_namespace(altered_source))
        producer.complete_reference_adapter = lambda scope: None
        uncorrected = producer.run(source)
        path = root / "disabled-adapter.json"
        path.write_text(json.dumps(uncorrected))
        rejected("disabled_adapter", lambda: verifier.verify(path))
    return dict(artifact_id="reiyah.empty-output-score-control.negative-controls", version="0.1.0",
                status="pass", controls=controls)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True)
    parser.add_argument("--result", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    receipt = run(args.source, args.result)
    with open(args.output, "x") as output:
        json.dump(receipt, output, indent=2, allow_nan=False)
        output.write("\n")
