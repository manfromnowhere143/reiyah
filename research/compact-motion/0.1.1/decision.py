"""One recorded coordinate-export decision with an equally informed baseline."""

import argparse
import math
from pathlib import Path
import time

from audit import TARGET, TARGET_HEADER, rows
from binding import bind, digest, mat_rows, read_json, require, verify_files, write_new


def decision_bind(packet, sources, original, supplement):
    bind(packet, sources, original)
    require(
        digest(packet / "decision-freeze.json") == supplement,
        "decision_freeze_identity",
    )
    freeze = read_json(packet / "decision-freeze.json")
    require(freeze["analysis_freeze_sha256"] == original, "analysis_freeze_identity")
    verify_files(packet, freeze["files"])
    return freeze


def load_population(sources):
    csv = rows(sources / TARGET, TARGET_HEADER)
    mat = mat_rows(sources / TARGET.replace(".csv", ".mat"))
    require(mat[0] == TARGET_HEADER, "decision_columns")
    require(len(csv) == len(mat) - 1, "decision_row_count")
    require(
        all(a["Time"] == b[0] for a, b in zip(csv, mat[1:])), "decision_time_identity"
    )
    return [([a["Latitude"], a["Longitude"]], b[1:3]) for a, b in zip(csv, mat[1:])]


class Oracle:
    """Logical reveals; the full source file has already been acquired and decoded."""

    def __init__(self, population):
        self.population = population
        self.calls = []

    def reveal(self, index):
        require(
            index == len(self.calls) and index < len(self.population), "query_order"
        )
        self.calls.append(index)
        return self.population[index]


def interval_method(oracle):
    n = len(oracle.population)
    require(n > 0, "empty_population")
    lower, upper = 0, n
    trace = [
        {
            "queries": 0,
            "lower_mismatches": 0,
            "upper_mismatches": n,
            "decision": "unresolved",
        }
    ]
    for index in range(n):
        csv, mat = oracle.reveal(index)
        values = []
        for value in [*csv, *mat]:
            values.append(float(value) if value != "" else math.nan)
        pairs = list(zip(values[:2], values[2:]))
        if any(math.isfinite(a) and math.isfinite(b) and a != b for a, b in pairs):
            lower += 1
        elif all(math.isfinite(a) and math.isfinite(b) and a == b for a, b in pairs):
            upper -= 1
        decision = (
            "contradicted" if lower > 0 else "supported" if upper == 0 else "unresolved"
        )
        trace.append(
            {
                "queries": index + 1,
                "lower_mismatches": lower,
                "upper_mismatches": upper,
                "decision": decision,
            }
        )
        if decision != "unresolved":
            break
    return {"decision": decision, "queries": len(oracle.calls), "trace": trace}


def conventional_method(oracle):
    require(len(oracle.population) > 0, "empty_population")
    unknown = False
    for i in range(len(oracle.population)):
        text, original = oracle.reveal(i)
        pair = []
        available = True
        for left, right in zip(text, original):
            if left == "":
                available = False
                continue
            a, b = float(left), float(right)
            if not math.isfinite(a) or not math.isfinite(b):
                available = False
                continue
            pair.append((a, b))
        if any(left != right for left, right in pair):
            return {"decision": "contradicted", "queries": len(oracle.calls)}
        if not available:
            unknown = True
    return {
        "decision": "unresolved" if unknown else "supported",
        "queries": len(oracle.calls),
    }


def measured(function, population):
    oracle = Oracle(population)
    wall, cpu = time.perf_counter(), time.process_time()
    answer = function(oracle)
    return answer | {
        "wall_seconds": time.perf_counter() - wall,
        "process_cpu_seconds": time.process_time() - cpu,
        "query_indices": oracle.calls,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sources", type=Path, required=True)
    parser.add_argument("--freeze", required=True)
    parser.add_argument("--decision-freeze", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    start, cpu = time.perf_counter(), time.process_time()
    decision_bind(
        Path(__file__).parent, args.sources, args.freeze, args.decision_freeze
    )
    population = load_population(args.sources)
    shared = {
        "wall_seconds": time.perf_counter() - start,
        "process_cpu_seconds": time.process_time() - cpu,
    }
    result = {
        "document_id": "reiyah.compact-motion.decision",
        "version": "0.1.0",
        "status": "exploratory",
        "analysis_freeze_sha256": args.freeze,
        "decision_freeze_sha256": args.decision_freeze,
        "population_records": len(population),
        "allocated_decisions": 1,
        "shared_binding_and_decode": shared,
        "reiyah": measured(interval_method, population),
        "conventional": measured(conventional_method, population),
        "source_acquisition_charged_separately_once": True,
        "logical_reveal_is_not_physical_acquisition": True,
        "physical_clearance": "unresolved",
        "independent_baseline_authorship": False,
    }
    write_new(args.output, result)
    print(
        {
            "population": len(population),
            "reiyah": result["reiyah"]["decision"],
            "conventional": result["conventional"]["decision"],
        }
    )
