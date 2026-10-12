#!/usr/bin/env python3
"""Compose checked fixed-procedure matching cases; no inference or new native caps."""
import argparse
import copy
from decimal import Decimal
from fractions import Fraction
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tools.perception_revision import contract, kernel, checker

PROTOCOL_SHA = "d27a73f692ab15ec7402ff052c8a7aa0a0ef3539d89dda0ec1c38b8588ce6f08"
AUDIT_SHA = "5830fa0d56755a014c0a206f9bb5123bf148f3399cb51048d12b07875e0d892d"
PROCEDURES = ("t0", "t1_A", "t1_B")
MODELS = ("faster", "yolo")
MAX_COORDINATE = 10_000_000


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def ratio(value):
    return f"{value.numerator}/{value.denominator}"


def wire(value):
    return contract.wire(Fraction(value))


def closed(value, keys, reason):
    require(type(value) is dict and set(value) == set(keys), reason)


def load_audit():
    path = Path(__file__).resolve().parents[1] / "0.1.0/audit.py"
    require(sha(path.read_bytes()) == AUDIT_SHA, "annotation audit changed")
    spec = importlib.util.spec_from_file_location("multiorg_frozen_annotation_audit", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_bound(path, digest, limit, audit):
    require(path.is_file() and not path.is_symlink(), "bound input unavailable or symlinked")
    with path.open("rb") as stream:
        raw = stream.read(limit + 1)
    require(len(raw) <= limit and sha(raw) == digest, "bound input digest or byte limit differs")
    return audit.strict_json(raw)


def number(value):
    require(type(value) is int or type(value) is Decimal and value.is_finite(), "finite exact numeric coordinate/score required")
    return Fraction(value)


def rectangle(values):
    require(type(values) is list and len(values) == 4, "xyxy rectangle shape")
    box = tuple(number(value) for value in values)
    require(all(abs(value) <= MAX_COORDINATE for value in box), "native coordinate magnitude cap exceeded")
    require(box[0] < box[2] and box[1] < box[3], "nonpositive rectangle extent")
    return box


def overlaps(a, b):
    width = max(Fraction(), min(a[2], b[2]) - max(a[0], b[0]))
    height = max(Fraction(), min(a[3], b[3]) - max(a[1], b[1]))
    intersection = width * height
    total = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1])
    return 3 * intersection >= total


def conventional_cardinality(detections, edges):
    adjacency = {d: sorted(o for left, o in edges if left == d) for d in detections}
    matched = {}
    def augment(detection, visited):
        for obj in adjacency[detection]:
            if obj in visited:
                continue
            visited.add(obj)
            if obj not in matched or augment(matched[obj], visited):
                matched[obj] = detection
                return True
        return False
    return sum(augment(detection, set()) for detection in sorted(detections))


def references(raw, source_path, audit):
    audit.annotation_geometry(raw, source_path)
    require(len(raw) <= 128, "native reference-object cap exceeded")
    result = []
    for box_id, corners in sorted(raw.items()):
        # Source is [row,column]; native continuous rectangles are [x,y,x,y].
        rows = [number(point[0]) for point in corners]
        columns = [number(point[1]) for point in corners]
        box = (min(columns), min(rows), max(columns), max(rows))
        require(all(abs(value) <= MAX_COORDINATE for value in box), "native reference coordinate cap exceeded")
        oid = "r-" + sha(canonical([source_path, box_id]))
        result.append((oid, box))
    return result


