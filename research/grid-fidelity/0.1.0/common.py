"""Strict contract and serialization. No decision solver is shared here."""

import json
import re
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path


class Invalid(ValueError):
    pass


def require(condition, reason):
    if not condition:
        raise Invalid(reason)


def exact(value):
    require(isinstance(value, str) and len(value) <= 160, "rational_type")
    try:
        result = Fraction(value)
    except (ValueError, ZeroDivisionError) as exc:
        raise Invalid("rational_syntax") from exc
    require(str(result) == value, "rational_canonical")
    require(
        max(abs(result.numerator).bit_length(), result.denominator.bit_length()) <= 256,
        "rational_size",
    )
    return result


def keys(value, expected):
    require(type(value) is dict and set(value) == set(expected.split()), "fields")


def unique(pairs):
    result = {}
    for name, value in pairs:
        require(name not in result, "duplicate_json_key")
        result[name] = value
    return result


def load(path):
    return json.loads(Path(path).read_text(), object_pairs_hook=unique)


def write_new(path, value):
    with Path(path).open("x") as stream:
        stream.write(json.dumps(value, indent=2, sort_keys=True) + "\n")


@dataclass(frozen=True)
class Model:
    identifier: str
    times: tuple
    baseline: tuple
    known: dict
    available: tuple
    rate: Fraction
    tolerance: Fraction
    quantum: Fraction
    minimum_integer: int
    maximum_integer: int


def integer_value(model, value):
    encoded = value / model.quantum
    require(encoded.denominator == 1, "unrepresentable_value")
    require(
        model.minimum_integer <= encoded.numerator <= model.maximum_integer,
        "encoding_range",
    )
    return encoded.numerator


def parse(raw):
    keys(
        raw,
        "id native_times_s coarse_indices observations availability rate_bound_mps2 tolerance_mps value_domain",
    )
    require(
        isinstance(raw["id"], str)
        and re.fullmatch(r"[a-z0-9][a-z0-9-]{0,79}", raw["id"]),
        "id",
    )
    require(
        type(raw["native_times_s"]) is list and 2 <= len(raw["native_times_s"]) <= 65,
        "native_size",
    )
    times = tuple(map(exact, raw["native_times_s"]))
    require(all(a < b for a, b in zip(times, times[1:])), "native_order")
    coarse = raw["coarse_indices"]
    require(
        type(coarse) is list
        and all(type(i) is int and 0 <= i < len(times) for i in coarse),
        "coarse_membership",
    )
    require(
        coarse == sorted(set(coarse))
        and len(coarse) >= 2
        and coarse[0] == 0
        and coarse[-1] == len(times) - 1,
        "coarse_order",
    )
    domain = raw["value_domain"]
    keys(domain, "kind quantum_mps minimum_integer maximum_integer")
    require(domain["kind"] == "uniform_integer_encoding", "domain_kind")
    quantum = exact(domain["quantum_mps"])
    lower, upper = domain["minimum_integer"], domain["maximum_integer"]
    require(quantum > 0, "quantum_positive")
    require(
        type(lower) is int
        and type(upper) is int
        and lower <= upper
        and max(abs(lower).bit_length(), abs(upper).bit_length()) <= 64,
        "encoding_bounds",
    )
    rate, tolerance = exact(raw["rate_bound_mps2"]), exact(raw["tolerance_mps"])
    require(rate >= 0 and tolerance >= 0, "nonnegative_contract")
    available = raw["availability"]
    require(
        type(available) is list
        and len(available) == len(times)
        and all(x in ("available", "unavailable", "unregistered") for x in available),
        "availability",
    )
    known = {}
    require(type(raw["observations"]) is list, "observations_type")
    for row in raw["observations"]:
        keys(row, "index value_mps")
        i = row["index"]
        require(
            type(i) is int and 0 <= i < len(times) and i not in known,
            "observation_membership",
        )
        known[i] = exact(row["value_mps"])
    require(all(i in known for i in coarse), "coarse_anchor_missing")
    baseline = [None] * len(times)
    for a, b in zip(coarse, coarse[1:]):
        for i in range(a, b + 1):
            baseline[i] = known[a] + (known[b] - known[a]) * (times[i] - times[a]) / (
                times[b] - times[a]
            )
    model = Model(
        raw["id"],
        times,
        tuple(baseline),
        known,
        tuple(available),
        rate,
        tolerance,
        quantum,
        lower,
        upper,
    )
    for value in known.values():
        integer_value(model, value)
    return model


def witness_error(model, known, integers):
    require(
        type(integers) is list and len(integers) == len(model.times), "witness_size"
    )
    require(
        all(
            type(z) is int and model.minimum_integer <= z <= model.maximum_integer
            for z in integers
        ),
        "witness_encoding",
    )
    values = [model.quantum * z for z in integers]
    require(all(values[i] == v for i, v in known.items()), "witness_observation")
    require(
        all(
            abs(b - a) <= model.rate * (t1 - t0)
            for a, b, t0, t1 in zip(values, values[1:], model.times, model.times[1:])
        ),
        "witness_rate",
    )
    return max(abs(v - b) for v, b in zip(values, model.baseline))
