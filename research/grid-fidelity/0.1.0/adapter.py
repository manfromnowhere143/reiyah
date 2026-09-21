"""Bound replay of previously exposed material, never a new empirical sample."""

import hashlib
from fractions import Fraction
from pathlib import Path

from cases import authored, case
from common import exact, integer_value, keys, load, parse, require

ROOT = Path(__file__).resolve().parent


def digest(path):
    data = Path(path).read_bytes()
    return dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())


def recorded(source_root):
    source_root = Path(source_root)
    ledger = load(ROOT / "inputs.json")
    for name, identity in ledger["files"].items():
        require(digest(source_root / name) == identity, "source_identity:" + name)
    decoded = load(source_root / "decoded-01.json")
    require(decoded["selection"] == list(range(1, 102)), "exposed_selection")
    require(decoded["source_slice"] == ledger["source_slice"], "source_slice")
    rows = decoded["rows"]
    selected = [rows[i] for i in decoded["selection"]]
    require(
        all(
            row["status"] == "eligible" and row["navigation_status"] == 4
            for row in selected
        ),
        "eligibility",
    )
    require(
        all(b["time_ms"] - a["time_ms"] == 10 for a, b in zip(selected, selected[1:])),
        "native_spacing",
    )
    result = []
    for part in range(5):
        chunk = selected[part * 20 : part * 20 + 21]
        times = [Fraction(r["time_ms"] - chunk[0]["time_ms"], 1000) for r in chunk]
        values = [Fraction(r["north_velocity_units"], 10000) for r in chunk]
        row = case(
            "exposed-tail-" + str(part),
            times,
            values,
            [0, 10, 20],
            5,
            "1/20",
            quantum="1/10000",
            limits=(-8388607, 8388607),
        )
        row["source_indices"] = [r["index"] for r in chunk]
        row["evidence_kind"] = "exposed_recorded_development"
        result.append(row)
    return result


def validate_case(row):
    keys(row, "model oracle_values_mps source_indices evidence_kind")
    require(
        row["evidence_kind"]
        in ("authored_development", "exposed_recorded_development"),
        "evidence_kind",
    )
    model = parse(row["model"])
    require(
        type(row["oracle_values_mps"]) is list
        and len(row["oracle_values_mps"]) == len(model.times),
        "oracle_size",
    )
    for value in row["oracle_values_mps"]:
        integer_value(model, exact(value))
    indices = row["source_indices"]
    require(
        type(indices) is list
        and len(indices) == len(model.times)
        and all(type(i) is int and i >= 0 for i in indices)
        and len(set(indices)) == len(indices),
        "oracle_source_mapping",
    )
    require(
        all(exact(row["oracle_values_mps"][i]) == v for i, v in model.known.items()),
        "initial_source_binding",
    )
    return model


def all_cases(source_root=None):
    rows = authored() + ([] if source_root is None else recorded(source_root))
    require(len({row["model"]["id"] for row in rows}) == len(rows), "case_identity")
    for row in rows:
        validate_case(row)
    return rows