def predictions(payload, image, model):
    require(type(payload) is dict, "prediction object required")
    require(payload.get("status") == "complete" and payload.get("image_id") == image and payload.get("model") == model, "prediction identity/completion differs")
    for key in ("image_shape_hw", "rescaled_shape_hw"):
        require(type(payload.get(key)) is list and len(payload[key]) == 2 and all(type(v) is int and v > 0 for v in payload[key]), "image shape invalid")
    count = payload.get("tile_count_expected")
    require(type(count) is int and count > 0 and type(payload.get("tile_count_completed")) is int and payload["tile_count_completed"] == count, "incomplete tile coverage")
    tiles = payload.get("tiles")
    height, width = payload["rescaled_shape_hw"]
    require(payload["rescaled_shape_hw"] == [max(1, round(value / 2)) for value in payload["image_shape_hw"]], "rescale shape differs")
    require(height * width <= 20_000_000, "rescaled pixel cap exceeded")
    expected_tiles = [(r, c) for r in range(0, height, 256) for c in range(0, width, 256)]
    require(type(tiles) is list and len(tiles) == count == len(expected_tiles) and count <= 512, "tile roster differs")
    raw_rows = 0
    for ordinal, (tile, coordinates) in enumerate(zip(tiles, expected_tiles)):
        closed(tile, ("ordinal", "rescaled_row", "rescaled_column", "onnx_rows", "below_storage_floor"), "tile trace properties")
        require(all(type(value) is int and value >= 0 for value in tile.values()), "tile trace types")
        require(tile["ordinal"] == ordinal and (tile["rescaled_row"], tile["rescaled_column"]) == coordinates, "tile position/ordinal differs")
        require(tile["below_storage_floor"] <= tile["onnx_rows"], "tile output counts differ")
        raw_rows += tile["onnx_rows"]
    require(type(payload.get("raw_onnx_rows")) is int and payload["raw_onnx_rows"] == raw_rows <= 200_000, "raw output count/cap differs")
    storage = payload.get("storage_predictions")
    require(type(storage) is list and len(storage) <= 1_000_000, "storage prediction bound")
    seen, selected, expected_analysis = set(), [], []
    for row in storage:
        closed(row, ("id", "box_xyxy", "score"), "prediction row properties")
        require(type(row["id"]) is int and row["id"] >= 0 and row["id"] not in seen, "duplicate/invalid prediction identity")
        seen.add(row["id"])
        box, score = rectangle(row["box_xyxy"]), number(row["score"])
        # Float32 0.05 lies above exact 1/20; no tolerance admits lower scores.
        require(Fraction(1, 20) <= score <= 1, "stored score outside declared range")
        if score > Fraction(1, 2):
            expected_analysis.append(row)
            did = model + "-" + str(row["id"])
            record_digest = sha(canonical({"image": image, "model": model, "row": row["id"], "xyxy": [ratio(v) for v in box], "score": ratio(score)}))
            selected.append((did, box, record_digest))
    require(payload.get("analysis_predictions") == expected_analysis and type(payload.get("empty_analysis")) is bool and payload["empty_analysis"] == (not selected), "analysis filter/empty state differs")
    require(len(selected) <= 1024, "native detection cap exceeded")
    require(len(storage) <= raw_rows - sum(tile["below_storage_floor"] for tile in tiles), "stored rows exceed eligible ONNX rows")
    return selected


