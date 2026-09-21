"""Conventional exact decimal sums with explicit missing-score endpoints."""

from decimal import Decimal
from fractions import Fraction
import json


def pairs(items):
    result = {}
    for key, item in items:
        if key in result:
            raise ValueError("duplicate_json_key")
        result[key] = item
    return result


def bad_number(value):
    raise ValueError("nonfinite_json_number")


def read(payload):
    return json.loads(
        payload, parse_float=Decimal, parse_constant=bad_number, object_pairs_hook=pairs
    )


def records(document, n):
    if not isinstance(document, dict) or not isinstance(
        document.get("_checkpoint"), dict
    ):
        raise ValueError("checkpoint")
    rows = document["_checkpoint"].get("records")
    if not isinstance(rows, list) or len(rows) > n:
        raise ValueError("record_count")
    ids, output = set(), []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("record")
        names = tuple(
            row.get(k) for k in ("route_id", "scenario_name", "town_name", "weather_id")
        )
        if any(type(s) is not str or not s or len(s) > 256 for s in names):
            raise ValueError("record_identity")
        if names[0] in ids:
            raise ValueError("duplicate_route")
        ids.add(names[0])
        state = row.get("status")
        if type(state) is not str or (
            state not in {"Completed", "Perfect", "Crashed"}
            and not state.startswith("Failed")
        ):
            raise ValueError("unavailable_status")
        events = row.get("infractions")
        if (
            not isinstance(events, dict)
            or not events
            or not all(
                isinstance(k, str) and type(v) is list for k, v in events.items()
            )
        ):
            raise ValueError("infractions")
        metric = row.get("scores")
        if not isinstance(metric, dict):
            raise ValueError("scores")
        number = metric.get("score_composed")
        if type(number) not in (int, Decimal):
            raise ValueError("score_type")
        number = Decimal(number)
        if not number.is_finite() or number < 0 or number > 100:
            raise ValueError("score_range")
        exact = Fraction(number)
        if max(exact.numerator.bit_length(), exact.denominator.bit_length()) > 512:
            raise ValueError("score_range")
        output.append((names, number))
    return output


def scaled_total(rows):
    places = max([0] + [-x[1].as_tuple().exponent for x in rows])
    scale = 10**places
    total = 0
    for _, value in rows:
        sign, digits, exponent = value.as_tuple()
        coefficient = 0
        for digit in digits:
            coefficient = coefficient * 10 + digit
        total += (-1 if sign else 1) * coefficient * 10 ** (exponent + places)
    return Fraction(total, scale)


def calculate(base_document, tiny_document, n=220):
    if type(n) is not int or not 1 <= n <= 220:
        raise ValueError("population_size")
    a, b = records(base_document, n), records(tiny_document, n)
    ai = {row[0][0]: row[0] for row in a}
    bi = {row[0][0]: row[0] for row in b}
    intersection = ai.keys() & bi.keys()
    population = ai.keys() | bi.keys()
    if len(population) > n:
        raise ValueError("union_exceeds_population")
    for key in intersection:
        if ai[key] != bi[key]:
            raise ValueError("metadata_conflict")
    sa, sb = scaled_total(a), scaled_total(b)
    lower = (sa - sb - 100 * (n - len(b))) / n
    upper = (sa - sb + 100 * (n - len(a))) / n
    decision = "supported" if lower > 0 else "excluded" if upper <= 0 else "unresolved"
    return {
        "summary": {
            "n": n,
            "base_count": len(a),
            "tiny_count": len(b),
            "shared_count": len(intersection),
            "union_count": len(population),
            "original_complete_pair": "supported"
            if len(a) == len(b) == len(intersection) == n
            else "blocked",
            "base_sum": str(sa),
            "tiny_sum": str(sb),
            "zero_fill_means": [str(sa / n), str(sb / n)],
            "difference_bounds": [str(lower), str(upper)],
            "conditional_aggregate_decision": decision,
            "missing": [n - len(a), n - len(b)],
            "scope": "Conditional recorded-score completion; official cohort and execution binding unresolved",
        }
    }
