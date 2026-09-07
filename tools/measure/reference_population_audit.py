#!/usr/bin/env python3
"""Offline reference-population audit over explicitly supplied, aligned tables.

Exact arithmetic on recorded decimal coordinates does not establish physical
accuracy. This tool checks membership and proximity, never object existence,
annotation completeness, calibration, detector correctness, or safety.
"""
from __future__ import annotations

import argparse
from collections import Counter
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re
import sys

VERSION = "reiyah.reference-population-audit.v1"
INPUT_VERSION = "reiyah.reference-population-input.v1"
DECIMAL = re.compile(r"-?(?:0|[1-9][0-9]{0,11})(?:\.[0-9]{1,32})?\Z")
IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:/-]{0,159}\Z")
MAX_BYTES = 8 * 1024 * 1024
MAX_DISTANCE_PAIRS = 1_000_000


class AuditInputError(ValueError):
    """Invalid or unsupported evidence input; no scientific output is produced."""


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def exact_keys(value: object, names: tuple[str, ...], where: str) -> dict:
    if not isinstance(value, dict) or set(value) != set(names):
        raise AuditInputError(where + ": missing or unknown property")
    return value


def identifier(value: object, where: str) -> str:
    if not isinstance(value, str) or not IDENTIFIER.fullmatch(value):
        raise AuditInputError(where + ": invalid identifier")
    return value


def decimal(value: object, where: str) -> Fraction:
    if not isinstance(value, str) or not DECIMAL.fullmatch(value):
        raise AuditInputError(where + ": expected bounded decimal string")
    return Fraction(value)


def unique(values: list, where: str) -> None:
    if len(values) != len(set(values)):
        raise AuditInputError(where + ": duplicate identifier")


def objects(rows: object, where: str) -> dict:
    if not isinstance(rows, list):
        raise AuditInputError(where + ": expected array")
    parsed = {}
    for row in rows:
        exact_keys(row, ("id", "xy_m"), where)
        rid = identifier(row["id"], where)
        xy = row["xy_m"]
        if not isinstance(xy, list) or len(xy) != 2:
            raise AuditInputError(where + ": expected two coordinates")
        if rid in parsed:
            raise AuditInputError(where + ": duplicate identifier")
        parsed[rid] = tuple(decimal(v, where) for v in xy)
    return parsed


def parse(raw: bytes) -> dict:
    if len(raw) > MAX_BYTES:
        raise AuditInputError("input exceeds bounded demonstration size")

    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise AuditInputError("duplicate JSON property")
            result[key] = value
        return result

    def nonfinite(_):
        raise AuditInputError("nonfinite JSON number")

    try:
        doc = json.loads(raw.decode("utf-8"), object_pairs_hook=pairs, parse_constant=nonfinite)
    except AuditInputError:
        raise
    except (UnicodeError, ValueError, RecursionError) as exc:
        raise AuditInputError("invalid UTF-8 JSON") from exc
    exact_keys(doc, ("schema_version", "artifact_id", "upstream_selection_id", "evaluation_scope_id",
                     "wider_reference_scope_id", "radius_m", "frames"), "input")
    if doc["schema_version"] != INPUT_VERSION:
        raise AuditInputError("unsupported input version")
    for key in ("artifact_id", "upstream_selection_id", "evaluation_scope_id", "wider_reference_scope_id"):
        identifier(doc[key], key)
    if doc["evaluation_scope_id"] == doc["wider_reference_scope_id"]:
        raise AuditInputError("reference scopes must have distinct identities")
    radius = decimal(doc["radius_m"], "radius_m")
    if radius <= 0:
        raise AuditInputError("radius must be positive")
    if not isinstance(doc["frames"], list) or not doc["frames"]:
        raise AuditInputError("nonempty frame array required")
    frame_ids = []
    cost = 0
    parsed_frames = []
    for frame in doc["frames"]:
        exact_keys(frame, ("id", "timestamp_us", "coordinate_frame_id", "reference_state",
                           "annotations", "evaluation_annotation_ids", "predictions"), "frame")
        fid = identifier(frame["id"], "frame.id")
        frame_ids.append(fid)
        identifier(frame["coordinate_frame_id"], "coordinate_frame_id")
        if type(frame["timestamp_us"]) is not int or not 0 <= frame["timestamp_us"] <= 9007199254740991:
            raise AuditInputError("timestamp_us must be an exact nonnegative JSON-safe integer")
        predictions = objects(frame["predictions"], "predictions")
        state = frame["reference_state"]
        if state not in ("available", "unavailable", "withheld", "invalid"):
            raise AuditInputError("unsupported reference state")
        if state == "available":
            annotations = objects(frame["annotations"], "annotations")
            ids = frame["evaluation_annotation_ids"]
            if not isinstance(ids, list):
                raise AuditInputError("evaluation ids must be an array")
            for aid in ids:
                identifier(aid, "evaluation_annotation_ids")
            unique(ids, "evaluation_annotation_ids")
            if not set(ids) <= set(annotations):
                raise AuditInputError("evaluation reference is not a subset of supplied wider reference")
            cost += len(predictions) * (len(annotations) + len(ids))
        else:
            if frame["annotations"] is not None or frame["evaluation_annotation_ids"] is not None:
                raise AuditInputError("unavailable reference must remain null, not empty")
            annotations, ids = {}, []
        parsed_frames.append((frame, predictions, annotations, set(ids)))
    unique(frame_ids, "frames")
    if cost > MAX_DISTANCE_PAIRS:
        raise AuditInputError("distance-pair budget exceeded; split input into explicit batches")
    return {"input": doc, "radius": radius, "frames": parsed_frames}


