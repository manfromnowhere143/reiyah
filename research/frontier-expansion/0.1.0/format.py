"""Exact authored relational contracts. Offline research, no driving control."""
from fractions import Fraction as Q
import hashlib, json, re

VERSION = "0.1.0"
LIMIT_WORLDS, LIMIT_SAMPLES = 128, 256

class Invalid(ValueError):
    pass

def require(ok, code):
    if not ok:
        raise Invalid(code)

def keys(value, expected, where):
    require(type(value) is dict and set(value) == set(expected.split()), where + ":keys")

def rational(value):
    require(type(value) is str and len(value) <= 64 and re.fullmatch(r"-?(0|[1-9][0-9]*)(/[1-9][0-9]*)?", value) is not None, "rational")
    q = Q(value)
    require(str(q) == value, "canonical_rational")
    require(abs(q.numerator) <= 10**18 and q.denominator <= 10**18, "rational_size")
    return q

def ident(value):
    require(type(value) is str and re.fullmatch(r"[A-Za-z0-9._-]{1,80}", value) is not None, "identifier")

def digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()

def load_json(path):
    def unique(pairs):
        out = {}
        for k, v in pairs:
            require(k not in out, "duplicate_json_key")
            out[k] = v
        return out
    with open(path) as stream:
        return json.load(stream, object_pairs_hook=unique, parse_constant=lambda _: (_ for _ in ()).throw(Invalid("nonfinite_json")))

def validate(case):
    keys(case, "schema_version case_id claim model worlds", "case")
    require(case["schema_version"] == VERSION, "version")
    ident(case["case_id"])
    claim = case["claim"]
    keys(claim, "id kind frame_id distance_unit time_unit window minimum_gap interpretation evidence_id", "claim")
    for field in ("id", "frame_id", "evidence_id"):
        ident(claim[field])
    require(claim["kind"] == "minimum_longitudinal_clearance", "claim_kind")
    require(claim["distance_unit"] == "m" and claim["time_unit"] == "s", "units")
    require(claim["interpretation"] == "authored_front_bumper_to_lead_rear", "interpretation")
    require(type(claim["window"]) is list and len(claim["window"]) == 2, "window")
    begin, end = map(rational, claim["window"])
    require(begin < end and rational(claim["minimum_gap"]) >= 0, "window_or_gap")
    keys(case["model"], "world_set interpolation", "model")
    require(case["model"]["world_set"] == "authored_finite_exhaustive", "world_set")
    require(case["model"]["interpolation"] in ("piecewise_linear", "unspecified"), "interpolation")
    require(type(case["worlds"]) is list and len(case["worlds"]) <= LIMIT_WORLDS, "world_limit")
    seen = set()
    for world in case["worlds"]:
        keys(world, "id actor_id ego lead", "world")
        ident(world["id"]); require(world["id"] not in seen, "duplicate_world"); seen.add(world["id"])
        if world["actor_id"] is not None:
            ident(world["actor_id"])
        require(world["actor_id"] is not None or world["lead"] is None, "unbound_actor")
        for role in ("ego", "lead"):
            trace = world[role]
            if trace is None:
                continue
            keys(trace, "frame_id point clock_shift samples evidence_id", "trace")
            require(trace["frame_id"] == claim["frame_id"], "frame_mismatch")
            require(trace["point"] == ("front_bumper" if role == "ego" else "rear_bumper"), "reference_point")
            ident(trace["evidence_id"])
            rational(trace["clock_shift"])
            samples = trace["samples"]
            require(type(samples) is list and 1 <= len(samples) <= LIMIT_SAMPLES, "sample_limit")
            times = []
            for pair in samples:
                require(type(pair) is list and len(pair) == 2, "sample")
                times.append(rational(pair[0])); rational(pair[1])
            require(all(a < b for a, b in zip(times, times[1:])), "sample_time_order")
    return case
