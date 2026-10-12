#!/usr/bin/env python3
"""Independent finite-world checker; no producer or engine imports.

Risks come from Fraction curve quadrature, including enumeration of all
within-tie acceptance permutations. Decisions come from complete label worlds;
certificates from distinguishing subsets; policy from a world-partition tree.
Canonical expected records are rebuilt and compared byte for byte.
"""

import argparse
from collections import Counter
from fractions import Fraction
from functools import lru_cache
import gzip
import hashlib
import itertools
import json
from pathlib import Path
import signal
import sys


PROTOCOL_SHA256 = "e3e134d7423a721fd673ee021cd5404f6b32cee7d0cefad322179a33899afd0d"
DEFAULT_PROTOCOL = Path(__file__).with_name("protocol.json")
GRID = ((1, 2), (2, 2), (3, 2), (1, 3), (2, 3))
NAMED_IDS = ("paper-four-row", "majority-three", "metric-convention", "identical-candidates")
MAX_LINE_BYTES = 262144


class Rejection(ValueError):
    """A declared input or reconstruction check failed."""


def canonical(record):
    return (json.dumps(record, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=True) + "\n").encode("ascii")


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def validate_labels(values, n):
    """Only complete, genuinely integer binary labels; never impute unknowns."""
    if type(n) is not int or n < 1:
        raise Rejection("label_domain: invalid population size")
    if type(values) not in (list, tuple) or len(values) != n:
        raise Rejection("label_domain: missing or wrong-length labels")
    if any(type(v) is not int or v not in (0, 1) for v in values):
        raise Rejection("label_domain: unavailable, nonbinary or noninteger label")
    return tuple(values)


def load_protocol(path):
    raw = Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != PROTOCOL_SHA256:
        raise Rejection("protocol_hash: frozen protocol bytes differ")
    obj = json.loads(raw)
    # Exact-byte pin rejects every unapproved structural or population change.
    if tuple((p["n"], p["k"]) for p in obj["population"]["grid"]) != GRID:
        raise Rejection("protocol_structure: grid differs")
    if tuple(c["id"] for c in obj["named_cases"]) != NAMED_IDS:
        raise Rejection("protocol_structure: named cases differ")
    for case in obj["named_cases"]:
        n = len(case["labels"])
        validate_labels(case["labels"], n)
        for prediction in case["prediction"]:
            validate_labels(prediction, n)
        for ranks in case["ranks"]:
            validate_ranks(ranks, n)
    return obj


def validate_ranks(ranks, n):
    if type(ranks) not in (list, tuple) or len(ranks) != n:
        raise Rejection("rank_domain: missing or wrong-length ranks")
    if any(type(r) is not int or not 0 <= r < n for r in ranks):
        raise Rejection("rank_domain: noninteger or out-of-range rank")
    if set(ranks) != set(range(max(ranks) + 1)):
        raise Rejection("rank_domain: ranks must be contiguous")


@lru_cache(None)
def domain(n):
    worlds = tuple(itertools.product((0, 1), repeat=n))
    histories = tuple(itertools.product((0, 1, 2), repeat=n))
    compatible = tuple(tuple(w for w, labels in enumerate(worlds)
                             if all(h == 0 or labels[i] == h - 1
                                    for i, h in enumerate(history)))
                       for history in histories)
    orders = tuple(itertools.permutations(range(n)))
    return worlds, histories, compatible, orders


@lru_cache(None)
def curve_risks(prediction, ranks):
    """Scaled area of cumulative error mass against accepted population mass."""
    n = len(prediction)
    validate_labels(prediction, n)
    validate_ranks(ranks, n)
    compatible_orders = tuple(order for order in itertools.permutations(range(n))
                              if all(ranks[order[t]] <= ranks[order[t + 1]]
                                     for t in range(n - 1)))
    risks = []
    for labels in domain(n)[0]:
        areas = []
        for order in compatible_orders:
            previous_x = Fraction(0)
            previous_y = Fraction(0)
            errors = 0
            area = Fraction(0)
            for accepted, row in enumerate(order, start=1):
                errors += int(prediction[row] != labels[row])
                x = Fraction(accepted, n)
                y = Fraction(errors, n)
                area += (x - previous_x) * (y + previous_y) / 2
                previous_x, previous_y = x, y
            areas.append(area)
        scaled = sum(areas, Fraction(0)) / len(areas) * (2 * n * n)
        if scaled.denominator != 1:
            raise Rejection("curve_integrality: tie-averaged scaled area not integral")
        risks.append(scaled.numerator)
    return tuple(risks)


