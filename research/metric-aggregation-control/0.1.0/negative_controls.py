"""Known-bad controls for population accounting, states, inputs and correction."""
import argparse
import copy
import importlib.util
import json
from pathlib import Path
import tempfile

HERE = Path(__file__).resolve().parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(source, result_path):
    producer, verifier = load("aggregation_producer", HERE / "reproduce.py"), load("aggregation_verifier", HERE / "verify.py")
    result = json.loads(Path(result_path).read_text())
    fixture = HERE / "fixtures.json"
    mutations = {}

    def altered(label, case, population, field, value):
        candidate = copy.deepcopy(result)
        row = next(r for r in candidate["configurations"] if r["case"] == case)
        if field in ("count", "state"):
            row["corrected"][population][field] = value
        else:
            row["corrected"][population]["means"][field] = value
        mutations[label] = candidate

    altered("wrong_mean", "primary_A", "all", "TVD", 0.0)
    altered("wrong_count", "primary_A", "all", "count", 1)
    altered("image_weighted_mean", "unequal_detection_counts", "all", "TVD", 0.3125)
    altered("zero_for_undefined", "all_empty", "all", "TVD", 0.0)
    altered("defined_for_empty", "all_empty", "all", "state", "defined")
    altered("boolean_count", "no_matches", "all", "count", True)
    candidate = copy.deepcopy(result)
    candidate["configurations"].pop()
    mutations["missing_configuration"] = candidate
    controls = {}

    def reject(label, call):
        try:
            call()
        except ValueError as exc:
            controls[label] = {"status": "rejected", "reason": str(exc)}
        else:
            raise ValueError("alteration accepted: " + label)

    with tempfile.TemporaryDirectory(prefix="reiyah-aggregation-controls-") as temporary:
        root = Path(temporary)
        for label, candidate in mutations.items():
            path = root / (label + ".json")
            path.write_text(json.dumps(candidate))
            reject(label, lambda: verifier.verify(path, fixture))
        changed_source = root / "changed-source.py"
        changed_source.write_bytes(Path(source).read_bytes() + b"\n")
        reject("source_byte_change", lambda: producer.run(changed_source, fixture))
        changed_fixture = root / "changed-fixture.json"
        changed_fixture.write_bytes(fixture.read_bytes() + b"\n")
        reject("fixture_byte_change", lambda: producer.run(source, changed_fixture))
        producer.collect_all_metrics = lambda scope: None
        disabled = producer.run(source, fixture)
        path = root / "disabled-correction.json"
        path.write_text(json.dumps(disabled))
        reject("disabled_correction", lambda: verifier.verify(path, fixture))
    return dict(artifact_id="reiyah.metric-aggregation-control.negative-controls", version="0.1.0",
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
