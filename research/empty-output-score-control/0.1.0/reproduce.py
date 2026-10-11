"""Authored controls; supply separately obtained, hash-bound upstream source."""
import argparse
import ast
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
from itertools import combinations
import json
from pathlib import Path

import numpy as np
import torch

SOURCE_SHA256 = "d19fab4078ffc61c594e72ad1719bd2179108187de26099c6614eb39ddeeba20"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def native_namespace(source):
    raw = Path(source).read_bytes()
    require(hashlib.sha256(raw).hexdigest() == SOURCE_SHA256, "source digest")
    tree = ast.parse(raw)
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
    require(len(functions) == 13, "source function inventory")
    require(all(not f.decorator_list for f in functions), "source decorators")
    scope = dict(torch=torch, np=np, defaultdict=defaultdict,
                 ThreadPoolExecutor=ThreadPoolExecutor, as_completed=as_completed,
                 tqdm=lambda values, **kwargs: values)
    # Exact function ASTs; no rewritten native statements or mocked tensor calls.
    exec(compile(ast.Module(body=functions, type_ignores=[]), str(source), "exec"), scope)
    return scope


def flatten_successful(roster, records):
    require(all(type(i) is int for i in roster), "roster IDs")
    require(len(set(roster)) == len(roster), "duplicate roster")
    ids = [r["image_id"] for r in records]
    require(all(type(i) is int for i in ids), "record IDs")
    require(len(set(ids)) == len(ids), "duplicate record")
    require(set(ids) == set(roster), "record membership")
    require(all(r["status"] == "success" for r in records), "unsuccessful output")
    detections = []
    for record in records:
        require(type(record["detections"]) is list, "detections must be explicit list")
        require(all(type(d["image_id"]) is int and d["image_id"] == record["image_id"]
                    for d in record["detections"]), "detection membership")
        detections.extend(record["detections"])
    return detections


def complete_reference_adapter(scope):
    original = scope["prepare_image_data"]

    def prepare(detections, annotations, dataset, model, mapping, device="cpu"):
        prepared = original(detections, annotations, dataset, model, mapping, device)
        grouped = defaultdict(list)
        for annotation in annotations:
            grouped[annotation["image_id"]].append(annotation)
        for image_id, refs in grouped.items():
            if image_id in prepared:
                continue
            labels = torch.tensor([r["soft_label"] for r in refs], dtype=torch.float32, device=device)
            boxes = torch.tensor([[x, y, x + w, y + h]
                                  for x, y, w, h in (r["bbox"] for r in refs)],
                                 dtype=torch.float32, device=device)
            prepared[image_id] = {
                "pred_boxes": torch.empty((0, 4), dtype=torch.float32, device=device),
                "pred_scores": torch.empty((0,), dtype=torch.float32, device=device),
                "probs": torch.empty((0, labels.shape[1]), dtype=torch.float32, device=device),
                "pred_areas": torch.empty((0,), dtype=torch.float32, device=device),
                "gt_boxes": boxes,
                "gt_labels": labels,
                "gt_areas": (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1]),
                "iou_matrix": torch.empty((0, len(refs)), dtype=torch.float32, device=device),
            }
        return prepared

    scope["prepare_image_data"] = prepare


def reference(image_id, width=10):
    return dict(id=image_id, image_id=image_id, category_id=1,
                bbox=[10, 10, width, width], soft_label=[1.0] + [0.0] * 80,
                area=width * width, iscrowd=0)


def detection(image_id, probability=1.0):
    return dict(image_id=image_id, category_id=1, bbox=[10, 10, 10, 10],
                score=probability, probs=[probability] + [0.0] * 79)


def records(roster, detected, probability=1.0):
    return [dict(image_id=i, status="success",
                 detections=[detection(i, probability)] if i in detected else [])
            for i in roster]


