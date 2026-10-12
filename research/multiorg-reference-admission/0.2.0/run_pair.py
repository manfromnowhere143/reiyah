#!/usr/bin/env python3
"""Private, independently authored finite MultiOrg ONNX feasibility runner.

Algorithm parameters were read from the pinned upstream source; this file does
not import or copy upstream code. It is not a reproduction of published scores.
No network requests, downloads, training, labels, or diameter filters.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import resource
import signal
import shutil
import subprocess
import sys
import time

import numpy as np

OWNER = Path(__file__).resolve().parents[1]
PROTOCOL_SHA256 = "d27a73f692ab15ec7402ff052c8a7aa0a0ef3539d89dda0ec1c38b8588ce6f08"
CONFIG = {"window_original": 1024, "downsample": 2, "overlap": 0.5,
          "nms_iou": 0.5, "storage_score_gte": 0.05,
          "analysis_score_gt": 0.5, "diameter_filter": None,
          "boundary_policy": "preserve_decoded_coordinates_and_report",
          "nms_tie_policy": "descending_float32_score_then_tile_row_order_and_output_row",
          "provider": "CPUExecutionProvider", "intra_threads": 2,
          "inter_threads": 1}
MODELS = {
    "faster": {"md5": "e5c2768b8d7d06811b4bb5bf06660663", "bytes": 165472306,
               "height": 800, "width": 1333,
               "mean": [123.675, 116.28, 103.53], "std": [58.395, 57.12, 57.375]},
    "yolo": {"md5": "1644a90c3c003cd754f6243feea6d1ae", "bytes": 246090044,
             "height": 416, "width": 416, "mean": [0, 0, 0], "std": [255, 255, 255]},
}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def load_json(path):
    def unique(pairs):
        out = {}
        for key, value in pairs:
            if key in out:
                raise ValueError("duplicate JSON property")
            out[key] = value
        return out
    return json.loads(path.read_text(), object_pairs_hook=unique,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))


def confined(path):
    p = Path(path).resolve(strict=True)
    if not p.is_file() or not p.is_relative_to(OWNER):
        raise ValueError("input outside private owner or not a regular file")
    return p


def checked_file(record, cap, *, expected_md5=None, expected_size=None):
    if set(record) != {"path", "sha256"}:
        raise ValueError("source record requires exactly path and sha256")
    if not isinstance(record["sha256"], str) or len(record["sha256"]) != 64:
        raise ValueError("invalid digest")
    p = confined(record["path"])
    if p.stat().st_size > cap:
        raise ValueError("source size cap")
    data = p.read_bytes()
    if hashlib.sha256(data).hexdigest() != record["sha256"]:
        raise ValueError("source hash mismatch")
    if expected_size is not None and len(data) != expected_size:
        raise ValueError("model size differs from pinned publication")
    if expected_md5 and hashlib.md5(data).hexdigest() != expected_md5:
        raise ValueError("model MD5 differs from pinned publication")
    return data


def validated_manifest(path):
    p = confined(path)
    if p.stat().st_size > 65536:
        raise ValueError("manifest size cap")
    m = load_json(p)
    if not isinstance(m, dict) or set(m) != {"protocol", "images", "models", "limits"}:
        raise ValueError("manifest schema")
    protocol_bytes = checked_file(m["protocol"], 1048576)
    if m["protocol"]["sha256"] != PROTOCOL_SHA256:
        raise ValueError("runner requires its frozen source-specific protocol")
    if not isinstance(m["images"], list) or not 1 <= len(m["images"]) <= 4:
        raise ValueError("need one to four frozen images")
    protocol = json.loads(protocol_bytes)
    ids, paths = set(), set()
    for row in m["images"]:
        if not isinstance(row, dict) or set(row) != {"id", "source"}:
            raise ValueError("image schema")
        ident = row["id"]
        if not isinstance(ident, str) or not ident or len(ident) > 200 or ident in ids:
            raise ValueError("duplicate or invalid image identity")
        if ident not in protocol["selected_images"]:
            raise ValueError("image is outside frozen four-image selection")
        source = row["source"]
        p = confined(source["path"])
        if p in paths:
            raise ValueError("duplicate image path")
        ids.add(ident); paths.add(p)
    if not isinstance(m["models"], dict) or set(m["models"]) != set(MODELS):
        raise ValueError("exact Faster/YOLO pair required")
    limits = m["limits"]
    allowed = {"wall_seconds": (30, 600), "memory_bytes": (1073741824, 6442450944),
               "max_tiles_per_image": (1, 512), "max_raw_boxes_per_image": (1, 200000)}
    if not isinstance(limits, dict) or set(limits) != set(allowed):
        raise ValueError("limits schema")
    for name, (low, high) in allowed.items():
        value = limits[name]
        if type(value) is not int or not low <= value <= high:
            raise ValueError("limit outside explicit supported bounds")
    return m


def tile_roster(height, width):
    """Full prepadding lattice; each tile has its stable encounter ordinal."""
    if type(height) is not int or type(width) is not int or min(height, width) <= 0:
        raise ValueError("bad lattice dimensions")
    step = 256  # (1024 / 2) * 0.5
    return [(r, c) for r in range(0, height, step) for c in range(0, width, step)]


def prepare_image(image):
    from skimage.transform import rescale
    gray = np.squeeze(image)
    if gray.ndim != 2 or not np.issubdtype(gray.dtype, np.number):
        raise ValueError("image is not a single numeric 2D grayscale plane")
    if gray.size > 80000000 or not np.isfinite(gray).all():
        raise ValueError("image pixel cap or nonfinite input")
    # Explicit parameters fix the defaults used by the documented skimage path.
    small = rescale(gray, 0.5, order=1, mode="reflect", preserve_range=True,
                    anti_aliasing=True, channel_axis=None)
    height, width = small.shape
    if not np.isfinite(small).all() or float(small.max()) <= float(small.min()):
        raise ValueError("constant or nonfinite rescaled image")
    target_h = (height // 256) * 256 + 512
    target_w = (width // 256) * 256 + 512
    padded = np.pad(small, ((0, target_h - height), (0, target_w - width)), mode="edge")
    lo, hi = padded.min(), padded.max()
    quantized = (255 * ((padded - lo) / (hi - lo))).astype(np.uint8)
    return quantized, (height, width), tuple(map(int, gray.shape))


def model_input(tile, model):
    import cv2
    spec = MODELS[model]
    if tile.shape != (512, 512) or tile.dtype != np.uint8:
        raise ValueError("incomplete tile or dtype")
    side = min(spec["height"], spec["width"])
    # Source path round-trips uint8 -> float32/255 -> uint8 before resize.
    roundtrip = ((tile.astype(np.float32) / np.float32(255)) * np.float32(255)).astype(np.uint8)
    expanded = cv2.resize(roundtrip, (side, side), interpolation=cv2.INTER_LINEAR)
    rgb = np.repeat(expanded[None, :, :], 3, axis=0)[None, :, :, :].astype(np.float32)
    means = np.asarray(spec["mean"], dtype=np.float32)[None, :, None, None]
    scales = np.asarray(spec["std"], dtype=np.float32)[None, :, None, None]
    return np.ascontiguousarray((rgb - means) / scales), side


def decode_output(outputs, row, column, resized_side):
    """Return original-image horizontal XYXY, preserving outside-image boxes."""
    if not isinstance(outputs, (tuple, list)) or len(outputs) != 2:
        raise ValueError("ONNX must return exactly dets and labels")
    dets, labels = [np.asarray(x) for x in outputs]
    if dets.ndim != 3 or dets.shape[0] != 1 or dets.shape[2] != 5:
        raise ValueError("unexpected detector output shape")
    if labels.shape != dets.shape[:2] or not np.issubdtype(labels.dtype, np.integer):
        raise ValueError("unexpected labels output shape or dtype")
    if not np.isfinite(dets).all() or (dets[..., 4] < 0).any() or (dets[..., 4] > 1).any():
        raise ValueError("invalid confidence or nonfinite output")
    # Pre-filter below storage floor: such rows cannot suppress a retained row.
    # Keep their count, including zero-score padded rows, in the trace.
    values = dets[0].astype(np.float32, copy=True)
    mask = values[:, 4] >= np.float32(CONFIG["storage_score_gte"])
    eligible = values[mask]
    cats = labels[0][mask]
    if (cats != 0).any():
        raise ValueError("unexpected foreground class for one-class detector")
    if len(eligible) and ((eligible[:, 2] <= eligible[:, 0]) | (eligible[:, 3] <= eligible[:, 1])).any():
        raise ValueError("degenerate retained detector box")
    factor = np.float32(512 / resized_side)
    box = eligible[:, :4] * factor
    box[:, [0, 2]] += np.float32(column)
    box[:, [1, 3]] += np.float32(row)
    box = np.floor(box / np.float32(0.5)).astype(np.float32)
    if len(box) and ((box[:, 2] <= box[:, 0]) | (box[:, 3] <= box[:, 1])).any():
        raise ValueError("floor produced degenerate retained box")
    return box, eligible[:, 4], {"onnx_rows": int(len(values)),
                                  "below_storage_floor": int((~mask).sum())}


def stable_nms(boxes, scores, threshold=0.5):
    """Float32 continuous-coordinate IoU; exact score ties keep first arrival."""
    b = np.asarray(boxes, dtype=np.float32).reshape(-1, 4)
    s = np.asarray(scores, dtype=np.float32).reshape(-1)
    if len(b) != len(s) or not np.isfinite(b).all() or not np.isfinite(s).all() or (np.abs(b) > 1e9).any():
        raise ValueError("invalid NMS arrays")
    area = (b[:, 2] - b[:, 0]) * (b[:, 3] - b[:, 1])
    if (area <= 0).any():
        raise ValueError("invalid NMS area")
    order = np.argsort(-s, kind="stable")
    kept = []
    while order.size:
        idx = int(order[0]); kept.append(idx)
        remaining = order[1:]
        low = np.maximum(b[idx, :2], b[remaining, :2])
        high = np.minimum(b[idx, 2:], b[remaining, 2:])
        sides = np.maximum(high - low, np.float32(0))
        intersection = sides[:, 0] * sides[:, 1]
        union = area[idx] + area[remaining] - intersection
        iou = intersection / union
        order = remaining[iou <= np.float32(threshold)]
    return np.asarray(kept, dtype=np.int64)


def outside_count(boxes, shape):
    h, w = shape
    b = np.asarray(boxes).reshape(-1, 4)
    return int(((b[:, 0] < 0) | (b[:, 1] < 0) | (b[:, 2] > w) | (b[:, 3] > h)).sum())


def environment():
    names = ["numpy", "onnxruntime", "scikit-image", "opencv-python-headless", "tifffile"]
    versions = {}
    for name in names:
        try: versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError: versions[name] = None
    dependencies = {x.metadata["Name"]: x.version for x in importlib.metadata.distributions()}
    return {"python": sys.version, "executable": sys.executable,
            "platform": platform.platform(), "packages": versions, "all_distributions": dict(sorted(dependencies.items()))}


def execute(manifest_path, destination):
    import cv2
    import onnxruntime as ort
    import tifffile
    m = validated_manifest(manifest_path)
    manifest_sha256 = hashlib.sha256(Path(manifest_path).read_bytes()).hexdigest()
    runner_sha256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    started = time.monotonic(); deadline = started + m["limits"]["wall_seconds"]
    cv2.setNumThreads(1)
    destination = Path(destination)
    if destination.exists() or not destination.parent.resolve().is_relative_to(OWNER):
        raise ValueError("output must be new and private")
    destination.mkdir()
    cpu_limit = m["limits"]["wall_seconds"] * CONFIG["intra_threads"]
    resource.setrlimit(resource.RLIMIT_CPU, (cpu_limit, cpu_limit + 2))
    resource.setrlimit(resource.RLIMIT_FSIZE, (64 * 1024 * 1024, 64 * 1024 * 1024))
    observations = []
    for model in ("faster", "yolo"):
        spec = MODELS[model]
        raw = checked_file(m["models"][model], 300000000,
                           expected_md5=spec["md5"], expected_size=spec["bytes"])
        options = ort.SessionOptions()
        options.intra_op_num_threads = CONFIG["intra_threads"]
        options.inter_op_num_threads = CONFIG["inter_threads"]
        options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
        # Bytes instead of a file path denies an implicit external-data base directory.
        session = ort.InferenceSession(raw, sess_options=options, providers=["CPUExecutionProvider"])
        del raw
        if session.get_providers() != ["CPUExecutionProvider"] or len(session.get_inputs()) != 1 or len(session.get_outputs()) != 2:
            raise ValueError("unexpected provider or ONNX IO contract")
        inp = session.get_inputs()[0]
        if inp.type != "tensor(float)" or len(inp.shape) != 4:
            raise ValueError("unexpected ONNX input dtype/rank")
        for image in m["images"]:
            if time.monotonic() >= deadline: raise TimeoutError("worker wall budget")
            begin = time.monotonic(); cpu = time.process_time()
            contents = checked_file(image["source"], 100000000)
            import io
            with tifffile.TiffFile(io.BytesIO(contents)) as tf:
                series = tf.series[0]
                if len(tf.series) != 1 or math.prod(series.shape) > 80000000:
                    raise ValueError("unsupported TIFF series or decompressed size cap")
                data = series.asarray()
            del contents
            pixels, resized_shape, shape = prepare_image(data)
            del data
            roster = tile_roster(*map(int, resized_shape))
            if len(roster) > m["limits"]["max_tiles_per_image"]:
                raise ValueError("tile work cap; no partial-image inference")
            all_boxes, all_scores, trace = [], [], []
            seen = 0
            for ordinal, (row, column) in enumerate(roster):
                if time.monotonic() >= deadline: raise TimeoutError("worker wall budget")
                tensor, side = model_input(pixels[row:row + 512, column:column + 512], model)
                for expected, actual in zip(inp.shape, tensor.shape):
                    if type(expected) is int and expected != actual:
                        raise ValueError("graph input shape incompatible with current preprocessing")
                out = session.run(None, {inp.name: tensor})
                box, score, counts = decode_output(out, row, column, side)
                seen += counts["onnx_rows"]
                if seen > m["limits"]["max_raw_boxes_per_image"]:
                    raise ValueError("raw box work cap; no partial-image result")
                all_boxes.append(box); all_scores.append(score)
                trace.append({"ordinal": ordinal, "rescaled_row": row, "rescaled_column": column, **counts})
            boxes = np.concatenate(all_boxes, axis=0)
            scores = np.concatenate(all_scores, axis=0)
            keep = stable_nms(boxes, scores, CONFIG["nms_iou"])
            boxes, scores = boxes[keep], scores[keep]
            rows = [{"id": int(k), "box_xyxy": list(map(int, b)), "score": float(s)}
                    for k, b, s in zip(keep, boxes, scores)]
            analysis = [r for r in rows if r["score"] > CONFIG["analysis_score_gt"]]
            result = {"image_id": image["id"], "model": model, "status": "complete",
                      "image_shape_hw": shape, "rescaled_shape_hw": resized_shape,
                      "tile_count_expected": len(roster), "tile_count_completed": len(trace),
                      "tiles": trace, "raw_onnx_rows": seen,
                      "storage_predictions": rows, "analysis_predictions": analysis,
                      "storage_outside_image": outside_count(boxes, shape),
                      "analysis_outside_image": outside_count([r["box_xyxy"] for r in analysis], shape),
                      "empty_analysis": not bool(analysis), "wall_seconds": time.monotonic() - begin,
                      "cpu_seconds": time.process_time() - cpu,
                      "onnx_input": {"name": inp.name, "shape": inp.shape, "type": inp.type},
                      "onnx_outputs": [{"name": x.name, "shape": x.shape, "type": x.type} for x in session.get_outputs()]}
            # Recheck custody after execution before declaring complete.
            checked_file(image["source"], 100000000)
            filename = hashlib.sha256(canonical([image["id"], model])).hexdigest() + ".json"
            (destination / filename).write_bytes(canonical(result) + b"\n")
            observations.append({"image_id": image["id"], "model": model, "file": filename,
                                 "sha256": hashlib.sha256((destination / filename).read_bytes()).hexdigest(),
                                 "analysis_count": len(analysis), "storage_count": len(rows)})
        checked_file(m["models"][model], 300000000,
                     expected_md5=spec["md5"], expected_size=spec["bytes"])
        del session
    checked_file(m["protocol"], 1048576)
    if hashlib.sha256(Path(manifest_path).read_bytes()).hexdigest() != manifest_sha256:
        raise ValueError("manifest changed during execution")
    if hashlib.sha256(Path(__file__).read_bytes()).hexdigest() != runner_sha256:
        raise ValueError("runner changed during execution")
    result = {"status": "complete", "config": CONFIG, "manifest": m,
              "manifest_sha256": manifest_sha256, "runner_sha256": runner_sha256,
              "environment": environment(), "wall_seconds": time.monotonic() - started,
              "maxrss_native": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
              "maxrss_unit": "bytes" if sys.platform == "darwin" else "KiB",
              "observations": observations}
    (destination / "result.json").write_bytes(canonical(result) + b"\n")


def launch(manifest_path, output):
    m = validated_manifest(manifest_path)
    out = Path(output).resolve()
    if out.exists() or not out.parent.is_dir() or not out.parent.is_relative_to(OWNER):
        raise ValueError("output path must be new under owner")
    if shutil.disk_usage(OWNER).free < 4294967296:
        raise ValueError("free disk floor4GiB")
    log = out.with_suffix(".log")
    status_path = out.with_suffix(".process.json")
    if log.exists() or status_path.exists(): raise ValueError("process receipts already exist")
    env = os.environ.copy()
    env.update({"PYTHONDONTWRITEBYTECODE": "1", "OMP_NUM_THREADS": "2", "OPENBLAS_NUM_THREADS": "1",
                "VECLIB_MAXIMUM_THREADS": "2", "MKL_NUM_THREADS": "2", "CUDA_VISIBLE_DEVICES": ""})
    start = time.monotonic(); maximum_rss = 0; reason = None
    with log.open("xb") as stream:
        process = subprocess.Popen([sys.executable, "-B", str(Path(__file__).resolve()), "--worker",
                                    "--manifest", str(Path(manifest_path).resolve()), "--output", str(out)],
                                   cwd=OWNER, env=env, stdout=stream, stderr=stream, start_new_session=True)
        try:
            while process.poll() is None:
                elapsed = time.monotonic() - start
                sample = subprocess.run(["/bin/ps", "-o", "rss=", "-p", str(process.pid)],
                                        capture_output=True, text=True, timeout=2)
                if sample.returncode == 0 and sample.stdout.strip():
                    maximum_rss = max(maximum_rss, int(sample.stdout.strip()) * 1024)
                disk_low = shutil.disk_usage(OWNER).free < 4294967296
                if elapsed > m["limits"]["wall_seconds"] or maximum_rss > m["limits"]["memory_bytes"] or disk_low:
                    reason = "disk_floor" if disk_low else ("wall_limit" if elapsed > m["limits"]["wall_seconds"] else "memory_limit")
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait(timeout=10)
                    break
                time.sleep(0.2)
        finally:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=10)

    receipt = {"status": "complete" if process.returncode == 0 and (out / "result.json").exists() else "failed",
               "returncode": process.returncode, "termination_reason": reason,
               "wall_seconds": time.monotonic() - start, "peak_sampled_rss_bytes": maximum_rss,
               "sampling_period_seconds": 0.2, "memory_boundary": "sampled_RSS_not_hard_address_space_limit",
               "log": log.name}
    status_path.write_bytes(canonical(receipt) + b"\n")
    print(json.dumps(receipt))
    return 0 if receipt["status"] == "complete" else 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest")
    parser.add_argument("--output")
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--probe", action="store_true")
    args = parser.parse_args()
    if args.probe:
        print(json.dumps(environment(), indent=2)); return 0
    if not args.manifest or not args.output:
        parser.error("--manifest and --output required")
    if args.worker:
        execute(args.manifest, args.output); return 0
    return launch(args.manifest, args.output)


if __name__ == "__main__":
    raise SystemExit(main())
