"""Reuse the existing finite-population primitive on four explicit blocks."""

from fractions import Fraction as F
import importlib.util
import json
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "reiyah_existing_sequential",
    Path(__file__).resolve().parents[2] / "sequential-audit/0.1.0/methods.py",
)
EXISTING = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EXISTING)


def unique(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError("duplicate_json_key")
        out[key] = value
    return out


def constant(value):
    raise ValueError("nonfinite_json_number")


def read(payload):
    return json.loads(
        payload, parse_float=F, parse_constant=constant, object_pairs_hook=unique
    )


def validate_document(document, n):
    if type(document) is not dict or type(document.get("_checkpoint")) is not dict:
        raise ValueError("checkpoint")
    rows = document["_checkpoint"].get("records")
    if type(rows) is not list or len(rows) > n:
        raise ValueError("record_count")
    result = {}
    for row in rows:
        if type(row) is not dict:
            raise ValueError("record")
        labels = {}
        for key in ("route_id", "scenario_name", "town_name", "weather_id"):
            value = row.get(key)
            if type(value) is not str or not 1 <= len(value) <= 256:
                raise ValueError("record_identity")
            labels[key] = value
        rid = labels["route_id"]
        if rid in result:
            raise ValueError("duplicate_route")
        status = row.get("status")
        if type(status) is not str or not (
            status in ("Completed", "Perfect", "Crashed") or status.startswith("Failed")
        ):
            raise ValueError("unavailable_status")
        infractions = row.get("infractions")
        if (
            type(infractions) is not dict
            or not infractions
            or any(
                type(k) is not str or type(v) is not list
                for k, v in infractions.items()
            )
        ):
            raise ValueError("infractions")
        scores = row.get("scores")
        if type(scores) is not dict:
            raise ValueError("scores")
        score = scores.get("score_composed")
        if type(score) not in (int, F):
            raise ValueError("score_type")
        score = F(score)
        if (
            not 0 <= score <= 100
            or max(score.numerator.bit_length(), score.denominator.bit_length()) > 512
        ):
            raise ValueError("score_range")
        result[rid] = {"labels": labels, "score": score}
    return result


def calculate(base_document, tiny_document, n=220):
    if type(n) is not int or not 1 <= n <= 220:
        raise ValueError("population_size")
    base = validate_document(base_document, n)
    tiny = validate_document(tiny_document, n)
    shared, union = set(base) & set(tiny), set(base) | set(tiny)
    if len(union) > n:
        raise ValueError("union_exceeds_population")
    if any(base[r]["labels"] != tiny[r]["labels"] for r in shared):
        raise ValueError("metadata_conflict")
    b, t = len(base), len(tiny)
    sb = sum((r["score"] for r in base.values()), F(0))
    st = sum((r["score"] for r in tiny.values()), F(0))
    units = []

    def add(identity, count, lo, hi, state):
        if count:
            units.append(
                {
                    "id": identity,
                    "weight": str(F(count, 2 * n)),
                    "lower": str(lo),
                    "upper": str(hi),
                    "proxy": "0",
                    "status": state,
                    "cluster": identity,
                }
            )

    if b:
        value = 2 * sb / (100 * b) - 1
        add("base_observed", b, value, value, "observed")
    if t:
        value = 1 - 2 * st / (100 * t)
        add("tiny_observed", t, value, value, "observed")
    add("base_missing", n - b, F(-1), F(1), "missing")
    add("tiny_missing", n - t, F(-1), F(1), "missing")
    population = {
        "id": "recorded-score-completion",
        "version": "0.1.0",
        "threshold": "0",
        "purpose": "conditional missing-score diagnostic",
        "units": units,
    }
    EXISTING.validate(population)
    decision, lower, upper = EXISTING.logical(population, set(range(len(units))))
    summary = {
        "n": n,
        "base_count": b,
        "tiny_count": t,
        "shared_count": len(shared),
        "union_count": len(union),
        "original_complete_pair": "supported"
        if b == t == len(shared) == n
        else "blocked",
        "base_sum": str(sb),
        "tiny_sum": str(st),
        "zero_fill_means": [str(sb / n), str(st / n)],
        "difference_bounds": [str(100 * lower), str(100 * upper)],
        "conditional_aggregate_decision": decision,
        "missing": [n - b, n - t],
        "scope": "Conditional recorded-score completion; official cohort and execution binding unresolved",
    }
    return {"summary": summary, "population": population}