def fixed_case(image, procedure, aa, bb, refs, context_digest):
    require(len(refs) <= 128 and len(aa) <= 1024 and len(bb) <= 1024, "native object/detection cap exceeded")
    require((len(aa) + len(bb)) * len(refs) <= contract.MAX_WORK, "geometry pair-screening cap exceeded")
    edges = {(did, oid) for did, box, _ in aa + bb for oid, ref in refs if overlaps(box, ref)}
    require(len(edges) <= 2048, "native edge cap exceeded")
    iid = sha(image.encode())
    case = {"artifact_id": "reiyah.perception-revision.input", "version": "0.1.0", "comparison_id": "multiorg-" + iid[:32] + "-" + procedure,
            "cohort_id": "multiorg-" + iid, "input_scope": "normalized_research_graphs", "evidence_kind": "conditional_reference_graph",
            "reference_context_sha256": context_digest,
            "assumptions": ["One complete recorded annotation procedure; not physical truth or complete physical uncertainty.", "Unit FP/FN; exact continuous IoU>=1/2; whole-image source coordinates retained without repair."],
            "loss": {"false_negative": wire(1), "false_positive": wire(1), "tolerance": wire(0)}, "model": {"variables": [], "clauses": []},
            "anchors": [{"id": "image", "weight": wire(1),
                         "output_a": {"state": "observed", "value": [{"id": d, "record_sha256": h} for d, _, h in aa]},
                         "output_b": {"state": "observed", "value": [{"id": d, "record_sha256": h} for d, _, h in bb]},
                         "reference": {"state": "finite", "objects": [{"id": o, "when": []} for o, _ in refs],
                                       "edges": [{"detection": d, "object": o, "when": []} for d, o in sorted(edges)]}}]}
    contract.validate(case)
    require(len(contract.encoded(case)) <= contract.MAX_INPUT_BYTES, "native input-byte cap exceeded")
    worlds, work = contract.capacity(case)
    require(worlds <= contract.MAX_WORLDS and worlds * work <= contract.MAX_WORK, "native screening-work cap exceeded")
    proposal = kernel.produce(case)
    verified = checker.check(case, proposal)
    require(verified["execution_status"] == "succeeded" and verified["enclosure_kind"] == "exact_for_finite_model", "native fixed graph not exact")
    ta = conventional_cardinality([r[0] for r in aa], edges)
    tb = conventional_cardinality([r[0] for r in bb], edges)
    delta = len(aa) - len(bb) + 2 * (tb - ta)
    require(contract.rational(verified["bounds"]["lower"]) == delta == contract.rational(verified["bounds"]["upper"]), "native and conventional delta disagree")
    anchor = proposal["proof"]["worlds"][0]["anchors"][0]
    require(len(anchor["output_a"]["matching"]) == ta and len(anchor["output_b"]["matching"]) == tb, "native and conventional cardinality disagree")
    require(len(contract.encoded(proposal)) <= contract.MAX_PACKET_BYTES, "native proof-byte cap exceeded")
    cell = {"tiff_path": image, "procedure": procedure, "reference_count": len(refs), "detections_a": len(aa), "detections_b": len(bb),
            "tp_a": ta, "tp_b": tb, "fp_a": len(aa) - ta, "fp_b": len(bb) - tb, "fn_a": len(refs) - ta, "fn_b": len(refs) - tb,
            "delta": ratio(Fraction(delta)), "native_input_sha256": sha(contract.encoded(case)), "native_proof_sha256": sha(contract.encoded(proposal)), "native_work_units": worlds * work}
    return cell, case, proposal


def decision(lower, upper):
    return "prefer_b" if lower > 0 else "prefer_a" if upper < 0 else "unresolved"


def compose(cells, images, complete):
    require(images and len(set(images)) == len(images), "nonempty unique image roster required")
    values = {(row["tiff_path"], row["procedure"]): Fraction(row["delta"]) for row in cells}
    require(len(values) == len(cells) and set(values) == {(image, proc) for image in images for proc in PROCEDURES}, "composition cell roster differs")
    n = len(images)
    sums = {proc: sum((values[image, proc] for image in images), Fraction()) / n for proc in PROCEDURES}
    low_proc = min(PROCEDURES, key=lambda proc: (sums[proc], proc))
    high_proc = min(PROCEDURES, key=lambda proc: (-sums[proc], proc))
    gl, gh = sums[low_proc], sums[high_proc]
    lows = [{"tiff_path": image, "procedure": min(PROCEDURES, key=lambda proc: (values[image, proc], proc))} for image in images]
    highs = [{"tiff_path": image, "procedure": min(PROCEDURES, key=lambda proc: (-values[image, proc], proc))} for image in images]
    pl = sum((values[row["tiff_path"], row["procedure"]] for row in lows), Fraction()) / n
    ph = sum((values[row["tiff_path"], row["procedure"]] for row in highs), Fraction()) / n
    require(pl <= gl <= gh <= ph, "global interval not contained in imagewise interval")
    gd, pd = decision(gl, gh), decision(pl, ph)
    primary = "inconclusive_incomplete_selected_cohort"
    if complete and n >= 2:
        primary = "inconclusive_global_unresolved" if gd == "unresolved" else "coupling_fragility" if pd == "unresolved" else "no_observed_fragility"
        require(pd == "unresolved" or pd == gd, "nested families yielded opposite resolved decisions")
    return {"global": {"lower": ratio(gl), "upper": ratio(gh), "decision": gd, "lower_procedure": low_proc, "upper_procedure": high_proc},
            "imagewise": {"lower": ratio(pl), "upper": ratio(ph), "decision": pd, "lower_choices": lows, "upper_choices": highs},
            "primary_status": primary}