def calculate(scope, roster, outputs, annotations, area=(0, 1e10), chunk=64, workers=1):
    detections = flatten_successful(roster, outputs)
    require(all(a["image_id"] in roster for a in annotations), "reference membership")
    eligible = sum(area[0] <= a["bbox"][2] * a["bbox"][3] <= area[1] for a in annotations)
    require(eligible > 0, "undefined metric: no eligible reference objects")
    integral = scope["compute_AUSRC"]
    denominators = []

    def traced_integral(scores, similarities, bbox_tp, total_gt):
        denominators.append(total_gt)
        return integral(scores, similarities, bbox_tp, total_gt)

    scope["compute_AUSRC"] = traced_integral
    try:
        scored = scope["AUSRC_evaluation"](
            "coco", "authored-control", detections, annotations,
            iou_thresholds=[0.5], similarity_measures=["tv"], metrics=[],
            scores_to_sort=["maxprob"], device="cpu", area_ranges={"selected": area},
            chunk_size=chunk, num_workers=workers)
    except (RuntimeError, IndexError, ValueError) as exc:
        return {"status": "error", "exception": type(exc).__name__, "message": str(exc)}
    finally:
        scope["compute_AUSRC"] = integral
    require(len(scored) == 1, "unexpected score cardinality")
    require(len(denominators) == 1, "unexpected integral count")
    value = scored[0]["AUSRC"]
    require(np.isfinite(value), "nonfinite metric")
    return {"status": "defined", "AUSRC": value, "total_gt": denominators[0]}


def run(source):
    torch.set_num_threads(1)
    native, corrected = native_namespace(source), native_namespace(source)
    complete_reference_adapter(corrected)
    refs = [reference(1), reference(2)]
    primary = {}
    for arm, detected, probability in [("A", [1], 1.0), ("B", [1, 2], 0.8)]:
        outputs = records([1, 2], detected, probability)
        variants = []
        for reverse in (False, True):
            for chunk, workers in ((1, 1), (1, 2), (64, 1), (64, 2)):
                current_refs = list(reversed(refs)) if reverse else refs
                current_outputs = list(reversed(outputs)) if reverse else outputs
                variants.append({"reverse": reverse, "chunk_size": chunk, "workers": workers,
                    "native": calculate(native, [1, 2], current_outputs, current_refs, chunk=chunk, workers=workers),
                    "corrected": calculate(corrected, [1, 2], current_outputs, current_refs, chunk=chunk, workers=workers)})
        primary[arm] = variants

    subsets = []
    roster = [1, 2, 3]
    refs3 = [reference(i) for i in roster]
    for size in range(4):
        for selected in combinations(roster, size):
            outputs = records(roster, selected)
            subsets.append({"detected_image_ids": list(selected),
                            "native": calculate(native, roster, outputs, refs3),
                            "corrected": calculate(corrected, roster, outputs, refs3)})

    single = {name: calculate(scope, [1], records([1], [1]), [reference(1)])
              for name, scope in (("native", native), ("corrected", corrected))}
    outside_area = {name: calculate(scope, [1, 2], records([1, 2], [1]),
                                    [reference(1), reference(2, 64)], area=(0, 1024))
                    for name, scope in (("native", native), ("corrected", corrected))}

    # Keep native tensors for every nonempty image, including prediction-only images.
    tensor_rows = []
    ds = [detection(1), detection(3, 0.8)]
    for scope in (native, corrected):
        mapping = scope["build_coco_mapping"](device="cpu")
        tensor_rows.append(scope["prepare_image_data"](ds, refs, "coco", "authored-control", mapping, "cpu"))
    checks = 0
    for i in (1, 3):
        require(tensor_rows[0][i].keys() == tensor_rows[1][i].keys(), "tensor key parity")
        for key in tensor_rows[0][i]:
            require(torch.equal(tensor_rows[0][i][key], tensor_rows[1][i][key]), "nonempty tensor parity")
            checks += 1

    bad_cases = {
        "missing": records([1], [1]),
        "failed": [dict(image_id=1, status="success", detections=[detection(1)]),
                   dict(image_id=2, status="failed", detections=[])],
        "duplicate": records([1, 2], [1]) + records([2], []),
        "extra": records([1, 2, 3], [1]),
        "boolean_id": [dict(image_id=True, status="success", detections=[]),
                       dict(image_id=2, status="success", detections=[])],
    }
    rejections = {}
    for label, bad in bad_cases.items():
        try:
            flatten_successful([1, 2], bad)
        except ValueError as exc:
            rejections[label] = str(exc)
        else:
            raise ValueError("expected input rejection: " + label)
    try:
        calculate(corrected, [1], records([1], []), [], area=(0, 100))
    except ValueError as exc:
        rejections["undefined_denominator"] = str(exc)
    else:
        raise ValueError("expected undefined metric rejection")
    return dict(artifact_id="reiyah.empty-output-score-control.result", version="0.1.0",
                source_sha256=SOURCE_SHA256, primary=primary, presence_subsets=subsets,
                single_image=single, outside_area=outside_area,
                nonempty_tensor_equalities=checks, rejections=rejections)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = run(args.source)
    with open(args.output, "x") as output:
        json.dump(result, output, indent=2, allow_nan=False)
        output.write("\n")