@lru_cache(None)
def decision_analysis(n, winners):
    """Independent tree recursion on possible-world partitions, not bounds."""
    worlds, histories, compatible, orders = domain(n)

    @lru_cache(None)
    def solve(possible):
        values = {winners[w] for w in possible}
        if len(values) == 1:
            return next(iter(values)), 0, None
        alternatives = []
        for row in range(n):
            zero = tuple(w for w in possible if worlds[w][row] == 0)
            one = tuple(w for w in possible if worlds[w][row] == 1)
            if zero and one:
                alternatives.append((1 + max(solve(zero)[1], solve(one)[1]), row))
        if not alternatives:
            raise Rejection("tree_partition: unresolved world cannot be split")
        depth, query = min(alternatives)
        return None, depth, query

    history_results = tuple(solve(possible) for possible in compatible)
    history_index = {history: i for i, history in enumerate(histories)}
    subsets = tuple(subset for size in range(n + 1)
                    for subset in itertools.combinations(range(n), size))
    certificates = []
    policy_queries = []
    fixed_queries = []

    def fixed_count(labels, order):
        history = [0] * n
        used = 0
        while history_results[history_index[tuple(history)]][0] is None:
            row = order[used]
            history[row] = labels[row] + 1
            used += 1
        return used

    for w, labels in enumerate(worlds):
        # Direct distinguishing-subset enumeration never uses coefficient cover.
        for subset in subsets:
            possible = tuple(v for v, other in enumerate(worlds)
                             if all(other[row] == labels[row] for row in subset))
            if all(winners[v] == winners[w] for v in possible):
                certificates.append(len(subset))
                break
        history = [0] * n
        used = 0
        while True:
            winner, _, query = history_results[history_index[tuple(history)]]
            if winner is not None:
                break
            if query is None or history[query] != 0:
                raise Rejection("policy_access: query is unavailable or repeated")
            history[query] = labels[query] + 1
            used += 1
        policy_queries.append(used)
        fixed_queries.append(tuple(fixed_count(labels, order) for order in orders))
    return history_results, tuple(certificates), tuple(policy_queries), tuple(fixed_queries)


def expected_record(case_id, candidates):
    n = len(candidates[0][0])
    k = len(candidates)
    worlds, histories, compatible, _ = domain(n)
    by_model = tuple(curve_risks(prediction, ranks) for prediction, ranks in candidates)
    risks = tuple(tuple(model[w] for model in by_model) for w in range(len(worlds)))
    winners = tuple(min(range(k), key=lambda model: (risk[model], model)) for risk in risks)
    analysis, certificates, policy_queries, fixed_queries = decision_analysis(n, winners)
    pairs = tuple(itertools.combinations(range(k), 2))
    differences = tuple(tuple(risks[w][j] - risks[w][m] for w in range(len(worlds)))
                        for j, m in pairs)
    records = []
    for h, possible in enumerate(compatible):
        bounds = [[min(diff[w] for w in possible), max(diff[w] for w in possible)]
                  for diff in differences]
        winner, depth, query = analysis[h]
        records.append({"bounds": bounds, "winner": winner, "depth": depth, "query": query})

    # Infer each affine label coefficient through directly integrated basis worlds.
    coefficients = tuple(tuple(model[1 << (n - 1 - row)] - model[0] for row in range(n))
                         for model in by_model)
    widths = [max(abs(coefficients[j][row] - coefficients[m][row]) for j, m in pairs)
              for row in range(n)]
    order = tuple(sorted(range(n), key=lambda row: (-widths[row], row)))
    order_index = domain(n)[3].index(order)
    width_queries = tuple(counts[order_index] for counts in fixed_queries)
    if any(cost < certificate for certificate, costs in zip(certificates, fixed_queries)
           for cost in costs):
        raise Rejection("certificate_lower_bound: fixed path shorter than witness")
    if any(cost < certificate for certificate, cost in zip(certificates, policy_queries)):
        raise Rejection("certificate_lower_bound: adaptive path shorter than witness")
    return {"id": list(case_id),
            "candidates": [{"prediction": list(p), "ranks": list(r)} for p, r in candidates],
            "risks": risks, "histories": records, "certificates": certificates,
            "policy_queries": policy_queries, "fixed_queries": fixed_queries,
            "width_queries": width_queries}


def grid_cases():
    for n, k in GRID:
        ranks = tuple(r for r in itertools.product(range(n), repeat=n)
                      if set(r) == set(range(max(r) + 1)))
        candidates = tuple((prediction, rank) for prediction in domain(n)[0] for rank in ranks)
        for index, chosen in enumerate(itertools.product(candidates, repeat=k)):
            yield (n, k, index), chosen


def named_cases(protocol):
    for case in protocol["named_cases"]:
        n, k = len(case["labels"]), len(case["prediction"])
        candidates = tuple((tuple(p), tuple(r)) for p, r in zip(case["prediction"], case["ranks"]))
        yield (n, k, case["id"]), candidates


