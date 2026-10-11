"""Check the complete revised reference against the frozen score-file target."""

import argparse
import collections
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load(path, digest):
    require(sha(path) == digest, "Reference/input qualification failed")
    return json.loads(
        path.read_text(), parse_constant=lambda s: (_ for _ in ()).throw(ValueError(s))
    )


def unique(rows, key="id"):
    require(
        all((type(r[key]) is int for r in rows)), "Reference/input qualification failed"
    )
    result = {r[key]: r for r in rows}
    require(len(result) == len(rows), "Reference/input qualification failed")
    return result


def audit(dataset):
    images = unique(dataset["images"])
    categories = unique(dataset["categories"])
    annotations = unique(dataset["annotations"])
    for a in annotations.values():
        require(
            a["image_id"] in images and a["category_id"] in categories,
            "Reference/input qualification failed",
        )
        require(
            len(a["bbox"]) == 4 and all((math.isfinite(x) for x in a["bbox"])),
            "Reference/input qualification failed",
        )
        require(
            all((x >= 0 for x in a["bbox"][2:])), "Reference/input qualification failed"
        )
        require(
            math.isfinite(a["area"]) and a["area"] >= 0,
            "Reference/input qualification failed",
        )
        require(a["iscrowd"] in [0, 1], "Reference/input qualification failed")
    return (images, categories, annotations)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    inputs = json.loads((ROOT / "inputs.json").read_text())
    records = {row["name"]: row for row in inputs["files"]}
    old = load(
        args.data_dir / "instances_val2017.json",
        records["instances_val2017.json"]["sha256"],
    )
    new = load(
        args.data_dir / "instances_valrem.json",
        records["instances_valrem.json"]["sha256"],
    )
    oi, oc, oa = audit(old)
    ni, nc, na = audit(new)
    require(
        len(oi) == len(ni) == 5000 and set(oi) == set(ni),
        "Reference/input qualification failed",
    )
    require(
        all(
            (
                (oi[i]["width"], oi[i]["height"]) == (ni[i]["width"], ni[i]["height"])
                for i in oi
            )
        ),
        "Reference/input qualification failed",
    )
    require(
        len(oc) == len(nc) == 80 and set(oc) == set(nc),
        "Reference/input qualification failed",
    )
    require(
        all((oc[i]["name"] == nc[i]["name"] for i in oc)),
        "Reference/input qualification failed",
    )
    by_source = collections.Counter(
        (a.get("source", "unavailable") for a in na.values())
    )
    mapped, box_changes, area_changes, crowd_changes, invalid_links = (
        [],
        [],
        [],
        [],
        [],
    )
    for a in na.values():
        if a.get("source") != "coco":
            continue
        b = oa.get(a.get("source_id"))
        if b is None or (b["image_id"], b["category_id"]) != (
            a["image_id"],
            a["category_id"],
        ):
            invalid_links.append(a["id"])
            continue
        mapped.append(a["source_id"])
        if a["bbox"] != b["bbox"]:
            box_changes.append(a["id"])
        if a["area"] != b["area"]:
            area_changes.append(a["id"])
        if a["iscrowd"] != b["iscrowd"]:
            crowd_changes.append(a["id"])
    require(
        not invalid_links and len(mapped) == len(set(mapped)),
        "Reference/input qualification failed",
    )

    def signatures(anns):
        d = collections.defaultdict(collections.Counter)
        for a in anns.values():
            d[a["image_id"]][a["category_id"], *a["bbox"], a["area"], a["iscrowd"]] += 1
        return d

    os, ns = (signatures(oa), signatures(na))
    changed_images = [i for i in sorted(oi) if os[i] != ns[i]]
    models = {}
    for name in ("r50.json", "r101.json"):
        record = records[name]
        detections = load(args.data_dir / name, record["sha256"])
        for d in detections:
            require(
                d["image_id"] in oi and d["category_id"] in oc,
                "Reference/input qualification failed",
            )
            require(
                len(d["bbox"]) == 4 and all((math.isfinite(x) for x in d["bbox"])),
                "Reference/input qualification failed",
            )
            require(
                all((x >= 0 for x in d["bbox"][2:])),
                "Reference/input qualification failed",
            )
            require(
                math.isfinite(d["score"]) and 0 <= d["score"] <= 1,
                "Reference/input qualification failed",
            )
        observed = {d["image_id"] for d in detections}
        models[Path(name).stem] = {
            "prediction_rows": len(detections),
            "rows_filtered": 0,
            "images_without_submitted_detection_rows": sorted(set(oi) - observed),
            "zero_extent_rows_retained": sum(
                (d["bbox"][2] == 0 or d["bbox"][3] == 0 for d in detections)
            ),
        }
    out = {
        "artifact_id": "reiyah.reference-compatibility",
        "version": "0.1.0",
        "status": "compatible_for_conditional_bbox_score_file_replay",
        "inputs_manifest_sha256": sha(ROOT / "inputs.json"),
        "script_sha256": sha(Path(__file__)),
        "original_annotation_count": len(oa),
        "revised_annotation_count": len(na),
        "images": 5000,
        "categories": 80,
        "all_image_dimensions_and_category_names_match": True,
        "new_reference_source_counts": dict(by_source),
        "valid_unique_original_coco_source_links": len(mapped),
        "original_annotations_without_retained_coco_source_link": len(oa) - len(mapped),
        "matched_source_bbox_changed_count": len(box_changes),
        "matched_source_area_changed_count": len(area_changes),
        "matched_source_crowd_flag_changed_count": len(crowd_changes),
        "images_with_changed_bbox_evaluation_reference": len(changed_images),
        "models": models,
        "interpretation": "Reference revision, not measured annotation error rate or independently verified physical truth",
        "original_inference_completion": "unverified; absent rows mean no submitted detections only",
        "full_work_trial_admitted": False,
        "Reiyah_arm": "not_run",
    }
    expected = json.loads((ROOT / "reference-summary.json").read_text())
    for key, value in expected.items():
        if key not in ("plan_sha256", "script_sha256"):
            require(out[key] == value, "Reference summary changed: " + key)
    with args.output.open("x") as stream:
        stream.write(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