def load_runs(run_bindings, selected, audit):
    observations, bindings = {}, []
    for path, digest in run_bindings:
        path = Path(path)
        receipt = load_bound(path, digest, 4 << 20, audit)
        require(receipt.get("status") == "complete", "inference result incomplete")
        process_path = path.parent.with_suffix(".process.json")
        require(process_path.is_file() and not process_path.is_symlink(), "supervisor receipt unavailable")
        with process_path.open("rb") as stream:
            process_raw = stream.read((1 << 20) + 1)
        require(len(process_raw) <= 1 << 20, "supervisor receipt exceeds byte cap")
        process = audit.strict_json(process_raw)
        require(type(process) is dict and process.get("status") == "complete" and type(process.get("returncode")) is int and process["returncode"] == 0 and "termination_reason" in process and process["termination_reason"] is None, "inference supervisor did not complete")
        manifest = receipt.get("manifest")
        require(type(manifest) is dict and manifest.get("protocol", {}).get("sha256") == PROTOCOL_SHA, "inference protocol binding differs")
        ids = [row["id"] for row in manifest["images"]]
        require(ids and len(set(ids)) == len(ids) and set(ids) <= set(selected), "inference image assignment differs")
        config = receipt["config"]
        for key, value in (("storage_score_gte", Fraction(1, 20)), ("analysis_score_gt", Fraction(1, 2)), ("nms_iou", Fraction(1, 2)), ("window_original", Fraction(1024)), ("downsample", Fraction(2)), ("overlap", Fraction(1, 2))):
            require(number(config[key]) == value, "inference configuration differs")
        require(config["diameter_filter"] is None and config["boundary_policy"] == "preserve_decoded_coordinates_and_report", "inference coordinate/filter policy differs")
        seen = set()
        for descriptor in receipt["observations"]:
            key = descriptor["image_id"], descriptor["model"]
            require(key not in seen and key not in observations, "duplicate prediction opportunity")
            seen.add(key)
            relative = audit.relative(descriptor["file"])
            require(len(relative.parts) == 1, "prediction output must be local file")
            payload = load_bound(path.parent / descriptor["file"], descriptor["sha256"], 64 << 20, audit)
            rows = predictions(payload, *key)
            require(descriptor["analysis_count"] == len(rows) and descriptor["storage_count"] == len(payload["storage_predictions"]), "prediction count metadata differs")
            observations[key] = (rows, payload["image_shape_hw"], descriptor["sha256"])
        require(seen == {(image, model) for image in ids for model in MODELS}, "incomplete A/B opportunity roster")
        bindings.append({"result_sha256": digest, "process_receipt_sha256": sha(process_raw), "runner_sha256": receipt["runner_sha256"], "inference_manifest_sha256": receipt["manifest_sha256"], "image_ids": ids})
    images = [image for image in selected if (image, "faster") in observations]
    require(images and images == selected[:len(images)], "partial cohort must preserve frozen image prefix")
    for image in images:
        require(observations[image, "faster"][1] == observations[image, "yolo"][1], "paired image dimensions differ")
    return observations, images, bindings


