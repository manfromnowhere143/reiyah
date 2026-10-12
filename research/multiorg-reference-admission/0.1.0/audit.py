#!/usr/bin/env python3
"""Offline MultiOrg annotation admission; no image/model inference or repair."""
import argparse
from decimal import Decimal
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys

PROCEDURES = ("t0", "t1_A", "t1_B")
SELECTION_PREFIX = "reiyah.multiorg.pilot.v1\n"
MAX_MANIFEST = 4 << 20
MAX_FILE = 1 << 20
MAX_TOTAL = 16 << 20
PROTOCOL_SHA = "c62b333937f168ec0a7ff4915c8eaf2f0cd49fa7ac88e11f78f39a371c49a670"


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def closed(value, keys, reason):
    require(type(value) is dict and set(value) == set(keys), reason)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def strict_json(data):
    def pairs(items):
        out = {}
        for key, value in items:
            require(key not in out, "duplicate JSON key")
            out[key] = value
        return out
    def constant(_):
        raise ValueError("nonfinite JSON constant")
    return json.loads(data.decode("utf-8", errors="strict"), object_pairs_hook=pairs,
                      parse_float=Decimal, parse_constant=constant)


def relative(value):
    require(type(value) is str and 0 < len(value) <= 1024 and "\\" not in value, "invalid relative path")
    path = PurePosixPath(value)
    require(not path.is_absolute() and path.as_posix() == value and all(part not in ("", ".", "..") for part in path.parts), "noncanonical or traversing path")
    return path


def source_path(root, relative_path):
    path = root
    require(not root.is_symlink() and root.is_dir(), "source root unavailable or symlinked")
    for part in relative(relative_path).parts:
        path = path / part
        require(not path.is_symlink(), "source symlink refused")
    require(path.is_file(), "source file unavailable")
    require(path.resolve().is_relative_to(root.resolve()), "source escaped root")
    return path


def bound_bytes(path, length, digest, limit):
    require(type(length) is int and 0 <= length <= limit, "source length outside bound")
    require(type(digest) is str and re.fullmatch(r"[0-9a-f]{64}", digest) is not None, "invalid source digest")
    with path.open("rb") as stream:
        data = stream.read(length + 1)
    require(len(data) == length and sha(data) == digest, "source length or digest differs")
    return data


def validate_manifest(value, expected_images=55, allow_incomplete=False):
    closed(value, ("artifact_id", "version", "images"), "manifest properties")
    require(value["artifact_id"] == "reiyah.multiorg.annotation-manifest" and value["version"] == "0.1.0", "manifest identity")
    require(type(value["images"]) is list and len(value["images"]) == expected_images, "image roster length")
    images, publics, locals_ = set(), set(), set()
    total = 0
    for image in value["images"]:
        closed(image, ("tiff_path", "annotations"), "image properties")
        tiff = relative(image["tiff_path"])
        require(tiff.as_posix().startswith("MultiOrg_v2/test/") and tiff.suffix == ".tiff", "wrong source population")
        require(tiff.as_posix() not in images, "duplicate image")
        images.add(tiff.as_posix())
        annotations = image["annotations"]
        require(type(annotations) is list and len(annotations) == 3, "annotation roster length")
        procedures = set()
        for source in annotations:
            closed(source, ("procedure", "source_path", "local_path", "byte_size", "sha256", "transport_valid"), "annotation descriptor properties")
            require(type(source["transport_valid"]) is bool, "transport state must be boolean")
            require(allow_incomplete or source["transport_valid"] is True, "source transport incomplete")
            procedure = source["procedure"]
            require(type(procedure) is str and procedure in PROCEDURES and procedure not in procedures, "annotation procedure roster")
            procedures.add(procedure)
            public = relative(source["source_path"])
            allowed = {tiff.stem + "_t0_A.json", tiff.stem + "_t0_B.json"} if procedure == "t0" else {tiff.stem + "_" + procedure + ".json"}
            require(public.parent == tiff.parent and public.name in allowed, "annotation image/procedure identity")
            local = relative(source["local_path"]).as_posix()
            require(public.as_posix() not in publics and local not in locals_, "repeated source path")
            publics.add(public.as_posix()); locals_.add(local)
            require(type(source["byte_size"]) is int and 0 <= source["byte_size"] <= MAX_FILE, "annotation byte bound")
            require(type(source["sha256"]) is str and re.fullmatch(r"[0-9a-f]{64}", source["sha256"]) is not None, "annotation digest format")
            total += source["byte_size"]
    require(total <= MAX_TOTAL, "annotation total byte bound")
    return total


