"""Strict source shape and byte bindings; no result arithmetic."""
from pathlib import Path
from fractions import Fraction
import hashlib
import json
import re

VERSION = "0.1.0"
SEED_KEYS = set("location vehicle_id frame_id global_time preceding lane_id".split())
TRACE_KEYS = set("location vehicle_id frame_id global_time local_y v_length lane_id preceding following space_headway v_class".split())

class Invalid(ValueError):
    pass

def require(ok, reason):
    if not ok:
        raise Invalid(reason)

def digest(data):
    return hashlib.sha256(data).hexdigest()

def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()

def load(path, ceiling=2_000_000):
    path = Path(path)
    require(path.stat().st_size <= ceiling, "file_size")
    def unique(pairs):
        out = {}
        for key, value in pairs:
            require(key not in out, "duplicate_json_key")
            out[key] = value
        return out
    def bad(value):
        raise Invalid("nonfinite_json")
    try:
        return json.loads(path.read_bytes(), object_pairs_hook=unique, parse_constant=bad)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise Invalid("json_syntax") from exc

def integer(value, positive=False):
    require(type(value) is str and re.fullmatch(r"0|[1-9][0-9]{0,15}", value) is not None, "integer")
    n = int(value)
    require(not positive or n > 0, "positive_integer")
    return n

def number(value):
    require(type(value) is str and len(value) <= 40 and re.fullmatch(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?", value) is not None, "decimal_string")
    n = Fraction(value)
    require(abs(n) <= 10**15 and n.denominator <= 10**12, "number_size")
    return n

def validate(seeds, rows):
    require(type(seeds) is list and len(seeds) == 200, "seed_population")
    require(type(rows) is list and 0 < len(rows) < 5001, "trace_population_or_cap")
    for records, expected in ((seeds, SEED_KEYS), (rows, TRACE_KEYS)):
        for row in records:
            require(type(row) is dict and set(row) == expected, "source_fields")
            require(row["location"] == "us-101", "source_location")
            for key in expected - {"location", "local_y", "v_length", "space_headway"}:
                integer(row[key], key in {"vehicle_id", "frame_id", "global_time"})
            if expected == TRACE_KEYS:
                for key in ("local_y", "v_length", "space_headway"):
                    number(row[key])
                require(number(row["v_length"]) > 0, "nonpositive_length")
    require(all(integer(s["preceding"]) > 0 for s in seeds), "seed_lead")
    require(seeds == sorted(seeds, key=lambda r: (integer(r["global_time"]), integer(r["vehicle_id"]), integer(r["frame_id"]))), "seed_order")
    return seeds, rows

def frozen_sources(directory, expected_freeze):
    packet = Path(__file__).resolve().parent
    freeze_path = packet / "freeze.json"
    require(digest(freeze_path.read_bytes()) == expected_freeze, "freeze_binding")
    freeze = load(freeze_path)
    require(freeze["document_id"] == "reiyah.public-motion.freeze" and freeze["version"] == VERSION, "freeze_version")
    for item in freeze["implementation"]:
        path = packet / item["path"]
        require(path.parent == packet and path.is_file(), "implementation_path")
        data = path.read_bytes()
        require(len(data) == item["bytes"] and digest(data) == item["sha256"], "implementation_binding")
    directory = Path(directory).resolve()
    for item in freeze["evidence"]:
        require(item["path"] in ("ngsim-metadata.json", "us101-metadata.pdf", "catalog.html"), "evidence_path")
        path = directory / item["path"]
        require(path.resolve().parent == directory, "evidence_escape")
        data = path.read_bytes()
        require(len(data) == item["bytes"] and digest(data) == item["sha256"], "evidence_binding")
    inputs = {}
    for item in freeze["sources"]:
        require(item["path"] in ("seeds.json", "traces.json"), "source_path")
        path = directory / item["path"]
        require(path.resolve().parent == directory, "source_escape")
        data = path.read_bytes()
        require(len(data) == item["bytes"] and digest(data) == item["sha256"], "source_binding")
        inputs[item["path"]] = load(path)
    validate(inputs["seeds.json"], inputs["traces.json"])
    return inputs["seeds.json"], inputs["traces.json"], digest(freeze_path.read_bytes())

def write_new(path, value):
    with Path(path).open("x") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")