def run(args):
    audit = load_audit()
    protocol_path = Path(__file__).with_name("protocol.json")
    protocol = load_bound(protocol_path, PROTOCOL_SHA, 1 << 20, audit)
    manifest = load_bound(args.annotations, protocol["source_manifest_sha256"], 4 << 20, audit)
    census = audit.audit_manifest(manifest, args.sources)
    require(census["annotation_census"] == "complete", "annotation census incomplete")
    eligible = [row for row in census["images"] if all(count <= 128 for count in row["annotation_counts"].values())]
    selected = [row["tiff_path"] for row in sorted(eligible, key=lambda row: (row["selection_sha256"], row["tiff_path"]))[:4]]
    require(len(eligible) == protocol["individually_object_eligible_count"] and selected == protocol["selected_images"], "fixed-procedure selection differs")
    observations, images, run_bindings = load_runs(args.run, selected, audit)
    require(not args.output.exists(), "output already exists")
    cells, packets = [], []
    by_image = {row["tiff_path"]: row for row in manifest["images"]}
    for image in images:
        aa, bb = observations[image, "faster"][0], observations[image, "yolo"][0]
        sources = {row["procedure"]: row for row in by_image[image]["annotations"]}
        for procedure in PROCEDURES:
            source = sources[procedure]
            raw = load_bound(audit.source_path(args.sources, source["local_path"]), source["sha256"], 1 << 20, audit)
            refs = references(raw, source["source_path"], audit)
            context = sha(canonical({"procedure": procedure, "source_sha256": source["sha256"], "source_path": source["source_path"], "protocol_sha256": PROTOCOL_SHA}))
            cell, case, proposal = fixed_case(image, procedure, aa, bb, refs, context)
            cells.append(cell); packets.append((sha(image.encode()) + "-" + procedure, case, proposal))
    result = {"artifact_id": "reiyah.multiorg.fixed-procedure.result", "version": "0.2.0", "status": "verified_fixed_cases",
              "protocol_sha256": PROTOCOL_SHA, "producer_sha256": sha(Path(__file__).read_bytes()), "annotation_manifest_sha256": protocol["source_manifest_sha256"],
              "run_bindings": run_bindings, "n_images": len(images), "images": images, "selected_images": selected,
              "missing_selected_images": [image for image in selected if image not in images], "cells": cells,
              **compose(cells, images, images == selected),
              "limits": {"composition_not_monolithic_native_certificate": True, "source_selected_engineering_pilot": True,
                         "physical_truth_verified": False, "full_55_image_endpoint": False, "human_work_advantage": False, "novel_algorithm": False}}
    args.output.mkdir()
    for name, case, proposal in packets:
        (args.output / (name + ".input.json")).write_bytes(contract.encoded(case))
        (args.output / (name + ".proof.json")).write_bytes(contract.encoded(proposal))
    (args.output / "result.json").write_bytes(canonical(result) + b"\n")
    return result