def nearest(prediction: tuple, annotations: dict, ids: set) -> dict | None:
    if not ids:
        return None
    distance, aid = min((sum((a - b) ** 2 for a, b in zip(prediction, annotations[aid])), aid)
                        for aid in ids)
    return {"annotation_id": aid, "distance_squared_m2": {
        "numerator": str(distance.numerator), "denominator": str(distance.denominator)}}


def inside(witness: dict | None, radius: Fraction) -> bool:
    if witness is None:
        return False
    value = witness["distance_squared_m2"]
    return Fraction(int(value["numerator"]), int(value["denominator"])) <= radius ** 2


def audit(raw: bytes) -> dict:
    data = parse(raw)
    rows = []
    for frame, predictions, annotations, selected in sorted(data["frames"], key=lambda v: v[0]["id"]):
        for pid, xy in sorted(predictions.items()):
            row = {"frame_id": frame["id"], "prediction_id": pid,
                   "reference_state": frame["reference_state"], "physical_object_presence": "unknown",
                   "nearest_evaluation_reference": None, "nearest_wider_reference": None}
            if frame["reference_state"] != "available":
                row["status"] = "reference_unknown"
            else:
                evaluation = nearest(xy, annotations, selected)
                wider = nearest(xy, annotations, set(annotations))
                row.update(nearest_evaluation_reference=evaluation, nearest_wider_reference=wider)
                if inside(evaluation, data["radius"]):
                    row["status"] = "evaluation_reference_near"
                elif inside(wider, data["radius"]):
                    row["status"] = "excluded_reference_near"
                else:
                    row["status"] = "unmatched_in_supplied_wider_reference"
            rows.append(row)
    counts = Counter(r["status"] for r in rows)
    known_unmatched = counts["excluded_reference_near"] + counts["unmatched_in_supplied_wider_reference"]
    return {
        "schema_version": VERSION, "lifecycle_status": "exploratory",
        "input_artifact_id": data["input"]["artifact_id"],
        "input_sha256": hashlib.sha256(raw).hexdigest(),
        "analyzer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "upstream_selection_id": data["input"]["upstream_selection_id"],
        "evaluation_scope_id": data["input"]["evaluation_scope_id"],
        "wider_reference_scope_id": data["input"]["wider_reference_scope_id"],
        "metric": "squared Euclidean distance in the supplied aligned XY plane",
        "radius_m": data["input"]["radius_m"], "boundary": "inclusive",
        "counts": {s: counts[s] for s in ("evaluation_reference_near", "excluded_reference_near",
                    "unmatched_in_supplied_wider_reference", "reference_unknown")},
        "exclusion_fraction_among_observed_evaluation_unmatched": {
            "numerator": counts["excluded_reference_near"], "denominator": known_unmatched,
            "identified": known_unmatched > 0},
        "unknown_reference_prediction_count": counts["reference_unknown"],
        "physical_false_positive_rate": None,
        "limits": ["Membership is supplied, not independently reconstructed from an upstream evaluator",
                   "Caller supplies alignment and timestamps; no calibration or motion validation",
                   "A supplied wider table is not certified exhaustive of the physical world",
                   "Exact arithmetic concerns the input decimals, not sensor accuracy",
                   "Rows are proximity witnesses, not one-to-one detection matches"],
        "rows": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    args = parser.parse_args()
    try:
        with args.input.open("rb") as handle:
            raw = handle.read(MAX_BYTES + 1)
        result = audit(raw)
    except (OSError, AuditInputError) as exc:
        print(json.dumps({"schema_version": VERSION, "status": "invalid", "diagnostic": str(exc)}), file=sys.stderr)
        return 2
    sys.stdout.buffer.write(canonical(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
