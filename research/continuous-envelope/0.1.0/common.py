"""Strict authored input and byte custody only; no clearance mathematics."""

from fractions import Fraction
from pathlib import Path
import hashlib
import json
import re


class Invalid(ValueError):
    pass


def require(ok, reason):
    if not ok:
        raise Invalid(reason)


def keys(value, expected):
    require(type(value) is dict and set(value) == set(expected), "properties")


def rational(value, *, operand=True):
    require(
        type(value) is str and len(value) <= (40 if operand else 256), "rational_type"
    )
    require(re.fullmatch(r"-?(0|[1-9][0-9]*)(/[1-9][0-9]*)?", value), "rational_syntax")
    result = Fraction(value)
    require(str(result) == value, "rational_canonical")
    if operand:
        require(abs(result) <= 10**9 and result.denominator <= 10**6, "rational_cap")
    return result


def identifier(value):
    require(
        type(value) is str and re.fullmatch(r"[a-z0-9][a-z0-9-]{0,79}", value),
        "identifier",
    )


def parse_case(case):
    keys(
        case,
        (
            "id",
            "horizon_s",
            "threshold_m",
            "quantity",
            "motion",
            "clock",
            "observations",
        ),
    )
    identifier(case["id"])
    horizon = case["horizon_s"]
    require(type(horizon) is list and len(horizon) == 2, "horizon_shape")
    a, b = map(rational, horizon)
    require(a <= b, "horizon_order")
    d = rational(case["threshold_m"])
    if case["quantity"] is not None:
        keys(case["quantity"], ("kind", "unit", "provenance"))
        require(
            case["quantity"]
            == {
                "kind": "road_projected_signed_clearance",
                "unit": "m",
                "provenance": "authored",
            },
            "quantity_scope",
        )
    k = tau = None
    if case["motion"] is not None:
        keys(case["motion"], ("kind", "rate_mps"))
        require(case["motion"]["kind"] == "global_lipschitz", "motion_kind")
        k = rational(case["motion"]["rate_mps"])
        require(k >= 0, "motion_negative")
    if case["clock"] is not None:
        keys(case["clock"], ("kind", "radius_s"))
        require(case["clock"]["kind"] == "common_offset", "clock_kind")
        tau = rational(case["clock"]["radius_s"])
        require(tau >= 0, "clock_negative")
    rows = case["observations"]
    require(type(rows) is list and len(rows) <= 16, "observation_cap")
    points, ids, last = [], set(), None
    for row in rows:
        keys(row, ("id", "time_s", "interval_m"))
        identifier(row["id"])
        require(row["id"] not in ids, "duplicate_id")
        ids.add(row["id"])
        t = rational(row["time_s"])
        require(last is None or last < t, "time_order")
        last = t
        interval = row["interval_m"]
        if interval is None:
            points.append((t, None, None))
        else:
            require(type(interval) is list and len(interval) == 2, "interval_shape")
            lo, hi = map(rational, interval)
            require(lo <= hi, "interval_order")
            points.append((t, lo, hi))
    missing = [name for name in ("quantity", "motion", "clock") if case[name] is None]
    if not points:
        missing.append("observations")
    if any(lo is None for _, lo, _ in points):
        missing.append("observation_interval")
    return a, b, d, k, tau, points, missing


def pairs(items):
    out = {}
    for key, value in items:
        require(key not in out, "duplicate_json_key")
        out[key] = value
    return out


def load(path, cap=2_000_000):
    with Path(path).open("rb") as stream:
        data = stream.read(cap + 1)
    require(len(data) <= cap, "file_cap")
    try:
        return json.loads(
            data,
            object_pairs_hook=pairs,
            parse_constant=lambda _: require(False, "nonfinite_json"),
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Invalid("json_syntax") from exc


def digest(path):
    with Path(path).open("rb") as stream:
        data = stream.read(2_000_001)
    require(len(data) <= 2_000_000, "file_cap")
    return hashlib.sha256(data).hexdigest()


def frozen(packet, expected):
    require(digest(packet / "freeze.json") == expected, "freeze_digest")
    freeze = load(packet / "freeze.json")
    require(
        freeze["document_id"] == "reiyah.continuous-envelope.freeze"
        and freeze["version"] == "0.1.0",
        "freeze_identity",
    )
    for name, binding in freeze["files"].items():
        require(re.fullmatch(r"[A-Za-z0-9_.-]+", name), "freeze_path")
        require(digest(packet / name) == binding["sha256"], "file_binding:" + name)
        require(
            (packet / name).stat().st_size == binding["bytes"], "file_length:" + name
        )
    cases = load(packet / "cases.json")
    keys(cases, ("document_id", "version", "cases"))
    require(
        cases["document_id"] == "reiyah.continuous-envelope.cases"
        and cases["version"] == "0.1.0",
        "case_identity",
    )
    require(type(cases["cases"]) is list and 0 < len(cases["cases"]) <= 32, "case_cap")
    ids = []
    for case in cases["cases"]:
        parse_case(case)
        ids.append(case["id"])
    require(len(ids) == len(set(ids)), "duplicate_case")
    return cases["cases"]


def write_new(path, value):
    with Path(path).open("x") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")