def self_test():
    audit = load_audit()
    refs = references({"0": [[2, 10], [4, 10], [4, 16], [2, 16]]}, "authored", audit)
    require(refs[0][1] == (10, 2, 16, 4), "row-column control")
    aa = [("a0", (Fraction(0), Fraction(0), Fraction(2), Fraction(2)), "0" * 64)]
    bb = [("b0", (Fraction(0), Fraction(0), Fraction(1), Fraction(2)), "1" * 64)]
    cell, case, proof = fixed_case("authored", "t0", aa, bb, [("r0", (Fraction(0), Fraction(0), Fraction(2), Fraction(2)))], "2" * 64)
    require(cell["tp_a"] == cell["tp_b"] == 1 and cell["delta"] == "0/1", "inclusive half IoU control")
    require(decision(Fraction(0), Fraction(0)) == "unresolved", "strict zero boundary")
    empty, _, _ = fixed_case("empty", "t0", [], [], [], "3" * 64)
    require(empty["delta"] == "0/1", "valid empty control")
    values = {"x": (4, -1, 4), "y": (-1, 4, 4)}
    rows = [{"tiff_path": image, "procedure": proc, "delta": ratio(Fraction(values[image][j]))} for image in values for j, proc in enumerate(PROCEDURES)]
    result = compose(rows, ["x", "y"], True)
    require(result["primary_status"] == "coupling_fragility" and result["imagewise"]["lower"] == "-1/1", "coupling control")
    require(compose(rows, ["x", "y"], False)["primary_status"] == "inconclusive_incomplete_selected_cohort", "partial cohort cannot establish primary endpoint")
    base = {"status": "complete", "image_id": "authored", "model": "faster", "image_shape_hw": [512, 512], "rescaled_shape_hw": [256, 256],
            "tile_count_expected": 1, "tile_count_completed": 1, "tiles": [{"ordinal": 0, "rescaled_row": 0, "rescaled_column": 0, "onnx_rows": 2, "below_storage_floor": 0}],
            "raw_onnx_rows": 2, "storage_predictions": [{"id": 0, "box_xyxy": [0, 0, 1, 1], "score": Decimal("0.5")}, {"id": 1, "box_xyxy": [0, 0, 2, 2], "score": Decimal("0.75")}],
            "analysis_predictions": [{"id": 1, "box_xyxy": [0, 0, 2, 2], "score": Decimal("0.75")}], "empty_analysis": False}
    require(len(predictions(base, "authored", "faster")) == 1, "strict score boundary control")
    mutations = []
    missing = copy.deepcopy(base); missing["tile_count_completed"] = 0; mutations.append(missing)
    shifted = copy.deepcopy(base); shifted["tiles"][0]["rescaled_column"] = 256; mutations.append(shifted)
    false_empty = copy.deepcopy(base); false_empty["analysis_predictions"] = []; false_empty["empty_analysis"] = True; mutations.append(false_empty)
    below = copy.deepcopy(base); below["storage_predictions"][0]["score"] = Decimal("0.049999999"); mutations.append(below)
    for mutation in mutations:
        try: predictions(mutation, "authored", "faster")
        except ValueError: pass
        else: raise AssertionError("prediction admission control accepted")
    with tempfile.TemporaryDirectory() as directory:
        destination = Path(directory) / "authored-run"; destination.mkdir()
        descriptors = []
        for model in MODELS:
            payload = copy.deepcopy(base); payload["model"] = model
            raw = json.dumps(payload, default=float, allow_nan=False).encode()
            filename = model + ".json"; (destination / filename).write_bytes(raw)
            descriptors.append({"image_id": "authored", "model": model, "file": filename, "sha256": sha(raw), "analysis_count": 1, "storage_count": 2})
        receipt = {"status": "complete", "manifest": {"protocol": {"sha256": PROTOCOL_SHA}, "images": [{"id": "authored"}]},
                   "config": {"storage_score_gte": 0.05, "analysis_score_gt": 0.5, "nms_iou": 0.5, "window_original": 1024, "downsample": 2, "overlap": 0.5,
                              "diameter_filter": None, "boundary_policy": "preserve_decoded_coordinates_and_report"},
                   "observations": descriptors, "runner_sha256": "0" * 64, "manifest_sha256": "1" * 64}
        result_path = destination / "result.json"; raw = canonical(receipt); result_path.write_bytes(raw)
        process_path = destination.with_suffix(".process.json")
        process_path.write_bytes(canonical({"status": "complete", "returncode": 0, "termination_reason": None}))
        admitted, images, _ = load_runs([(result_path, sha(raw))], ["authored"], audit)
        require(len(admitted) == 2 and images == ["authored"], "complete paired receipt control")
        process_path.write_bytes(canonical({"status": "failed", "returncode": 1, "termination_reason": None}))
        try: load_runs([(result_path, sha(raw))], ["authored"], audit)
        except ValueError: pass
        else: raise AssertionError("failed supervisor promoted to complete")
        process_path.write_bytes(canonical({"status": "complete", "returncode": 0, "termination_reason": None}))
        receipt["observations"].pop(); raw = canonical(receipt); result_path.write_bytes(raw)
        try: load_runs([(result_path, sha(raw))], ["authored"], audit)
        except ValueError: pass
        else: raise AssertionError("missing model promoted to empty")
    for broken in ([0, 0, 0, 1], [0, 0, True, 1], [0, 0, Decimal("NaN"), 1]):
        try: rectangle(broken)
        except ValueError: pass
        else: raise AssertionError("invalid geometry accepted")
    proof["result"]["bounds"]["upper"] = wire(1)
    try: checker.check(case, proof)
    except ValueError: pass
    else: raise AssertionError("forged native result accepted")
    try: fixed_case("too-many", "t0", [], [], [(str(i), (0, 0, 1, 1)) for i in range(129)], "0" * 64)
    except ValueError: pass
    else: raise AssertionError("native reference cap bypassed")
    return {"status": "passed", "scope": "authored_controls_only"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--annotations", type=Path)
    parser.add_argument("--sources", type=Path)
    parser.add_argument("--run", nargs=2, action="append", metavar=("RESULT_JSON", "SHA256"))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    try:
        if args.self_test:
            print(json.dumps(self_test(), sort_keys=True))
        else:
            require(args.annotations and args.sources and args.run and args.output, "all comparison paths required")
            result = run(args)
            print(json.dumps({"status": result["status"], "images": result["n_images"], "primary_status": result["primary_status"]}, sort_keys=True))
    except Exception as exc:
        print(json.dumps({"status": "invalid", "reason": str(exc) if isinstance(exc, ValueError) else type(exc).__name__}, sort_keys=True), file=sys.stderr)
        raise SystemExit(2)