def selection_hash(tiff_path):
    return sha((SELECTION_PREFIX + tiff_path).encode("utf-8"))


def select(images):
    eligible = [row for row in images if row["native_object_cap_eligible"]]
    ordered = sorted(eligible, key=lambda row: (row["selection_sha256"], row["tiff_path"]))
    return [row["tiff_path"] for row in ordered[:4]]


def annotation_geometry(value, public_path):
    """Four row/column corners per source box, with no coordinate repair."""
    require(type(value) is dict, "annotation root must be a box-ID dictionary")
    require(len(value) <= 100000, "annotation object bound")
    identities = []
    negative = 0
    for box_id, corners in value.items():
        require(type(box_id) is str and 0 < len(box_id) <= 256, "invalid box identity")
        require(type(corners) is list and len(corners) == 4, "rectangle must have four corners")
        points = []
        for corner in corners:
            require(type(corner) is list and len(corner) == 2, "corner must contain row and column")
            require(all(type(c) is int or type(c) is Decimal and c.is_finite() for c in corner), "coordinate must be finite numeric, not boolean")
            points.append(tuple(corner))
        rows, columns = {point[0] for point in points}, {point[1] for point in points}
        require(len(rows) == len(columns) == 2 and len(set(points)) == 4, "degenerate or non-axis-aligned rectangle")
        require(set(points) == {(row, column) for row in rows for column in columns}, "rectangle corner product differs")
        negative += any(coordinate < 0 for point in points for coordinate in point)
        identities.append(sha(json.dumps([public_path, box_id], ensure_ascii=False, separators=(",", ":")).encode("utf-8")))
    identities.sort()
    return {"box_count": len(value), "negative_coordinate_boxes": negative,
            "source_qualified_ids_sha256": sha(("\n".join(identities) + ("\n" if identities else "")).encode("utf-8"))}