def first_difference(actual, expected, path="$", limit=120):
    """Useful diagnostic only; acceptance always uses exact expected bytes."""
    # Expected tuples encode as JSON arrays; normalize without weakening input types.
    if isinstance(expected, tuple):
        expected = list(expected)
    if type(actual) is not type(expected):
        return path + ":type"
    if isinstance(expected, dict):
        if set(actual) != set(expected):
            return path + ":keys"
        for key in sorted(expected):
            difference = first_difference(actual[key], expected[key], path + "." + key)
            if difference:
                return difference[:limit]
    elif isinstance(expected, list):
        if len(actual) != len(expected):
            return path + ":length"
        for index, (a, e) in enumerate(zip(actual, expected)):
            difference = first_difference(a, e, path + "[" + str(index) + "]")
            if difference:
                return difference[:limit]
    elif actual != expected:
        return path + ":value"
    return None


HISTOGRAMS = ("certificate_size", "fixed_queries", "fixed_minus_certificate",
              "width_queries", "width_minus_certificate", "adaptive_queries",
              "adaptive_minus_certificate", "minimax_minus_max_certificate")


def empty_aggregate():
    return {"counts": Counter(), "histograms": {name: Counter() for name in HISTOGRAMS}}


def add_record(aggregate, record):
    counts = aggregate["counts"]
    histograms = aggregate["histograms"]
    counts.update({"cases": 1, "histories": len(record["histories"]),
                   "labelings": len(record["risks"]),
                   "fixed_paths": sum(len(costs) for costs in record["fixed_queries"]),
                   "resolved_histories": sum(h["winner"] is not None for h in record["histories"])})
    for w, certificate in enumerate(record["certificates"]):
        histograms["certificate_size"][certificate] += 1
        for cost in record["fixed_queries"][w]:
            histograms["fixed_queries"][cost] += 1
            histograms["fixed_minus_certificate"][cost - certificate] += 1
        for field, prefix in (("width_queries", "width"), ("policy_queries", "adaptive")):
            cost = record[field][w]
            histograms[prefix + "_queries"][cost] += 1
            histograms[prefix + "_minus_certificate"][cost - certificate] += 1
    gap = record["histories"][0]["depth"] - max(record["certificates"])
    histograms["minimax_minus_max_certificate"][gap] += 1


def freeze_aggregate(aggregate):
    return {"counts": dict(aggregate["counts"]),
            "histograms": {name: {str(key): value for key, value in sorted(counts.items()) if value}
                           for name, counts in aggregate["histograms"].items()}}


def named_summary(record, case):
    n = record["id"][0]
    w = domain(n)[0].index(tuple(case["labels"]))
    order_index = domain(n)[3].index(tuple(case["order"]))
    risks = record["risks"][w]
    return {"id": case["id"], "scaled_risks": risks, "scale": 2 * n * n,
            "winner": min(range(len(risks)), key=lambda m: (risks[m], m)),
            "minimum_certificate": record["certificates"][w],
            "declared_order_queries": record["fixed_queries"][w][order_index],
            "width_queries": record["width_queries"][w],
            "adaptive_queries": record["policy_queries"][w],
            "minimax_depth": record["histories"][0]["depth"],
            "maximum_certificate": max(record["certificates"]),
            "initial_universal_winner": record["histories"][0]["winner"]}


