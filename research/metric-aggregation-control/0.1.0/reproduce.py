"""Check native auxiliary aggregation on fixed, authored detection populations."""
import argparse
from fractions import Fraction
import hashlib
import importlib.util
from itertools import permutations
import json
import math
from pathlib import Path

import torch

HERE = Path(__file__).resolve().parent
METRICS = ("MAE", "MSE", "KL", "JSD", "TVD", "cosine_dist")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load_inputs(fixtures_path):
    protocol = json.loads((HERE / "protocol.json").read_text())
    raw = Path(fixtures_path).read_bytes()
    require(hashlib.sha256(raw).hexdigest() == protocol["fixtures_sha256"], "fixture digest")
    prior_path = HERE.parent.parent / "empty-output-score-control/0.1.0/reproduce.py"
    require(hashlib.sha256(prior_path.read_bytes()).hexdigest() == protocol["prior_control_sha256"],
            "inherited control digest")
    spec = importlib.util.spec_from_file_location("empty_output_control", prior_path)
    prior = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prior)
    return json.loads(raw), prior


def collect_all_metrics(scope):
    original = scope["process_chunk"]

    def process(chunk, *args, **kwargs):
        require(bool(chunk), "empty execution chunk")
        parts = [original({image_id: data}, *args, **kwargs) for image_id, data in chunk.items()]
        score_keys, sim_keys = parts[0][0].keys(), parts[0][1].keys()
        scores = {k: [a for p in parts for a in p[0][k]] for k in score_keys}
        similarities = {k: [a for p in parts for a in p[1][k]] for k in sim_keys}
        true_positives = [a for p in parts for a in p[2]]
        reference_count = sum(p[3] for p in parts)
        all_metrics = {k: torch.cat([p[4][k] for p in parts]) for k in parts[0][4]}
        matched_metrics = {k: torch.cat([p[5][k] for p in parts]) for k in parts[0][5]}
        return scores, similarities, true_positives, reference_count, all_metrics, matched_metrics

    scope["process_chunk"] = process


def native_inputs(case, order, prior):
    by_id = {image["id"]: image for image in case["images"]}
    refs, outputs = [], []
    for image_id in order:
        image = by_id[image_id]
        for box in image["reference_boxes"]:
            refs.append(dict(id=len(refs) + 1, image_id=image_id, category_id=1,
                             bbox=box, soft_label=[1.0] + [0.0] * 80,
                             area=box[2] * box[3], iscrowd=0))
        detections = []
        for detection in image["detections"]:
            probability = float(Fraction(detection["probability"]))
            detections.append(dict(image_id=image_id, category_id=1, bbox=detection["bbox"],
                                   score=probability, probs=[probability] + [0.0] * 79))
        outputs.append(dict(image_id=image_id, status="success", detections=detections))
    return prior.flatten_successful(list(order), outputs), refs


def calculate(scope, case, order, chunk_size, workers, prior):
    detections, annotations = native_inputs(case, order, prior)
    process, integrate = scope["process_chunk"], scope["compute_AUSRC"]
    counts, denominators = [], []

    def traced_process(chunk, *args, **kwargs):
        result = process(chunk, *args, **kwargs)
        for population in (4, 5):
            sizes = {result[population][metric].numel() for metric in METRICS}
            require(len(sizes) == 1, "metric population mismatch")
        counts.append((result[4]["TVD"].numel(), result[5]["TVD"].numel()))
        return result

    def traced_integral(scores, similarities, bbox_tp, total_gt):
        denominators.append(total_gt)
        return integrate(scores, similarities, bbox_tp, total_gt)

    scope["process_chunk"], scope["compute_AUSRC"] = traced_process, traced_integral
    try:
        rows = scope["AUSRC_evaluation"](
            "coco", "authored-control", detections, annotations,
            iou_thresholds=[0.5], similarity_measures=["tv"], metrics=list(METRICS),
            scores_to_sort=["maxprob"], device="cpu",
            area_ranges={"selected": tuple(case.get("area", [0, 1e10]))},
            chunk_size=chunk_size, num_workers=workers)
    finally:
        scope["process_chunk"], scope["compute_AUSRC"] = process, integrate
    require(len(rows) == len(denominators) == 1 and denominators[0] > 0, "scoring population")
    record = {"AUSRC": rows[0]["AUSRC"], "total_gt": denominators[0]}
    for i, population in enumerate(("all", "matched")):
        count = sum(c[i] for c in counts)
        means = {}
        for metric in METRICS:
            value = rows[0][f"mean_{metric}_{population}"]
            if count:
                require(math.isfinite(value), "nonfinite mean with nonempty population")
                means[metric] = value
            else:
                require(math.isnan(value), "expected native undefined mean")
                means[metric] = None
        record[population] = {"count": count, "state": "defined" if count else "undefined_no_samples",
                              "means": means}
    return record


def run(source, fixtures_path):
    torch.set_num_threads(1)
    fixtures, prior = load_inputs(fixtures_path)
    native, corrected = prior.native_namespace(source), prior.native_namespace(source)
    for scope in (native, corrected):
        prior.complete_reference_adapter(scope)
    collect_all_metrics(corrected)
    rows = []
    for case in fixtures["cases"]:
        for order in permutations(image["id"] for image in case["images"]):
            for chunk_size in (1, 2, 64):
                for workers in (1, 2):
                    a = calculate(native, case, order, chunk_size, workers, prior)
                    b = calculate(corrected, case, order, chunk_size, workers, prior)
                    require(a["AUSRC"] == b["AUSRC"] and a["total_gt"] == b["total_gt"],
                            "aggregation changed AUSRC or reference count")
                    rows.append(dict(case=case["id"], order=list(order), chunk_size=chunk_size,
                                     workers=workers, native=a, corrected=b))
    require(len(rows) == 90, "configuration count")
    return dict(artifact_id="reiyah.metric-aggregation-control.result", version="0.1.0",
                fixtures_sha256=hashlib.sha256(Path(fixtures_path).read_bytes()).hexdigest(),
                source_sha256=prior.SOURCE_SHA256, configurations=rows)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True)
    parser.add_argument("--fixtures", default=str(HERE / "fixtures.json"))
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = run(args.source, args.fixtures)
    with open(args.output, "x") as output:
        json.dump(result, output, indent=2, allow_nan=False)
        output.write("\n")