def audit_manifest(manifest, sources):
    total_bytes = validate_manifest(manifest, allow_incomplete=True)
    expected = {s["local_path"] for image in manifest["images"] for s in image["annotations"]}
    require(all(s["local_path"] == "raw/" + s["source_path"] for image in manifest["images"] for s in image["annotations"]), "local source layout differs")
    raw_root = sources / "raw" / "MultiOrg_v2" / "test"
    require(raw_root.is_dir(), "annotation census directory unavailable")
    actual = set()
    for path in raw_root.rglob("*"):
        require(not path.is_symlink(), "source-tree symlink refused")
        if path.is_file():
            actual.add(path.relative_to(sources).as_posix())
    require(actual == expected, "missing or extra source files")
    images = []
    failures = []
    valid_files = valid_bytes = 0
    totals = {procedure: 0 for procedure in PROCEDURES}
    negative_totals = {procedure: 0 for procedure in PROCEDURES}
    for entry in sorted(manifest["images"], key=lambda image: image["tiff_path"]):
        counts, negative, ids, states = {}, {}, {}, {}
        for source in sorted(entry["annotations"], key=lambda item: item["procedure"]):
            path = source_path(sources, source["local_path"])
            raw = bound_bytes(path, source["byte_size"], source["sha256"], MAX_FILE)
            procedure = source["procedure"]
            if not source["transport_valid"]:
                counts[procedure] = negative[procedure] = ids[procedure] = None
                states[procedure] = "transport_unavailable"
                failures.append({"source_path": source["source_path"], "procedure": procedure, "state": "transport_unavailable"})
                continue
            result = annotation_geometry(strict_json(raw), source["source_path"])
            valid_files += 1
            valid_bytes += len(raw)
            states[procedure] = "validated_annotation"
            counts[procedure] = result["box_count"]
            negative[procedure] = result["negative_coordinate_boxes"]
            ids[procedure] = result["source_qualified_ids_sha256"]
            totals[procedure] += result["box_count"]
            negative_totals[procedure] += result["negative_coordinate_boxes"]
        complete = all(value is not None for value in counts.values())
        count = sum(counts.values()) if complete else None
        images.append({"tiff_path": entry["tiff_path"], "selection_sha256": selection_hash(entry["tiff_path"]),
                       "annotation_counts": counts, "sum_reference_objects": count, "native_object_cap_eligible": count <= 128 if complete else None,
                       "annotation_states": states, "annotation_set_complete": complete,
                       "negative_coordinate_box_counts": negative, "source_qualified_ids_sha256": ids})
    census_complete = not failures
    selected = select(images) if census_complete else []
    return {"artifact_id": "reiyah.multiorg.annotation-admission.result", "version": "0.1.0",
            "status": "incomplete_census" if not census_complete else "eligible_subset" if selected else "no_eligible_images",
            "annotation_census": "complete" if census_complete else "incomplete",
            "image_count": len(images), "annotation_file_count": 3 * len(images), "total_annotation_bytes": total_bytes,
            "valid_annotation_file_count": valid_files, "valid_annotation_bytes": valid_bytes, "failed_annotation_file_count": len(failures),
            "source_failures": failures, "counts_scope": "complete_census" if census_complete else "validated_available_sources_only",
            "annotation_counts_by_procedure": totals, "negative_coordinate_boxes_by_procedure": negative_totals,
            "native_reference_object_cap": 128, "eligible_images": sum(row["native_object_cap_eligible"] for row in images) if census_complete else None,
            "images": images, "selected_images": selected, "feasibility_pilot": selected[0] if selected else None,
            "selection_state": "evaluated_complete_census" if census_complete else "blocked_incomplete_census",
            "coordinate_check": "all_finite_nondegenerate_axis_aligned_rectangles" if census_complete else "validated_available_sources_only",
            "limits": {"physical_truth_verified": False, "reviewer_independence_verified": False,
                       "image_coordinate_bounds_checked": False, "negative_coordinates_repaired": False,
                       "objects_merged_across_sources": False, "native_edge_work_byte_caps_checked": False,
                       "native_coordinate_magnitude_cap_checked": False, "inference_performed": False,
                       "human_work_measured": False, "pilot_population_representative": False}}


def run(manifest_path, manifest_sha256, sources, output):
    require(not output.exists(), "output already exists")
    protocol_bytes = Path(__file__).with_name("protocol.json").read_bytes()
    require(sha(protocol_bytes) == PROTOCOL_SHA, "frozen protocol changed")
    require(type(manifest_sha256) is str and re.fullmatch(r"[0-9a-f]{64}", manifest_sha256) is not None, "manifest digest format")
    with manifest_path.open("rb") as stream:
        raw = stream.read(MAX_MANIFEST + 1)
    require(len(raw) <= MAX_MANIFEST and sha(raw) == manifest_sha256, "manifest size or digest differs")
    result = audit_manifest(strict_json(raw), sources)
    result.update(protocol_sha256=PROTOCOL_SHA, source_manifest_sha256=manifest_sha256,
                  producer_sha256=sha(Path(__file__).read_bytes()))
    with output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--sources", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = run(args.manifest, args.manifest_sha256, args.sources, args.output)
        print(json.dumps({"status": result["status"], "images": result["image_count"], "eligible_images": result["eligible_images"], "selected_images": len(result["selected_images"])}, sort_keys=True))
        if result["status"] == "incomplete_census":
            raise SystemExit(3)
    except Exception as exc:
        reason = str(exc) if type(exc) is ValueError else type(exc).__name__
        print(json.dumps({"status": "invalid", "reason": reason}, sort_keys=True), file=sys.stderr)
        raise SystemExit(2)