def verify_stream(path, cases, expected_count, protocol):
    with Path(path).open("rb") as compressed:
        header = compressed.read(10)
    # Canonical transport declares deflate, no optional header fields and mtime0.
    # The final XFL/OS bytes are compressor/platform metadata, not scientific data.
    if len(header) != 10 or header[:8] != b"\x1f\x8b\x08\x00\x00\x00\x00\x00":
        raise Rejection("gzip_header: require deflate, zero flags and mtime0")
    count = histories = worlds = pair_endpoints = decoded_bytes = 0
    h = hashlib.sha256()
    summaries = []
    total = empty_aggregate()
    grids = {}
    with gzip.open(path, "rb") as stream:
        for case_id, candidates in cases:
            wanted = expected_record(case_id, candidates)
            line = stream.readline(MAX_LINE_BYTES + 1)
            if not line:
                raise Rejection("trace_truncated: missing case " + str(case_id))
            if len(line) > MAX_LINE_BYTES:
                raise Rejection("trace_line_limit: excessive line")
            expected = canonical(wanted)
            if line != expected:
                try:
                    difference = first_difference(json.loads(line), wanted)
                except (UnicodeError, ValueError, TypeError):
                    difference = "invalid_json"
                raise Rejection("trace_mismatch:" + str(case_id) + ":" + (difference or "noncanonical"))
            h.update(line)
            decoded_bytes += len(line)
            count += 1
            histories += len(wanted["histories"])
            worlds += len(wanted["risks"])
            pair_endpoints += 2 * len(wanted["histories"]) * (len(candidates) * (len(candidates) - 1) // 2)
            if isinstance(case_id[2], str):
                case = next(c for c in protocol["named_cases"] if c["id"] == case_id[2])
                summaries.append(named_summary(wanted, case))
            else:
                grid = tuple(case_id[:2])
                add_record(total, wanted)
                add_record(grids.setdefault(grid, empty_aggregate()), wanted)
        if stream.read(1):
            raise Rejection("trace_extra: bytes after declared population")
    if count != expected_count:
        raise Rejection("population_count: incorrect reconstructed population")
    return {"cases": count, "histories": histories, "full_label_worlds": worlds,
            "pair_endpoints": pair_endpoints, "canonical_sha256": h.hexdigest(),
            "gzip_sha256": digest(path), "named_summaries": summaries,
            "metadata": {"uncompressed_sha256": h.hexdigest(), "uncompressed_bytes": decoded_bytes,
                         "gzip_sha256": digest(path), "gzip_bytes": Path(path).stat().st_size},
            "population": freeze_aggregate(total),
            "grids": [{"n": n, "k": k, **freeze_aggregate(grids[(n, k)])}
                      for n, k in GRID if (n, k) in grids]}


def verify_result(path, grid, named):
    result = json.loads(Path(path).read_bytes())
    allowed = {"population", "grids", "named_cases", "trace", "named_trace", "version",
               "artifact_id", "lifecycle_status", "protocol_sha256", "scope"}
    if type(result) is not dict or set(result) != allowed:
        raise Rejection("result_structure: missing or extra result properties")
    if result["protocol_sha256"] != PROTOCOL_SHA256 or result["version"] != "0.1.0":
        raise Rejection("result_identity: protocol or version differs")
    for field in ("artifact_id", "lifecycle_status", "scope"):
        if type(result[field]) is not str or not result[field]:
            raise Rejection("result_structure: invalid descriptive field " + field)
    expected = {"population": grid["population"], "grids": grid["grids"],
                "named_cases": named["named_summaries"], "trace": grid["metadata"],
                "named_trace": named["metadata"]}
    for field, value in expected.items():
        if canonical(result[field]) != canonical(value):
            difference = first_difference(result[field], value)
            raise Rejection("result_mismatch:" + field + ":" + str(difference))
    return {"sha256": digest(path), "numeric_fields": list(expected),
            "descriptive_fields": "bound by result digest; not scientific acceptance"}


def timeout_handler(_signum, _frame):
    raise Rejection("resource_limit: 150-second execution cap")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trace", type=Path)
    parser.add_argument("--named", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--result", type=Path)
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument("--named-only", action="store_true")
    args = parser.parse_args(argv)
    if not args.named_only and args.trace is None:
        parser.error("--trace is required unless --named-only")
    if args.named_only and args.trace is not None:
        parser.error("--named-only must not include --trace")
    if args.named_only and args.result is not None:
        parser.error("--result requires complete grid verification")
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(150)
    report = {"artifact_id": "reiyah.exact-choice-baseline.verification", "version": "0.1.0",
              "protocol_sha256": PROTOCOL_SHA256, "checker_sha256": digest(__file__),
              "mode": "named-only" if args.named_only else "complete", "status": "invalid"}
    try:
        protocol = load_protocol(args.protocol)
        if not args.named_only:
            report["grid"] = verify_stream(args.trace, grid_cases(), 12700, protocol)
        report["named"] = verify_stream(args.named, named_cases(protocol), 4, protocol)
        if args.result is not None:
            report["result"] = verify_result(args.result, report["grid"], report["named"])
        report["checks"] = ["exact_pinned_protocol", "fraction_curve_tie_enumeration",
                            "complete_world_pair_bounds_and_tie_winner", "distinguishing_subsets",
                            "independent_world_partition_tree", "all_fixed_and_width_paths",
                            "exact_canonical_bytes_and_population", "pinned_label_domain"]
        if args.result is not None:
            report["checks"].append("reconstructed_aggregate_histograms_named_values_and_file_metadata")
        report["status"] = "supported"
    except (Rejection, OSError, EOFError, ValueError, KeyError, TypeError) as error:
        report["failure"] = str(error)
    finally:
        signal.alarm(0)
    args.output.write_bytes(canonical(report))
    print(json.dumps({"status": report["status"], "failure": report.get("failure")}))
    return 0 if report["status"] == "supported" else 1


if __name__ == "__main__":
    sys.exit(main())
